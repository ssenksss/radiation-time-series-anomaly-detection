<script setup lang="ts">
defineProps<{
  title: string
  description: string
  priority?: string
  buttonLabel?: string
}>()

const emit = defineEmits<{
  (e: 'acknowledge'): void
}>()
</script>

<template>
  <div class="panel alert-panel" role="alert">
    <div class="panel__header">
      <div>
        <p class="panel__eyebrow">System Alert</p>
        <h2>{{ title }}</h2>
      </div>
    </div>

    <p class="alert-panel__text">
      {{ description }}
    </p>

    <div class="alert-panel__footer">
      <div class="alert-panel__priority">
        <span class="alert-dot"></span>
        <span>{{ priority ?? 'High priority event' }}</span>
      </div>

      <button
          v-if="buttonLabel"
          class="alert-button"
          type="button"
          @click="emit('acknowledge')"
      >
        {{ buttonLabel }}
      </button>
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
  justify-content: space-between;
  gap: 14px;
  color: #ffb3b3;
  font-weight: 600;
  font-size: 14px;
}

.alert-panel__priority {
  display: flex;
  align-items: center;
  gap: 10px;
}

.alert-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #ff6b6b;
  box-shadow: 0 0 14px rgba(255, 107, 107, 0.8);
}

.alert-button {
  height: 38px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 170, 185, 0.24);
  background: linear-gradient(180deg, rgba(255, 106, 128, 0.96), rgba(217, 56, 84, 0.96));
  color: #fff7f8;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}
</style>