<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import RadiationChart from '../components/RadiationChart.vue'
import { useDatasetStore } from '../stores/useDatasetStore'
import { getAnomalies, getMeasurements, getSummary } from '../services/api'

interface Measurement {
  timestamp: string
  radiationLevel: number
  sensorId: string
  location: string
  temperature: number | null
  humidity: number | null
  isAnomaly: boolean
  anomalyScore: number
  anomalyType: string
  status: string
}

interface Summary {
  datasetName: string
  totalMeasurements: number
  totalAnomalies: number
  currentLevel: number
  averageLevel: number
  maxLevel: number
  minLevel: number
  threshold: number
  activeAlert: boolean
  lastUpdated: string
}

type DatasetRecord = Record<string, string | number | boolean | null | undefined>

const router = useRouter()
const { datasetState } = useDatasetStore()

const MAX_CHART_POINTS = 500
const RANGE_TOLERANCE_MS = 15 * 60 * 1000

const period = ref('Month')
const quickRange = ref('24h')
const selectedStatus = ref('All statuses')
const searchQuery = ref('')
const fromDate = ref('')
const toDate = ref('')
const rangeUnavailableMessage = ref('')

const backendMeasurements = ref<Measurement[]>([])
const backendAnomalies = ref<Measurement[]>([])
const summary = ref<Summary | null>(null)

const isLoading = ref(true)
const errorMessage = ref('')

const isCustomDatasetLoaded = computed(() => datasetState.isLoaded)

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) return '0.0000'
  return Number(value).toFixed(4)
}

function formatChartLabel(timestamp: string) {
  const parts = timestamp.split(' ')
  return parts[1]?.slice(0, 5) ?? timestamp
}

function parseTimestamp(timestamp: string) {
  return new Date(timestamp.replace(' ', 'T'))
}

function normalizeText(value: unknown, fallback: string) {
  const text = String(value ?? '').trim()
  return text || fallback
}

function getRecordValue(record: DatasetRecord, candidates: string[]) {
  const normalizedEntries = Object.entries(record).reduce<Record<string, unknown>>((acc, [key, value]) => {
    acc[key.toLowerCase().trim()] = value
    return acc
  }, {})

  for (const candidate of candidates) {
    const key = candidate.toLowerCase().trim()

    if (key in normalizedEntries) {
      return normalizedEntries[key]
    }
  }

  return undefined
}

function parseOptionalNumber(value: unknown) {
  if (value === null || value === undefined || value === '') return null

  const parsed = Number(String(value).replace(',', '.'))
  return Number.isFinite(parsed) ? parsed : null
}

function parseBooleanValue(value: unknown) {
  if (value === null || value === undefined || value === '') return null

  if (typeof value === 'boolean') return value

  const normalized = String(value).toLowerCase().trim()

  if (['1', 'true', 'yes', 'y', 'anomaly', 'anomalous'].includes(normalized)) {
    return true
  }

  if (['0', 'false', 'no', 'n', 'normal'].includes(normalized)) {
    return false
  }

  return null
}

function formatAnomalyType(type: string | null | undefined) {
  if (!type || type === 'normal') return 'Anomaly'

  const labels: Record<string, string> = {
    threshold_detection: 'Threshold Detection',
    spike: 'Spike',
    sustained_increase: 'Sustained Increase',
    sensor_drop: 'Sensor Drop',
  }

  return labels[type] ?? type.replaceAll('_', ' ')
}

function getStatusType(status: string | null | undefined) {
  if (status === 'Critical') return 'critical'
  if (status === 'High') return 'high'
  if (status === 'Normal') return 'normal'

  return 'alert'
}

function getQuickRangeMs(range: string) {
  if (range === '24h') return 24 * 60 * 60 * 1000
  if (range === '1W') return 7 * 24 * 60 * 60 * 1000
  if (range === '14d') return 14 * 24 * 60 * 60 * 1000

  return 0
}

