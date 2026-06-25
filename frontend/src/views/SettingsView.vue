<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import MainLayout from '../layouts/MainLayout.vue'
import RadiationChart from '../components/RadiationChart.vue'
import type { PipelineStatus } from '../types/api'
import { useNotificationSettingsStore } from '../stores/useNotificationSettingsStore'
import {
  getMeasurements,
  getModelInfo,
  getPipelineStatus,
  getSettings,
  getSummary,
  updateActiveModel,
  updateThreshold,
} from '../services/api'

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

interface AvailableModel {
  id: string
  name: string
  status: string
}

interface SelectedModels {
  modelA: string
  modelB: string
}

interface ModelComparisonItem {
  id: string
  model: string
  score: number | null
  modelScore?: number | null
  accuracy: number | null
  precision: number | null
  recall: number | null
  fpr: number | null
  fnr: number | null
  evaluationMode?: 'supervised' | 'unsupervised' | 'pending'
  totalRecords?: number
  totalAnomalies?: number
  anomalyRate?: number | null
  active: boolean
  status: string
}

interface ModelInfo {
  currentModel: string
  accuracy: number | null
  precision: number | null
  recall?: number | null
  fpr: number | null
  fnr?: number | null
  modelScore?: number | null
  evaluationMode?: 'supervised' | 'unsupervised' | 'pending'
  totalRecords?: number
  totalAnomalies?: number
  anomalyRate?: number | null
  source?: string
  availableModels?: AvailableModel[]
  selectedModels?: SelectedModels
  comparison?: ModelComparisonItem[]
}

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

const modelDescriptions: Record<string, string> = {
  isolation_forest: 'Unsupervised anomaly detection model currently used as the primary model.',
  lof: 'Local density-based anomaly detection model implemented for comparison with Isolation Forest.',
  rnn: 'Sequence-based neural network model planned for a future phase.',
}

const summary = ref<Summary | null>(null)
const modelInfo = ref<ModelInfo | null>(null)
const measurements = ref<Measurement[]>([])
const editableThreshold = ref(0.18)
const savedThreshold = ref(0.18)

const selectedModel = ref('isolation_forest')
const isModelDropdownOpen = ref(false)

const { notificationSettings, saveNotificationSettings } = useNotificationSettingsStore()

const isPreviewEnabled = ref(true)

const saveStatus = ref('')
const emailStatus = ref('')
const emailStatusType = ref<'success' | 'warning'>('success')
const isLoading = ref(true)
const isModelLoading = ref(false)
const isPipelineRunning = ref(false)
const pipelineStatus = ref<PipelineStatus | null>(null)
const errorMessage = ref('')

const thresholdNumber = computed(() => {
  return editableThreshold.value
})

const thresholdValue = computed(() => {
  return `${thresholdNumber.value.toFixed(2)} µSv/h`
})

const hasUnsavedThresholdChanges = computed(() => {
  return Math.abs(editableThreshold.value - savedThreshold.value) > 0.0001
})

const metricsAreStale = computed(() => {
  return hasUnsavedThresholdChanges.value || isPipelineRunning.value
})

const thresholdSliderMax = computed(() => {
  const maxLevel = summary.value?.maxLevel ?? 1

  return Math.max(1, maxLevel, thresholdNumber.value)
})

const thresholdPercent = computed(() => {
  const percent = (thresholdNumber.value / thresholdSliderMax.value) * 100

  return Math.min(100, Math.max(0, percent))
})

const thresholdFillStyle = computed(() => ({
  width: `${thresholdPercent.value}%`,
}))

const thresholdThumbStyle = computed(() => ({
  left: `calc(${thresholdPercent.value}% - 8px)`,
}))

const availableModels = computed(() => {
  const models = modelInfo.value?.availableModels

  if (models && models.length > 0) {
    return models
  }

  return fallbackModels
})

const selectedModelOption = computed(() => {
  return availableModels.value.find((model) => model.id === selectedModel.value) ?? availableModels.value[0]
})

const modelName = computed(() => {
  return selectedModelOption.value?.name ?? 'Detection Model'
})

const modelStatus = computed(() => {
  return selectedModelOption.value?.status ?? 'pending'
})

const isSelectedModelImplemented = computed(() => {
  return modelStatus.value === 'implemented'
})

