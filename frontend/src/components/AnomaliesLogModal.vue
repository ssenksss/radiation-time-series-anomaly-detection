<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getAnomalies } from '../services/api'
import type { Measurement } from '../types/api'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const router = useRouter()

const anomalies = ref<Measurement[]>([])
const searchQuery = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

function normalizeText(value: string | null | undefined) {
  return String(value ?? '')
      .trim()
      .toLowerCase()
      .replaceAll('_', ' ')
      .replaceAll('-', ' ')
      .replace(/\s+/g, ' ')
}

function normalizeForCompare(value: string | null | undefined) {
  return normalizeText(value).replaceAll(' ', '')
}

function hasMeaningfulValue(value: string | null | undefined) {
  const normalized = normalizeText(value)

  return Boolean(
      normalized &&
      normalized !== 'unknown' &&
      normalized !== 'unknown sensor' &&
      normalized !== 'unknown_sensor' &&
      normalized !== 'nan' &&
      normalized !== 'none' &&
      normalized !== 'null',
  )
}

function formatDisplayValue(value: string | null | undefined) {
  if (!hasMeaningfulValue(value)) return '—'

  return String(value).trim().replaceAll('_', ' ')
}

function sensorIsSameAsLocation(sensorId: string | null | undefined, location: string | null | undefined) {
  if (!hasMeaningfulValue(sensorId) || !hasMeaningfulValue(location)) return false

  return normalizeForCompare(sensorId) === normalizeForCompare(location)
}

const formatAnomalyType = (type: string | null | undefined) => {
  if (!type) return 'Normal'

  const normalizedType = type.toLowerCase().replaceAll(' ', '_')

  const labels: Record<string, string> = {
    normal: 'Normal',
    warning: 'Warning',
    spike: 'Spike',

    threshold_detection: 'Warning',
    model_detection: 'Warning',
    ml_detected: 'Warning',
    sustained_increase: 'Warning',
    sensor_drop: 'Warning',
  }

  return labels[normalizedType] ?? normalizedType.replaceAll('_', ' ')
}

const getSeverityType = (status: string | null | undefined) => {
  if (status === 'Critical') return 'critical'
  if (status === 'High') return 'high'
  if (status === 'Normal') return 'normal'

  return 'alert'
}

const shouldShowLocation = computed(() => {
  return anomalies.value.some((item) => hasMeaningfulValue(item.location))
})

const shouldShowSensor = computed(() => {
  return anomalies.value.some((item) => {
    if (!hasMeaningfulValue(item.sensorId)) return false

    if (!hasMeaningfulValue(item.location)) return true

    return !sensorIsSameAsLocation(item.sensorId, item.location)
  })
})

const tableGridStyle = computed(() => {
  const columns = ['1.45fr', '1fr', '0.82fr', '0.62fr', '0.78fr']

  if (shouldShowLocation.value) {
    columns.push('0.9fr')
  }

  if (shouldShowSensor.value) {
    columns.push('0.9fr')
  }

  return {
    gridTemplateColumns: columns.join(' '),
  }
})

const logRows = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()

  return anomalies.value
      .filter((item) => {
        if (!query) return true

        return [
          item.timestamp,
          item.radiationLevel,
          item.status,
          item.sensorId,
          item.location,
          item.anomalyType,
          item.anomalyScore,
        ]
            .join(' ')
            .toLowerCase()
            .includes(query)
      })
      .map((item) => ({
        timestamp: item.timestamp,
        value: `${Number(item.radiationLevel).toFixed(4)} µSv/h`,
        severity: item.status,
        severityType: getSeverityType(item.status),
        anomalyScore: Number(item.anomalyScore ?? 0).toFixed(3),
        anomalyType: formatAnomalyType(item.anomalyType),
        location: formatDisplayValue(item.location),
        sensor: sensorIsSameAsLocation(item.sensorId, item.location)
            ? '—'
            : formatDisplayValue(item.sensorId),
      }))
})

