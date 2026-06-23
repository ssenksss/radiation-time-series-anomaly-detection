<template>
  <div class="chart-wrapper">
    <canvas v-show="hasData" ref="chartRef"></canvas>

    <div v-if="!hasData" class="chart-empty">
      No chart data available.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Chart from 'chart.js/auto'

const props = withDefaults(
    defineProps<{
      labels?: string[]
      values?: number[]
      threshold?: number
      anomalyFlags?: boolean[]
    }>(),
    {
      threshold: 0.18,
    },
)

const values = computed(() => props.values ?? [])

const labels = computed(() => {
  const incomingLabels = props.labels ?? []

  if (!values.value.length) {
    return []
  }

  if (incomingLabels.length === values.value.length) {
    return incomingLabels
  }

  return values.value.map((_, index) => incomingLabels[index] ?? `#${index + 1}`)
})

const hasData = computed(() => {
  return labels.value.length > 0 && values.value.length > 0
})

const anomalyValues = computed(() =>
    values.value.map((value, index) => {
      if (props.anomalyFlags && props.anomalyFlags.length) {
        return props.anomalyFlags[index] ? value : null
      }

      return value > props.threshold ? value : null
    }),
)

const thresholdValues = computed(() =>
    values.value.map(() => props.threshold),
)

const chartRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

const destroyChart = () => {
  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }
}

const renderChart = () => {
  destroyChart()

  if (!chartRef.value || !hasData.value) return

  const ctx = chartRef.value.getContext('2d')
  if (!ctx) return

  const gradient = ctx.createLinearGradient(0, 0, 0, 320)
  gradient.addColorStop(0, 'rgba(110, 231, 255, 0.20)')
  gradient.addColorStop(1, 'rgba(110, 231, 255, 0.01)')

  const maxValue = Math.max(...values.value, props.threshold)
  const roundedMax = Math.ceil((maxValue + 0.1) * 10) / 10

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels.value,
      datasets: [
        {
          label: 'Radiation Levels',
          data: values.value,
          borderColor: '#79dbff',
          backgroundColor: gradient,
          fill: true,
          tension: 0.42,
          borderWidth: 3,
          pointRadius: 0,
          pointHoverRadius: 4,
        },
        {
          label: 'Detected Anomalies',
          data: anomalyValues.value,
          borderColor: 'transparent',
          backgroundColor: '#ff8d6f',
          pointBorderColor: '#ffc3ad',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 6,
          showLine: false,
        },
        {
          label: 'Anomaly Threshold',
          data: thresholdValues.value,
          borderColor: '#ff9b58',
          borderWidth: 2,
          borderDash: [8, 6],
          pointRadius: 0,
          tension: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          backgroundColor: 'rgba(9, 14, 28, 0.96)',
          borderColor: 'rgba(120, 151, 235, 0.16)',
          borderWidth: 1,
          titleColor: '#eef4ff',
          bodyColor: '#d6e3ff',
          displayColors: true,
        },
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(255,255,255,0.04)',
          },
          border: {
            display: false,
          },
          ticks: {
            color: '#8296be',
            font: {
              size: 12,
            },
            maxTicksLimit: 8,
          },
        },
        y: {
          min: 0,
          max: roundedMax,
          ticks: {
            color: '#8296be',
            font: {
              size: 12,
            },
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
    () => [props.labels, props.values, props.threshold, props.anomalyFlags],
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
.chart-wrapper {
  position: relative;
  height: 320px;
  border-radius: 18px;
  overflow: hidden;
  background:
      linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px),
      linear-gradient(180deg, rgba(8, 13, 28, 0.58), rgba(8, 13, 28, 0.92));
  background-size: 100% 48px, 48px 100%, 100% 100%;
  border: 1px solid rgba(120, 151, 235, 0.08);
  padding: 12px 14px 8px;
}

.chart-wrapper canvas {
  filter: drop-shadow(0 0 10px rgba(121, 219, 255, 0.18));
}

.chart-empty {
  height: 100%;
  display: grid;
  place-items: center;
  color: #8296be;
  font-size: 14px;
}
</style>