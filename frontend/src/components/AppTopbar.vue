<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getAnomalies } from '../services/api'
import { useDatasetStore } from '../stores/useDatasetStore'
import { useNotificationSettingsStore } from '../stores/useNotificationSettingsStore'
import type { Measurement } from '../types/api'

const props = defineProps<{
  isSidebarCollapsed?: boolean
}>()

const emit = defineEmits<{
  (event: 'toggle-sidebar'): void
}>()

const router = useRouter()
const fileInputRef = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const isAlertsOpen = ref(false)
const isProfileOpen = ref(false)
const isAlertsLoading = ref(false)
const alertError = ref('')
const recentAlerts = ref<Measurement[]>([])

const { datasetState, uploadCsv } = useDatasetStore()
const { notificationSettings } = useNotificationSettingsStore()

const datasetLabel = computed(() =>
    datasetState.isLoaded ? datasetState.name : 'Select CSV dataset',
)

const inAppAlertsEnabled = computed(() => notificationSettings.inAppAlertsEnabled)

const visibleAlertCount = computed(() => {
  if (!inAppAlertsEnabled.value) return 0

  return recentAlerts.value.length
})

const alertButtonLabel = computed(() => {
  if (!inAppAlertsEnabled.value) return 'In-app alerts disabled'
  if (visibleAlertCount.value === 0) return 'No active in-app alerts'

  return `${visibleAlertCount.value} active in-app alerts`
})

const sidebarButtonLabel = computed(() => {
  return props.isSidebarCollapsed ? 'Show sidebar' : 'Hide sidebar'
})

const loadAlertFeed = async () => {
  if (!inAppAlertsEnabled.value) {
    recentAlerts.value = []
    return
  }

  try {
    isAlertsLoading.value = true
    alertError.value = ''
    recentAlerts.value = await getAnomalies(6)
  } catch (error) {
    console.error(error)
    alertError.value = 'Alerts could not be loaded from backend.'
  } finally {
    isAlertsLoading.value = false
  }
}

const toggleSidebar = () => {
  emit('toggle-sidebar')
}

const toggleAlerts = async () => {
  isAlertsOpen.value = !isAlertsOpen.value
  isProfileOpen.value = false

  if (isAlertsOpen.value) {
    await loadAlertFeed()
  }
}

const toggleProfile = () => {
  isProfileOpen.value = !isProfileOpen.value
  isAlertsOpen.value = false
}

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
    isUploading.value = true
    await uploadCsv(file)
    await router.push('/dataset')
  } catch (error) {
    console.error(error)
    alert('The CSV file could not be loaded.')
  } finally {
    isUploading.value = false
    target.value = ''
  }
}

const goToDataset = () => {
  router.push('/dataset')
}

const goToSettings = () => {
  isAlertsOpen.value = false
  isProfileOpen.value = false
  router.push('/settings')
}

const goToHelp = () => {
  isProfileOpen.value = false
  router.push('/help')
}

const goToDashboard = () => {
  isProfileOpen.value = false
  router.push('/')
}

const formatAlertTime = (timestamp: string) => {
  const parts = timestamp.split(' ')
  return parts[1]?.slice(0, 5) ?? timestamp
}

watch(
    () => notificationSettings.inAppAlertsEnabled,
    (enabled) => {
      if (enabled) {
        loadAlertFeed()
      } else {
        recentAlerts.value = []
        isAlertsOpen.value = false
      }
    },
)

onMounted(() => {
  loadAlertFeed()
})
</script>

