<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { getModelInfo } from '../services/api'
import type { AvailableModel, ModelComparisonItem, ModelInfo } from '../types/api'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'updated', modelInfo: ModelInfo): void
}>()

const fallbackModels: AvailableModel[] = [
  {
    id: 'isolation_forest',
    name: 'Isolation Forest',
    status: 'implemented',
  },
  {
    id: 'lof',
    name: 'Local Outlier Factor',
    status: 'implemented',
  },
  {
    id: 'rnn',
    name: 'Recurrent Neural Network',
    status: 'pending',
  },
]

const modelInfo = ref<ModelInfo | null>(null)
const selectedModelA = ref('isolation_forest')
const selectedModelB = ref('lof')

const isLoading = ref(false)
const errorMessage = ref('')

const availableModels = computed(() => {
  return modelInfo.value?.availableModels?.length
      ? modelInfo.value.availableModels
      : fallbackModels
})

const comparisonItems = computed<ModelComparisonItem[]>(() => {
  return modelInfo.value?.comparison ?? []
})

const modelAResult = computed(() => comparisonItems.value[0] ?? null)
const modelBResult = computed(() => comparisonItems.value[1] ?? null)

const modelAName = computed(() => {
  return modelAResult.value?.model ?? getModelName(selectedModelA.value)
})

const modelBName = computed(() => {
  return modelBResult.value?.model ?? getModelName(selectedModelB.value)
})

const isUnsupervised = computed(() => {
  return modelInfo.value?.evaluationMode === 'unsupervised'
})

const activeModelName = computed(() => {
  return modelAResult.value?.model ?? modelInfo.value?.currentModel ?? 'Detection Model'
})

const primaryMetricLabel = computed(() => {
  if (modelInfo.value?.evaluationMode === 'unsupervised') return 'Model Score'
  if (modelInfo.value?.evaluationMode === 'supervised') return 'Accuracy'

  return 'Model Status'
})

const primaryMetricValue = computed(() => {
  if (modelInfo.value?.evaluationMode === 'unsupervised') {
    return modelAResult.value?.modelScore ??
        modelAResult.value?.score ??
        modelInfo.value?.modelScore ??
        null
  }

  return modelAResult.value?.accuracy ?? modelInfo.value?.accuracy ?? null
})

const progressWidth = computed(() => {
  const value = primaryMetricValue.value ?? 0

  return `${Math.max(0, Math.min(100, value))}%`
})

const hasResults = computed(() => comparisonItems.value.length > 0)

const bars = computed(() =>
    comparisonItems.value.map((item, index) => {
      const displayScore = item.evaluationMode === 'unsupervised'
          ? item.modelScore ?? item.score
          : item.accuracy ?? item.score

      const score = Number(displayScore ?? 0)
      const safeScore = Math.max(0, Math.min(100, score))
      const isPending = item.status.toLowerCase().includes('pending')

      return {
        label: item.model,
        value: isPending ? 'Pending' : formatPercent(displayScore),
        height: isPending ? '22px' : `${Math.max(36, Math.round(safeScore * 0.9))}px`,
        active: index === 0,
        pending: isPending,
        status: item.status,
        subtitle: item.evaluationMode === 'unsupervised'
            ? `${formatNumber(item.totalAnomalies)} anomalies · ${formatPercent(item.anomalyRate, 3)} rate`
            : `Precision ${formatMetric(item.precision)}`,
      }
    }),
)