const selectedModelMetrics = computed(() => {
  return modelInfo.value?.comparison?.find((item) => item.id === selectedModel.value) ?? null
})

const selectedEvaluationMode = computed(() => {
  return selectedModelMetrics.value?.evaluationMode ?? modelInfo.value?.evaluationMode ?? 'pending'
})

const isUnsupervisedModel = computed(() => {
  return selectedEvaluationMode.value === 'unsupervised'
})

const isSupervisedModel = computed(() => {
  return selectedEvaluationMode.value === 'supervised'
})

const modelMetricTitle = computed(() => {
  if (metricsAreStale.value) return 'Metrics Need Update'
  if (!isSelectedModelImplemented.value) return 'Model Status'
  if (isUnsupervisedModel.value) return 'Current Model Score'

  return 'Current Accuracy'
})

const primaryMetricValue = computed(() => {
  if (metricsAreStale.value) return 'Save required'
  if (!isSelectedModelImplemented.value) return 'Pending'

  if (isUnsupervisedModel.value) {
    const score =
        selectedModelMetrics.value?.modelScore ??
        selectedModelMetrics.value?.score ??
        modelInfo.value?.modelScore

    if (score === null || score === undefined) return 'N/A'

    return `${Number(score).toFixed(1)}%`
  }

  const accuracy = selectedModelMetrics.value?.accuracy ?? modelInfo.value?.accuracy

  if (accuracy === null || accuracy === undefined) return 'N/A'

  return `${Number(accuracy).toFixed(1)}%`
})

const precisionValue = computed(() => {
  if (metricsAreStale.value) return 'Save required'
  if (!isSelectedModelImplemented.value) return 'Pending'

  const precision = selectedModelMetrics.value?.precision ?? modelInfo.value?.precision

  if (precision === null || precision === undefined) return 'N/A'

  return Number(precision).toFixed(3)
})

const recallValue = computed(() => {
  if (metricsAreStale.value) return 'Save required'
  if (!isSelectedModelImplemented.value) return 'Pending'

  const recall = selectedModelMetrics.value?.recall ?? modelInfo.value?.recall

  if (recall === null || recall === undefined) return 'N/A'

  return Number(recall).toFixed(3)
})

const fprValue = computed(() => {
  if (metricsAreStale.value) return 'Save required'
  if (!isSelectedModelImplemented.value) return 'Pending'

  const fpr = selectedModelMetrics.value?.fpr ?? modelInfo.value?.fpr

  if (fpr === null || fpr === undefined) return 'N/A'

  return Number(fpr).toFixed(3)
})

const fnrValue = computed(() => {
  if (metricsAreStale.value) return 'Save required'
  if (!isSelectedModelImplemented.value) return 'Pending'

  const fnr = selectedModelMetrics.value?.fnr ?? modelInfo.value?.fnr

  if (fnr === null || fnr === undefined) return 'N/A'

  return Number(fnr).toFixed(3)
})

const detectedAnomaliesValue = computed(() => {
  if (metricsAreStale.value) return 'Save required'

  const totalAnomalies =
      selectedModelMetrics.value?.totalAnomalies ??
      modelInfo.value?.totalAnomalies ??
      summary.value?.totalAnomalies

  if (totalAnomalies === null || totalAnomalies === undefined) return 'N/A'

  return Number(totalAnomalies).toLocaleString()
})

const totalRecordsValue = computed(() => {
  if (metricsAreStale.value) return 'Save required'

  const totalRecords =
      selectedModelMetrics.value?.totalRecords ??
      modelInfo.value?.totalRecords ??
      summary.value?.totalMeasurements

  if (totalRecords === null || totalRecords === undefined) return 'N/A'

  return Number(totalRecords).toLocaleString()
})

const anomalyRateValue = computed(() => {
  if (metricsAreStale.value) return 'Save required'

  const anomalyRate = selectedModelMetrics.value?.anomalyRate ?? modelInfo.value?.anomalyRate

  if (anomalyRate !== null && anomalyRate !== undefined) {
    return `${Number(anomalyRate).toFixed(3)}%`
  }

  const totalRecords =
      selectedModelMetrics.value?.totalRecords ??
      modelInfo.value?.totalRecords ??
      summary.value?.totalMeasurements ??
      0

  const totalAnomalies =
      selectedModelMetrics.value?.totalAnomalies ??
      modelInfo.value?.totalAnomalies ??
      summary.value?.totalAnomalies ??
      0

  if (!totalRecords) return 'N/A'

  return `${((Number(totalAnomalies) / Number(totalRecords)) * 100).toFixed(3)}%`
})

