<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import RadiationChart from '../components/RadiationChart.vue'
import ModelTestingModal from '../components/ModelTestingModal.vue'
import AnomaliesLogModal from '../components/AnomaliesLogModal.vue'
import { dashboardData } from '../mock/dashboardData'

const router = useRouter()

const isModelModalOpen = ref(false)
const isLogModalOpen = ref(false)
const alertVisible = ref(true)

const openModelModal = () => {
  isModelModalOpen.value = true
}

const closeModelModal = () => {
  isModelModalOpen.value = false
}

const openLogModal = () => {
  isLogModalOpen.value = true
}

const closeLogModal = () => {
  isLogModalOpen.value = false
}

const acknowledgeAlert = () => {
  alertVisible.value = false
}

const goToDataset = () => {
  router.push('/dataset')
}
</script>

<template>
  <MainLayout>
    <div class="dashboard-page">
      <section class="hero-panel">
        <div class="hero-panel__content">
          <h1>{{ dashboardData.header.title }}</h1>
          <p>{{ dashboardData.header.subtitle }}</p>
        </div>

        <div class="hero-panel__visual">
          <div class="hero-panel__stars"></div>
          <div class="hero-wave hero-wave--one"></div>
          <div class="hero-wave hero-wave--two"></div>
          <div class="hero-wave hero-wave--three"></div>
          <div class="hero-glow"></div>
        </div>
      </section>

      <section class="content-grid">
        <div class="left-column">
          <div class="glass-panel chart-panel">
            <h2>{{ dashboardData.chart.title }}</h2>

            <div class="chart-legend">
              <span>
                <i class="legend legend--line"></i>{{ dashboardData.chart.legend.radiation }}
              </span>
              <span>
                <i class="legend legend--dot"></i>{{ dashboardData.chart.legend.anomalies }}
              </span>
              <span>
                <i class="legend legend--threshold"></i>{{ dashboardData.chart.legend.threshold }}
              </span>
            </div>

            <RadiationChart />

            <div v-if="alertVisible" class="alert-panel">
              <div class="alert-panel__icon">!</div>

              <div class="alert-panel__content">
                <h3>{{ dashboardData.alert.title }}</h3>
                <p>{{ dashboardData.alert.description }}</p>
              </div>

              <button class="ack-button" type="button" @click="acknowledgeAlert">
                {{ dashboardData.alert.buttonLabel }}
              </button>
            </div>
          </div>

          <div class="stats-row">
            <div
                v-for="stat in dashboardData.stats"
                :key="stat.title"
                class="stat-card"
                :class="{ 'stat-card--danger': stat.danger }"
            >
              <div class="stat-card__icon">{{ stat.icon }}</div>
              <div class="stat-card__content">
                <p>{{ stat.title }}</p>
                <h3>{{ stat.value }}</h3>
                <span v-if="stat.meta">{{ stat.meta }}</span>
                <button
                    v-if="stat.hasButton"
                    class="mini-button"
                    type="button"
                    @click="openModelModal"
                >
                  {{ stat.buttonLabel }}
                </button>
              </div>
            </div>
          </div>

          <div class="glass-panel details-panel">
            <div class="details-panel__header">
              <div class="details-panel__title">
                <span class="details-panel__circle">›</span>
                <h2>{{ dashboardData.anomalyDetails.title }}</h2>
              </div>

              <button class="view-all-button view-all-button--small" type="button" @click="openLogModal">
                {{ dashboardData.common.viewAll }}
              </button>
            </div>

            <div class="details-table">
              <div class="details-table__head">
                <span v-for="column in dashboardData.anomalyDetails.columns" :key="column">
                  {{ column }}
                </span>
              </div>

              <div
                  v-for="row in dashboardData.anomalyDetails.rows"
                  :key="row.timestamp"
                  class="details-row"
              >
                <span>{{ row.timestamp }}</span>
                <span class="accent-value">{{ row.level }}</span>
                <span class="table-pill" :class="`table-pill--${row.tagType}`">
                  {{ row.tag }}
                </span>
                <span class="table-pill" :class="`table-pill--${row.statusType}`">
                  {{ row.status }}
                </span>
              </div>
            </div>

            <div class="details-panel__footer">
              <button class="view-all-button view-all-button--bottom" type="button" @click="openLogModal">
                {{ dashboardData.common.viewAll }}
              </button>
            </div>
          </div>
        </div>

        <div class="right-column">
          <div class="glass-panel current-panel">
            <p class="current-panel__label">{{ dashboardData.current.label }}</p>

            <div class="current-panel__value">
              <span class="sparkle">✦</span>
              <strong>{{ dashboardData.current.value }}</strong>
              <span>{{ dashboardData.current.unit }}</span>
            </div>

            <p class="current-panel__change">{{ dashboardData.current.change }}</p>

            <div class="current-panel__footer">
              <span>{{ dashboardData.current.source }}</span>
              <button class="csv-button" type="button" @click="goToDataset">
                {{ dashboardData.current.datasetLabel }}
              </button>
            </div>
          </div>

          <div class="glass-panel log-panel">
            <h2>{{ dashboardData.anomaliesLog.title }}</h2>

            <div class="log-list">
              <div
                  v-for="item in dashboardData.anomaliesLog.items"
                  :key="item.timestamp"
                  class="log-item"
              >
                <div class="log-item__dot"></div>
                <div class="log-item__content">
                  <p>{{ item.timestamp }}</p>
                  <strong>{{ item.value }}</strong>
                </div>
                <span v-if="item.isNew" class="log-item__tag">NEW</span>
              </div>
            </div>

            <button class="view-all-button view-all-button--full" type="button" @click="openLogModal">
              {{ dashboardData.common.viewAll }}
            </button>
          </div>

          <div class="glass-panel model-panel">
            <h2>{{ dashboardData.modelTesting.title }}</h2>

            <div class="model-panel__row">
              <span>{{ dashboardData.modelTesting.accuracyLabel }}</span>
              <strong>{{ dashboardData.modelTesting.accuracyValue }}</strong>
            </div>

            <div class="progress-bar">
              <div class="progress-bar__fill"></div>
            </div>

            <div class="model-panel__meta">
              <span>{{ dashboardData.modelTesting.source }}</span>
              <span>{{ dashboardData.modelTesting.action }}</span>
            </div>

            <div class="mini-bars">
              <div
                  v-for="bar in dashboardData.modelTesting.bars"
                  :key="bar.percent"
                  class="mini-bars__item"
              >
                <span class="mini-bars__percent">{{ bar.percent }}</span>
                <div class="mini-bars__bar" :class="`mini-bars__bar--${bar.className}`"></div>
              </div>
            </div>

            <div class="mini-bars__labels">
              <span>{{ dashboardData.modelTesting.labels[0] }}</span>
              <span>{{ dashboardData.modelTesting.labels[1] }}</span>
            </div>

            <button class="view-all-button view-all-button--full" type="button" @click="openModelModal">
              {{ dashboardData.common.viewAll }}
            </button>
          </div>
        </div>
      </section>

      <ModelTestingModal :is-open="isModelModalOpen" @close="closeModelModal" />
      <AnomaliesLogModal :is-open="isLogModalOpen" @close="closeLogModal" />
    </div>
  </MainLayout>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero-panel,
