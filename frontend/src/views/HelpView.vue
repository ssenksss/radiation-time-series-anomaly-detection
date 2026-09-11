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
    a: 'Anomalies are detected using traditional machine learning models trained on radiation measurement features. The application supports unsupervised anomaly detection models and supervised classifiers when labeled data is available.',
  },
  {
    q: 'What is the difference between supervised and unsupervised models?',
    a: 'Supervised models use original anomaly labels during training. Unsupervised models are trained without labels and learn unusual patterns from the feature values. If labels exist, they are used only later for evaluation.',
  },
  {
    q: 'What does labeled evaluation mean?',
    a: 'Labeled evaluation means that the dataset contains original anomaly labels. For unsupervised models, these labels are not used during training, but they are used after prediction to calculate Accuracy, Precision, Recall, F1-score, ROC-AUC, PR-AUC and the confusion matrix.',
  },
  {
    q: 'Why are metrics based on test records?',
    a: 'The project uses a chronological 70/30 train-test split. Older measurements are used for training and later measurements are used for testing, which is more suitable for time-series radiation data than random splitting.',
  },
  {
    q: 'Why do I need to click Save Changes in Settings?',
    a: 'Changing the active model or threshold updates the saved application settings. Save Changes stores the selected model, radiation threshold and notification settings, then refreshes the displayed monitoring data. Model training is run separately through the ML pipeline.',
  },
  {
    q: 'What does Model Testing show?',
    a: 'Model Testing compares two selected models using the metrics stored in PostgreSQL. For labeled datasets, it also shows ROC and Precision-Recall curves calculated on the chronological test split.',
  },
  {
    q: 'What happens with unlabeled real datasets?',
    a: 'If a dataset does not contain anomaly labels, supervised models are disabled and classification metrics cannot be calculated. The system then shows unsupervised detection results such as detected anomalies, anomaly rate and score statistics.',
  },
  {
    q: 'Is this a production safety system?',
    a: 'No. This is a bachelor thesis prototype for radiation monitoring, anomaly detection, visualization and decision support. A real safety-critical system would require calibration, validation and production-grade infrastructure.',
  },
]

const usageNotes: UsageItem[] = [
  {
    title: 'Dashboard',
    description: 'Review current radiation readings, alert status, detected anomalies and active monitoring summary.',
    badge: 'Monitoring',
  },
  {
    title: 'Anomalies',
    description: 'Inspect detected events by timestamp, severity, anomaly score, model name and selected time range.',
    badge: 'Detection',
  },
  {
    title: 'Dataset',
    description: 'Upload and activate CSV datasets. Labeled datasets enable supervised training and objective model evaluation.',
    badge: 'Data',
  },
  {
    title: 'Settings',
    description: 'Choose the active detection model, adjust the radiation threshold and notification settings, then save the configuration. Model training is run separately through the ML pipeline.',
    badge: 'Config',
  },
  {
    title: 'Model Testing',
    description: 'Compare implemented models using Accuracy, Precision, Recall, F1-score, ROC-AUC, PR-AUC and confusion matrix values.',
    badge: 'Evaluation',
  },
  {
    title: 'ML Outputs',
    description: 'Generated reports, CSV metric tables and plots are stored in ml/outputs for use in project documentation.',
    badge: 'Reports',
  },
]

const modelGroups: UsageItem[] = [
  {
    title: 'Unsupervised models',
    description: 'Isolation Forest, Local Outlier Factor, One-Class SVM, K-Means, Gaussian Mixture Model, PCA, HBOS and ECOD. DBSCAN is included separately as a clustering-based baseline because it marks low-density points as noise instead of using the same reusable train/predict workflow.',
    badge: '9 models',
  },
  {
    title: 'Supervised models',
    description: 'Logistic Regression, Decision Tree, Random Forest, Gradient Boosting and KNN Classifier. These models require original anomaly labels.',
    badge: '5 models',
  },
  {
    title: 'Evaluation outputs',
    description: 'The project generates model_evaluation_report.md, full metric CSV tables, best-metric markers, feature diagnostics, confusion matrices, ROC/PR curves and comparison bar charts.',
    badge: 'Outputs',
  },
  {
    title: 'Decision support',
    description: 'The decision support layer helps organize and interpret model results. Traditional ML is used for model training, prediction and metric calculation.',
    badge: 'Support',
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
          Guidance for using the radiation monitoring dashboard, understanding model
          evaluation results and interpreting the current bachelor thesis prototype.
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

      <section class="panel">
        <div class="section-header">
          <div>
            <h2>Model Evaluation</h2>
          </div>
        </div>

        <div class="usage-list">
          <article
            v-for="item in modelGroups"
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
            <h2>Research Prototype</h2>
          </div>
        </div>

        <p>
          This application is developed as part of a bachelor thesis. It demonstrates
          a radiation level monitoring system with traditionally trained machine
          learning models and a decision support framework. It is not intended for
          real safety-critical operation without additional validation, calibration
          and production infrastructure.
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
  white-space: nowrap;
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