const evaluationValue = computed(() => {
  if (metricsAreStale.value) return 'Save required'
  if (!isSelectedModelImplemented.value) return 'Pending'
  if (isUnsupervisedModel.value) return 'Unsupervised'
  if (isSupervisedModel.value) return 'Supervised'

  return 'Pending'
})

const metricCardOneLabel = computed(() => {
  return isUnsupervisedModel.value ? 'Detected Anomalies' : 'Precision'
})

const metricCardOneValue = computed(() => {
  return isUnsupervisedModel.value ? detectedAnomaliesValue.value : precisionValue.value
})

const metricCardTwoLabel = computed(() => {
  return isUnsupervisedModel.value ? 'Total Records' : 'Recall'
})

const metricCardTwoValue = computed(() => {
  return isUnsupervisedModel.value ? totalRecordsValue.value : recallValue.value
})

const metricCardThreeLabel = computed(() => {
  return isUnsupervisedModel.value ? 'Anomaly Rate' : 'FPR'
})

const metricCardThreeValue = computed(() => {
  return isUnsupervisedModel.value ? anomalyRateValue.value : fprValue.value
})

const metricCardFourLabel = computed(() => {
  return isUnsupervisedModel.value ? 'Evaluation' : 'FNR'
})

const metricCardFourValue = computed(() => {
  return isUnsupervisedModel.value ? evaluationValue.value : fnrValue.value
})

const unsavedThresholdMessage = computed(() => {
  if (!hasUnsavedThresholdChanges.value) return ''

  return `Unsaved threshold change. Save Changes to retrain models and update metrics. Last saved threshold: ${savedThreshold.value.toFixed(2)} µSv/h.`
})

const notificationSummary = computed(() => {
  if (!notificationSettings.emailAlertsEnabled && !notificationSettings.inAppAlertsEnabled) {
    return 'Notifications are currently disabled.'
  }

  const channels: string[] = []

  if (notificationSettings.emailAlertsEnabled) {
    channels.push('email')
  }

  if (notificationSettings.inAppAlertsEnabled) {
    channels.push('in-app')
  }

  return `${notificationSettings.selectedAlertSeverity} · ${notificationSettings.selectedNotificationFrequency} · ${channels.join(' + ')}`
})

const previewMeasurements = computed(() =>
    measurements.value.slice(-60),
)

const chartLabels = computed(() =>
    previewMeasurements.value.map((item) => formatChartLabel(item.timestamp)),
)

const chartValues = computed(() =>
    previewMeasurements.value.map((item) => item.radiationLevel),
)

const chartAnomalyFlags = computed(() =>
    previewMeasurements.value.map((item) => item.radiationLevel > editableThreshold.value),
)

const chartRenderKey = computed(() => {
  const firstLabel = chartLabels.value[0] ?? 'empty'
  const lastLabel = chartLabels.value[chartLabels.value.length - 1] ?? 'empty'

  return [
    selectedModel.value,
    editableThreshold.value.toFixed(2),
    chartValues.value.length,
    firstLabel,
    lastLabel,
  ].join('-')
})

const getModelDescription = (model: AvailableModel) => {
  return modelDescriptions[model.id] ?? 'Model configuration from backend.'
}

const isModelImplemented = (model: AvailableModel) => {
  return model.status === 'implemented'
}

const getModelStatusLabel = (model: AvailableModel) => {
  if (model.status === 'implemented') return 'Available'

  return 'Pending'
}

const toggleModelDropdown = () => {
  isModelDropdownOpen.value = !isModelDropdownOpen.value
}

const getSecondaryModelForComparison = (primaryModel: string) => {
  if (primaryModel !== 'isolation_forest') return 'isolation_forest'
  return 'lof'
}

