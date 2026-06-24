<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import MainLayout from '../layouts/MainLayout.vue'
import RadiationChart from '../components/RadiationChart.vue'
import {
  getDatasets,
  getMeasurements,
  getSummary,
  uploadDataset,
} from '../services/api'
import type { DatasetInfo, Measurement, Summary } from '../types/api'

type CsvPreviewRecord = Record<string, string | number | boolean | null | undefined>

const fileInputRef = ref<HTMLInputElement | null>(null)
const previewSectionRef = ref<HTMLElement | null>(null)

const backendMeasurements = ref<Measurement[]>([])
const backendSummary = ref<Summary | null>(null)
const datasets = ref<DatasetInfo[]>([])

const isLoading = ref(true)
const isUploading = ref(false)
const errorMessage = ref('')
const uploadStatus = ref('')
const isCsvPreviewModalOpen = ref(false)

const activeDataset = computed(() => {
  return datasets.value.find((dataset) => dataset.isActive) ?? datasets.value[0] ?? null
})

const backendRows = computed(() =>
    backendMeasurements.value.map((row) => ({
      label: row.timestamp,
      value: row.radiationLevel,
      isAnomaly: row.isAnomaly,
      status: row.status,
    })),
)

const activeRows = computed(() => backendRows.value)

const activeThreshold = computed(() => {
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
const chartRenderKey = computed(() => {
  const datasetId = activeDataset.value?.id ?? 'no-dataset'
  const firstLabel = chartLabels.value[0] ?? 'empty'
  const lastLabel = chartLabels.value[chartLabels.value.length - 1] ?? 'empty'

  return `${datasetId}-${chartLabels.value.length}-${firstLabel}-${lastLabel}`
})
const csvPreviewHeaders = computed(() => {
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
  return backendSummary.value?.totalAnomalies ?? 0
})

const currentLevel = computed(() => {
  return `${Number(backendSummary.value?.currentLevel ?? 0).toFixed(4)} µSv/h`
})

const datasetName = computed(() => {
  return backendSummary.value?.datasetName ?? activeDataset.value?.name ?? 'Loading dataset...'
})

const datasetInfoText = computed(() => {
  if (isUploading.value) {
    return 'Status: Uploading CSV and running ML pipeline...'
  }

  if (isLoading.value) {
    return 'Status: Loading backend dataset...'
  }

  if (errorMessage.value) {
    return 'Status: Backend dataset could not be loaded.'
  }

  const status = activeDataset.value?.status ?? 'active'
  const uploadedAt = activeDataset.value?.uploadedAt ?? backendSummary.value?.lastUpdated ?? 'active'

  return `Status: ${status} · ${uploadedAt}`
})

const sourceText = computed(() => {
  return activeDataset.value?.sourceType
      ? `PostgreSQL / ${activeDataset.value.sourceType.toUpperCase()}`
      : 'PostgreSQL backend'
})

const dataPointsText = computed(() => {
  return backendSummary.value?.totalMeasurements ?? backendMeasurements.value.length
})

const columnsText = computed(() => {
  const firstMeasurement = backendMeasurements.value[0]

  if (!firstMeasurement) {
    return isLoading.value ? 'Loading columns...' : 'No columns available'
  }

  return Object.keys(firstMeasurement).join(', ')
})

const datasetTableRows = computed(() => {
  if (datasets.value.length > 0) {
    return datasets.value.map((dataset) => ({
      name: dataset.name,
      uploaded: dataset.uploadedAt,
      size: `${dataset.rowCount} rows`,
      status: dataset.isActive ? 'Active' : dataset.status,
    }))
  }

  return [
    {
      name: datasetName.value,
      uploaded: backendSummary.value?.lastUpdated || 'Loaded from backend',
      size: `${Math.max(Number(dataPointsText.value), 1)} rows`,
      status: 'Active',
    },
  ]
})

const formatCsvCell = (row: CsvPreviewRecord, header: string) => {
  const value = row[header]

  if (value === null || value === undefined || value === '') {
    return '—'
  }

  return String(value)
}

const openFilePicker = () => {
  if (isUploading.value) return
  fileInputRef.value?.click()
}

const openCsvPreviewModal = () => {
  isCsvPreviewModalOpen.value = true
}

const closeCsvPreviewModal = () => {
  isCsvPreviewModalOpen.value = false
}

const loadBackendDataset = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''

    const [measurementsResponse, summaryResponse, datasetsResponse] = await Promise.all([
      getMeasurements(1000),
      getSummary(),
      getDatasets(),
    ])

    backendMeasurements.value = measurementsResponse
    backendSummary.value = summaryResponse
    datasets.value = datasetsResponse
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Backend dataset could not be loaded.'
  } finally {
    isLoading.value = false
  }
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
    isUploading.value = true
    uploadStatus.value = 'Uploading CSV and running ML pipeline...'
    errorMessage.value = ''

    await uploadDataset(file)
    await loadBackendDataset()

    uploadStatus.value = 'Dataset uploaded and processed successfully.'

    await nextTick()
    scrollToPreview()
  } catch (error) {
    console.error(error)
    errorMessage.value = error instanceof Error ? error.message : 'Dataset upload failed.'
    uploadStatus.value = ''
  } finally {
    isUploading.value = false
    target.value = ''

    window.setTimeout(() => {
      uploadStatus.value = ''
    }, 3500)
  }
}

const scrollToPreview = () => {
  previewSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const handleReset = async () => {
  closeCsvPreviewModal()
  await loadBackendDataset()
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
        <div v-if="uploadStatus" class="dataset-success">
          {{ uploadStatus }}
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
          <button
              class="load-button"
              type="button"
              :disabled="isUploading"
              @click="openFilePicker"
          >
            {{ isUploading ? 'Processing...' : 'Load Dataset' }}
          </button>
          <button
              class="ghost-button"
              type="button"
              :disabled="isUploading"
              @click="openFilePicker"
          >
            {{ isUploading ? 'Processing...' : 'Upload CSV' }}
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
              :key="chartRenderKey"
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
  height: 320px;
  margin-bottom: 14px;
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
}.dataset-success {
   margin-bottom: 18px;
   padding: 12px 14px;
   border-radius: 14px;
   border: 1px solid rgba(126, 240, 191, 0.18);
   background: rgba(126, 240, 191, 0.08);
   color: #9ee8ce;
 }
</style>