.glass-panel,
.stat-card {
  position: relative;
  overflow: hidden;
  border-radius: 22px;
  border: 1px solid rgba(120, 151, 235, 0.12);
  background:
      radial-gradient(circle at top right, rgba(76, 111, 255, 0.08), transparent 30%),
      linear-gradient(180deg, rgba(12, 18, 35, 0.88), rgba(9, 14, 28, 0.96));
  box-shadow:
      0 10px 36px rgba(0, 0, 0, 0.22),
      inset 0 1px 0 rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(14px);
}

.hero-panel {
  min-height: 140px;
  padding: 22px 24px;
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  align-items: center;
}

.hero-panel__content h1 {
  margin-bottom: 10px;
  color: #eef4ff;
  font-size: 28px;
}

.hero-panel__content p {
  color: #a6b6d8;
  max-width: 470px;
  line-height: 1.45;
  font-size: 15px;
}

.hero-panel__visual {
  position: relative;
  min-height: 96px;
  height: 100%;
}

.hero-panel__stars {
  position: absolute;
  inset: 0;
  background-image:
      radial-gradient(1px 1px at 30px 20px, rgba(255, 255, 255, 0.28), transparent),
      radial-gradient(1px 1px at 80px 55px, rgba(255, 255, 255, 0.16), transparent),
      radial-gradient(1px 1px at 160px 36px, rgba(255, 255, 255, 0.18), transparent),
      radial-gradient(1px 1px at 250px 70px, rgba(255, 255, 255, 0.12), transparent),
      radial-gradient(1px 1px at 340px 30px, rgba(255, 255, 255, 0.22), transparent);
  opacity: 0.3;
}

