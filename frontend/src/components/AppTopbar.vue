<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDatasetStore } from '../stores/useDatasetStore'

const router = useRouter()
const fileInputRef = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)

const { datasetState, uploadCsv } = useDatasetStore()

const datasetLabel = computed(() =>
    datasetState.isLoaded ? datasetState.name : 'Select CSV dataset',
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
</script>

<template>
  <header class="topbar">
    <div class="topbar__left">
    

      <button class="icon-button" type="button" aria-label="External link">
        ↗
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
        <span class="dataset-button__label">
          {{ isUploading ? 'Uploading CSV...' : `Dataset: ${datasetLabel}` }}
        </span>
        <span class="dataset-button__arrow">⌄</span>
      </button>

      <button class="icon-button" type="button" aria-label="Open dataset" @click="goToDataset">
        📁
      </button>

      <button class="icon-button" type="button" aria-label="Alerts">
        <span class="icon-button__badge">1</span>
        🔔
      </button>

      <button class="profile-button" type="button" aria-label="Profile">
        👤
      </button>
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

.hidden-file-input {
  display: none;
}

.icon-button,
.profile-button,
.dataset-button {
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: rgba(255, 255, 255, 0.035);
  color: #dce7ff;
  border-radius: 14px;
  height: 42px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

.icon-button,
.profile-button {
  width: 42px;
  display: grid;
  place-items: center;
  position: relative;
  cursor: pointer;
}

.profile-button {
  border-radius: 999px;
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
  width: 16px;
  height: 16px;
  border-radius: 999px;
  background: #ff6175;
  color: white;
  font-size: 10px;
  display: grid;
  place-items: center;
  border: 2px solid #10192d;
}

.icon-button__dot {
  position: absolute;
  top: 9px;
  right: 10px;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: #ff6175;
}

@media (max-width: 900px) {
  .dataset-button {
    min-width: 200px;
    max-width: 260px;
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
}
</style>