const selectModel = async (model: AvailableModel) => {
  if (!isModelImplemented(model)) {
    return
  }

  selectedModel.value = model.id
  isModelDropdownOpen.value = false
  saveStatus.value = ''

  try {
    isModelLoading.value = true

    modelInfo.value = await getModelInfo(
        model.id,
        getSecondaryModelForComparison(model.id),
    ) as ModelInfo
  } catch (error) {
    console.error(error)
    saveStatus.value = 'Model info could not be loaded.'

    window.setTimeout(() => {
      saveStatus.value = ''
    }, 2500)
  } finally {
    isModelLoading.value = false
  }
}

const delay = (milliseconds: number) => {
  return new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds)
  })
}

const refreshSettingsDashboardData = async (threshold: number) => {
  const [summaryResponse, modelInfoResponse, measurementsResponse] = await Promise.all([
    getSummary(),
    getModelInfo(selectedModel.value, getSecondaryModelForComparison(selectedModel.value)),
    getMeasurements(200),
  ])

  summary.value = {
    ...(summaryResponse as Summary),
    threshold,
  }

  modelInfo.value = modelInfoResponse as ModelInfo
  measurements.value = measurementsResponse as Measurement[]
  editableThreshold.value = threshold
  savedThreshold.value = threshold
}

const waitForPipelineToFinish = async () => {
  const maxAttempts = 120

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    const status = await getPipelineStatus()
    pipelineStatus.value = status

    if (status.status === 'success') {
      return status
    }

    if (status.status === 'failed') {
      throw new Error(status.errorMessage ?? status.message ?? 'ML pipeline failed.')
    }

    if (status.status === 'running') {
      const elapsedSeconds = Math.round((attempt * 750) / 1000)
      saveStatus.value = `ML pipeline is running in background... ${elapsedSeconds}s`
    } else {
      saveStatus.value = 'Waiting for ML pipeline to start...'
    }

    await delay(750)
  }

  throw new Error('ML pipeline took too long to finish.')
}

const saveChanges = async () => {
  const selectedThreshold = editableThreshold.value

  try {
    saveStatus.value = 'Saving settings and starting ML pipeline...'

    await updateActiveModel(selectedModel.value)

    const settingsResponse = await updateThreshold(selectedThreshold)

    pipelineStatus.value = settingsResponse.pipeline ?? null
    isPipelineRunning.value = true

    saveNotificationSettings()

    summary.value = summary.value
        ? {
          ...summary.value,
          threshold: selectedThreshold,
        }
        : summary.value

    editableThreshold.value = selectedThreshold

    saveStatus.value = 'Threshold saved. ML pipeline started in background.'

    await waitForPipelineToFinish()

    saveStatus.value = 'ML pipeline finished. Reloading metrics...'
    isModelLoading.value = true

    await refreshSettingsDashboardData(selectedThreshold)

    saveStatus.value = `Settings saved. Models retrained with threshold ${selectedThreshold.toFixed(2)} µSv/h.`
  } catch (error) {
    console.error(error)
    saveStatus.value = error instanceof Error
        ? error.message
        : 'Settings could not be saved.'
  } finally {
    isPipelineRunning.value = false
    isModelLoading.value = false
  }

  window.setTimeout(() => {
    saveStatus.value = ''
  }, 5000)
}

const sendTestNotification = () => {
  if (!notificationSettings.emailAlertsEnabled && !notificationSettings.inAppAlertsEnabled) {
    emailStatus.value = 'Enable a notification channel first.'
    emailStatusType.value = 'warning'
  } else if (notificationSettings.emailAlertsEnabled && !notificationSettings.alertEmail.trim()) {
    emailStatus.value = 'Enter an email address first.'
    emailStatusType.value = 'warning'
  } else {
    emailStatus.value = 'Test notification sent.'
    emailStatusType.value = 'success'
  }

  window.setTimeout(() => {
    emailStatus.value = ''
  }, 2500)
}

const formatChartLabel = (timestamp: string) => {
  const parts = timestamp.split(' ')
  return parts[1]?.slice(0, 5) ?? timestamp
}