const comparisonRows = computed(() => {
  if (isUnsupervised.value) {
    return [
      {
        metric: 'Model Score',
        modelA: formatPercent(modelAResult.value?.modelScore ?? modelAResult.value?.score),
        modelB: formatPercent(modelBResult.value?.modelScore ?? modelBResult.value?.score),
      },
      {
        metric: 'Detected Anomalies',
        modelA: formatNumber(modelAResult.value?.totalAnomalies),
        modelB: formatNumber(modelBResult.value?.totalAnomalies),
      },
      {
        metric: 'Total Records',
        modelA: formatNumber(modelAResult.value?.totalRecords),
        modelB: formatNumber(modelBResult.value?.totalRecords),
      },
      {
        metric: 'Anomaly Rate',
        modelA: formatPercent(modelAResult.value?.anomalyRate, 3),
        modelB: formatPercent(modelBResult.value?.anomalyRate, 3),
      },
      {
        metric: 'Evaluation',
        modelA: 'Unsupervised',
        modelB: 'Unsupervised',
      },
      {
        metric: 'Status',
        modelA: modelAResult.value?.status ?? 'N/A',
        modelB: modelBResult.value?.status ?? 'N/A',
      },
    ]
  }

  return [
    {
      metric: 'Accuracy',
      modelA: formatPercent(modelAResult.value?.accuracy),
      modelB: formatPercent(modelBResult.value?.accuracy),
    },
    {
      metric: 'Precision',
      modelA: formatMetric(modelAResult.value?.precision),
      modelB: formatMetric(modelBResult.value?.precision),
    },
    {
      metric: 'Recall',
      modelA: formatMetric(modelAResult.value?.recall),
      modelB: formatMetric(modelBResult.value?.recall),
    },
    {
      metric: 'FPR',
      modelA: formatMetric(modelAResult.value?.fpr),
      modelB: formatMetric(modelBResult.value?.fpr),
    },
    {
      metric: 'FNR',
      modelA: formatMetric(modelAResult.value?.fnr),
      modelB: formatMetric(modelBResult.value?.fnr),
    },
    {
      metric: 'Status',
      modelA: modelAResult.value?.status ?? 'N/A',
      modelB: modelBResult.value?.status ?? 'N/A',
    },
  ]
})

const evaluationNote = computed(() => {
  if (modelInfo.value?.evaluationMode === 'unsupervised') {
    return 'Real dataset does not contain manual anomaly labels, so the app shows Model Score, detected anomalies and anomaly rate.'
  }

  if (modelInfo.value?.evaluationMode === 'supervised') {
    return 'This dataset contains anomaly labels, so the app shows Accuracy, Precision, Recall, FPR and FNR.'
  }

  return 'Model metrics will be available after training.'
})

function getModelName(modelId: string) {
  const model = availableModels.value.find((item) => item.id === modelId)

  return model?.name ?? modelId
}

function formatPercent(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A'

  return `${Number(value).toFixed(digits)}%`
}

function formatMetric(value: number | null | undefined) {
  if (value === null || value === undefined) return 'N/A'

  return Number(value).toFixed(3)
}

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A'

  return Number(value).toLocaleString()
}

function modelStatusLabel(model: AvailableModel) {
  return model.status === 'implemented' ? 'Available' : 'Pending ML'
}

async function loadModelInfo() {
  try {
    isLoading.value = true
    errorMessage.value = ''

    const response = await getModelInfo(selectedModelA.value, selectedModelB.value)

    modelInfo.value = response
    selectedModelA.value = response.selectedModels.modelA
    selectedModelB.value = response.selectedModels.modelB

    emit('updated', response)
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Model data could not be loaded. Check if FastAPI is running.'
  } finally {
    isLoading.value = false
  }
}

function handleModelAChange() {
  if (selectedModelA.value === selectedModelB.value) {
    const replacement = availableModels.value.find((model) => model.id !== selectedModelA.value)
    selectedModelB.value = replacement?.id ?? 'isolation_forest'
  }

  loadModelInfo()
}

function handleModelBChange() {
  if (selectedModelA.value === selectedModelB.value) {
    const replacement = availableModels.value.find((model) => model.id !== selectedModelB.value)
    selectedModelA.value = replacement?.id ?? 'isolation_forest'
  }

  loadModelInfo()
}

