<script setup lang="ts">
import MainLayout from '../layouts/MainLayout.vue'

const faq = [
  {
    q: 'How are anomalies detected?',
    a: 'Anomalies are identified using model-based analysis and configurable radiation thresholds.',
  },
  {
    q: 'What dataset is used?',
    a: 'The prototype currently simulates a CSV-based radiation dataset loaded into the dashboard.',
  },
  {
    q: 'Can the threshold be changed?',
    a: 'Yes, the threshold is configurable in the Settings module.',
  },
]
</script>

<template>
  <MainLayout>
    <div class="page">
      <section class="hero">
        <h1>Help & Documentation</h1>
        <p>Quick guidance for using the monitoring dashboard and interpreting anomaly results.</p>
      </section>

      <section class="panel">
        <h2>FAQ</h2>

        <div class="faq-list">
          <div v-for="item in faq" :key="item.q" class="faq-item">
            <h3>{{ item.q }}</h3>
            <p>{{ item.a }}</p>
          </div>
        </div>
      </section>

      <section class="panel">
        <h2>Usage Notes</h2>
        <ul>
          <li>Review the dashboard for current readings and threshold exceedances.</li>
          <li>Use the Anomalies page to inspect timestamps and severity.</li>
          <li>Use Detection and Settings pages to understand model behavior.</li>
        </ul>
      </section>
    </div>
  </MainLayout>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero,
.panel,
.faq-item {
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

.hero,
.panel {
  padding: 24px;
}

.hero h1,
.panel h2 {
  margin-bottom: 10px;
  color: #eef4ff;
}

.hero p,
.faq-item p,
ul {
  color: #a6b6d8;
}

.faq-list {
  display: grid;
  gap: 12px;
}

.faq-item {
  padding: 18px;
}

.faq-item h3 {
  margin-bottom: 8px;
  color: #eef4ff;
  font-size: 16px;
}

ul {
  padding-left: 18px;
}

li + li {
  margin-top: 8px;
}
</style>