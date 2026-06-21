<template>
  <aside class="sidebar">
    <div class="sidebar__brand">
      <div class="sidebar__atom">⌬</div>
      <span class="sidebar__title">Radiation Monitoring</span>
    </div>

    <nav class="sidebar__nav">
      <RouterLink to="/" class="sidebar__link" active-class="sidebar__link--active">
        <span class="sidebar__icon">◫</span>
        <span class="sidebar__label">Dashboard</span>
      </RouterLink>

      <RouterLink to="/anomalies" class="sidebar__link" active-class="sidebar__link--active">
        <span class="sidebar__icon">⌁</span>
        <span class="sidebar__label">Anomalies</span>
      </RouterLink>

      <RouterLink to="/dataset" class="sidebar__link" active-class="sidebar__link--active">
        <span class="sidebar__icon">✦</span>
        <span class="sidebar__label">Dataset</span>
      </RouterLink>

      <RouterLink to="/settings" class="sidebar__link" active-class="sidebar__link--active">
        <span class="sidebar__icon">⚙</span>
        <span class="sidebar__label">Settings</span>
      </RouterLink>

      <RouterLink to="/help" class="sidebar__link" active-class="sidebar__link--active">
        <span class="sidebar__icon sidebar__icon--help">?</span>
        <span class="sidebar__label">Help</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 18px 14px;
  border-right: 1px solid rgba(120, 151, 235, 0.1);
  background:
    radial-gradient(circle at 18% 20%, rgba(82, 104, 255, 0.14), transparent 24%),
    radial-gradient(circle at 20% 74%, rgba(84, 194, 255, 0.08), transparent 20%),
    linear-gradient(180deg, rgba(8, 12, 24, 0.96), rgba(7, 10, 20, 0.99));
  overflow: hidden;
}

.sidebar::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at 26px 30px, rgba(255,255,255,0.22), transparent),
    radial-gradient(1px 1px at 80px 120px, rgba(255,255,255,0.16), transparent),
    radial-gradient(1px 1px at 120px 240px, rgba(255,255,255,0.14), transparent),
    radial-gradient(1px 1px at 60px 360px, rgba(255,255,255,0.18), transparent),
    radial-gradient(1px 1px at 148px 460px, rgba(255,255,255,0.14), transparent);
  opacity: 0.22;
  pointer-events: none;
}

.sidebar__brand {
  position: relative;
  z-index: 1;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
  padding: 0 4px 12px;
  border-bottom: 1px solid rgba(120, 151, 235, 0.08);
}

.sidebar__atom {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  color: #c0daff;
  font-size: 22px;
  flex-shrink: 0;
}

.sidebar__title {
  color: #eef4ff;
  font-size: 13px;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
}

.sidebar__nav {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sidebar__link {
  min-height: 52px;
  padding: 0 14px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  gap: 14px;
  text-decoration: none;
  color: #a8b8d8;
  border: 1px solid transparent;
  transition: 0.2s ease;
}

.sidebar__link:hover {
  background: rgba(255, 255, 255, 0.035);
  color: #eef4ff;
}

.sidebar__link--active {
  background: rgba(107, 158, 255, 0.1);
  border-color: rgba(107, 158, 255, 0.16);
  color: #f4f8ff;
  box-shadow:
    inset 3px 0 0 #65abff,
    0 0 16px rgba(101, 171, 255, 0.06);
}

.sidebar__icon {
  width: 18px;
  text-align: center;
  color: #bfd5ff;
  flex-shrink: 0;
}

.sidebar__label {
  font-size: 14px;
  line-height: 1.2;
}

@media (max-width: 1100px) {
  .sidebar {
    padding-inline: 10px;
  }

  .sidebar__title,
  .sidebar__label {
    display: none;
  }

  .sidebar__brand,
  .sidebar__link {
    justify-content: center;
    padding-inline: 0;
  }
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }
}
</style>