function formatDuration(milliseconds: number) {
  const totalMinutes = Math.max(Math.floor(milliseconds / (1000 * 60)), 1)
  const totalHours = Math.floor(totalMinutes / 60)
  const days = Math.floor(totalHours / 24)
  const hours = totalHours % 24

  if (days > 0 && hours > 0) {
    return `${days}d ${hours}h`
  }

  if (days > 0) {
    return `${days}d`
  }

  if (totalHours > 0) {
    return `${totalHours}h`
  }

  return `${totalMinutes}min`
}

function hasCustomDateRange() {
  return Boolean(fromDate.value || toDate.value)
}

function isInsideDateRange(timestamp: string) {
  const itemDate = parseTimestamp(timestamp)

  if (Number.isNaN(itemDate.getTime())) {
    return true
  }

  if (fromDate.value) {
    const startDate = new Date(`${fromDate.value}T00:00:00`)

    if (itemDate < startDate) {
      return false
    }
  }

  if (toDate.value) {
    const endDate = new Date(`${toDate.value}T23:59:59`)

    if (itemDate > endDate) {
      return false
    }
  }

  return true
}

function reduceChartPoints(rows: Measurement[]) {
  if (rows.length <= MAX_CHART_POINTS) {
    return rows
  }

  const step = Math.ceil(rows.length / MAX_CHART_POINTS)

  return rows.filter((_, index) => {
    return index % step === 0 || index === rows.length - 1
  })
}

const activeThreshold = computed(() => {
  return summary.value?.threshold ?? datasetState.threshold ?? 0.18
})

const uploadedMeasurements = computed<Measurement[]>(() => {
  if (!datasetState.isLoaded) return []

  const threshold = activeThreshold.value

  const baseRows = datasetState.rows.map((row) => {
    const record = row.record as DatasetRecord
    const radiationLevel = Number(row.value)

    const explicitAnomaly = parseBooleanValue(getRecordValue(record, [
      'is_anomaly',
      'ground_truth',
      'ground_truth_anomaly',
      'label',
      'target',
    ]))

    const isAnomaly = explicitAnomaly ?? radiationLevel > threshold

    const rawType = normalizeText(
        getRecordValue(record, ['anomaly_type', 'type', 'event_type']),
        isAnomaly ? 'threshold_detection' : 'normal',
    )

    const anomalyType = isAnomaly ? rawType.replace('normal', 'threshold_detection') : 'normal'

    return {
      timestamp: row.label,
      radiationLevel,
      sensorId: normalizeText(
          getRecordValue(record, ['sensor_id', 'sensor', 'sensor_name', 'detector', 'device', 'station']),
          'Uploaded CSV',
      ),
      location: normalizeText(
          getRecordValue(record, ['location', 'place', 'room', 'site']),
          'Uploaded dataset',
      ),
      temperature: parseOptionalNumber(
          getRecordValue(record, ['temperature_c', 'temperature', 'temp', 'temp_c']),
      ),
      humidity: parseOptionalNumber(
          getRecordValue(record, ['humidity_percent', 'humidity', 'rh', 'relative_humidity']),
      ),
      isAnomaly,
      anomalyScore: 0,
      anomalyType,
      status: 'Normal',
    }
  })

  const distances = baseRows.map((row) => Math.max(0, row.radiationLevel - threshold))
  const maxDistance = Math.max(...distances, 0)

  return baseRows.map((row, index) => {
    const anomalyScore = maxDistance > 0
        ? Number((distances[index] / maxDistance).toFixed(3))
        : 0

    let status = 'Normal'

    if (row.isAnomaly) {
      status = threshold > 0 && row.radiationLevel >= threshold * 2 ? 'Critical' : 'High'
    }

    return {
      ...row,
      anomalyScore,
      status,
    }
  })
})

const allMeasurements = computed(() => {
  if (isCustomDatasetLoaded.value) {
    return uploadedMeasurements.value
  }

  return backendMeasurements.value
})