watch(
    () => props.isOpen,
    (isOpen) => {
      if (isOpen) {
        loadModelInfo()
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
            <p class="modal-card__eyebrow">Model Testing</p>
            <h2>Compare detection models</h2>
            <p class="modal-card__subtitle">
              Compare model performance. Labeled datasets show Accuracy, while real unlabeled datasets show Model Score.
            </p>
          </div>

          <button class="close-button" type="button" @click="emit('close')">✕</button>
        </div>

        <div class="model-selector-grid">
          <div class="model-select-card model-select-card--primary">
            <div class="model-select-card__top">
              <label>Model A</label>
              <span class="model-badge">Primary</span>
            </div>

            <select
                v-model="selectedModelA"
                class="model-select"
                :disabled="isLoading"
                @change="handleModelAChange"
            >
              <option
                  v-for="model in availableModels"
                  :key="model.id"
                  :value="model.id"
                  :disabled="model.id === selectedModelB"
              >
                {{ model.name }} · {{ modelStatusLabel(model) }}
              </option>
            </select>
          </div>

          <div class="model-vs">vs</div>

          <div class="model-select-card">
            <div class="model-select-card__top">
              <label>Model B</label>
              <span class="model-badge model-badge--muted">Comparison</span>
            </div>

            <select
                v-model="selectedModelB"
                class="model-select"
                :disabled="isLoading"
                @change="handleModelBChange"
            >
              <option
                  v-for="model in availableModels"
                  :key="model.id"
                  :value="model.id"
                  :disabled="model.id === selectedModelA"
              >
                {{ model.name }} · {{ modelStatusLabel(model) }}
              </option>
            </select>
          </div>
        </div>

        <div v-if="isLoading" class="panel-block panel-block--state">
          Loading model results...
        </div>

        <div v-else-if="errorMessage" class="panel-block panel-block--state panel-block--error">
          {{ errorMessage }}
        </div>

        <div v-else class="modal-grid">
          <div class="panel-block">
            <div class="panel-block__top">
              <div>
                <span>{{ primaryMetricLabel }}</span>
                <strong>{{ activeModelName }}</strong>
              </div>

              <div class="accuracy-chip">
                {{ formatPercent(primaryMetricValue) }}
              </div>
            </div>

            <div class="progress-bar">
              <div class="progress-bar__fill" :style="{ width: progressWidth }"></div>
            </div>

            <div v-if="bars.length" class="mini-bars">
              <div
                  v-for="bar in bars"
                  :key="bar.label"
                  class="mini-bars__item"
              >
                <span class="mini-bars__percent">{{ bar.value }}</span>

                <div
                    class="mini-bars__bar"
                    :class="{
                    'mini-bars__bar--active': bar.active,
                    'mini-bars__bar--pending': bar.pending,
                  }"
                    :style="{ height: bar.height }"
                ></div>

                <span class="mini-bars__label">{{ bar.label }}</span>
                <span class="mini-bars__subtitle">{{ bar.subtitle }}</span>
                <span
                    class="model-status"
                    :class="{ 'model-status--pending': bar.pending }"
                >
                  {{ bar.status }}
                </span>
              </div>
            </div>

            <div v-else class="empty-state">
              No model comparison data available.
            </div>

            <p class="model-source">
              {{ evaluationNote }}
            </p>
          </div>

          <div class="panel-block">
            <div class="metrics-header">
              <div>
                <h3>Model Metrics</h3>
                <p>{{ modelAName }} compared with {{ modelBName }}</p>
              </div>
            </div>

            <div v-if="hasResults" class="comparison-table">
              <div class="comparison-table__head comparison-table__head--three">
                <span>Metric</span>
                <span>{{ modelAName }}</span>
                <span>{{ modelBName }}</span>
              </div>

              <div
                  v-for="row in comparisonRows"
                  :key="row.metric"
                  class="comparison-table__row comparison-table__row--three"
              >
                <span>{{ row.metric }}</span>
                <span class="accent">{{ row.modelA }}</span>
                <span class="accent accent--secondary">{{ row.modelB }}</span>
              </div>
            </div>

            <div v-else class="empty-state">
              Select two models to compare their metrics.
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button
              class="action-button action-button--secondary"
              type="button"
              @click="emit('close')"
          >
            Close
          </button>

          <button
              class="action-button"
              type="button"
              :disabled="isLoading"
              @click="loadModelInfo"
          >
            Compare Again
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
  width: min(980px, 100%);
  max-height: calc(100vh - 48px);
  overflow: auto;
  border-radius: 26px;
  border: 1px solid rgba(120, 151, 235, 0.14);
  background:
      radial-gradient(circle at top right, rgba(76, 111, 255, 0.12), transparent 34%),
      radial-gradient(circle at bottom left, rgba(143, 230, 198, 0.08), transparent 32%),
      linear-gradient(180deg, rgba(12, 18, 35, 0.98), rgba(9, 14, 28, 0.99));
  box-shadow:
      0 24px 70px rgba(0, 0, 0, 0.38),
      inset 0 1px 0 rgba(255,255,255,0.04);
  padding: 22px;
  color: #eef4ff;
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
  margin: 0;
  font-size: 26px;
  color: #eef4ff;
}

.modal-card__subtitle {
  margin-top: 8px;
  max-width: 520px;
  color: #8ea5d2;
  font-size: 14px;
  line-height: 1.5;
}

.close-button {
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  border-radius: 13px;
  border: 1px solid rgba(120, 151, 235, 0.14);
  background: rgba(255,255,255,0.04);
  color: #dce8ff;
  cursor: pointer;
}

.close-button:hover {
  background: rgba(255,255,255,0.08);
}

.model-selector-grid {
  margin-bottom: 18px;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: end;
  gap: 14px;
}

.model-select-card {
  border-radius: 18px;
  border: 1px solid rgba(120, 151, 235, 0.14);
  background:
      linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.025));
  padding: 14px;
}

