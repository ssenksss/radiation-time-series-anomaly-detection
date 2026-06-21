<script setup lang="ts">
defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const comparisonRows = [
  { metric: 'Accuracy', isolationForest: '93.4%', lof: '87.9%' },
  { metric: 'Precision', isolationForest: '0.91', lof: '0.84' },
  { metric: 'Recall', isolationForest: '0.89', lof: '0.81' },
  { metric: 'FPR', isolationForest: '0.04', lof: '0.08' },
]

const bars = [
  { label: 'Isolation Forest', value: '93.4%', height: '88px', active: true },
  { label: 'LOF', value: '87.9%', height: '64px', active: false },
]
</script>

<template>
  <transition name="modal-fade">
    <div v-if="isOpen" class="modal-overlay" @click.self="emit('close')">
      <div class="modal-card">
        <div class="modal-card__header">
          <div>
            <p class="modal-card__eyebrow">Model Testing</p>
            <h2>Isolation Forest Evaluation</h2>
          </div>

          <button class="close-button" type="button" @click="emit('close')">✕</button>
        </div>

        <div class="modal-grid">
          <div class="panel-block">
            <div class="panel-block__top">
              <span>Recent Accuracy</span>
              <strong>93.4%</strong>
            </div>

            <div class="progress-bar">
              <div class="progress-bar__fill"></div>
            </div>

            <div class="mini-bars">
              <div
                  v-for="bar in bars"
                  :key="bar.label"
                  class="mini-bars__item"
              >
                <span class="mini-bars__percent">{{ bar.value }}</span>
                <div
                    class="mini-bars__bar"
                    :class="{ 'mini-bars__bar--active': bar.active }"
                    :style="{ height: bar.height }"
                ></div>
                <span class="mini-bars__label">{{ bar.label }}</span>
              </div>
            </div>
          </div>

          <div class="panel-block">
            <h3>Model Comparison</h3>

            <div class="comparison-table">
              <div class="comparison-table__head">
                <span>Metric</span>
                <span>Isolation Forest</span>
                <span>LOF</span>
              </div>

              <div
                  v-for="row in comparisonRows"
                  :key="row.metric"
                  class="comparison-table__row"
              >
                <span>{{ row.metric }}</span>
                <span class="accent">{{ row.isolationForest }}</span>
                <span>{{ row.lof }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="action-button action-button--secondary" type="button" @click="emit('close')">
            Close
          </button>
          <button class="action-button" type="button">
            Export Results
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
  width: min(920px, 100%);
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

.modal-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.panel-block {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.03);
}

.panel-block h3 {
  margin-bottom: 14px;
  color: #eef4ff;
  font-size: 18px;
}

.panel-block__top {
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #aabadd;
}

.panel-block__top strong {
  color: #7ef0bf;
  font-size: 22px;
}

.progress-bar {
  height: 12px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  overflow: hidden;
  margin-bottom: 22px;
}

.progress-bar__fill {
  width: 93.4%;
  height: 100%;
  background: linear-gradient(90deg, #d3fbff, #85dfff, #99efcf);
}

.mini-bars {
  height: 180px;
  display: flex;
  align-items: end;
  justify-content: space-around;
  gap: 18px;
}

.mini-bars__item {
  width: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.mini-bars__percent {
  color: #a4b6d8;
  font-size: 13px;
}

.mini-bars__bar {
  width: 54px;
  border-radius: 14px 14px 0 0;
  background: linear-gradient(180deg, rgba(230, 235, 245, 0.9), rgba(157, 168, 194, 0.9));
  box-shadow: 0 0 12px rgba(255,255,255,0.05);
}

.mini-bars__bar--active {
  background: linear-gradient(180deg, #d3fcff, #93deff);
  box-shadow: 0 0 20px rgba(125, 219, 255, 0.3);
}

.mini-bars__label {
  color: #d7e4ff;
  font-size: 13px;
  text-align: center;
}

.comparison-table {
  display: flex;
  flex-direction: column;
}

.comparison-table__head,
.comparison-table__row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  align-items: center;
}

.comparison-table__head {
  padding: 12px 0;
  color: #90a4cd;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.comparison-table__row {
  padding: 14px 0;
  color: #eaf1ff;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.accent {
  color: #8fe6c6;
  font-weight: 600;
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
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: linear-gradient(180deg, rgba(255, 193, 94, 0.92), rgba(224, 153, 54, 0.92));
  color: #2c1f10;
  font-weight: 700;
  cursor: pointer;
}

.action-button--secondary {
  background: rgba(255,255,255,0.04);
  color: #dce8ff;
}

@media (max-width: 900px) {
  .modal-grid {
    grid-template-columns: 1fr;
  }

  .modal-overlay {
    padding: 14px;
  }

  .modal-footer {
    flex-direction: column;
  }
}
</style>