const allAnomalies = computed(() => {
  if (isCustomDatasetLoaded.value) {
    return uploadedMeasurements.value
        .filter((item) => item.isAnomaly)
        .sort((a, b) => parseTimestamp(b.timestamp).getTime() - parseTimestamp(a.timestamp).getTime())
  }

  return backendAnomalies.value
})

const activeDatasetName = computed(() => {
  if (isCustomDatasetLoaded.value) {
    return datasetState.name
  }

  return summary.value?.datasetName ?? 'Dataset loading...'
})

const datasetTimeRange = computed(() => {
  const timestamps = allMeasurements.value
      .map((item) => parseTimestamp(item.timestamp))
      .filter((date) => !Number.isNaN(date.getTime()))
      .sort((a, b) => a.getTime() - b.getTime())

  if (!timestamps.length) {
    return null
  }

  const start = timestamps[0]
  const end = timestamps[timestamps.length - 1]
  const durationMs = Math.max(end.getTime() - start.getTime(), 0)

  return {
    start,
    end,
    durationMs,
    label: formatDuration(durationMs),
  }
})

function isInsideSelectedTimeRange(timestamp: string) {
  if (hasCustomDateRange()) {
    return isInsideDateRange(timestamp)
  }

  const datasetRange = datasetTimeRange.value

  if (!datasetRange) {
    return true
  }

  const selectedRangeMs = getQuickRangeMs(quickRange.value)

  if (!selectedRangeMs) {
    return true
  }

  const rangeStart = new Date(datasetRange.end)
  rangeStart.setTime(datasetRange.end.getTime() - selectedRangeMs)

  const itemTimestamp = parseTimestamp(timestamp)

  if (Number.isNaN(itemTimestamp.getTime())) {
    return true
  }

  return itemTimestamp >= rangeStart
}

const rangeFilteredMeasurements = computed(() =>
    allMeasurements.value.filter((item) => isInsideSelectedTimeRange(item.timestamp)),
)

const chartWarning = computed(() => {
  if (rangeUnavailableMessage.value) {
    return rangeUnavailableMessage.value
  }

  if (
      hasCustomDateRange() &&
      allMeasurements.value.length > 0 &&
      rangeFilteredMeasurements.value.length === 0
  ) {
    return 'No chart data found for selected date range. Showing full available dataset.'
  }

  return ''
})

const chartMeasurements = computed(() => {
  const selectedRows = rangeFilteredMeasurements.value.length
      ? rangeFilteredMeasurements.value
      : allMeasurements.value

  return reduceChartPoints(selectedRows)
})

const chartLabels = computed(() =>
    chartMeasurements.value.map((item) => formatChartLabel(item.timestamp)),
)

const chartValues = computed(() =>
    chartMeasurements.value.map((item) => item.radiationLevel),
)

const chartAnomalyFlags = computed(() =>
    chartMeasurements.value.map((item) => item.isAnomaly),
)

const chartRenderKey = computed(() => {
  const firstLabel = chartLabels.value[0] ?? 'empty'
  const lastLabel = chartLabels.value[chartLabels.value.length - 1] ?? 'empty'

  return [
    activeDatasetName.value,
    quickRange.value,
    fromDate.value,
    toDate.value,
    chartValues.value.length,
    firstLabel,
    lastLabel,
  ].join('-')
})

const filteredAnomalies = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return allAnomalies.value.filter((item) => {
    const statusMatches =
        selectedStatus.value === 'All statuses' ||
        item.status.toLowerCase() === selectedStatus.value.toLowerCase()

    const dateMatches = isInsideSelectedTimeRange(item.timestamp)

    const queryMatches =
        !query ||
        [
          item.timestamp,
          item.location,
          item.sensorId,
          item.status,
          item.anomalyType,
          formatAnomalyType(item.anomalyType),
          String(item.radiationLevel),
          String(item.anomalyScore),
        ]
            .join(' ')
            .toLowerCase()
            .includes(query)

    return statusMatches && dateMatches && queryMatches
  })
})