.hero-wave {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #72cfff, transparent);
}

.hero-wave--one {
  top: 38%;
  transform: rotate(-3deg);
  box-shadow: 0 0 20px rgba(114, 207, 255, 0.45);
}

.hero-wave--two {
  top: 52%;
  transform: rotate(5deg);
  opacity: 0.35;
}

.hero-wave--three {
  top: 66%;
  transform: rotate(-6deg);
  opacity: 0.18;
}

.hero-glow {
  position: absolute;
  right: 28%;
  top: 48%;
  width: 130px;
  height: 130px;
  transform: translateY(-50%);
  background: radial-gradient(circle, rgba(113, 224, 255, 0.42), transparent 66%);
  filter: blur(16px);
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 286px;
  gap: 14px;
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.glass-panel {
  padding: 18px;
}

.chart-panel h2,
.log-panel h2,
.model-panel h2 {
  margin-bottom: 10px;
  color: #eef4ff;
  font-size: 18px;
}

.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  margin-bottom: 12px;
  color: #b6c5e4;
  font-size: 13px;
}

.chart-legend span {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.legend {
  display: inline-block;
}

.legend--line {
  width: 16px;
  height: 3px;
  border-radius: 999px;
  background: #76d6ff;
}

.legend--dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #ff7d73;
}

.legend--threshold {
  width: 16px;
  height: 3px;
  border-radius: 999px;
  background: #ff9854;
}

.alert-panel {
  margin-top: 14px;
  min-height: 104px;
  border-radius: 18px;
  border: 1px solid rgba(255, 92, 117, 0.22);
  background:
      radial-gradient(circle at 12% 100%, rgba(255, 74, 106, 0.16), transparent 28%),
      linear-gradient(180deg, rgba(104, 24, 33, 0.64), rgba(57, 13, 20, 0.62));
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 16px 18px;
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.04),
      0 10px 22px rgba(92, 14, 26, 0.22);
}

.alert-panel__icon {
  width: 54px;
  height: 54px;
  border-radius: 16px;
  border: 2px solid rgba(255, 214, 214, 0.26);
  display: grid;
  place-items: center;
  color: #ffe8e8;
  font-size: 24px;
  font-weight: 700;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.03);
}

.alert-panel__content {
  flex: 1;
}

.alert-panel__content h3 {
  margin-bottom: 6px;
  color: #ffd7df;
  font-size: 18px;
  letter-spacing: 0.03em;
}

.alert-panel__content p {
  color: #ffe8ec;
  max-width: 380px;
  line-height: 1.3;
  font-size: 14px;
}

.ack-button,
.mini-button,
.view-all-button,
.csv-button {
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: rgba(255, 255, 255, 0.045);
  color: #dbe8ff;
  border-radius: 12px;
  cursor: pointer;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.02);
}