<template>
  <header class="topbar">
    <div class="topbar__left">
      <button
          class="sidebar-toggle"
          :class="{ 'sidebar-toggle--collapsed': props.isSidebarCollapsed }"
          type="button"
          :aria-expanded="!props.isSidebarCollapsed"
          :aria-label="sidebarButtonLabel"
          @click="toggleSidebar"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M15 6L9 12L15 18" />
        </svg>
      </button>
    </div>

    <div class="topbar__right">
      <input
          ref="fileInputRef"
          type="file"
          accept=".csv"
          class="hidden-file-input"
          @change="handleFileChange"
      />

      <button
          class="dataset-button"
          type="button"
          :disabled="isUploading"
          @click="openFilePicker"
      >
        <span class="dataset-icon">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 7.5C4 6.7 4.7 6 5.5 6H10L12 8H18.5C19.3 8 20 8.7 20 9.5V17.5C20 18.3 19.3 19 18.5 19H5.5C4.7 19 4 18.3 4 17.5V7.5Z" />
          </svg>
        </span>

        <span class="dataset-button__label">
          {{ isUploading ? 'Uploading CSV...' : datasetLabel }}
        </span>

        <span class="dataset-button__arrow">⌄</span>
      </button>

      <button class="icon-button" type="button" aria-label="Open dataset" @click="goToDataset">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 7.5C4 6.7 4.7 6 5.5 6H10L12 8H18.5C19.3 8 20 8.7 20 9.5V17.5C20 18.3 19.3 19 18.5 19H5.5C4.7 19 4 18.3 4 17.5V7.5Z" />
        </svg>
      </button>

      <div class="topbar-menu">
        <button
            class="icon-button alert-button"
            :class="{ 'icon-button--muted': !inAppAlertsEnabled }"
            type="button"
            :aria-label="alertButtonLabel"
            @click="toggleAlerts"
        >
          <span v-if="visibleAlertCount > 0" class="icon-button__badge">{{ visibleAlertCount }}</span>

          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M18 9.8C18 6.6 15.6 4 12 4C8.4 4 6 6.6 6 9.8V13.6L4.8 16.2C4.6 16.7 4.9 17.2 5.4 17.2H18.6C19.1 17.2 19.4 16.7 19.2 16.2L18 13.6V9.8Z" />
            <path d="M9.8 19C10.2 19.9 11 20.5 12 20.5C13 20.5 13.8 19.9 14.2 19" />
          </svg>
        </button>

        <div v-if="isAlertsOpen" class="dropdown-panel alerts-panel">
          <div class="dropdown-panel__header">
            <div>
              <strong>In-app alerts</strong>
              <span>{{ notificationSettings.selectedAlertSeverity }} · {{ notificationSettings.selectedNotificationFrequency }}</span>
            </div>
            <button class="text-button" type="button" @click="goToSettings">Settings</button>
          </div>

          <div v-if="!inAppAlertsEnabled" class="empty-state">
            <strong>In-app alerts are turned off.</strong>
            <span>Enable them in Settings to show anomaly warnings here.</span>
          </div>

          <div v-else-if="isAlertsLoading" class="empty-state">
            <strong>Loading alerts...</strong>
            <span>Reading recent anomaly events from the backend.</span>
          </div>

          <div v-else-if="alertError" class="empty-state empty-state--warning">
            <strong>{{ alertError }}</strong>
            <span>Check whether the backend server is running.</span>
          </div>

          <div v-else-if="recentAlerts.length === 0" class="empty-state">
            <strong>No active alerts.</strong>
            <span>The latest measurements are within the configured rules.</span>
          </div>

          <div v-else class="alert-list">
            <article v-for="item in recentAlerts" :key="`${item.timestamp}-${item.sensorId}`" class="alert-item">
              <div class="alert-item__top">
                <strong>{{ item.anomalyType || 'Radiation anomaly' }}</strong>
                <span>{{ formatAlertTime(item.timestamp) }}</span>
              </div>
              <p>{{ item.location }} · {{ item.sensorId }}</p>
              <div class="alert-item__meta">
                <span>{{ item.radiationLevel.toFixed(2) }} µSv/h</span>
                <span>score {{ item.anomalyScore.toFixed(2) }}</span>
              </div>
            </article>
          </div>
        </div>
      </div>

      <div class="topbar-menu">
        <button class="profile-button" type="button" aria-label="Profile" @click="toggleProfile">
          <span class="profile-avatar">
            <span>RM</span>
          </span>

          <span class="profile-button__text">
            <strong>Operator Console</strong>
            <small>Monitoring session</small>
          </span>

          <svg class="profile-chevron" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7 10L12 15L17 10" />
          </svg>
        </button>

        <div v-if="isProfileOpen" class="dropdown-panel profile-panel">
          <div class="profile-header">
            <span class="profile-avatar profile-avatar--large">
              <span>RM</span>
            </span>

            <div>
              <strong>Radiation Monitor</strong>
              <span>Prototype workspace</span>
            </div>
          </div>

          <div class="profile-status">
            <div>
              <span>Status</span>
              <strong>Active session</strong>
            </div>
            <span class="online-pill">
              <span></span>
              Online
            </span>
          </div>

          <div class="profile-grid">
            <div>
              <span>Role</span>
              <strong>Operator</strong>
            </div>

            <div>
              <span>Dataset</span>
              <strong>{{ datasetState.isLoaded ? 'CSV loaded' : 'Demo mode' }}</strong>
            </div>
          </div>

          <div class="profile-actions">
            <button type="button" @click="goToDashboard">
              <span>Dashboard overview</span>
              <small>Open monitoring dashboard</small>
            </button>

            <button type="button" @click="goToSettings">
              <span>System settings</span>
              <small>Thresholds, alerts and model config</small>
            </button>

            <button type="button" @click="goToHelp">
              <span>Help & documentation</span>
              <small>Usage guide and FAQ</small>
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  height: 70px;
  padding: 0 12px;
  border-bottom: 1px solid rgba(120, 151, 235, 0.08);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 14px;
  background: linear-gradient(180deg, rgba(9, 13, 27, 0.78), rgba(9, 13, 27, 0.18));
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 50;
}

