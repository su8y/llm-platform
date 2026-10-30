<script setup>
import { onMounted, watch, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import * as echarts from 'echarts';
import { PieChart } from "echarts/charts";
import 'echarts/lib/chart/line'
import 'echarts/lib/chart/pie'
import 'echarts/lib/component/tooltip'
import 'echarts/lib/component/legend'
import {thousand} from "@/libs/utils.js";

const props = defineProps({
  x: Array,
  data: Array,
  type: String
})

const { t } = useI18n()

const pieRef = ref(null)

onMounted(() => {
  onChart()
})

const onChart = () => {
  const pie = pieRef.value

  const getColorByDays = (days, maxDays, minColor, maxColor) => {
    const ratio = maxDays === 0 ? 0 : days / maxDays

    const r = Math.round(minColor.r + (maxColor.r - minColor.r) * ratio)
    const g = Math.round(minColor.g + (maxColor.g - minColor.g) * ratio)
    const b = Math.round(minColor.b + (maxColor.b - minColor.b) * ratio)

    const toHex = (value) => {
      const hex = value.toString(16)
      return hex.length === 1 ? '0' + hex : hex
    }

    return `#${toHex(r)}${toHex(g)}${toHex(b)}`
  }

  const chartOptions = {
    textStyle: {
      color: '#444',
      fontFamily: 'Pretendard Variable, "Noto Sans KR", "Noto Sans JP", sans-serif'
    },
    tooltip: {
      trigger: 'item',
      width: 126,
      height: 61,
      borderWidth: 0,
      borderRadius: 8,
      padding: 14,
      extraCssText: 'box-shadow: 0px 0px 0px 1px rgba(0, 0, 0, 0.08), 0px 8px 16px 0px rgba(0, 0, 0, 0.16);',
      formatter: function (params) {
        return `
                <div style="min-width: 98px; display: flex; flex-direction: column; gap: 8px;">
                  <span style="display: flex; align-items: center; gap: 8px;">
                    <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: ${params.color};"></span>
                    <span style="font-size: 12px; font-weight: 400; color: #666;">${params.name}</span>
                  </span>
                  <span style="font-size: 13px; font-weight: 600; color: #444;">${params.percent.toFixed(1)}%(${thousand(params.value)}${t('plan.questionCount')})</span>
                </div>
              `;
      }
    },
    series: [
      {
        type: 'pie',
        radius: ['30%', '100%'],
        center: ['50%', '50%'],
        data: props.data,
        label: {
          show: false
        },
        labelLine: {
          show: false
        },
        emphasis: {
          label: {
            show: false
          },
          labelLine: {
            show: false
          },
          scale: false,
          scaleSize: 0
        }
      }
    ]
  };

  if (props.type === 'received') {
    chartOptions.series[0].data = props.data?.map((data) => {
      return {
        value: data.value,
        name: t(`penpal.statusList.${data.name}`),
        itemStyle: {
          color: data.color
        }
      }
    })
  }

  if (props.type === 'pending' || props.type === 'inProgress') {

    const maxDays = Math.max(...props.data.map(item => parseInt(item.name)))

    chartOptions.series[0].data = props.data.map((data) => {
      const days = parseInt(data.name)
      const color = getColorByDays(days, maxDays, data.color[0], data.color[1])

      return {
        value: data.value,
        name: `${data.name}${t('penpal.dashboard.workStatus.delayDay')}`,
        itemStyle: {
          color: color,
          borderColor: 'rgba(255, 255, 255, 0.60)',
          borderWidth: 1,
        }
      }
    })
  }

  if (props.type === 'manager') {
    chartOptions.series[0].data = props.data.map((data, i) => {
      let color;
      if (data.name === 'none') {
        color = '#d7d7d7';
      } else if (data.name === 'other') {
        color = data.color[data.color.length - 1]
      } else {
        color = data.color[i];
      }

      return {
        value: data.value,
        name: data.name === 'none'
                ? t('penpal.detail.noneManager')
                : data.name === 'other'
                  ? t('penpal.dashboard.managerAssignmentRatio.other')
                  : data.name,
        itemStyle: {
          color: color
        }
      }
    })
  }

  if (pie) {
    echarts.use([PieChart])
    const chart = echarts.init(pie)
    chart.setOption(chartOptions)
  }
}

watch(() => props.data, () => {
  onChart()
})
</script>

<template>
  <div class="chart pie_chart" :class="props.type" ref="pieRef"></div>
</template>

<style lang="scss" scoped>
.pie_chart {
  width: 190px !important;
  height: 190px !important;

  > div {
    height: 190px !important;
  }

  &.manager {
    width: 240px !important;
    height: 240px !important;
  }
}

</style>
