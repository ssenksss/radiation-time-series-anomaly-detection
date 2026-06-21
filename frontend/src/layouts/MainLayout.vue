<script setup lang="ts">
import AppSidebar from '../components/AppSidebar.vue'
import AppTopbar from '../components/AppTopbar.vue'
</script>

<template>
  <div class="main-layout">
    <AppSidebar />

    <div class="main-layout__content">
      <AppTopbar />

      <main class="main-layout__page">
        <div class="main-layout__inner">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.main-layout {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 210px minmax(0, 1fr);
  background:
      radial-gradient(circle at 12% 35%, rgba(56, 88, 210, 0.08), transparent 18%),
      linear-gradient(180deg, rgba(8, 12, 24, 0.98), rgba(7, 10, 20, 1));
}

.main-layout__content {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.main-layout__page {
  flex: 1;
  padding: 16px 16px 24px;
}

.main-layout__inner {
  width: 100%;
  max-width: 1240px;
  margin: 0 auto;
}

@media (max-width: 1100px) {
  .main-layout {
    grid-template-columns: 88px minmax(0, 1fr);
  }
}

@media (max-width: 768px) {
  .main-layout {
    grid-template-columns: 1fr;
  }

  .main-layout__page {
    padding: 14px;
  }

  .main-layout__inner {
    max-width: 100%;
  }
}
</style>