const loadSettingsData = async () => {
  try {
    isLoading.value = true
    errorMessage.value = ''

    const [settingsResponse, summaryResponse, measurementsResponse] = await Promise.all([
      getSettings(),
      getSummary(),
      getMeasurements(200),
    ])

    selectedModel.value = settingsResponse.activeModel || 'isolation_forest'

    const modelInfoResponse = await getModelInfo(
        selectedModel.value,
        getSecondaryModelForComparison(selectedModel.value),
    )

    summary.value = summaryResponse as Summary
    editableThreshold.value = summaryResponse.threshold
    savedThreshold.value = summaryResponse.threshold

    const loadedModelInfo = modelInfoResponse as ModelInfo
    modelInfo.value = loadedModelInfo

    if (loadedModelInfo.selectedModels?.modelA) {
      selectedModel.value = loadedModelInfo.selectedModels.modelA
    }

    measurements.value = measurementsResponse as Measurement[]
  } catch (error) {
    console.error(error)
    errorMessage.value = 'Backend settings data could not be loaded.'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadSettingsData()
})
</script>

<template>
  <MainLayout>
    <div class="settings-page">
      <section class="panel threshold-panel">
        <h1>Settings</h1>

        <div v-if="errorMessage" class="feedback">
          {{ errorMessage }}
        </div>

        <div class="threshold-block">
          <div class="threshold-header">
            <h2>Detection Threshold</h2>
          </div>

          <div class="threshold-row">
            <span>Radiation Level Threshold</span>
            <strong>{{ isLoading ? 'Loading...' : thresholdValue }}</strong>
          </div>

          <div class="slider">
            <div class="slider__fill" :style="thresholdFillStyle"></div>
            <div class="slider__thumb" :style="thresholdThumbStyle"></div>

            <input
                v-model.number="editableThreshold"
                class="slider-input"
                type="range"
                min="0"
                max="1"
                step="0.01"
            />
          </div>
        </div>

        <div class="model-block">
          <div class="model-block__header">
            <h2>Anomaly Detection Model</h2>
            <div class="accuracy-box">
              <span>{{ modelMetricTitle }}</span>
              <strong>{{ isLoading || isModelLoading ? 'Loading...' : primaryMetricValue }}</strong>
            </div>
          </div>

          <div class="select-row">
            <span>Active Detection Model</span>

            <div class="model-select">
              <button
                  class="select-button"
                  type="button"
                  @click="toggleModelDropdown"
              >
                {{ modelName }} ⌄
              </button>

              <div v-if="isModelDropdownOpen" class="model-dropdown">
                <button
                    v-for="model in availableModels"
                    :key="model.id"
                    class="model-option"
                    :class="{
                    'model-option--active': selectedModel === model.id,
                    'model-option--disabled': !isModelImplemented(model),
                  }"
                    type="button"
                    :disabled="!isModelImplemented(model)"
                    @click="selectModel(model)"
                >
                  <div class="model-option__top">
                    <strong>{{ model.name }}</strong>
                    <span
                        class="model-status"
                        :class="{
                        'model-status--available': isModelImplemented(model),
                        'model-status--pending': !isModelImplemented(model),
                      }"
                    >
                      {{ getModelStatusLabel(model) }}
                    </span>
                  </div>

                  <span>{{ getModelDescription(model) }}</span>
                </button>
              </div>
            </div>
          </div>

          <p v-if="unsavedThresholdMessage" class="unsaved-warning">
            {{ unsavedThresholdMessage }}
          </p>

          <div class="config-grid">
            <div class="config-item">
              <span>{{ metricCardOneLabel }}</span>
              <strong>{{ metricCardOneValue }}</strong>
            </div>
            <div class="config-item">
              <span>{{ metricCardTwoLabel }}</span>
              <strong>{{ metricCardTwoValue }}</strong>
            </div>
            <div class="config-item">
              <span>{{ metricCardThreeLabel }}</span>
              <strong>{{ metricCardThreeValue }}</strong>
            </div>
            <div class="config-item">
              <span>{{ metricCardFourLabel }}</span>
              <strong>{{ metricCardFourValue }}</strong>
            </div>
          </div>

          <div class="save-row">
            <button
                class="save-button"
                type="button"
                :disabled="isPipelineRunning || isModelLoading"
                @click="saveChanges"
            >
              {{ isPipelineRunning ? 'Retraining...' : 'Save Changes' }}
            </button>
            <span v-if="saveStatus" class="feedback feedback--success">{{ saveStatus }}</span>
          </div>
        </div>

        <div class="notifications-block">
          <div class="notifications-header">
            <div>
              <h2>Notification Settings</h2>
              <p>{{ notificationSummary }}</p>
            </div>
          </div>

          <div class="notification-layout">
            <div class="notification-column">
              <div class="notification-section-title">
                <span>Alert Channels</span>
                <small>Choose where the warning should appear.</small>
              </div>

              <button
                  class="channel-card"
                  :class="{ 'channel-card--active': notificationSettings.emailAlertsEnabled }"
                  type="button"
                  @click="notificationSettings.emailAlertsEnabled = !notificationSettings.emailAlertsEnabled"
              >
                <div>
                  <strong>Email alerts</strong>
                  <span>Send alert message to the configured email address.</span>
                </div>
                <span
                    class="toggle"
                    :class="{ 'toggle--on': notificationSettings.emailAlertsEnabled }"
                ></span>
              </button>

              <button
                  class="channel-card"
                  :class="{ 'channel-card--active': notificationSettings.inAppAlertsEnabled }"
                  type="button"
                  @click="notificationSettings.inAppAlertsEnabled = !notificationSettings.inAppAlertsEnabled"
              >
                <div>
                  <strong>In-app alerts</strong>
                  <span>Show active warning inside the monitoring dashboard.</span>
                </div>
                <span
                    class="toggle"
                    :class="{ 'toggle--on': notificationSettings.inAppAlertsEnabled }"
                ></span>
              </button>
            </div>

            <div class="notification-column">
              <div class="notification-section-title">
                <span>Alert Rules</span>
                <small>Choose which anomaly severity should trigger alerts.</small>
              </div>

              <div class="option-group">
                <button
                    type="button"
                    :class="{ 'option-button--active': notificationSettings.selectedAlertSeverity === 'Critical only' }"
                    class="option-button"
                    @click="notificationSettings.selectedAlertSeverity = 'Critical only'"
                >
                  Critical only
                </button>
                <button
                    type="button"
                    :class="{ 'option-button--active': notificationSettings.selectedAlertSeverity === 'High + Critical' }"
                    class="option-button"
                    @click="notificationSettings.selectedAlertSeverity = 'High + Critical'"
                >
                  High + Critical
                </button>
                <button
                    type="button"
                    :class="{ 'option-button--active': notificationSettings.selectedAlertSeverity === 'All anomalies' }"
                    class="option-button"
                    @click="notificationSettings.selectedAlertSeverity = 'All anomalies'"
                >
                  All anomalies
                </button>
              </div>

              <div class="notification-section-title notification-section-title--spaced">
                <span>Delivery</span>
                <small>Choose how often alert messages are delivered.</small>
              </div>

              <div class="option-group">
                <button
                    type="button"
                    :class="{ 'option-button--active': notificationSettings.selectedNotificationFrequency === 'Immediate' }"
                    class="option-button"
                    @click="notificationSettings.selectedNotificationFrequency = 'Immediate'"
                >
                  Immediate
                </button>
                <button
                    type="button"
                    :class="{ 'option-button--active': notificationSettings.selectedNotificationFrequency === 'Daily summary' }"
                    class="option-button"
                    @click="notificationSettings.selectedNotificationFrequency = 'Daily summary'"
                >
                  Daily summary
                </button>
              </div>
            </div>
          </div>

          <div class="alert-email-row">
            <div>
              <span>Alert email</span>
              <small>Used only when Email alerts are enabled.</small>
            </div>

            <input
                v-model="notificationSettings.alertEmail"
                class="input-box input-box--editable"
                type="email"
                placeholder="alert@gmail.com"
                :disabled="!notificationSettings.emailAlertsEnabled"
            />
          </div>

          <div class="send-row">
            <button class="send-button" type="button" @click="sendTestNotification">
              Send Test Notification
            </button>
            <span
                v-if="emailStatus"
                class="notification-feedback"
                :class="`notification-feedback--${emailStatusType}`"
            >
              {{ emailStatus }}
            </span>
          </div>
        </div>

        <div
            class="preview-block"
            :class="{ 'preview-block--collapsed': !isPreviewEnabled }"
        >
          <div class="preview-header">
            <div>
              <h2>Threshold Preview</h2>
              <p v-if="!isPreviewEnabled">Preview is hidden. Enable it to inspect threshold impact on recent measurements.</p>
            </div>

            <button
                class="mini-toggle"
                :class="{ 'mini-toggle--off': !isPreviewEnabled }"
                type="button"
                @click="isPreviewEnabled = !isPreviewEnabled"
                :aria-label="isPreviewEnabled ? 'Hide threshold preview' : 'Show threshold preview'"
            ></button>
          </div>

          <div v-if="isPreviewEnabled" class="preview-chart">
            <RadiationChart
                :key="chartRenderKey"
                :labels="chartLabels.length ? chartLabels : undefined"
                :values="chartValues.length ? chartValues : undefined"
                :threshold="editableThreshold"
                :anomaly-flags="chartAnomalyFlags"
            />
          </div>
        </div>
      </section>
    </div>
  </MainLayout>