const anomalyRowsTop = computed(() =>
    filteredAnomalies.value.slice(0, 2).map((item) => ({
      timestamp: item.timestamp,
      level: `${formatNumber(item.radiationLevel)} µSv/h`,
      status: item.status,
      statusType: getStatusType(item.status),
      scoreLeft: 'Score',
      scoreRight: Number(item.anomalyScore ?? 0).toFixed(2),
    })),
)

const anomalyRowsOverview = computed(() =>
    filteredAnomalies.value.map((item) => ({
      timestamp: item.timestamp,
      level: `${formatNumber(item.radiationLevel)} µSv/h`,
      score: Number(item.anomalyScore ?? 0).toFixed(2),
      status: item.status,
      statusType: getStatusType(item.status),
    })),
)

const totalEventsLabel = computed(() =>
    `${filteredAnomalies.value.length} Total Events`,
)

const dateRangeLabel = computed(() => {
  if (fromDate.value || toDate.value) {
    return `${fromDate.value || 'Start'} → ${toDate.value || 'End'}`
  }

  return quickRange.value
})

function setQuickRange(range: string) {
  fromDate.value = ''
  toDate.value = ''

  const selectedRangeMs = getQuickRangeMs(range)
  const datasetRange = datasetTimeRange.value

  if (
      selectedRangeMs > 0 &&
      datasetRange &&
      datasetRange.durationMs + RANGE_TOLERANCE_MS < selectedRangeMs
  ) {
    rangeUnavailableMessage.value = `Dataset contains only ${datasetRange.label}, so ${range} range is not available.`
    return
  }

  quickRange.value = range
  rangeUnavailableMessage.value = ''
}

function applyCustomDateRange() {
  quickRange.value = 'Custom'
  rangeUnavailableMessage.value = ''
}

const resetFilters = () => {
  period.value = 'Month'
  quickRange.value = '24h'
  selectedStatus.value = 'All statuses'
  searchQuery.value = ''
  fromDate.value = ''
  toDate.value = ''
  rangeUnavailableMessage.value = ''
}

async function loadAnomaliesPage() {
  try {
    isLoading.value = true
    errorMessage.value = ''

    const [measurementsResponse, anomaliesResponse, summaryResponse] = await Promise.all([
      getMeasurements(10000),
      getAnomalies(500),
      getSummary(),
    ])

    backendMeasurements.value = measurementsResponse as Measurement[]
    backendAnomalies.value = anomaliesResponse as Measurement[]
    summary.value = summaryResponse as Summary
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Backend data could not be loaded. Check if FastAPI is running.'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadAnomaliesPage()
})
</script>

