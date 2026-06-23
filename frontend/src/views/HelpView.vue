<script setup lang="ts">
import { ref } from 'vue'
import MainLayout from '../layouts/MainLayout.vue'

interface FaqItem {
  q: string
  a: string
}

interface UsageItem {
  title: string
  description: string
  badge: string
}

const activeFaq = ref<number | null>(0)

const faq: FaqItem[] = [
  {
    q: 'How are anomalies detected?',
    a: 'Anomalies are identified using the active detection model and configurable radiation thresholds. The current prototype supports threshold-based detection, while additional ML models are prepared for the next implementation phase.',
  },
  {
    q: 'What dataset is used?',
    a: 'The application works with a CSV-based radiation dataset. During development, a mock dataset is used until the real measured dataset becomes available.',
  },
  {
    q: 'Can the threshold be changed?',
    a: 'Yes. The threshold can be changed in the Settings module. After saving, the updated value is applied across the application.',
  },
  {
    q: 'Why are some models marked as pending?',
    a: 'Some models are visible because they are planned for the ML phase, but they are not active until they are fully implemented in the backend.',
  },
  {
    q: 'Is this a production system?',
    a: 'No. This is a bachelor thesis prototype for demonstrating radiation monitoring, anomaly detection, visualization, and early-warning system concepts.',
  },
]

const usageNotes: UsageItem[] = [
  {
    title: 'Dashboard',
    description: 'Review current radiation readings, alert status, detected anomalies, and model comparison overview.',
    badge: 'Monitoring',
  },
  {
    title: 'Anomalies',
    description: 'Inspect detected events by timestamp, severity, anomaly score, and selected time range.',
    badge: 'Detection',
  },
  {
    title: 'Dataset',
    description: 'Load, preview, and validate the active CSV dataset before analysis.',
    badge: 'Data',
  },
  {
    title: 'Settings',
    description: 'Adjust the detection threshold, active model, notification rules, and threshold preview.',
    badge: 'Config',
  },
]

const toggleFaq = (index: number) => {
  activeFaq.value = activeFaq.value === index ? null : index
}
</script>

<template>
  <MainLayout>
    <div class="page">
      <section class="hero">

        <h1>Help & Documentation</h1>
        <p>
          Quick guidance for using the monitoring dashboard, interpreting anomaly results,
          and understanding the current prototype scope.
        </p>
      </section>

      <section class="panel">
        <div class="section-header">
          <div>

            <h2>FAQ</h2>
          </div>
        </div>

        <div class="faq-list">
          <button
              v-for="(item, index) in faq"
              :key="item.q"
              class="faq-item"
              type="button"
              @click="toggleFaq(index)"
          >
            <div class="faq-question">
              <h3>{{ item.q }}</h3>
              <span>{{ activeFaq === index ? '−' : '+' }}</span>
            </div>

            <p v-if="activeFaq === index">
              {{ item.a }}
            </p>
          </button>
        </div>
      </section>

      <section class="panel">
        <div class="section-header">
          <div>

            <h2>Usage Notes</h2>
          </div>
        </div>

        <div class="usage-list">
          <article
              v-for="item in usageNotes"
              :key="item.title"
              class="usage-item"
          >
            <div class="usage-item__top">
              <h3>{{ item.title }}</h3>
              <span>{{ item.badge }}</span>
            </div>
            <p>{{ item.description }}</p>
          </article>
        </div>
      </section>

      <section class="panel prototype-note">
        <div class="section-header">
          <div>
            <h2>Prototype Scope</h2>
          </div>
        </div>

        <p>
          This application is a research prototype developed as part of a bachelor thesis.
          It demonstrates the structure of a radiation monitoring and early-warning system,
          but it is not intended for real safety-critical operation without validation,
          calibration, and production-grade infrastructure.
        </p>
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
.faq-item,
.usage-item {
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

.eyebrow {
  display: inline-block;
  margin-bottom: 8px;
  color: #7ef0bf;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.eyebrow--warning {
  color: #ffb36a;
}

.hero h1,
.panel h2 {
  margin-bottom: 10px;
  color: #eef4ff;
}

.hero p,
.faq-item p,
.usage-item p,
.prototype-note p {
  color: #a6b6d8;
  line-height: 1.6;
}

.section-header {
  margin-bottom: 14px;
}

.faq-list {
  display: grid;
  gap: 12px;
}

.faq-item {
  width: 100%;
  padding: 18px;
  text-align: left;
  cursor: pointer;
}

.faq-question {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.faq-question h3 {
  color: #eef4ff;
  font-size: 16px;
}

.faq-question span {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: rgba(255,255,255,0.05);
  color: #dbe8ff;
  display: grid;
  place-items: center;
  font-size: 18px;
  flex: 0 0 auto;
}

.faq-item p {
  margin-top: 12px;
}

.usage-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.usage-item {
  padding: 18px;
  box-shadow: none;
}

.usage-item__top {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.usage-item h3 {
  color: #eef4ff;
  font-size: 16px;
}

.usage-item__top span {
  padding: 5px 9px;
  border-radius: 999px;
  background: rgba(107, 158, 255, 0.12);
  border: 1px solid rgba(107, 158, 255, 0.16);
  color: #cbdcff;
  font-size: 12px;
}

.prototype-note {
  border-color: rgba(255, 179, 106, 0.16);
  background:
      radial-gradient(circle at top right, rgba(255, 179, 106, 0.08), transparent 30%),
      linear-gradient(180deg, rgba(12, 18, 35, 0.88), rgba(9, 14, 28, 0.96));
}

@media (max-width: 760px) {
  .hero,
  .panel {
    padding: 18px;
  }

  .usage-list {
    grid-template-columns: 1fr;
  }
}
</style>