async function loadAnomalies() {
  try {
    isLoading.value = true
    errorMessage.value = ''

    anomalies.value = await getAnomalies(500)
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Anomalies could not be loaded.'
  } finally {
    isLoading.value = false
  }
}

function goToDataset() {
  emit('close')
  router.push('/dataset')
}

function exportCsv() {
  const header = ['timestamp', 'radiation_level', 'type', 'score', 'status']

  if (shouldShowLocation.value) {
    header.push('location')
  }

  if (shouldShowSensor.value) {
    header.push('sensor')
  }

  const rows = logRows.value.map((row) => {
    const cells = [
      row.timestamp,
      row.value,
      row.anomalyType,
      row.anomalyScore,
      row.severity,
    ]

    if (shouldShowLocation.value) {
      cells.push(row.location)
    }

    if (shouldShowSensor.value) {
      cells.push(row.sensor)
    }

    return cells
  })

  const csvContent = [header, ...rows]
      .map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(','))
      .join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = 'anomalies_log.csv'
  link.click()

  URL.revokeObjectURL(url)
}

watch(
    () => props.isOpen,
    (isOpen) => {
      if (isOpen) {
        loadAnomalies()
      }
    },
    { immediate: true },
)
</script>

<template>
  <transition name="modal-fade">
    <div v-if="isOpen" class="modal-overlay" @click.self="emit('close')">
      <div class="modal-card">
        <div class="modal-card__header">
          <div>
            <p class="modal-card__eyebrow">Anomalies Log</p>
            <h2>Detailed Event History</h2>
          </div>

          <button class="close-button" type="button" @click="emit('close')">✕</button>
        </div>

        <div class="log-toolbar">
          <input
              v-model="searchQuery"
              class="log-toolbar__search"
              type="search"
              placeholder="⌕ Search anomalies"
          />

          <button class="toolbar-button" type="button" @click="exportCsv">
            Export CSV
          </button>
        </div>

        <div v-if="isLoading" class="log-table">
          <div class="log-table__row log-table__row--message">
            <span>Loading anomalies...</span>
          </div>
        </div>

        <div v-else-if="errorMessage" class="log-table">
          <div class="log-table__row log-table__row--message">
            <span>{{ errorMessage }}</span>
          </div>
        </div>

        <div v-else-if="logRows.length === 0" class="log-table">
          <div class="log-table__row log-table__row--message">
            <span>No events match the current search.</span>
          </div>
        </div>

        <div v-else class="log-table">
          <div class="log-table__head" :style="tableGridStyle">
            <span>Timestamp</span>
            <span>Radiation Level</span>
            <span>Type</span>
            <span>Score</span>
            <span>Status</span>
            <span v-if="shouldShowLocation">Location</span>
            <span v-if="shouldShowSensor">Sensor</span>
          </div>

          <div
              v-for="row in logRows"
              :key="`${row.timestamp}-${row.location}-${row.sensor}`"
              class="log-table__row"
              :style="tableGridStyle"
          >
            <span class="timestamp">
              <i class="row-dot"></i>
              {{ row.timestamp }}
            </span>
            <span class="accent">{{ row.value }}</span>
            <span>{{ row.anomalyType }}</span>
            <span class="score-value">{{ row.anomalyScore }}</span>
            <span class="severity">
              <span class="severity-pill" :class="`severity-pill--${row.severityType}`">
                {{ row.severity }}
              </span>
            </span>
            <span v-if="shouldShowLocation">{{ row.location }}</span>
            <span v-if="shouldShowSensor">{{ row.sensor }}</span>
          </div>
        </div>

        <div class="modal-footer">
          <button class="action-button action-button--secondary" type="button" @click="emit('close')">
            Close
          </button>
          <button class="action-button" type="button" @click="goToDataset">
            View Dataset
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 0.2s ease;
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  padding: 24px;
  background: rgba(4, 8, 18, 0.72);
  backdrop-filter: blur(10px);
  display: grid;
  place-items: center;
}

