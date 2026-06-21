<script setup lang="ts">
import { computed, ref } from 'vue'
import MainLayout from '../layouts/MainLayout.vue'
import RadiationChart from '../components/RadiationChart.vue'
import { useDatasetStore } from '../stores/useDatasetStore'

const fileInputRef = ref<HTMLInputElement | null>(null)
const previewSectionRef = ref<HTMLElement | null>(null)

const { datasetState, uploadCsv, resetDataset } = useDatasetStore()

const fallbackDatasets = [
  { name: 'sample_radiation_A.csv', uploaded: 'Apr 18, 2024', size: '132KB' },
  { name: 'sample_radiation_B.csv', uploaded: 'Apr 20, 2024', size: '298KB' },
]

const previewRows = computed(() => datasetState.rows.slice(0, 8))
const chartLabels = computed(() => datasetState.rows.slice(0, 12).map((row) => row.label))
const chartValues = computed(() => datasetState.rows.slice(0, 12).map((row) => row.value))
const anomalyCount = computed(
    () => datasetState.rows.filter((row) => row.value > datasetState.threshold).length,
)
const currentLevel = computed(() => {
  const last = datasetState.rows[datasetState.rows.length - 1]
  return last ? `${last.value.toFixed(2)} µSv/h` : '0.75 µSv/h'
})

const datasetTableRows = computed(() => {
  const active = datasetState.isLoaded
      ? [
        {
          name: datasetState.name,
          uploaded: datasetState.uploadedAt || 'Just now',
          size: `${Math.max(datasetState.rows.length, 1)} rows`,
          status: 'Loaded',
        },
      ]
      : []

  const fallback = fallbackDatasets.map((item) => ({
    ...item,
    status: 'Sample',
  }))

  return [...active, ...fallback]
})

const datasetInfoText = computed(() => {
  if (!datasetState.isLoaded) {
    return 'Status: No custom dataset loaded yet.'
  }

  return `Status: Loaded successfully · ${datasetState.uploadedAt}`
})

const sourceText = computed(() => datasetState.source)
const dataPointsText = computed(() => datasetState.rows.length || 1247)
const columnsText = computed(() =>
    datasetState.headers.length > 0
        ? datasetState.headers.join(', ')
        : 'Timestamp, Radiation Level, Status',
)

const openFilePicker = () => {
  fileInputRef.value?.click()
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
}
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
            <h2>{{ datasetState.name }}</h2>
            <p>{{ datasetInfoText }}</p>
          </div>

          <div class="dataset-file__actions">
            <button class="icon-button" type="button" @click="openFilePicker">⌄</button>
          </div>
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
          <button class="ghost-button" type="button" @click="scrollToPreview">
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
              :threshold="datasetState.threshold"
          />
        </div>

        <div class="preview-table">
          <div class="preview-table__head">
            <span>Row</span>
            <span>{{ datasetState.headers[0] || 'Timestamp' }}</span>
            <span>{{ datasetState.headers[1] || 'Radiation Value' }}</span>
          </div>

          <div
              v-for="(row, index) in previewRows.length ? previewRows : []"
              :key="`${row.label}-${index}`"
              class="preview-table__row"
          >
            <span>#{{ index + 1 }}</span>
            <span>{{ row.label }}</span>
            <span>{{ row.value.toFixed(2) }}</span>
          </div>

          <div v-if="!previewRows.length" class="preview-empty">
            No uploaded CSV preview yet. Select a CSV file from the header or from this page.
          </div>
        </div>
      </section>
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
}
</style>