<template>
  <MainLayout>
    <div class="anomalies-page">
      <section class="hero-panel">
        <h1>Anomalies</h1>

        <div class="toolbar">
          <button class="tool-button tool-button--active">{{ period }}</button>

          <label
              class="date-trigger"
              :class="{ 'date-trigger--selected': fromDate }"
          >
            <span>{{ fromDate || 'From Date' }}</span>
            <input
                v-model="fromDate"
                class="date-trigger__input"
                type="date"
                @change="applyCustomDateRange"
            />
          </label>

          <label
              class="date-trigger"
              :class="{ 'date-trigger--selected': toDate }"
          >
            <span>{{ toDate || 'To Date' }}</span>
            <input
                v-model="toDate"
                class="date-trigger__input"
                type="date"
                @change="applyCustomDateRange"
            />
          </label>

          <button class="tool-button tool-button--ghost" @click="resetFilters">Reset</button>
        </div>

        <div class="search-row">
          <input
              v-model="searchQuery"
              class="search-box"
              placeholder="Search anomalies"
              type="search"
          />

          <div class="chips">
            <button
                class="chip"
                :class="{ 'chip--active': selectedStatus === 'Critical' }"
                type="button"
                @click="selectedStatus = 'Critical'"
            >
              Critical
            </button>

            <button
                class="chip"
                :class="{ 'chip--active': selectedStatus === 'High' }"
                type="button"
                @click="selectedStatus = 'High'"
            >
              High
            </button>

            <button
                class="chip"
                :class="{ 'chip--active': selectedStatus === 'All statuses' }"
                type="button"
                @click="selectedStatus = 'All statuses'"
            >
              All
            </button>
          </div>

          <div class="source-box">
            <span>Source:</span>
            <span class="source-dot"></span>
            <strong>{{ activeDatasetName }}</strong>
            <button class="tool-button tool-button--small" @click="router.push('/dataset')">View</button>
          </div>
        </div>

        <div v-if="isLoading" class="table-panel table-panel--top">
          <div class="table-footer">Loading anomalies...</div>
        </div>

        <div v-else-if="errorMessage" class="table-panel table-panel--top">
          <div class="table-footer">{{ errorMessage }}</div>
        </div>

        <div v-else class="table-panel table-panel--top">
          <div class="table-head">
            <span>Timestamp</span>
            <span>Radiation Level</span>
            <span>Status</span>
            <span>Anomaly Score</span>
          </div>

          <div v-for="row in anomalyRowsTop" :key="row.timestamp" class="table-row">
            <span class="cell-timestamp">
              <i class="row-dot"></i>
              {{ row.timestamp }}
            </span>

            <span class="cell-level">{{ row.level }}</span>

            <span class="cell-status">
              <span
                  class="status-pill"
                  :class="`status-pill--${row.statusType}`"
              >
                {{ row.status }}
              </span>
            </span>

            <span class="cell-score">
              <span class="score-left">{{ row.scoreLeft }}</span>
              <span class="score-bar"></span>
              <span class="score-right">{{ row.scoreRight }}</span>
            </span>
          </div>

          <div v-if="!anomalyRowsTop.length" class="table-row">
            <span>No anomalies match current filters</span>
            <span class="cell-level">—</span>
            <span class="cell-status">
              <span class="status-pill status-pill--normal">Clear</span>
            </span>
            <span class="cell-score">—</span>
          </div>

          <div class="table-footer">
            <button class="dataset-button" @click="router.push('/dataset')">View Dataset</button>
          </div>
        </div>
      </section>

      <section class="overview-panel">
        <div class="overview-header">
          <div class="overview-title">
            <h2>Anomalies Overview</h2>
            <span class="overview-toggle"></span>
          </div>

          <div class="overview-actions">
            <button
                class="tool-button tool-button--small"
                :class="{ 'tool-button--active': quickRange === '1W', 'tool-button--ghost': quickRange !== '1W' }"
                @click="setQuickRange('1W')"
            >
              1W
            </button>

            <button
                class="tool-button tool-button--small"
                :class="{ 'tool-button--active': quickRange === '24h', 'tool-button--ghost': quickRange !== '24h' }"
                @click="setQuickRange('24h')"
            >
              24h
            </button>

            <button
                class="tool-button tool-button--small"
                :class="{ 'tool-button--active': quickRange === '14d', 'tool-button--ghost': quickRange !== '14d' }"
                @click="setQuickRange('14d')"
            >
              14d
            </button>
          </div>
        </div>

        <p v-if="chartWarning" class="range-warning">
          {{ chartWarning }}
        </p>

        <div class="overview-chart">
          <RadiationChart
              :key="chartRenderKey"
              :labels="chartLabels"
              :values="chartValues"
              :threshold="activeThreshold"
              :anomaly-flags="chartAnomalyFlags"
          />
        </div>
      </section>

      <section class="summary-hero">
        <div>
          <h2>Detected Events Summary</h2>
          <p>Review detected events, severity levels, and anomaly scores across the active dataset.</p>
        </div>

        <div class="summary-hero__badge">{{ totalEventsLabel }}</div>
      </section>

      <section class="filters">
        <div class="filter-card">
          <label>Date Range</label>
          <div class="filter-value">{{ dateRangeLabel }}</div>
        </div>

        <div class="filter-card">
          <label>Status Filter</label>
          <div class="filter-value">{{ selectedStatus }}</div>
        </div>

        <div class="filter-card">
          <label>Search</label>
          <div class="filter-value">{{ searchQuery || 'timestamp / level / score' }}</div>
        </div>
      </section>

      <section class="summary-table-panel">
        <div class="summary-table-panel__header">
          <h2>Detected Anomalies</h2>
          <button type="button" @click="loadAnomaliesPage">Refresh</button>
        </div>

        <div class="summary-table">
          <div class="summary-table__head">
            <span>Timestamp</span>
            <span>Radiation Level</span>
            <span>Anomaly Score</span>
            <span>Status</span>
          </div>

          <div v-for="row in anomalyRowsOverview" :key="row.timestamp" class="summary-table__row">
            <span>{{ row.timestamp }}</span>
            <span class="accent">{{ row.level }}</span>
            <span>{{ row.score }}</span>
            <span
                class="status"
                :class="`status--${row.statusType}`"
            >
              {{ row.status }}
            </span>
          </div>

          <div v-if="!anomalyRowsOverview.length" class="summary-table__row">
            <span>No anomalies match current filters</span>
            <span class="accent">—</span>
            <span>—</span>
            <span class="status status--normal">Clear</span>
          </div>
        </div>
      </section>
    </div>
  </MainLayout>
