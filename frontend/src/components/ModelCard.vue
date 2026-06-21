<template>
  <div class="panel model-panel">
    <div class="panel__header">
      <div>
        <p class="panel__eyebrow">Model Testing</p>
        <h2>Isolation Forest</h2>
      </div>
    </div>

    <div class="progress-block">
      <div class="progress-block__top">
        <span>Performance</span>
        <strong>93.4%</strong>
      </div>

      <div class="progress-bar">
        <div class="progress-bar__fill"></div>
      </div>
    </div>

    <div class="metrics-list">
      <div class="metrics-list__item">
        <span>Precision</span>
        <strong>0.91</strong>
      </div>
      <div class="metrics-list__item">
        <span>FPR</span>
        <strong>0.04</strong>
      </div>
      <div class="metrics-list__item">
        <span>FNR</span>
        <strong>0.07</strong>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel {
  position: relative;
  overflow: hidden;
  border-radius: 26px;
  padding: 24px;
  border: 1px solid rgba(131, 170, 255, 0.14);
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(10, 15, 30, 0.92));
  box-shadow:
      0 10px 30px rgba(0, 0, 0, 0.28),
      inset 0 1px 0 rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(14px);
}

.panel::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at top right, rgba(110, 168, 255, 0.14), transparent 34%);
  pointer-events: none;
}

.panel__header {
  position: relative;
  z-index: 1;
  margin-bottom: 20px;
}

.panel__eyebrow {
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #8aa4db;
}

.panel__header h2 {
  font-size: 22px;
  color: #f5f9ff;
}

.progress-block {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.progress-block__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #9db0d3;
  font-size: 14px;
}

.progress-block__top strong {
  color: #ffffff;
  font-size: 18px;
}

.progress-bar {
  width: 100%;
  height: 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

.progress-bar__fill {
  width: 93.4%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #5cc9ff 0%, #7f8cff 100%);
  box-shadow: 0 0 16px rgba(110, 168, 255, 0.35);
}

.metrics-list {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 14px;
}

.metrics-list__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 14px;
  color: #9eb0d1;
}

.metrics-list__item strong {
  color: #f5f9ff;
}
</style>