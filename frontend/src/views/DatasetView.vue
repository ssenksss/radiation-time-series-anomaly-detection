<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import MainLayout from '../layouts/MainLayout.vue'
import RadiationChart from '../components/RadiationChart.vue'
import { useDatasetStore } from '../stores/useDatasetStore'
import { getMeasurements, getSummary } from '../services/api'

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
  threshold: number
  lastUpdated: string
}

type CsvPreviewRecord = Record<string, string | number | boolean | null | undefined>

const fileInputRef = ref<HTMLInputElement | null>(null)
const previewSectionRef = ref<HTMLElement | null>(null)

const { datasetState, uploadCsv, resetDataset } = useDatasetStore()

const backendMeasurements = ref<Measurement[]>([])
const backendSummary = ref<Summary | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')
const isCsvPreviewModalOpen = ref(false)

const isCustomDatasetLoaded = computed(() => datasetState.isLoaded)

const backendRows = computed(() =>
    backendMeasurements.value.map((row) => ({
      label: row.timestamp,
      value: row.radiationLevel,
      isAnomaly: row.isAnomaly,
      status: row.status,
    })),
)

const activeRows = computed(() => {
  if (isCustomDatasetLoaded.value) {
    return datasetState.rows.map((row) => ({
      label: row.label,
      value: row.value,
      isAnomaly: row.value > datasetState.threshold,
      status: row.value > datasetState.threshold ? 'Anomaly' : 'Normal',
    }))
  }

  return backendRows.value
})

const activeThreshold = computed(() => {
  if (isCustomDatasetLoaded.value) {
    return datasetState.threshold
  }

  return backendSummary.value?.threshold ?? 0.18
})

const previewRows = computed(() => activeRows.value.slice(0, 8))

const chartLabels = computed(() =>
    activeRows.value.slice(0, 12).map((row) => row.label),
)

const chartValues = computed(() =>
    activeRows.value.slice(0, 12).map((row) => row.value),
)

const chartAnomalyFlags = computed(() =>
    activeRows.value.slice(0, 12).map((row) => row.isAnomaly),
)

const csvPreviewHeaders = computed(() => {
  if (isCustomDatasetLoaded.value && datasetState.headers.length > 0) {
    return datasetState.headers
  }

  const firstMeasurement = backendMeasurements.value[0]

  if (!firstMeasurement) {
    return []
  }

  return [
    'timestamp',
    'radiation_uSv_h',
    'sensor_id',
    'location',
    'temperature_c',
    'humidity_percent',
    'is_anomaly',
    'anomaly_score',
    'anomaly_type',
    'status',
  ]
})

const csvPreviewRows = computed<CsvPreviewRecord[]>(() => {
  if (isCustomDatasetLoaded.value) {
    return datasetState.rows.slice(0, 20).map((row) => row.record as CsvPreviewRecord)
  }

  return backendMeasurements.value.slice(0, 20).map((row) => ({
    timestamp: row.timestamp,
    radiation_uSv_h: Number(row.radiationLevel).toFixed(4),
    sensor_id: row.sensorId,
    location: row.location,
    temperature_c: row.temperature ?? '',
    humidity_percent: row.humidity ?? '',
    is_anomaly: row.isAnomaly,
    anomaly_score: Number(row.anomalyScore ?? 0).toFixed(4),
    anomaly_type: row.anomalyType,
    status: row.status,
  }))
})

const csvPreviewGridTemplate = computed(() => {
  const columns = Math.max(csvPreviewHeaders.value.length, 1)
  return `60px repeat(${columns}, 160px)`
})

const anomalyCount = computed(() => {
  if (isCustomDatasetLoaded.value) {
    return datasetState.rows.filter((row) => row.value > datasetState.threshold).length
  }

  return backendSummary.value?.totalAnomalies ?? 0
})

const currentLevel = computed(() => {
  if (isCustomDatasetLoaded.value) {
    const last = datasetState.rows[datasetState.rows.length - 1]
    return last ? `${last.value.toFixed(4)} µSv/h` : '0.0000 µSv/h'
  }

  return `${Number(backendSummary.value?.currentLevel ?? 0).toFixed(4)} µSv/h`
})

const datasetName = computed(() => {
  if (isCustomDatasetLoaded.value) {
    return datasetState.name
  }

  return backendSummary.value?.datasetName ?? 'Loading dataset...'
})

