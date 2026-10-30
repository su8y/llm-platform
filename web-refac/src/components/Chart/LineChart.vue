<script setup>
import { onBeforeMount, onBeforeUnmount, onMounted, watch } from 'vue'
import * as echarts from 'echarts';
import { LineChart } from "echarts/charts";
import 'echarts/lib/chart/line'
import 'echarts/lib/chart/bar'
import 'echarts/lib/component/tooltip'
import 'echarts/lib/component/legend'

const props = defineProps({
  x: Array,
  data: Array
})
onMounted(() => {
  onChart()
})

const onChart = () => {
  const line = document.querySelector('.line_chart')

  const chartOptions = {
    textStyle: {
      color: '#444',
      fontFamily: 'Pretendard Variable, "Noto Sans KR", "Noto Sans JP", sans-serif'
    },
    legend: {
      itemGap: 22,
      top: -20,
      right: 10,
      itemWidth: 8,
      itemHeight: 8,
      borderWidth: 0,
      symbolKeepAspect: true,
      textStyle: {
        padding: [
          2, 0, 0, 0
        ]
      }
    },
    xAxis: {
      type: 'category',
      data: props.x.map((data) => {
        return data.slice(5, data.length)
      }),
      boundaryGap: true,
      splitLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      axisLine: {
        lineStyle: {
          color: '#767676'
        }
      }
    },
    yAxis: {
      type: 'value',
      offset: 4,
      boundaryGap: true,
      interval: 1,
      splitLine: {
        show: true
      },
      axisTick: {
        show: false
      },
      axisLine: {
        show: false
      },
      min: 0,
      max: 5
    },
    series: [
      {
        data: props.data,
        barWidth: 10,
        itemStyle: {
          color: '#ec0047',
        },
        smooth: true,
        type: 'line'
      }
    ],
    grid: {
      containLabel: true,
      right: 20,
      left: 5,
      top: 30,
      bottom: 0
    },
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: '#fff',
      padding: 10,
      extraCssText: 'border-radius: 8px; box-shadow: 0 8px 15px 0 rgba(0, 0, 0, 0.16), 0 0 0 1px rgba(0, 0, 0, 0.16);',
      textStyle: {
        color: '#666',
        fontSize: 12
      },
      axisPointer: {
        type: 'shadow',
        lineStyle: {
          color: 'rgba(0, 0, 0, 0.25)'
        }
      },
      shadowStyle: {
        color: 'rgba(0, 0, 0, 0.06)'
      }
    },
  };

  if (line) {
    echarts.use([LineChart])
    const chart = echarts.init(line)

    window.onresize = function() {
      chart.resize();
    };
    chart.setOption(chartOptions)
  }
}

onBeforeMount(() => {
  window.addEventListener('resize', onChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onChart)
})

watch(() => props.data, () => {
  onChart()
})

</script>

<template>
  <div class="chart line_chart" ref="line"></div>
</template>

<style lang="scss" scoped>

</style>
