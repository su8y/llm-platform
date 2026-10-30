<script setup>
import {onBeforeMount, onBeforeUnmount, onMounted, watch} from 'vue'
import { useI18n } from 'vue-i18n'

import * as echarts from 'echarts';
import { LineChart } from "echarts/charts";
import 'echarts/lib/chart/line'
import 'echarts/lib/chart/bar'
import 'echarts/lib/component/tooltip'
import 'echarts/lib/component/legend'

const { t } = useI18n()
const props = defineProps({
  x: Array,
  data: Array,
  sessionData: Array,
  color: Array,
  name: Array,
  lineInterval: {
    type: Number,
    default: 50
  }
})

onMounted(() => {
  onChart()
})

const onChart = () => {
  const stacked = document.querySelector('.stacked_chart')

  const chartOptions = {
    textStyle: {
      color: '#444',
      fontFamily: 'Pretendard Variable, "Noto Sans KR", "Noto Sans JP", sans-serif'
    },
    tooltip: {
      trigger: 'axis',
      borderWidth: 0,
      borderRadius: 8,
      padding: [16, 20],
      extraCssText: 'box-shadow: 0px 0px 0px 1px rgba(0, 0, 0, 0.08), 0px 8px 16px 0px rgba(0, 0, 0, 0.16);',
      formatter: function (params) {
        return `
                <div style="min-width: 122px; display: flex; flex-direction: column; gap: 8px;">
                  <span style="color: #444; font-size: 13px; font-weight: 600;">${params[0].axisValueLabel}</span>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="display: flex; align-items: center; gap: 5px;">
                      ${params[0].marker}
                      <span style="font-size: 12px; font-weight: 400; color: #666;">${params[0].seriesName}</span>
                    </span>
                    <span style="font-size: 13px; font-weight: 600; color: #444;">${params[0].data}</span>
                  </div>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="display: flex; align-items: center; gap: 5px;">
                      ${params[1].marker}
                      <span style="font-size: 12px; font-weight: 400; color: #666;">${params[1].seriesName}</span>
                    </span>
                    <span style="font-size: 13px; font-weight: 600; color: #444;">${params[1].data}</span>
                  </div>
                </div>
              `;
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
      interval: props.lineInterval,
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      splitLine: {
        show: true,  // 이 부분을 추가하세요!
        lineStyle: {
          color: '#e5e5e5',
          width: 1,
          type: 'solid'
        }
      },

      min: 0
    },
    series: [
      {
        name: props.name[0],
        type: 'line',
        smooth: true,
        data: props.data,
        itemStyle: {
          color: props.color[0]
        }
      },
      {
        name: props.name[1],
        type: 'line',
        smooth: true,
        data: props.sessionData,
        itemStyle: {
          color: props.color[1]
        }
      },
    ],
    grid: {
      containLabel: true,
      right: 20,
      left: 5,
      top: 30,
      bottom: 0
    }
  };

  if (stacked) {
    echarts.use([LineChart])
    const chart = echarts.init(stacked)

    chart.resize()

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
  <div class="chart stacked_chart" ref="stacked"></div>
</template>

<style lang="scss" scoped>

</style>
