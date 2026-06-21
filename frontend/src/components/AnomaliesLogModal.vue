<script setup lang="ts">
defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const logRows = [
  {
    timestamp: 'Apr 23, 2024, 16:30',
    value: '0.75 µSv/h',
    severity: 'High',
    source: 'Sensor A-12',
  },
  {
    timestamp: 'Apr 23, 2024, 11:45',
    value: '0.76 µSv/h',
    severity: 'High',
    source: 'Sensor A-12',
  },
  {
    timestamp: 'Apr 22, 2024, 16:30',
    value: '0.80 µSv/h',
    severity: 'Critical',
    source: 'Sensor B-03',
  },
  {
    timestamp: 'Apr 22, 2024, 11:45',
    value: '0.75 µSv/h',
    severity: 'Medium',
    source: 'Sensor C-07',
  },
]
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
          <div class="log-toolbar__search">⌕ Search anomalies</div>
          <button class="toolbar-button" type="button">Export CSV</button>
        </div>

        <div class="log-table">
          <div class="log-table__head">
            <span>Timestamp</span>
            <span>Radiation Level</span>
            <span>Severity</span>
            <span>Source</span>
          </div>

          <div v-for="row in logRows" :key="row.timestamp" class="log-table__row">
            <span class="timestamp">
              <i class="row-dot"></i>
              {{ row.timestamp }}
            </span>
            <span class="accent">{{ row.value }}</span>
            <span class="severity">
              <span class="severity-pill">{{ row.severity }}</span>
            </span>
            <span>{{ row.source }}</span>
          </div>
        </div>

        <div class="modal-footer">
          <button class="action-button action-button--secondary" type="button" @click="emit('close')">
            Close
          </button>
          <button class="action-button" type="button">
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
  width: min(960px, 100%);
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
  grid-template-columns: 1.6fr 1fr 1fr 1fr;
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
  background: rgba(183, 78, 88, 0.32);
  border: 1px solid rgba(255, 124, 138, 0.18);
  color: #ffd3d8;
  display: inline-flex;
  align-items: center;
  justify-content: center;
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
    grid-template-columns: 1fr;
  }
}
</style>