# Radiation Monitoring Frontend

This folder contains the Vue 3 frontend for the Radiation Monitoring prototype.

## Main Technologies

- Vue 3
- TypeScript
- Vite
- Chart.js
- Pinia

## Main Screens

- Dashboard
- Dataset upload
- Settings
- Model Testing modal
- Anomalies log

## Frontend Role

The frontend communicates with the FastAPI backend and displays:

- radiation measurements
- anomaly markers
- threshold preview
- model metrics
- model comparison
- ROC and Precision-Recall curves
- notification settings
- decision support information based on model outputs

The frontend does not train models. It presents results created by the traditional ML pipeline and helps users interpret them through visual summaries and comparison views.

## Development

Install dependencies:

```bash
npm install
```

Run development server:

```bash
npm run dev
```

Build production bundle:

```bash
npm run build
```
