<script setup lang="ts">
withDefaults(
    defineProps<{
      title: string
      value: string
      meta: string
      type?: 'normal' | 'danger' | 'warning'
    }>(),
    {
      type: 'normal',
    }
)
</script>

<template>
  <div class="stat-card">
    <span class="stat-card__label">{{ title }}</span>
    <strong class="stat-card__value">{{ value }}</strong>
    <span
        class="stat-card__meta"
        :class="{
        'stat-card__meta--danger': type === 'danger',
        'stat-card__meta--warning': type === 'warning',
        'stat-card__meta--neutral': type === 'normal',
      }"
    >
      {{ meta }}
    </span>
  </div>
</template>

<style scoped>
.stat-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(131, 170, 255, 0.14);
  border-radius: 22px;
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(10, 15, 30, 0.92));
  box-shadow:
      0 10px 30px rgba(0, 0, 0, 0.28),
      inset 0 1px 0 rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(14px);
}

.stat-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at top right, rgba(110, 168, 255, 0.14), transparent 34%);
  pointer-events: none;
}

.stat-card__label {
  position: relative;
  z-index: 1;
  color: #8fa3c7;
  font-size: 13px;
}

.stat-card__value {
  position: relative;
  z-index: 1;
  font-size: 28px;
  line-height: 1;
  color: #ffffff;
}

.stat-card__meta {
  position: relative;
  z-index: 1;
  font-size: 13px;
  font-weight: 600;
}

.stat-card__meta--neutral {
  color: #8fd3ff;
}

.stat-card__meta--danger {
  color: #ff7d7d;
}

.stat-card__meta--warning {
  color: #ffbf75;
}
</style>