</template>

<style scoped>
.anomalies-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-panel,
.table-panel,
.overview-panel,
.summary-hero,
.filters,
.filter-card,
.summary-table-panel {
  border-radius: 22px;
  border: 1px solid rgba(120, 151, 235, 0.12);
  background:
      radial-gradient(circle at top right, rgba(76, 111, 255, 0.08), transparent 30%),
      linear-gradient(180deg, rgba(12, 18, 35, 0.88), rgba(9, 14, 28, 0.96));
  box-shadow:
      0 10px 36px rgba(0, 0, 0, 0.22),
      inset 0 1px 0 rgba(255,255,255,0.02);
  backdrop-filter: blur(14px);
}

.hero-panel,
.overview-panel,
.summary-hero,
.summary-table-panel {
  padding: 20px;
}

.hero-panel h1 {
  margin-bottom: 16px;
  color: #eef4ff;
  font-size: 32px;
  font-weight: 700;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.tool-button,
.dataset-button,
.summary-table-panel__header button {
  height: 34px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: rgba(255,255,255,0.05);
  color: #dbe8ff;
  font-size: 13px;
  cursor: pointer;
}

.tool-button--muted {
  color: #7f93b8;
}

.tool-button--ghost {
  background: rgba(255,255,255,0.03);
}

.tool-button--active {
  background: rgba(107, 158, 255, 0.12);
  border-color: rgba(107, 158, 255, 0.2);
}

.tool-button--small {
  height: 30px;
  padding: 0 12px;
  font-size: 12px;
}

.date-trigger {
  position: relative;
  height: 34px;
  min-width: 112px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: rgba(255,255,255,0.05);
  color: #7f93b8;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
}

.date-trigger--selected {
  color: #dbe8ff;
  border-color: rgba(107, 158, 255, 0.2);
  background: rgba(107, 158, 255, 0.08);
}

.date-trigger span {
  position: relative;
  z-index: 1;
  pointer-events: none;
  white-space: nowrap;
}

.date-trigger__input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.search-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr auto;
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
}

.search-box,
.source-box,
.chip {
  border: 1px solid rgba(120, 151, 235, 0.1);
  background: rgba(255,255,255,0.04);
  color: #93a7cf;
}