</template>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel {
  padding: 20px;
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

.panel h1 {
  margin-bottom: 18px;
  color: #eef4ff;
  font-size: 32px;
}

.threshold-block,
.model-block,
.notifications-block,
.preview-block {
  margin-bottom: 18px;
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(120, 151, 235, 0.1);
  background: rgba(255,255,255,0.03);
}

.threshold-header,
.preview-header,
.model-block__header,
.select-row,
.toggle-row,
.input-row,
.save-row,
.send-row,
.notifications-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.threshold-header,
.model-block__header,
.preview-header,
.notifications-header {
  margin-bottom: 14px;
}

.threshold-block h2,
.model-block h2,
.notifications-block h2,
.preview-block h2 {
  color: #eef4ff;
  font-size: 20px;
}

.notifications-header p,
.preview-header p,
.model-description {
  margin-top: 6px;
  color: #90a5cd;
  font-size: 13px;
  line-height: 1.4;
}

.threshold-row {
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #b7c7e4;
}

.threshold-row strong {
  color: #ffb36a;
}

.slider {
  position: relative;
  height: 8px;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
}

.slider__fill {
  width: 82%;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #ff8c68, #ffb16f);
}

.slider__thumb {
  position: absolute;
  top: 50%;
  left: calc(82% - 8px);
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: #ffd6c6;
  transform: translateY(-50%);
  box-shadow:
      0 0 12px rgba(255, 160, 120, 0.45),
      0 0 0 4px rgba(255, 160, 120, 0.12);
  pointer-events: none;
}

.accuracy-box {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  color: #90a5cd;
}

.accuracy-box strong {
  color: #7ef0bf;
  font-size: 30px;
}

.select-row,
.toggle-row,
.input-row {
  margin-bottom: 14px;
  color: #b7c7e4;
}

.select-button,
.save-button,
.send-button {
  height: 38px;
  padding: 0 16px;
  border-radius: 10px;
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: rgba(255,255,255,0.05);
  color: #dbe8ff;
  cursor: pointer;
}

.model-select {
  position: relative;
}

.model-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  z-index: 20;
  width: 380px;
  padding: 8px;
  border-radius: 14px;
  border: 1px solid rgba(120, 151, 235, 0.14);
  background: rgba(9, 14, 28, 0.98);
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
}