.ack-button {
  position: relative;
  height: 42px;
  min-width: 136px;
  padding: 0 16px;
  background: linear-gradient(180deg, rgba(255, 106, 128, 0.96), rgba(217, 56, 84, 0.96));
  border: 1px solid rgba(255, 170, 185, 0.24);
  color: #fff7f8;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.03em;
  box-shadow:
      0 8px 18px rgba(217, 56, 84, 0.28),
      inset 0 1px 0 rgba(255, 255, 255, 0.18);
  transition: all 0.22s ease;
}

.ack-button:hover {
  transform: translateY(-1px);
  background: linear-gradient(180deg, rgba(255, 122, 143, 1), rgba(228, 66, 95, 1));
  box-shadow:
      0 10px 24px rgba(217, 56, 84, 0.34),
      0 0 14px rgba(255, 92, 117, 0.16);
}

.ack-button:active {
  transform: translateY(0);
  box-shadow:
      0 4px 10px rgba(217, 56, 84, 0.24),
      inset 0 2px 5px rgba(0, 0, 0, 0.18);
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.stat-card {
  min-height: 122px;
  padding: 16px;
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.stat-card--danger {
  background:
      radial-gradient(circle at 10% 100%, rgba(255, 97, 97, 0.2), transparent 34%),
      linear-gradient(180deg, rgba(12, 18, 35, 0.88), rgba(9, 14, 28, 0.96));
}

.stat-card__icon {
  width: 54px;
  height: 54px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(114, 137, 255, 0.08);
  color: #b9d5ff;
  font-size: 22px;
  flex-shrink: 0;
}

.stat-card p {
  margin-bottom: 8px;
  color: #c9d7ee;
  font-size: 14px;
}

.stat-card h3 {
  margin-bottom: 8px;
  color: #f1f6ff;
  font-size: 18px;
}

.stat-card h3 small {
  color: #dbe7ff;
  font-size: 14px;
}

.stat-card span {
  color: #89e6c6;
  font-size: 13px;
}

.stat-card__content {
  width: 100%;
}

.mini-button,
.csv-button,
.view-all-button {
  height: 34px;
  padding: 0 14px;
  font-size: 12px;
}

.csv-button {
  min-width: 74px;
  background: linear-gradient(180deg, rgba(255, 193, 94, 0.92), rgba(224, 153, 54, 0.92));
  border-color: rgba(255, 208, 132, 0.24);
  color: #2c1f10;
  font-weight: 700;
}

.details-panel__header,
.details-panel__title,
.current-panel__footer,
.model-panel__meta,
.model-panel__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.details-panel__header {
  margin-bottom: 14px;
}

.details-panel__title {
  justify-content: flex-start;
}

.details-panel__circle {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(121, 140, 220, 0.12);
  color: #c6d8fb;
}

.details-panel__title h2 {
  font-size: 18px;
  color: #edf4ff;
}

.details-table {
  display: flex;
  flex-direction: column;
}

.details-table__head,
.details-row {
  display: grid;
  grid-template-columns: 1.8fr 1fr 0.8fr 0.8fr;
  gap: 12px;
  align-items: center;
}

.details-table__head {
  padding: 10px 12px;
  color: #9db0d5;
  font-size: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.details-row {
  padding: 16px 12px;
  color: #eaf1ff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.accent-value {
  color: #ffb29d;
}

.table-pill {
  min-width: 92px;
  height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
  background: linear-gradient(180deg, rgba(255, 104, 126, 0.2), rgba(217, 56, 84, 0.18));


}

.table-pill--alert {
  background: linear-gradient(180deg, rgba(255, 104, 126, 0.2), rgba(217, 56, 84, 0.18));
  color: #ffdbe2;

  border: 1px solid rgba(255, 132, 152, 0.18);
  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.04),
      0 0 10px rgba(217, 56, 84, 0.08);
}

.table-pill--normal {
  background: linear-gradient(180deg, rgba(118, 237, 191, 0.18), rgba(61, 182, 130, 0.16));
  color: #d8fff0;
  border: 1px solid rgba(118, 237, 191, 0.16);

  box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.04),
      0 0 10px rgba(118, 237, 191, 0.08);
}

.details-panel__footer {
  margin-top: 14px;
  display: flex;
  justify-content: center;
}

.current-panel__label {
  margin-bottom: 12px;
  color: #d6dff5;
  font-size: 14px;

}

.current-panel__value {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 10px;
}

.sparkle {
  color: #ff995d;
  font-size: 22px;
}

.current-panel__value strong {
  font-size: 38px;
  color: #f3f8ff;
  line-height: 1;
}

.current-panel__value span:last-child {
  color: #cfdaf0;
  font-size: 18px;
}

.current-panel__change {
  margin-bottom: 18px;
  color: #ffb16c;
  font-size: 14px;
}

.current-panel__footer {
  color: #a5b6d8;
  font-size: 14px;
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.log-item {
  display: grid;
  grid-template-columns: 14px 1fr auto;
  gap: 12px;
  align-items: start;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.log-item__dot {
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: #ff6a70;
  box-shadow: 0 0 16px rgba(255, 106, 112, 0.7);
  margin-top: 6px;
}

.log-item__content p {
  margin-bottom: 6px;
  color: #d0dcf1;

}

.log-item__content strong {
  color: #ff9d93;
  font-size: 18px;
}

.log-item__tag {
  min-width: 42px;
  height: 22px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(255, 104, 126, 0.18), rgba(217, 56, 84, 0.16));
  color: #ffd7df;
  border: 1px solid rgba(255, 132, 152, 0.16);
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
  box-shadow: 0 0 10px rgba(217, 56, 84, 0.08);
}

.view-all-button {
  min-width: 104px;
  background: rgba(255, 255, 255, 0.03);
  color: #d7e4ff;
}

.view-all-button--small {
  min-width: 88px;
  height: 32px;
  font-size: 12px;
}

.view-all-button--bottom {
  min-width: 90px;
  height: 34px;
}

.view-all-button--full {
  width: 100%;
  margin-top: 12px;
}

.model-panel {
  padding: 16px 16px 14px;
}

.model-panel h2 {
  margin-bottom: 12px;
}

.model-panel__row {
  margin-bottom: 10px;
  color: #b4c3de;
  font-size: 14px;
}

.model-panel__row strong {
  color: #7ef0bf;
  font-size: 18px;
}

.progress-bar {
  height: 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
  margin-bottom: 14px;
}

.progress-bar__fill {
  width: 93.4%;
  height: 100%;
  background: linear-gradient(90deg, #d3fbff, #85dfff, #99efcf);
}

.model-panel__meta {
  margin-bottom: 14px;
  color: #8094ba;
  font-size: 13px;
}

.mini-bars {
  display: flex;
  align-items: end;
  justify-content: space-around;
  gap: 12px;
  height: 124px;
  padding: 6px 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.mini-bars__item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: end;
  gap: 8px;
  width: 56px;
}

.mini-bars__percent {
  color: #a0b2d7;
  font-size: 11px;
}

.mini-bars__bar {
  width: 30px;
  border-radius: 10px 10px 0 0;
  background: linear-gradient(180deg, rgba(238, 238, 245, 0.92), rgba(163, 171, 197, 0.9));
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.06);
}

.mini-bars__bar--small {
  height: 48px;
}

.mini-bars__bar--large {
  height: 88px;
  background: linear-gradient(180deg, #d3fcff, #93deff);
  box-shadow: 0 0 16px rgba(125, 219, 255, 0.35);
}

.mini-bars__bar--medium {
  height: 56px;
}

.mini-bars__labels {
  display: flex;
  justify-content: space-between;
  margin: 10px 0 12px;
  color: #a5b7d9;
  font-size: 12px;
}

@media (max-width: 1280px) {
  .stats-row {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 1100px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .right-column {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .hero-panel {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .stats-row,
  .right-column,
  .details-table__head,
  .details-row {
    grid-template-columns: 1fr;
  }

  .alert-panel {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>