.topbar__left,
.topbar__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.topbar__left {
  margin-right: auto;
}

.topbar-menu {
  position: relative;
}

.hidden-file-input {
  display: none;
}

.sidebar-toggle,
.icon-button,
.profile-button,
.dataset-button {
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: rgba(255, 255, 255, 0.035);
  color: #dce7ff;
  border-radius: 14px;
  height: 42px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
  transition: 0.18s ease;
}

.sidebar-toggle:hover,
.icon-button:hover,
.profile-button:hover,
.dataset-button:hover:not(:disabled) {
  border-color: rgba(119, 215, 255, 0.24);
  background: rgba(119, 215, 255, 0.055);
}

.sidebar-toggle {
  width: 42px;
  display: grid;
  place-items: center;
  cursor: pointer;
}

.sidebar-toggle svg {
  width: 20px;
  height: 20px;
  transition: transform 0.18s ease;
}

.sidebar-toggle--collapsed svg {
  transform: rotate(180deg);
}

.sidebar-toggle path,
.icon-button path,
.dataset-icon path,
.profile-chevron path {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.icon-button,
.profile-button {
  display: grid;
  place-items: center;
  position: relative;
  cursor: pointer;
}

.icon-button {
  width: 42px;
}

.icon-button svg {
  width: 20px;
  height: 20px;
}

.alert-button {
  color: #dce7ff;
}

.alert-button:hover {
  color: #ffffff;
}

.icon-button--muted {
  opacity: 0.55;
}

.dataset-button {
  min-width: 290px;
  max-width: 420px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  cursor: pointer;
  color: #cad6ef;
  font-size: 14px;
}

.dataset-button:disabled {
  opacity: 0.72;
  cursor: wait;
}

.dataset-icon {
  width: 20px;
  height: 20px;
  color: #9fcfff;
  flex: 0 0 auto;
}

.dataset-icon svg {
  width: 20px;
  height: 20px;
}

.dataset-button__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dataset-button__arrow {
  color: #7c8fb8;
}

.icon-button__badge {
  position: absolute;
  top: -4px;
  right: -2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: #ff6175;
  color: white;
  font-size: 10px;
  display: grid;
  place-items: center;
  border: 2px solid #10192d;
}

.profile-button {
  min-width: 214px;
  padding: 0 10px 0 6px;
  border-radius: 999px;
  grid-template-columns: 34px 1fr 18px;
  gap: 9px;
  text-align: left;
}

.profile-avatar {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background:
      radial-gradient(circle at 35% 20%, rgba(126, 240, 191, 0.24), transparent 46%),
      linear-gradient(135deg, rgba(119, 215, 255, 0.16), rgba(126, 240, 191, 0.1));
  color: #eef4ff;
  border: 1px solid rgba(119, 215, 255, 0.18);
  box-shadow: 0 0 18px rgba(119, 215, 255, 0.08);
}

.profile-avatar span {
  display: block;
  margin: 0;
  color: #eef4ff;
  font-size: 11px;
  font-weight: 850;
  letter-spacing: 0.03em;
  line-height: 1;
}

.profile-avatar--large {
  width: 44px;
  height: 44px;
}

.profile-button__text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}

.profile-button__text strong {
  font-size: 12px;
  color: #eef4ff;
  white-space: nowrap;
}

.profile-button__text small {
  font-size: 11px;
  color: #8193bb;
  white-space: nowrap;
}

.profile-chevron {
  width: 17px;
  height: 17px;
  color: #7f91b4;
}