.model-select-card--primary {
  border-color: rgba(121, 219, 255, 0.24);
}

.model-select-card__top {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.model-select-card label {
  color: #8ea5d2;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.model-badge {
  border-radius: 999px;
  background: rgba(121, 219, 255, 0.12);
  color: #9ee8ff;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 700;
}

.model-badge--muted {
  background: rgba(143, 230, 198, 0.1);
  color: #9ee8ce;
}

.model-select {
  width: 100%;
  border: 1px solid rgba(120, 151, 235, 0.18);
  border-radius: 13px;
  background: rgba(8, 13, 28, 0.94);
  color: #eef4ff;
  padding: 11px 12px;
  font-size: 14px;
  outline: none;
  cursor: pointer;
}

.model-select:focus {
  border-color: rgba(121, 219, 255, 0.6);
  box-shadow: 0 0 0 3px rgba(121, 219, 255, 0.08);
}

.model-select:disabled {
  opacity: 0.65;
  cursor: wait;
}

.model-vs {
  padding-bottom: 17px;
  color: #8ea5d2;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.16em;
}

.modal-grid {
  display: grid;
  grid-template-columns: 0.95fr 1.15fr;
  gap: 16px;
}

.panel-block {
  border-radius: 20px;
  border: 1px solid rgba(120, 151, 235, 0.1);
  background:
      linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.022));
  padding: 16px;
}

.panel-block--state {
  color: #aabbe0;
  text-align: center;
}

.panel-block--error {
  color: #ffb49f;
}

.panel-block__top {
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
  color: #aabbe0;
}

.panel-block__top span {
  display: block;
  margin-bottom: 6px;
  color: #8ea5d2;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.panel-block__top strong {
  display: block;
  color: #eef4ff;
  font-size: 18px;
}

.accuracy-chip {
  align-self: flex-start;
  border-radius: 999px;
  background: rgba(143, 230, 198, 0.12);
  color: #9ee8ce;
  padding: 8px 10px;
  font-size: 14px;
  font-weight: 800;
}

.progress-bar {
  height: 12px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  overflow: hidden;
  margin-bottom: 18px;
}

