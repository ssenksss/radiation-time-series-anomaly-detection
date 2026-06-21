<script setup lang="ts">
import { ref } from 'vue'
import MainLayout from '../layouts/MainLayout.vue'
import RadiationChart from '../components/RadiationChart.vue'

const thresholdValue = ref('0.75 µSv/h')
const saveStatus = ref('')
const emailStatus = ref('')

const saveChanges = () => {
  saveStatus.value = 'Settings saved successfully.'
}

const sendTestEmail = () => {
  emailStatus.value = 'Test notification sent.'
}
</script>

<template>
  <MainLayout>
    <div class="settings-page">
      <section class="panel threshold-panel">
        <h1>Settings</h1>

        <div class="threshold-block">
          <div class="threshold-header">
            <h2>Detection Threshold</h2>
          </div>

          <div class="threshold-row">
            <span>Radiation Level Threshold</span>
            <strong>{{ thresholdValue }}</strong>
          </div>

          <div class="slider">
            <div class="slider__fill"></div>
            <div class="slider__thumb"></div>
          </div>
        </div>

        <div class="model-block">
          <div class="model-block__header">
            <h2>Anomaly Detection Model</h2>
            <div class="accuracy-box">
              <span>Current Accuracy</span>
              <strong>93.5%</strong>
            </div>
          </div>

          <div class="select-row">
            <span>Detection Model</span>
            <button class="select-button">Isolation Forest ⌄</button>
          </div>

          <div class="config-grid">
            <div class="config-item">
              <span>Contamination</span>
              <strong>0.03</strong>
            </div>
            <div class="config-item">
              <span>Max Samples</span>
              <strong>266</strong>
            </div>
            <div class="config-item">
              <span>Max Features</span>
              <strong>1.0</strong>
            </div>
            <div class="config-item">
              <span>Random State</span>
              <strong>42</strong>
            </div>
          </div>

          <div class="save-row">
            <button class="save-button" @click="saveChanges">Save Changes</button>
            <span v-if="saveStatus" class="feedback feedback--success">{{ saveStatus }}</span>
          </div>
        </div>

        <div class="notifications-block">
          <h2>Notification Settings</h2>

          <div class="toggle-row">
            <span>Enable Push Notifications</span>
            <div class="toggle toggle--on"></div>
          </div>

          <div class="toggle-row">
            <span>Email alerts</span>
            <div class="toggle toggle--on toggle--small"></div>
          </div>

          <div class="input-row">
            <span>Email</span>
            <div class="input-box">alerts@mail.com</div>
          </div>

          <div class="input-row">
            <span>Password</span>
            <div class="input-box">••••••••••••••••</div>
          </div>

          <div class="send-row">
            <button class="send-button" @click="sendTestEmail">Send Test Email</button>
            <span v-if="emailStatus" class="feedback">{{ emailStatus }}</span>
          </div>
        </div>

        <div class="preview-block">
          <div class="preview-header">
            <h2>Threshold Preview</h2>
            <div class="mini-toggle"></div>
          </div>

          <div class="preview-chart">
            <RadiationChart />
          </div>
        </div>
      </section>
    </div>
  </MainLayout>
</template>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel {
  padding: 20px;
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

.panel h1 {
  margin-bottom: 18px;
  color: #eef4ff;
  font-size: 32px;
}

.threshold-block,
.model-block,
.notifications-block,
.preview-block {
  margin-bottom: 18px;
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(120, 151, 235, 0.1);
  background: rgba(255,255,255,0.03);
}

.threshold-header,
.preview-header,
.model-block__header,
.select-row,
.toggle-row,
.input-row,
.save-row,
.send-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.threshold-header,
.model-block__header,
.preview-header {
  margin-bottom: 14px;
}

.threshold-block h2,
.model-block h2,
.notifications-block h2,
.preview-block h2 {
  color: #eef4ff;
  font-size: 20px;
}

.threshold-row {
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #b7c7e4;
}

.threshold-row strong {
  color: #ffb36a;
}

.slider {
  position: relative;
  height: 8px;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
}

.slider__fill {
  width: 82%;
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #ff8c68, #ffb16f);
}

.slider__thumb {
  position: absolute;
  top: 50%;
  left: calc(82% - 8px);
  width: 16px;
  height: 16px;
  border-radius: 999px;
  background: #ffd6c6;
  transform: translateY(-50%);
  box-shadow: 0 0 12px rgba(255, 160, 120, 0.4);
}

.accuracy-box {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  color: #90a5cd;
}

.accuracy-box strong {
  color: #7ef0bf;
  font-size: 30px;
}

.select-row,
.toggle-row,
.input-row {
  margin-bottom: 14px;
  color: #b7c7e4;
}

.select-button,
.save-button,
.send-button {
  height: 38px;
  padding: 0 16px;
  border-radius: 10px;
  border: 1px solid rgba(120, 151, 235, 0.12);
  background: rgba(255,255,255,0.05);
  color: #dbe8ff;
  cursor: pointer;
}

.config-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.config-item {
  min-height: 64px;
  padding: 14px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.05);
  background: rgba(255,255,255,0.02);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
}

.config-item span,
.input-row span {
  color: #90a5cd;
}

.config-item strong,
.input-box {
  color: #eef4ff;
}

.save-row,
.send-row {
  margin-top: 16px;
  justify-content: flex-start;
}

.feedback {
  color: #8fe6c6;
  font-size: 14px;
}

.feedback--success {
  color: #7ef0bf;
}

.toggle {
  width: 48px;
  height: 26px;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  position: relative;
}

.toggle::after,
.mini-toggle::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 23px;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: #d8ecff;
}

.toggle--small {
  width: 42px;
}

.toggle--small::after {
  left: 19px;
}

.toggle--on,
.mini-toggle {
  background: rgba(126, 240, 191, 0.18);
  border: 1px solid rgba(126, 240, 191, 0.18);
}

.input-box {
  min-width: 240px;
  min-height: 40px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid rgba(120, 151, 235, 0.1);
  background: rgba(255,255,255,0.03);
  display: flex;
  align-items: center;
}

.mini-toggle {
  width: 44px;
  height: 24px;
  border-radius: 999px;
  position: relative;
}

.mini-toggle::after {
  top: 2px;
  left: 21px;
  width: 18px;
  height: 18px;
}

.preview-chart {
  height: 320px;
}

@media (max-width: 900px) {
  .config-grid {
    grid-template-columns: 1fr;
  }

  .threshold-row,
  .select-row,
  .toggle-row,
  .input-row,
  .model-block__header,
  .save-row,
  .send-row,
  .preview-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .input-box {
    min-width: 0;
    width: 100%;
  }
}
</style>
