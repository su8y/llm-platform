<script setup>
import { onMounted, watch } from 'vue'
import * as echarts from 'echarts';
import { BarChart } from "echarts/charts";
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
  const bar = document.querySelector('.bar_chart')

  const chartOptions = {
    textStyle: {
      color: '#444',
      fontFamily: 'Pretendard Variable, "Noto Sans KR", "Noto Sans JP", sans-serif'
    },
    xAxis: {
      type: 'category',
      data: props.x,
      boundaryGap: true,
      splitLine: {
        show: false
      },
      axisTick: {
        show: false
      },
    },
    yAxis: {
      type: 'value',
      offset: 4,
      boundaryGap: true,
      interval: 5,
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
      max: function (value) {
        return value.max * 2;
      }
    },
    series: [
      {
        data: props.data,
        barWidth: 10,
        itemStyle: {
          color: '#ec0047',
          barBorderRadius: 5
        },
        type: 'bar'
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

  if (bar) {
    echarts.use([BarChart])
    const chart = echarts.init(bar)

    chart.setOption(chartOptions)
  }
}

watch(() => props.data, () => {
  onChart()
})
</script>

<template>
  <div class="chart bar_chart" ref="bar"></div>
</template>

<style lang="scss" scoped>

</style>