.search-box {
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  padding: 0 14px;
}

.chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chip {
  height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}

.chip--active {
  background: rgba(107, 158, 255, 0.12);
  border-color: rgba(107, 158, 255, 0.2);
  color: #eef4ff;
}

.source-box {
  min-height: 42px;
  border-radius: 12px;
  padding: 6px 8px 6px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.source-dot,
.row-dot,
.overview-toggle {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #7ef0bf;
  box-shadow: 0 0 12px rgba(126, 240, 191, 0.4);
}

.table-panel {
  margin-top: 14px;
  padding: 0;
  overflow: hidden;
}

.table-head,
.table-row,
.summary-table__head,
.summary-table__row {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr 1fr;
  gap: 14px;
  align-items: center;
}

.table-head,
.summary-table__head {
  padding: 16px 20px;
  color: #8ea2c9;
  font-size: 13px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.table-row,
.summary-table__row {
  padding: 16px 20px;
  color: #d5e2ff;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.cell-timestamp,
.cell-score {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cell-level,
.accent {
  color: #8fe6ff;
}

.status-pill,
.status {
  display: inline-flex;
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  font-weight: 700;
}

.status-pill--critical,
.status--critical {
  background: rgba(255, 117, 141, 0.16);
  color: #ffb8c4;
  border: 1px solid rgba(255, 117, 141, 0.22);
}

.status-pill--high,
.status--high {
  background: rgba(255, 193, 94, 0.18);
  color: #ffe1b3;
  border: 1px solid rgba(255, 208, 132, 0.22);
}

.status-pill--normal,
.status--normal {
  background: rgba(126, 240, 191, 0.16);
  color: #d8fff0;
  border: 1px solid rgba(126, 240, 191, 0.2);
}

.status-pill--alert,
.status--alert {
  background: rgba(120, 151, 235, 0.14);
  color: #d7e4ff;
  border: 1px solid rgba(120, 151, 235, 0.18);
}

.score-left {
  min-width: 36px;
  color: #8ea2c9;
  font-size: 12px;
}

.score-right {
  min-width: 34px;
  color: #d5e2ff;
  font-size: 12px;
  text-align: right;
}

.score-bar {
  flex: 1;
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(107, 158, 255, 0.28), rgba(126, 240, 191, 0.32));
}

.table-footer {
  padding: 16px 20px 20px;
}

.overview-header,
.summary-table-panel__header,
.overview-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.overview-header,
.summary-table-panel__header {
  margin-bottom: 16px;
}

.overview-title h2,
.summary-hero h2,
.summary-table-panel__header h2 {
  color: #eef4ff;
}

.overview-actions {
  display: flex;
  gap: 8px;
}

.range-warning {
  margin: -4px 0 14px;
  color: #ffcf9a;
  font-size: 13px;
  line-height: 1.4;
}

.overview-chart {
  height: 320px;
}

.summary-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.summary-hero p {
  margin-top: 8px;
  color: #98abd0;
}

.summary-hero__badge {
  height: 42px;
  padding: 0 16px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  background: rgba(126, 240, 191, 0.12);
  color: #8fe6c6;
  border: 1px solid rgba(126, 240, 191, 0.18);
}

.filters {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}

.filter-card {
  padding: 18px;
}

.filter-card label {
  display: block;
  margin-bottom: 8px;
  color: #90a5cd;
  font-size: 13px;
}

.filter-value {
  color: #eef4ff;
}

.summary-table {
  overflow: hidden;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.05);
}

@media (max-width: 1100px) {
  .search-row,
  .filters,
  .table-head,
  .table-row,
  .summary-table__head,
  .summary-table__row {
    grid-template-columns: 1fr;
  }

  .summary-hero,
  .overview-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

.search-box {
  outline: none;
}

.search-box::placeholder {
  color: #6f83aa;
}
</style>