const datasetInfoText = computed(() => {
  if (isCustomDatasetLoaded.value) {
    return `Status: Loaded successfully · ${datasetState.uploadedAt}`
  }

  if (isLoading.value) {
    return 'Status: Loading backend dataset...'
  }

  if (errorMessage.value) {
    return 'Status: Backend dataset could not be loaded.'
  }

  return `Status: Loaded from FastAPI backend · ${backendSummary.value?.lastUpdated ?? 'active'}`
})

const sourceText = computed(() => {
  if (isCustomDatasetLoaded.value) {
    return datasetState.source
  }

  return 'Backend API'
})

const dataPointsText = computed(() => {
  if (isCustomDatasetLoaded.value) {
    return datasetState.rows.length
  }

  return backendSummary.value?.totalMeasurements ?? backendMeasurements.value.length
})

const columnsText = computed(() => {
  if (isCustomDatasetLoaded.value && datasetState.headers.length > 0) {
    return datasetState.headers.join(', ')
  }

  const firstMeasurement = backendMeasurements.value[0]

  if (!firstMeasurement) {
    return isLoading.value ? 'Loading columns...' : 'No columns available'
  }

  return Object.keys(firstMeasurement).join(', ')
})

const datasetTableRows = computed(() => [
  {
    name: datasetName.value,
    uploaded: isCustomDatasetLoaded.value
        ? datasetState.uploadedAt || 'Just now'
        : backendSummary.value?.lastUpdated || 'Loaded from backend',
    size: `${Math.max(Number(dataPointsText.value), 1)} rows`,
    status: isCustomDatasetLoaded.value ? 'Loaded' : 'Active',
  },
])

const formatCsvCell = (row: CsvPreviewRecord, header: string) => {
  const value = row[header]

  if (value === null || value === undefined || value === '') {
    return '—'
  }

  return String(value)
}

const openFilePicker = () => {
  fileInputRef.value?.click()
}

const openCsvPreviewModal = () => {
  isCsvPreviewModalOpen.value = true
}

const closeCsvPreviewModal = () => {
  isCsvPreviewModalOpen.value = false
}

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (!file) return

  if (!file.name.toLowerCase().endsWith('.csv')) {
    alert('Please select a CSV file.')
    target.value = ''
    return
  }

  try {
    await uploadCsv(file)
  } catch (error) {
    console.error(error)
    alert('The CSV file could not be loaded.')
  } finally {
    target.value = ''
  }
}

const scrollToPreview = () => {
  previewSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const handleReset = () => {
  resetDataset()
  closeCsvPreviewModal()
}

const loadBackendDataset = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''

    const [measurementsResponse, summaryResponse] = await Promise.all([
      getMeasurements(1000),
      getSummary(),
    ])

    backendMeasurements.value = measurementsResponse as Measurement[]
    backendSummary.value = summaryResponse as Summary
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Backend dataset could not be loaded.'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadBackendDataset()
})
</script>