.dropdown-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 80;
  width: 360px;
  padding: 12px;
  border-radius: 18px;
  border: 1px solid rgba(120, 151, 235, 0.14);
  background:
      radial-gradient(circle at top right, rgba(119, 215, 255, 0.08), transparent 35%),
      rgba(9, 14, 28, 0.98);
  box-shadow: 0 22px 70px rgba(0, 0, 0, 0.42);
  backdrop-filter: blur(16px);
}

.dropdown-panel__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  padding: 4px 4px 12px;
  border-bottom: 1px solid rgba(120, 151, 235, 0.08);
}

.dropdown-panel__header strong {
  display: block;
  color: #eef4ff;
  font-size: 14px;
}

.dropdown-panel__header span {
  display: block;
  margin-top: 4px;
  color: #8193bb;
  font-size: 12px;
}

.text-button {
  border: 0;
  background: transparent;
  color: #77d7ff;
  font-size: 12px;
  cursor: pointer;
}

.empty-state {
  padding: 18px 8px 8px;
}

.empty-state strong {
  display: block;
  color: #eef4ff;
  margin-bottom: 6px;
}

.empty-state span {
  color: #90a5cd;
  font-size: 13px;
  line-height: 1.4;
}

.empty-state--warning strong {
  color: #ffb36a;
}

.alert-list {
  max-height: 360px;
  overflow: auto;
  padding-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.alert-item {
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(255, 97, 117, 0.14);
  background: rgba(255, 97, 117, 0.055);
}

.alert-item__top,
.alert-item__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.alert-item__top strong {
  color: #ffe5e9;
  font-size: 13px;
}

.alert-item__top span,
.alert-item p,
.alert-item__meta span {
  color: #9fb0d0;
  font-size: 12px;
}

.alert-item p {
  margin: 6px 0 10px;
}

.alert-item__meta span {
  padding: 5px 8px;
  border-radius: 999px;
  background: rgba(255,255,255,0.045);
}

.profile-panel {
  width: 330px;
}

.profile-header {
  padding: 4px 4px 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(120, 151, 235, 0.08);
}

.profile-header strong {
  display: block;
  color: #eef4ff;
  font-size: 14px;
}

.profile-header > div > span {
  display: block;
  color: #8193bb;
  font-size: 12px;
  margin-top: 4px;
}

.profile-status {
  margin-top: 12px;
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(126, 240, 191, 0.13);
  background: rgba(126, 240, 191, 0.045);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.profile-status span,
.profile-grid span {
  display: block;
  color: #8193bb;
  font-size: 12px;
  margin-bottom: 4px;
}

.profile-status strong,
.profile-grid strong {
  display: block;
  color: #eef4ff;
  font-size: 13px;
}

.online-pill {
  margin: 0 !important;
  padding: 6px 9px;
  border-radius: 999px;
  border: 1px solid rgba(126, 240, 191, 0.17);
  background: rgba(126, 240, 191, 0.08);
  color: #9ff4cd !important;
  font-size: 11px !important;
  font-weight: 750;
  display: inline-flex !important;
  align-items: center;
  gap: 6px;
}

.online-pill span {
  width: 6px;
  height: 6px;
  margin: 0 !important;
  border-radius: 999px;
  background: #7ef0bf;
  box-shadow: 0 0 10px rgba(126, 240, 191, 0.55);
}

.profile-grid {
  margin-top: 10px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.profile-grid div {
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.05);
  background: rgba(255,255,255,0.025);
}

.profile-actions {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.profile-actions button {
  width: 100%;
  padding: 11px 12px;
  border: 0;
  border-radius: 13px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: 0.16s ease;
}

.profile-actions button:hover {
  background: rgba(119, 215, 255, 0.06);
}

.profile-actions span {
  display: block;
  color: #dce8ff;
  font-size: 13px;
  font-weight: 700;
}

.profile-actions small {
  display: block;
  margin-top: 4px;
  color: #8193bb;
  font-size: 12px;
  line-height: 1.35;
}

@media (max-width: 900px) {
  .dataset-button {
    min-width: 200px;
    max-width: 260px;
  }

  .profile-button {
    min-width: 42px;
    width: 42px;
    padding: 0;
    grid-template-columns: 1fr;
  }

  .profile-button__text,
  .profile-chevron {
    display: none;
  }
}

@media (max-width: 768px) {
  .topbar {
    padding-inline: 10px;
  }

  .dataset-button {
    min-width: 0;
    width: 190px;
    font-size: 13px;
  }

  .dropdown-panel {
    width: min(340px, calc(100vw - 28px));
  }
}

@media (max-width: 560px) {
  .dataset-button {
    display: none;
  }
}
</style>