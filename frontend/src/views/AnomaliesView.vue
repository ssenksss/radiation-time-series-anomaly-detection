<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import RadiationChart from '../components/RadiationChart.vue'

const router = useRouter()

const period = ref('Month')
const quickRange = ref('24h')
const selectedStatus = ref('All statuses')

const anomalyRowsTop = [
  {
    timestamp: 'Apr 23, 2024, 16:40',
    level: '0.78 µSv/h',
    status: 'Anomaly',
    scoreLeft: '0.26',
    scoreRight: '0.92',
  },
  {
    timestamp: 'Apr 23, 2024, 11:45',
    level: '0.76 µSv/h',
    status: 'Anomaly',
    scoreLeft: '0.18',
    scoreRight: '0.88',
  },
]

const anomalyRowsOverview = [
  { timestamp: 'Apr 23, 2024, 16:30', level: '0.75 µSv/h', score: '0.91', status: 'Critical' },
  { timestamp: 'Apr 23, 2024, 11:45', level: '0.76 µSv/h', score: '0.88', status: 'High' },
  { timestamp: 'Apr 22, 2024, 16:30', level: '0.80 µSv/h', score: '0.95', status: 'Critical' },
  { timestamp: 'Apr 22, 2024, 11:45', level: '0.75 µSv/h', score: '0.82', status: 'Medium' },
]

const resetFilters = () => {
  period.value = 'Month'
  quickRange.value = '24h'
  selectedStatus.value = 'All statuses'
}
</script>

<template>
  <MainLayout>
    <div class="anomalies-page">
      <section class="hero-panel">
        <h1>Anomalies</h1>

        <div class="toolbar">
          <button class="tool-button tool-button--active">{{ period }}</button>
          <button class="tool-button tool-button--muted">From Date</button>
          <button class="tool-button tool-button--muted">To Date</button>
          <button class="tool-button tool-button--ghost" @click="resetFilters">Reset</button>
        </div>

        <div class="search-row">
          <div class="search-box">⌕ Search anomalies</div>

          <div class="chips">
            <span class="chip">Critical</span>
            <span class="chip">High</span>
            <span class="chip">Radiation Peaks</span>
          </div>

          <div class="source-box">
            <span>Source:</span>
            <span class="source-dot"></span>
            <strong>radiation_data.csv</strong>
            <button class="tool-button tool-button--small" @click="router.push('/dataset')">View</button>
          </div>
        </div>

        <div class="table-panel table-panel--top">
          <div class="table-head">
            <span>Timestamp</span>
            <span>Radiation Level</span>
            <span>Status</span>
            <span>Anomaly Score</span>
          </div>

          <div v-for="row in anomalyRowsTop" :key="row.timestamp" class="table-row">
            <span class="cell-timestamp">
              <i class="row-dot"></i>
              {{ row.timestamp }}
            </span>

            <span class="cell-level">{{ row.level }}</span>

            <span class="cell-status">
              <span class="status-pill">{{ row.status }}</span>
            </span>

            <span class="cell-score">
              <span class="score-left">{{ row.scoreLeft }}</span>
              <span class="score-bar"></span>
              <span class="score-right">{{ row.scoreRight }}</span>
            </span>
          </div>

          <div class="table-footer">
            <button class="dataset-button" @click="router.push('/dataset')">View Dataset</button>
          </div>
        </div>
      </section>

      <section class="overview-panel">
        <div class="overview-header">
          <div class="overview-title">
            <h2>Anomalies Overview</h2>
            <span class="overview-toggle"></span>
          </div>

          <div class="overview-actions">
            <button class="tool-button tool-button--small" :class="{ 'tool-button--active': quickRange === '1W', 'tool-button--ghost': quickRange !== '1W' }" @click="quickRange = '1W'">1W</button>
            <button class="tool-button tool-button--small" :class="{ 'tool-button--active': quickRange === '24h', 'tool-button--ghost': quickRange !== '24h' }" @click="quickRange = '24h'">24h</button>
            <button class="tool-button tool-button--small" :class="{ 'tool-button--active': quickRange === '14d', 'tool-button--ghost': quickRange !== '14d' }" @click="quickRange = '14d'">14d</button>
          </div>
        </div>

        <div class="overview-chart">
          <RadiationChart />
        </div>
      </section>

      <section class="summary-hero">
        <div>
          <h2>Detected Events Summary</h2>
          <p>Review detected events, severity levels, and anomaly scores across the active dataset.</p>
        </div>

        <div class="summary-hero__badge">12 Total Events</div>
      </section>

      <section class="filters">
        <div class="filter-card">
          <label>Date Range</label>
          <div class="filter-value">Last 7 days</div>
        </div>

        <div class="filter-card">
          <label>Status Filter</label>
          <div class="filter-value">{{ selectedStatus }}</div>
        </div>

        <div class="filter-card">
          <label>Search</label>
          <div class="filter-value">timestamp / level / score</div>
        </div>
      </section>

      <section class="summary-table-panel">
        <div class="summary-table-panel__header">
          <h2>Detected Anomalies</h2>
          <button type="button">Export CSV</button>
        </div>

        <div class="summary-table">
          <div class="summary-table__head">
            <span>Timestamp</span>
            <span>Radiation Level</span>
            <span>Anomaly Score</span>
            <span>Status</span>
          </div>

          <div v-for="row in anomalyRowsOverview" :key="row.timestamp" class="summary-table__row">
            <span>{{ row.timestamp }}</span>
            <span class="accent">{{ row.level }}</span>
            <span>{{ row.score }}</span>
            <span class="status">{{ row.status }}</span>
          </div>
        </div>
      </section>
    </div>
  </MainLayout>