<template>
  <MainLayout>
    <div class="dataset-page">
      <section class="panel dataset-main">
        <div class="dataset-main__header">
          <h1>Dataset</h1>
        </div>

        <input
            ref="fileInputRef"
            type="file"
            accept=".csv"
            class="hidden-file-input"
            @change="handleFileChange"
        />

        <div class="dataset-file">
          <div>
            <h2>{{ datasetName }}</h2>
            <p>{{ datasetInfoText }}</p>
          </div>

          <div class="dataset-file__actions">
            <button class="icon-button" type="button" @click="openFilePicker">⌄</button>
          </div>
        </div>

        <div v-if="errorMessage" class="dataset-error">
          {{ errorMessage }}
        </div>

        <div class="dataset-info">
          <div class="dataset-info__left">
            <p><strong>Source:</strong> {{ sourceText }}</p>
            <p><strong>Data Points:</strong> {{ dataPointsText }}</p>
            <p><strong>Columns:</strong> {{ columnsText }}</p>
            <p><strong>Flagged anomalies:</strong> {{ anomalyCount }}</p>
          </div>

          <button class="ghost-button" type="button" @click="handleReset">Reset</button>
        </div>

        <div class="dataset-actions">
          <button class="load-button" type="button" @click="openFilePicker">
            Load Dataset
          </button>
          <button class="ghost-button" type="button" @click="scrollToPreview">
            View Dataset
          </button>
        </div>

        <div class="dataset-table">
          <div class="dataset-table__head">
            <span>Name</span>
            <span>Date Uploaded</span>
            <span>Size</span>
            <span>Status</span>
          </div>

          <div
              v-for="item in datasetTableRows"
              :key="`${item.name}-${item.status}`"
              class="dataset-table__row"
          >
            <span class="dataset-name">
              <i class="table-dot"></i>
              {{ item.name }}
            </span>
            <span>{{ item.uploaded }}</span>
            <span>{{ item.size }}</span>
            <span class="status-chip">{{ item.status }}</span>
          </div>
        </div>

        <div class="dataset-bottom">
          <button class="ghost-button" type="button" @click="openCsvPreviewModal">
            View Dataset Preview
          </button>
        </div>
      </section>

      <section ref="previewSectionRef" class="panel preview-panel">
        <div class="preview-header">
          <div class="preview-title">
            <span class="preview-icon">i</span>
            <h2>Sample Preview</h2>
          </div>

          <button class="ghost-button" type="button" @click="openFilePicker">
            Upload CSV
          </button>
        </div>

        <div class="preview-metric">
          <span>Current Level:</span>
          <strong>{{ currentLevel }}</strong>
        </div>

        <div class="preview-chart">
          <RadiationChart
              :labels="chartLabels.length ? chartLabels : undefined"
              :values="chartValues.length ? chartValues : undefined"
              :threshold="activeThreshold"
              :anomaly-flags="chartAnomalyFlags"
          />
        </div>

        <div class="preview-table">
          <div class="preview-table__head">
            <span>Row</span>
            <span>Timestamp</span>
            <span>Radiation Value</span>
          </div>

          <div
              v-for="(row, index) in previewRows"
              :key="`${row.label}-${index}`"
              class="preview-table__row"
          >
            <span>#{{ index + 1 }}</span>
            <span>{{ row.label }}</span>
            <span>{{ row.value.toFixed(4) }}</span>
          </div>

          <div v-if="!previewRows.length" class="preview-empty">
            No dataset preview available. Check if backend is running or upload a CSV file.
          </div>
        </div>
      </section>

      <div
          v-if="isCsvPreviewModalOpen"
          class="csv-modal-backdrop"
          @click.self="closeCsvPreviewModal"
      >
        <div class="csv-modal">
          <div class="csv-modal__header">
            <div>
              <p class="csv-modal__eyebrow">Dataset Preview</p>
              <h2>CSV File Preview</h2>
              <span>Showing first {{ csvPreviewRows.length }} rows from the active dataset.</span>
            </div>

            <button
                class="csv-modal__close"
                type="button"
                @click="closeCsvPreviewModal"
            >
              ×
            </button>
          </div>

          <div class="csv-modal__table">
            <div
                v-if="csvPreviewHeaders.length"
                class="csv-modal__head"
                :style="{ gridTemplateColumns: csvPreviewGridTemplate }"
            >
              <span>#</span>
              <span
                  v-for="header in csvPreviewHeaders"
                  :key="header"
              >
                {{ header }}
              </span>
            </div>

            <div
                v-for="(row, index) in csvPreviewRows"
                :key="index"
                class="csv-modal__row"
                :style="{ gridTemplateColumns: csvPreviewGridTemplate }"
            >
              <span>#{{ index + 1 }}</span>

              <span
                  v-for="header in csvPreviewHeaders"
                  :key="header"
              >
                {{ formatCsvCell(row, header) }}
              </span>
            </div>

            <div v-if="!csvPreviewRows.length" class="preview-empty">
              No CSV preview available. Check if backend is running or upload a CSV file.
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<style scoped>
.dataset-page {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
}

