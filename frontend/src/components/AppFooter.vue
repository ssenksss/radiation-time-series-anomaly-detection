<script setup lang="ts">
import { computed } from 'vue'
import { useDatasetStore } from '../stores/useDatasetStore'

const { datasetState } = useDatasetStore()

const currentYear = new Date().getFullYear()

const datasetText = computed(() => {
  if (!datasetState.isLoaded) return 'Demo dataset active'

  return `${datasetState.rows.length.toLocaleString()} measurements loaded`
})
</script>

<template>
  <footer class="app-footer">
    <div class="app-footer__inner">
      <div class="app-footer__left">
        <span>Radiation Monitoring Prototype</span>
        <span class="separator">•</span>
        <span>Bachelor Thesis Project</span>
      </div>

      <div class="app-footer__right">
        <span>All rights reserved</span>
        <span class="separator">•</span>
        <span>© {{ currentYear }}</span>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  width: 100%;
  margin-top: auto;
  border-top: 1px solid rgba(120, 151, 235, 0.1);
  background: rgba(8, 12, 24, 0.72);
  color: #7f8faf;
}

.app-footer__inner {
  width: 100%;
  min-height: 48px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  font-size: 12px;
  line-height: 1.4;
}

.app-footer__left,
.app-footer__right {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.app-footer__left span:first-child {
  color: #aebcda;
  font-weight: 600;
}

.separator {
  color: #4f5f7c;
}

@media (max-width: 760px) {
  .app-footer__inner {
    min-height: auto;
    padding: 14px 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .app-footer__left,
  .app-footer__right {
    flex-wrap: wrap;
    white-space: normal;
  }
}
</style>