.model-option {
  width: 100%;
  padding: 12px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  color: #dbe8ff;
  text-align: left;
  cursor: pointer;
}

.model-option__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 4px;
}

.model-option strong {
  display: block;
  color: #eef4ff;
}

.model-option span {
  color: #90a5cd;
  font-size: 12px;
  line-height: 1.4;
}

.model-option:hover,
.model-option--active {
  background: rgba(107, 158, 255, 0.1);
  border-color: rgba(107, 158, 255, 0.16);
}

.model-option--disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.model-option--disabled:hover {
  background: transparent;
  border-color: transparent;
}

.model-status {
  flex: 0 0 auto;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 11px !important;
  font-weight: 700;
}

.model-status--available {
  background: rgba(126, 240, 191, 0.12);
  color: #7ef0bf !important;
  border: 1px solid rgba(126, 240, 191, 0.18);
}

.model-status--pending {
  background: rgba(255, 179, 106, 0.1);
  color: #ffb36a !important;
  border: 1px solid rgba(255, 179, 106, 0.16);
}

.config-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.config-item {
  min-height: 64px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.05);
  background: rgba(255,255,255,0.02);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}

.config-item span,
.input-row span {
  color: #90a5cd;
}

.config-item strong,
.input-box {
  color: #eef4ff;
}