.panel {
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

.dataset-main,
.preview-panel {
  padding: 20px;
}

.hidden-file-input {
  display: none;
}

.dataset-main__header h1 {
  margin-bottom: 18px;
  color: #eef4ff;
  font-size: 32px;
}

.dataset-file {
  margin-bottom: 18px;
  min-height: 84px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(120, 151, 235, 0.1);
  background: rgba(255,255,255,0.03);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.dataset-file h2 {
  margin-bottom: 8px;
  color: #eef4ff;
  font-size: 28px;
  word-break: break-word;
}

.dataset-file p {
  color: #92a7cf;
}

.dataset-error {
  margin-bottom: 18px;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(255, 141, 111, 0.18);
  background: rgba(255, 141, 111, 0.08);
  color: #ffc3ad;
}

.icon-button,
.ghost-button,
.load-button {
  height: 36px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: rgba(255,255,255,0.04);
  color: #dbe8ff;
  cursor: pointer;
}

.icon-button {
  min-width: 36px;
  padding: 0;
}

.dataset-info {
  margin-bottom: 18px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.dataset-info__left {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #9fb1d1;
}

.dataset-actions {
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.load-button {
  min-width: 150px;
}

.dataset-table {
  margin-bottom: 16px;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.05);
}

.dataset-table__head,
.dataset-table__row {
  display: grid;
  grid-template-columns: 2fr 1fr 0.8fr 0.8fr;
  gap: 12px;
  align-items: center;
}

.dataset-table__head {
  padding: 12px 14px;
  color: #91a6cf;
  font-size: 14px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.dataset-table__row {
  padding: 14px;
  color: #eaf1ff;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.dataset-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.table-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #7ef0bf;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 80px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(126, 240, 191, 0.12);
  color: #7ef0bf;
  font-size: 12px;
}

.dataset-bottom {
  display: flex;
  justify-content: center;
}

.preview-header {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.preview-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.preview-title h2 {
  color: #eef4ff;
  font-size: 18px;
}

.preview-icon {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(121, 140, 220, 0.12);
  color: #c6d8fb;
  font-size: 12px;
}

.preview-metric {
  margin-bottom: 14px;
  color: #9fb1d1;
  display: flex;
  gap: 6px;
}

.preview-metric strong {
  color: #7ef0bf;
}

.preview-chart {
  margin-bottom: 18px;
}

.preview-table {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.05);
}

.preview-table__head,
.preview-table__row {
  display: grid;
  grid-template-columns: 0.7fr 1.6fr 1fr;
  gap: 12px;
  align-items: center;
}

.preview-table__head {
  padding: 12px 14px;
  color: #91a6cf;
  font-size: 14px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.preview-table__row {
  padding: 12px 14px;
  color: #eaf1ff;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.preview-empty {
  padding: 18px 14px;
  color: #93a7cd;
}

.csv-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 100;
  padding: 32px;
  background: rgba(3, 7, 18, 0.72);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.csv-modal {
  width: min(1100px, 100%);
  max-height: calc(100vh - 64px);
  padding: 20px;
  border-radius: 22px;
  border: 1px solid rgba(120, 151, 235, 0.16);
  background:
      radial-gradient(circle at top right, rgba(76, 111, 255, 0.08), transparent 30%),
      linear-gradient(180deg, rgba(12, 18, 35, 0.98), rgba(9, 14, 28, 0.98));
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.45);
  overflow: hidden;
}

.csv-modal__header {
  margin-bottom: 16px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.csv-modal__eyebrow {
  margin-bottom: 6px;
  color: #91a6cf;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.csv-modal__header h2 {
  color: #eef4ff;
  font-size: 24px;
}

.csv-modal__header span {
  display: inline-block;
  margin-top: 6px;
  color: #93a7cd;
  font-size: 13px;
}

.csv-modal__close {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid rgba(120, 151, 235, 0.14);
  background: rgba(255,255,255,0.04);
  color: #dbe8ff;
  font-size: 22px;
  cursor: pointer;
}

.csv-modal__table {
  max-height: calc(100vh - 190px);
  overflow: auto;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.05);
}

.csv-modal__head,
.csv-modal__row {
  display: grid;
  width: max-content;
  min-width: 100%;
}

.csv-modal__head {
  position: sticky;
  top: 0;
  z-index: 2;
  background: rgba(12, 18, 35, 0.98);
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.csv-modal__head span {
  padding: 11px 12px;
  color: #91a6cf;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  border-right: 1px solid rgba(255,255,255,0.05);
  overflow: hidden;
  text-overflow: ellipsis;
}

.csv-modal__row {
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.csv-modal__row span {
  padding: 11px 12px;
  color: #eaf1ff;
  font-size: 12px;
  white-space: nowrap;
  border-right: 1px solid rgba(255,255,255,0.04);
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 1100px) {
  .dataset-page {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dataset-actions,
  .dataset-info,
  .preview-header {
    flex-direction: column;
    align-items: stretch;
  }

  .dataset-table__head,
  .dataset-table__row,
  .preview-table__head,
  .preview-table__row {
    grid-template-columns: 1fr;
  }

  .csv-modal-backdrop {
    padding: 16px;
  }
}
</style>