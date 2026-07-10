<template>
    <div class="curve-card">
      <div class="curve-card__header">
        <div>
          <h3>{{ title }}</h3>
          <p>{{ subtitle }}</p>
        </div>
      </div>
  
      <div class="curve-chart-wrapper">
        <canvas v-show="hasData" ref="chartRef"></canvas>
  
        <div v-if="!hasData" class="curve-empty">
          Curve data is not available for the selected models.
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
  import Chart from 'chart.js/auto'
  import type { CurvePoint } from '../types/api'
  
  const props = defineProps<{
    title: string
    subtitle: string
    xLabel: string
    yLabel: string
    modelAName: string
    modelBName: string
    modelAPoints: CurvePoint[]
    modelBPoints: CurvePoint[]
  }>()
  
  const chartRef = ref<HTMLCanvasElement | null>(null)
  let chartInstance: Chart | null = null
  
  const hasData = computed(() => {
    return props.modelAPoints.length > 0 || props.modelBPoints.length > 0
  })
  
  const destroyChart = () => {
    if (chartInstance) {
      chartInstance.destroy()
      chartInstance = null
    }
  }
  
  const buildDataset = (label: string, points: CurvePoint[], active = false) => {
    return {
      label,
      data: points,
      parsing: false as const,
      borderColor: active ? '#85dfff' : '#8fe6c6',
      backgroundColor: active ? 'rgba(133, 223, 255, 0.14)' : 'rgba(143, 230, 198, 0.14)',
      borderWidth: active ? 3 : 2,
      pointRadius: 0,
      pointHoverRadius: 4,
      tension: 0.18,
    }
  }
  
  const renderChart = () => {
    destroyChart()
  
    if (!chartRef.value || !hasData.value) return
  
    const context = chartRef.value.getContext('2d')
    if (!context) return
  
    const datasets: ReturnType<typeof buildDataset>[] = []
  
    if (props.modelAPoints.length) {
      datasets.push(buildDataset(props.modelAName, props.modelAPoints, true))
    }
  
    if (props.modelBPoints.length) {
      datasets.push(buildDataset(props.modelBName, props.modelBPoints, false))
    }
  
    chartInstance = new Chart(context, {
      type: 'line',
      data: {
        datasets,
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: {
            display: true,
            labels: {
              color: '#b8c8e8',
              boxWidth: 10,
              boxHeight: 10,
              usePointStyle: true,
            },
          },
          tooltip: {
            backgroundColor: 'rgba(9, 14, 28, 0.96)',
            borderColor: 'rgba(120, 151, 235, 0.16)',
            borderWidth: 1,
            titleColor: '#eef4ff',
            bodyColor: '#d6e3ff',
            callbacks: {
              label: (context) => {
                const point = context.raw as CurvePoint
                return `${context.dataset.label}: ${props.xLabel} ${point.x.toFixed(3)}, ${props.yLabel} ${point.y.toFixed(3)}`
              },
            },
          },
        },
        scales: {
          x: {
            type: 'linear',
            min: 0,
            max: 1,
            title: {
              display: true,
              text: props.xLabel,
              color: '#90a4cd',
            },
            ticks: {
              color: '#8296be',
              callback: (value) => Number(value).toFixed(1),
            },
            grid: {
              color: 'rgba(255,255,255,0.04)',
            },
            border: {
              display: false,
            },
          },
          y: {
            min: 0,
            max: 1,
            title: {
              display: true,
              text: props.yLabel,
              color: '#90a4cd',
            },
            ticks: {
              color: '#8296be',
              callback: (value) => Number(value).toFixed(1),
            },
            grid: {
              color: 'rgba(255,255,255,0.04)',
            },
            border: {
              display: false,
            },
          },
        },
      },
    })
  }
  
  onMounted(renderChart)
  
  watch(
    () => [
      props.modelAName,
      props.modelBName,
      props.modelAPoints,
      props.modelBPoints,
      props.title,
    ],
    () => {
      renderChart()
    },
    { deep: true },
  )
  
  onBeforeUnmount(() => {
    destroyChart()
  })
  </script>
  
  <style scoped>
  .curve-card {
    border-radius: 18px;
    border: 1px solid rgba(120, 151, 235, 0.1);
    background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.022));
    padding: 14px;
  }
  
  .curve-card__header {
    margin-bottom: 12px;
  }
  
  .curve-card__header h3 {
    margin: 0 0 6px;
    color: #eef4ff;
    font-size: 16px;
  }
  
  .curve-card__header p {
    margin: 0;
    color: #8ea5d2;
    font-size: 12px;
    line-height: 1.4;
  }
  
  .curve-chart-wrapper {
    position: relative;
    height: 280px;
    border-radius: 16px;
    overflow: hidden;
    background: linear-gradient(180deg, rgba(8, 13, 28, 0.58), rgba(8, 13, 28, 0.92));
    border: 1px solid rgba(120, 151, 235, 0.08);
    padding: 12px;
  }
  
  .curve-empty {
    height: 100%;
    display: grid;
    place-items: center;
    color: #8296be;
    font-size: 13px;
    text-align: center;
  }
  </style>
  