</template>

<style scoped>
.anomalies-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-panel,
.table-panel,
.overview-panel,
.summary-hero,
.filters,
.filter-card,
.summary-table-panel {
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

.hero-panel,
.overview-panel,
.summary-hero,
.summary-table-panel {
  padding: 20px;
}

.hero-panel h1 {
  margin-bottom: 16px;
  color: #eef4ff;
  font-size: 32px;
  font-weight: 700;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.tool-button,
.dataset-button,
.summary-table-panel__header button {
  height: 34px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: rgba(255,255,255,0.05);
  color: #dbe8ff;
  font-size: 13px;
  cursor: pointer;
}

.tool-button--muted {
  color: #7f93b8;
}

.tool-button--ghost {
  background: rgba(255,255,255,0.03);
}

.tool-button--active {
  background: rgba(107, 158, 255, 0.12);
  border-color: rgba(107, 158, 255, 0.2);
}

.tool-button--small {
  height: 30px;
  padding: 0 12px;
  font-size: 12px;
}

.search-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr auto;
  gap: 12px;
  align-items: center;
  margin-bottom: 14px;
}

.search-box,
.source-box,
.chip {
  border: 1px solid rgba(120, 151, 235, 0.1);
  background: rgba(255,255,255,0.04);
  color: #93a7cf;
}

.search-box {
  height: 42px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  padding: 0 14px;
}

.chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chip {
  height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
}

.source-box {
  min-height: 42px;
  border-radius: 12px;
  padding: 6px 8px 6px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.source-dot,
.row-dot,
.overview-toggle {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #7ef0bf;
  box-shadow: 0 0 12px rgba(126, 240, 191, 0.4);
}

.table-panel {
  margin-top: 14px;
  padding: 0;
  overflow: hidden;
}

.table-head,
.table-row,
.summary-table__head,
.summary-table__row {
  display: grid;
  grid-template-columns: 1.4fr 1fr 1fr 1fr;
  gap: 14px;
  align-items: center;
}

.table-head,
.summary-table__head {
  padding: 16px 20px;
  color: #8ea2c9;
  font-size: 13px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.table-row,
.summary-table__row {
  padding: 16px 20px;
  color: #d5e2ff;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.cell-timestamp,
.cell-score {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cell-level,
.accent {
  color: #8fe6ff;
}

.status-pill,
.status {
  display: inline-flex;
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 117, 141, 0.12);
  color: #ff9aad;
  border: 1px solid rgba(255, 117, 141, 0.18);
}

.score-bar {
  flex: 1;
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(107, 158, 255, 0.28), rgba(126, 240, 191, 0.32));
}

.table-footer {
  padding: 16px 20px 20px;
}

.overview-header,
.summary-table-panel__header,
.overview-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.overview-header,
.summary-table-panel__header {
  margin-bottom: 16px;
}

.overview-title h2,
.summary-hero h2,
.summary-table-panel__header h2 {
  color: #eef4ff;
}

.overview-actions {
  display: flex;
  gap: 8px;
}

.overview-chart {
  height: 320px;
}

.summary-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.summary-hero p {
  margin-top: 8px;
  color: #98abd0;
}

.summary-hero__badge {
  height: 42px;
  padding: 0 16px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  background: rgba(126, 240, 191, 0.12);
  color: #8fe6c6;
  border: 1px solid rgba(126, 240, 191, 0.18);
}

.filters {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}

.filter-card {
  padding: 18px;
}

.filter-card label {
  display: block;
  margin-bottom: 8px;
  color: #90a5cd;
  font-size: 13px;
}

.filter-value {
  color: #eef4ff;
}

.summary-table {
  overflow: hidden;
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.05);
}

@media (max-width: 1100px) {
  .search-row,
  .filters,
  .table-head,
  .table-row,
  .summary-table__head,
  .summary-table__row {
    grid-template-columns: 1fr;
  }

  .summary-hero,
  .overview-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