.progress-bar__fill {
  width: 0;
  height: 100%;
  background: linear-gradient(90deg, #d3fbff, #85dfff, #99efcf);
  transition: width 0.25s ease;
}

.mini-bars {
  min-height: 190px;
  display: flex;
  align-items: end;
  justify-content: center;
  gap: 26px;
  padding-top: 10px;
}

.mini-bars__item {
  width: 132px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.mini-bars__percent {
  min-height: 18px;
  color: #a4b6d8;
  font-size: 13px;
  font-weight: 700;
}

.mini-bars__bar {
  width: 56px;
  border-radius: 14px 14px 4px 4px;
  background: linear-gradient(180deg, rgba(230, 235, 245, 0.9), rgba(157, 168, 194, 0.9));
  box-shadow: 0 0 12px rgba(255,255,255,0.05);
  transition: height 0.2s ease;
}

.mini-bars__bar--active {
  background: linear-gradient(180deg, #d3fcff, #93deff);
  box-shadow: 0 0 20px rgba(125, 219, 255, 0.3);
}

.mini-bars__bar--pending {
  background: linear-gradient(180deg, rgba(142, 165, 210, 0.35), rgba(142, 165, 210, 0.16));
  border: 1px dashed rgba(142, 165, 210, 0.3);
  box-shadow: none;
}

.mini-bars__label {
  color: #d7e4ff;
  font-size: 13px;
  text-align: center;
  line-height: 1.25;
}

.mini-bars__subtitle {
  color: #7187b3;
  font-size: 11px;
  text-align: center;
  line-height: 1.3;
}

.model-status {
  color: #8fe6c6;
  font-size: 11px;
  text-align: center;
}

.model-status--pending {
  color: #8ea5d2;
}

.model-source {
  margin-top: 14px;
  color: #90a4cd;
  font-size: 13px;
  line-height: 1.45;
}

.metrics-header {
  margin-bottom: 12px;
}

.metrics-header h3 {
  margin: 0 0 6px;
  color: #eef4ff;
  font-size: 18px;
}

.metrics-header p {
  margin: 0;
  color: #8ea5d2;
  font-size: 13px;
  line-height: 1.4;
}

.comparison-table {
  display: flex;
  flex-direction: column;
}

.comparison-table__head,
.comparison-table__row {
  display: grid;
  gap: 12px;
  align-items: center;
}

.comparison-table__head--three,
.comparison-table__row--three {
  grid-template-columns: 0.72fr 1fr 1fr;
}

.comparison-table__head {
  padding: 12px 0;
  color: #90a4cd;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.comparison-table__row {
  min-height: 48px;
  padding: 12px 0;
  color: #eaf1ff;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  font-size: 13px;
}

.accent {
  color: #8fe6c6;
  font-weight: 700;
}

.accent--secondary {
  color: #9ee8ff;
}

.empty-state {
  border-radius: 14px;
  border: 1px dashed rgba(120, 151, 235, 0.14);
  background: rgba(255,255,255,0.025);
  color: #8ea5d2;
  padding: 16px;
  text-align: center;
  font-size: 13px;
}

.modal-footer {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.action-button {
  height: 40px;
  padding: 0 16px;
  border-radius: 12px;
  border: 0;
  background: linear-gradient(135deg, #85dfff, #8fe6c6);
  color: #07101d;
  font-weight: 800;
  cursor: pointer;
}

.action-button:disabled {
  opacity: 0.6;
  cursor: wait;
}

.action-button--secondary {
  background: rgba(255,255,255,0.06);
  color: #dce8ff;
  border: 1px solid rgba(120, 151, 235, 0.12);
}

@media (max-width: 860px) {
  .modal-grid {
    grid-template-columns: 1fr;
  }

  .model-selector-grid {
    grid-template-columns: 1fr;
  }

  .model-vs {
    padding-bottom: 0;
    text-align: center;
  }
}

@media (max-width: 720px) {
  .modal-overlay {
    padding: 14px;
  }

  .modal-card {
    padding: 16px;
  }

  .comparison-table__head--three,
  .comparison-table__row--three {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .mini-bars {
    gap: 16px;
  }

  .mini-bars__item {
    width: 112px;
  }
}
</style>