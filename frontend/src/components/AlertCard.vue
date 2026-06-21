<template>
  <div class="panel alert-panel">
    <div class="panel__header">
      <div>
        <p class="panel__eyebrow">System Alert</p>
        <h2>Anomaly Detected</h2>
      </div>
    </div>

    <p class="alert-panel__text">
      Radiation level exceeded threshold. Immediate attention required.
    </p>

    <div class="alert-panel__footer">
      <span class="alert-dot"></span>
      <span>High priority event</span>
    </div>
  </div>
</template>

<style scoped>
.panel {
  border-radius: 26px;
  padding: 24px;
}

.alert-panel {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 107, 107, 0.18);
  background: linear-gradient(180deg, rgba(36, 14, 22, 0.88), rgba(18, 9, 18, 0.94));
  box-shadow:
      0 10px 30px rgba(0, 0, 0, 0.28),
      inset 0 1px 0 rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(14px);
}

.alert-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at top right, rgba(255, 107, 107, 0.18), transparent 36%);
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
  color: #ffb3b3;
}

.panel__header h2 {
  font-size: 22px;
  color: #fff1f1;
}

.alert-panel__text {
  position: relative;
  z-index: 1;
  color: #d8bfd0;
  line-height: 1.7;
  margin-bottom: 22px;
}

.alert-panel__footer {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #ffb3b3;
  font-weight: 600;
  font-size: 14px;
}

.alert-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #ff6b6b;
  box-shadow: 0 0 14px rgba(255, 107, 107, 0.8);
}
</style>