.unsaved-warning {
  margin: 8px 0 14px;
  color: #ffcf9a;
  font-size: 13px;
  line-height: 1.4;
}

.save-row,
.send-row {
  margin-top: 16px;
  justify-content: flex-start;
}

.feedback {
  color: #8fe6c6;
  font-size: 14px;
}

.feedback--success {
  color: #7ef0bf;
}

.notification-feedback {
  font-size: 14px;
}

.notification-feedback--success {
  color: #7ef0bf;
}

.notification-feedback--warning {
  color: #ffb36a;
}

.notification-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.notification-column {
  min-height: 180px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.05);
  background: rgba(255,255,255,0.02);
}

.notification-section-title {
  margin-bottom: 12px;
}

.notification-section-title--spaced {
  margin-top: 18px;
}

.notification-section-title span,
.alert-email-row span {
  display: block;
  color: #eef4ff;
  font-weight: 700;
  margin-bottom: 4px;
}

.notification-section-title small,
.alert-email-row small,
.channel-card span {
  color: #90a5cd;
  font-size: 12px;
  line-height: 1.4;
}

.channel-card {
  width: 100%;
  min-height: 74px;
  margin-bottom: 10px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(120, 151, 235, 0.1);
  background: rgba(255,255,255,0.025);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  text-align: left;
  cursor: pointer;
}

.channel-card strong {
  display: block;
  margin-bottom: 4px;
  color: #eef4ff;
}

.channel-card--active {
  background: rgba(126, 240, 191, 0.06);
  border-color: rgba(126, 240, 191, 0.16);
}

.toggle {
  width: 48px;
  height: 26px;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  position: relative;
  border: 1px solid rgba(120, 151, 235, 0.12);
  padding: 0;
  flex: 0 0 auto;
}

.toggle::after,
.mini-toggle::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: #d8ecff;
  transition: left 0.18s ease;
}

.toggle--on::after {
  left: 23px;
}

.toggle--on,
.mini-toggle:not(.mini-toggle--off) {
  background: rgba(126, 240, 191, 0.18);
  border: 1px solid rgba(126, 240, 191, 0.18);
}

.option-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.option-button {
  min-height: 34px;
  padding: 0 11px;
  border-radius: 999px;
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: rgba(255,255,255,0.04);
  color: #9fb1d1;
  cursor: pointer;
  font-size: 12px;
}

.option-button--active {
  color: #dff8ee;
  background: rgba(126, 240, 191, 0.12);
  border-color: rgba(126, 240, 191, 0.2);
}

.alert-email-row {
  margin-top: 14px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.05);
  background: rgba(255,255,255,0.02);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.input-box {
  min-width: 260px;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid rgba(120, 151, 235, 0.1);
  background: rgba(255,255,255,0.03);
  display: flex;
  align-items: center;
  color: #eef4ff;
}

.input-box--editable {
  outline: none;
  font: inherit;
}

.input-box--editable:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.input-box--editable::placeholder {
  color: #6f83aa;
}

.mini-toggle {
  width: 44px;
  height: 24px;
  border-radius: 999px;
  position: relative;
  border: 1px solid rgba(126, 240, 191, 0.18);
  cursor: pointer;
  padding: 0;
  appearance: none;
  flex: 0 0 auto;
}

.mini-toggle::after {
  top: 2px;
  left: 21px;
  width: 18px;
  height: 18px;
}

.mini-toggle--off {
  background: rgba(255,255,255,0.08);
  border-color: rgba(120, 151, 235, 0.12);
}

.mini-toggle--off::after {
  left: 3px;
}

.preview-block--collapsed {
  padding-bottom: 12px;
}

.preview-chart {
  height: 320px;
}

@media (max-width: 900px) {
  .config-grid,
  .notification-layout {
    grid-template-columns: 1fr;
  }

  .threshold-row,
  .select-row,
  .model-block__header,
  .save-row,
  .send-row,
  .preview-header,
  .notifications-header,
  .alert-email-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .model-select,
  .select-button,
  .input-box {
    min-width: 0;
    width: 100%;
  }

  .model-dropdown {
    left: 0;
    right: auto;
    width: min(380px, 100%);
  }
}

.slider-input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 3;
}

.save-button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>