.modal-card {
  width: min(1080px, 100%);
  border-radius: 24px;
  border: 1px solid rgba(120, 151, 235, 0.14);
  background:
      radial-gradient(circle at top right, rgba(76, 111, 255, 0.08), transparent 30%),
      linear-gradient(180deg, rgba(12, 18, 35, 0.96), rgba(9, 14, 28, 0.98));
  box-shadow:
      0 20px 60px rgba(0, 0, 0, 0.35),
      inset 0 1px 0 rgba(255,255,255,0.03);
  padding: 22px;
  color: #eef4ff;
  max-height: calc(100vh - 48px);
  overflow-y: auto;
  overflow-x: hidden;
}

.modal-card__header {
  margin-bottom: 18px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.modal-card__eyebrow {
  margin-bottom: 8px;
  color: #8ea5d2;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
}

.modal-card__header h2 {
  font-size: 26px;
  color: #eef4ff;
}

.close-button {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: rgba(255,255,255,0.04);
  color: #dce8ff;
  cursor: pointer;
}

.log-toolbar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.log-toolbar__search {
  flex: 1;
  height: 42px;
  border-radius: 12px;
  border: 1px solid rgba(120, 151, 235, 0.1);
  background: rgba(255,255,255,0.04);
  color: #93a7cf;
  display: flex;
  align-items: center;
  padding: 0 14px;
  outline: none;
}

.log-toolbar__search::placeholder {
  color: #93a7cf;
}

.toolbar-button,
.action-button {
  height: 40px;
  padding: 0 16px;
  border-radius: 12px;
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: rgba(255,255,255,0.04);
  color: #dce8ff;
  cursor: pointer;
}

.log-table {
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.05);
}

.log-table__head,
.log-table__row {
  display: grid;
  gap: 12px;
  align-items: center;
}

.log-table__head {
  padding: 14px 16px;
  color: #90a4cd;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.log-table__row {
  padding: 16px;
  color: #eaf1ff;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.log-table__row--message {
  display: block;
}

.timestamp {
  display: flex;
  align-items: center;
  gap: 10px;
}

.row-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #ff7076;
  box-shadow: 0 0 12px rgba(255, 112, 118, 0.5);
}

.accent {
  color: #ffb29d;
}

.severity-pill {
  min-width: 94px;
  height: 32px;
  padding: 0 12px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.severity-pill--critical {
  background: rgba(183, 78, 88, 0.32);
  border: 1px solid rgba(255, 124, 138, 0.18);
  color: #ffd3d8;
}

.severity-pill--high {
  background: rgba(255, 193, 94, 0.22);
  border: 1px solid rgba(255, 208, 132, 0.24);
  color: #ffe6bd;
}

.severity-pill--normal {
  background: rgba(118, 237, 191, 0.22);
  border: 1px solid rgba(118, 237, 191, 0.24);
  color: #d8fff0;
}

.severity-pill--alert {
  background: rgba(120, 151, 235, 0.16);
  border: 1px solid rgba(120, 151, 235, 0.18);
  color: #d7e4ff;
}

.score-value {
  color: #8fe6c6;
  font-weight: 400;
}

.modal-footer {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.action-button {
  background: linear-gradient(180deg, rgba(255, 193, 94, 0.92), rgba(224, 153, 54, 0.92));
  color: #2c1f10;
  font-weight: 700;
}

.action-button--secondary {
  background: rgba(255,255,255,0.04);
  color: #dce8ff;
}

@media (max-width: 900px) {
  .modal-overlay {
    padding: 14px;
  }

  .log-toolbar,
  .modal-footer {
    flex-direction: column;
  }

  .log-table__head,
  .log-table__row {
    grid-template-columns: 1fr !important;
  }
}
</style>
