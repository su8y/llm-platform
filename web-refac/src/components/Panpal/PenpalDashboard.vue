<script setup>
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, ref } from "vue"
import { useI18n } from 'vue-i18n'

import { dateFormatter, thousand } from '@/libs/utils.js'
import { PENPAL_STATUS } from '@/libs/constants.js'

import PenpalDashboardNoneData from "@/components/Panpal/PenpalDashboardNoneData.vue"

const PieChart = defineAsyncComponent(() =>
  import('@/components/Chart/PieChart.vue')
)
const StackedChart = defineAsyncComponent(() =>
  import('@/components/Chart/StackedChart.vue')
)

const props = defineProps({
  workStatusData: Object,
  lineChartData: Object,
  managerData: Array || Object,
  dateRange: Object
})

const receivedColorList = {
  parsed: '#04A6FF',
  answering: '#004585',
  sent: '#FFD900',
  spam: '#d7d7d7',
  close: '#9ACC67'
}
const pendingColorList = [{r: 212, g: 234, b: 189}, {r: 87, g: 171, b: 0}]
const inProgressColorList = [{r: 186, g: 223, b: 255}, {r: 0, g: 116, b: 255}]
const managerColorList = [
'#5A9BE6',
'#F2C34A',
'#4FB7A8',
'#E65D6E',
'#58A96B',
'#9D7CC7',
'#6DC2EA',
'#F5A24A',
'#7F8FD6',
'#B7D96B',
'#D65D89',
'#65C7C2',
'#C178A6',
'#E3D85A',
'#6C8FB2',
'#8BCB6B',
'#F07E5E',
'#7FA1B5',
'#B6C2D2',
'#9AB2C7',
'#8A8A8A'
]

const { locale } = useI18n()

const isDatePicker = ref(false)

const penpalStatus = computed(() => {
  return Object.keys(PENPAL_STATUS).map(key => PENPAL_STATUS[key]).filter(item => item !== 'all')
})

const managerChartData = computed(() => {
  if (!props.managerData) {
    return []
  }

  if (!Array.isArray(props.managerData)) {
    const dataArray = Object.entries(props.managerData).sort((a, b) => b[1] - a[1])

    let processedData = []

    if (dataArray.length > 20) {
      const top20 = dataArray.slice(0, 20)
      const others = dataArray.slice(20)
      const otherSum = others.reduce((sum, [key, value]) => sum + value, 0)

      processedData = top20.map(([key, value]) => ({
        name: key,
        value: value,
        color: managerColorList
      }))


      if (otherSum > 0) {
        processedData.push({
          name: 'other',
          value: otherSum,
          color: managerColorList
        })
      }
    } else {
      processedData = dataArray.map(([key, value]) => ({
        name: key,
        value: value,
        color: managerColorList
      }))
    }

    return processedData
  }

  return []
})

const receivedData = computed(() => {
  if (!props.workStatusData?.all) {
    return []
  }

  if (!Array.isArray(props.workStatusData?.all)) {
    return Object.entries(props.workStatusData?.all).map(([key, value]) => {
      const name = key.slice(5).toLowerCase()
      return {
        name: name === 'closed' ? 'close' : name,
        value: value,
        color: receivedColorList[name]
      }
    }).filter(item => item.name !== 'all')
  }

  return []
})

const receivedTotal = computed(() => {
  return !Array.isArray(props.workStatusData?.all) ? props.workStatusData?.all.countAll : 0
})

const pendingData = computed(() => {
  if (!props.workStatusData?.parsed) {
    return []
  }

  return props.workStatusData?.parsed.map((item) => {
    return {
      name: item.days,
      value: item.count,
      color: pendingColorList
    }
  })
})

const pendingTotal = computed(() => {
  let total = 0

  if (props.workStatusData?.parsed.length) {
    total = props.workStatusData?.parsed.reduce((acc, cur) => {
      return acc + cur.count
    }, 0)
  }

  return total
})

const inProgressData = computed(() => {
  if (!props.workStatusData?.answering) {
    return []
  }

  return props.workStatusData?.answering.map((item) => {
    return {
      name: item.days,
      value: item.count,
      color: inProgressColorList
    }
  })
})

const inProgressTotal = computed(() => {
  let total = 0

  if (props.workStatusData?.answering.length) {
    total = props.workStatusData?.answering.reduce((acc, cur) => {
      return acc + cur.count
    }, 0)
  }

  return total
})

onMounted(() => {
  window.addEventListener('click', (e) => {
    const className = e.target.className
    if (!className.includes('vc')) {
      isDatePicker.value = false
    }
  })
})

onBeforeUnmount(() => {
  document.body.style.overflow = 'auto'

  window.removeEventListener('click', () => {
    isDatePicker.value = false
  })
})

const dateRangeStr = computed(() => {
  return `${dateFormatter(props.dateRange.start)} ~ ${dateFormatter(props.dateRange.end)}`
})

</script>

<template>
  <div class="dashboard" ref="dashboard">
    <div class="dashboard--period-wrapper">
      <span class="period-label">{{ $t('dashboard.dateRange') }}</span>
      <div class="period">
        <span class="period-date">{{ dateRangeStr }}</span>
      </div>
    </div>
    <div class="dashboard--analyzed-wrapper">
      <div class="analyzed">
        <div class="analyzed-rating">
          <span class="analyzed-title">{{ $t('penpal.dashboard.workStatus.title') }}</span>
          <div class="charts-wrapper" :class="locale">
            <div class="chart-received">
              <span class="chart-title">{{ $t('penpal.dashboard.workStatus.received', { count: thousand(receivedTotal) }) }}</span>
              <template v-if="!receivedData.length">
                <div class="none-data">
                  <div class="graph">
                    <PenpalDashboardNoneData :type="'noneReceived'" />
                    <div class="pie_chart"></div>
                  </div>
                  <div class="label">
                    <div class="marker"></div>
                    <span>{{ $t('penpal.detail.noneManager') }}</span>
                  </div>
                </div>
              </template>
              <template v-else>
                <PieChart :data="receivedData" :type="'received'" />
                <div class="label">
                  <template v-for="name in penpalStatus" :key="name">
                    <div>
                      <span class="dashboard-status">
                        <i :class="`label-status-${name}`"></i>
                      </span>
                      <span class="label-text">{{ $t(`penpal.statusList.${name}`) }}</span>
                    </div>
                  </template>
                </div>
              </template>
            </div>
            <div class="chart-pending">
              <span class="chart-title">{{ $t('penpal.dashboard.workStatus.pending', { count: thousand(pendingTotal) }) }}</span>
              <template v-if="!pendingData.length">
                <div class="none-data">
                  <div class="graph">
                    <PenpalDashboardNoneData :type="'nonePending'" />
                    <div class="pie_chart"></div>
                  </div>
                  <div class="label delay">
                    <span class="label-title">{{ $t('penpal.dashboard.workStatus.delayDayCount') }}</span>
                    <i class="icon icon--none-delay-day" />
                    <div class="label-text flex x-between y-center">
                      <span v-html="$t('penpal.dashboard.workStatus.dayCount')"></span>
                      <span>6{{ $t('why.visual.days') }}</span>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <PieChart :data="pendingData" :type="'pending'" />
                <div class="label">
                  <span class="label-title">{{ $t('penpal.dashboard.workStatus.delayDayCount') }}</span>
                  <i class="icon icon--delay-day" />
                  <div class="label-text flex x-between y-center">
                    <span v-html="$t('penpal.dashboard.workStatus.dayCount')"></span>
                    <span>6{{ $t('why.visual.days') }}</span>
                  </div>
                </div>
              </template>
            </div>
            <div class="chart-in-progress">
              <span class="chart-title">{{ $t('penpal.dashboard.workStatus.inProgress', { count: thousand(inProgressTotal) }) }}</span>
              <template v-if="!inProgressData.length">
                <div class="none-data">
                  <div class="graph">
                    <PenpalDashboardNoneData :type="'noneInProgress'" />
                    <div class="pie_chart"></div>
                  </div>
                  <div class="label delay">
                    <span class="label-title">{{ $t('penpal.dashboard.workStatus.delayDayCount') }}</span>
                    <i class="icon icon--none-delay-day" />
                    <div class="label-text flex x-between y-center">
                      <span v-html="$t('penpal.dashboard.workStatus.dayCount')"></span>
                      <span>6{{ $t('why.visual.days') }}</span>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <PieChart :data="inProgressData" :type="'inProgress'" />
                <div class="label">
                  <span class="label-title">{{ $t('penpal.dashboard.workStatus.delayDayCount') }}</span>
                  <i class="icon icon--delay-day-blue" />
                  <div class="label-text flex x-between y-center">
                    <span v-html="$t('penpal.dashboard.workStatus.dayCount')"></span>
                    <span>6{{ $t('why.visual.days') }}</span>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
      <div class="analyzed bottom" :class="locale">
        <div class="analyzed-answer">
          <div class="analyzed-answer-header">
            <span class="analyzed-title">
              {{ $t('penpal.dashboard.sentCount.title') }}
            </span>
            <div class="legend">
              <span class="question">
                {{ $t('penpal.dashboard.sentCount.received') }}
              </span>
              <span class="session">
                {{ $t('penpal.dashboard.sentCount.sentReply') }} {{ $t('penpal.dashboard.sentCount.byShipmentDate') }}
              </span>
            </div>
          </div>
          <div class="analyzed-response-graph">
            <template v-if="!props.lineChartData"></template>
            <template v-else>
              <StackedChart
                  :x="props.lineChartData?.received.X"
                  :data="props.lineChartData?.received.data"
                  :session-data="props.lineChartData?.sent.data"
                  :color="['#bbb', '#ec0047']"
                  :name="[$t('penpal.dashboard.sentCount.received'), $t('penpal.dashboard.sentCount.sentReply')]"
                  :line-interval="25"
              />
            </template>
          </div>
          <div class="annotation">
            <span>{{ $t('penpal.dashboard.sentCount.annotation') }}</span>
          </div>
        </div>
        <div class="analyzed-ranking">
          <span class="analyzed-title">{{ $t('penpal.dashboard.managerAssignmentRatio.title') }}</span>
          <div class="charts-wrapper">
            <template v-if="!managerChartData.length">
              <div class="none-data">
                <PenpalDashboardNoneData :type="'noneReceived'" />
                <div class="pie_chart"></div>
              </div>
            </template>
            <template v-else>
              <PieChart :data="managerChartData" :type="'manager'" />
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.dashboard {
  padding: 32px 40px;
  box-sizing: border-box;
  &--period-wrapper {
    display: flex;
    align-items: center;
    gap: 16px;
    .period {
      position: relative;
      display: flex;
      align-items: center;
      gap: 16px;

      &-label {
        color: $grey-300;
        font-size: 13px;
        font-weight: 600;
      }

      &-date {
        color: $grey-600;
        font-size: 16px;
        font-weight: 700;
      }
    }
  }

  &--analyzed-wrapper {
    margin-top: 14px;
    display: flex;
    flex-direction: column;
    gap: 24px;

    .analyzed {
      display: flex;
      gap: 24px;

      > div {
        padding: 28px;
        border-radius: $radius-16;
        background: $whiteColor;
        box-shadow: 0px 1px 3px 0px rgba(0, 0, 0, 0.16);
        height: 406px;
        flex: 1;
      }

      &.bottom {
        &.en {
          min-width: 1040px;
        }
        > div {
          padding: 28px;
          border-radius: $radius-16;
          background: $whiteColor;
          box-shadow: 0px 1px 3px 0px rgba(0, 0, 0, 0.16);

          &:first-child {
            flex: 1;
            height: 420px;
          }
          &:last-child {
            max-width: 424px;
            width: 424px;
            height: 420px;
          }
        }

        .analyzed-answer-header {
          display: flex;
          align-items: center;
          justify-content: space-between;

          .legend {
            display: flex;
            align-items: center;
            gap: 50px;

            span {
              color: #2F2F2F;
              font-size: 12px;
              font-weight: 400;

              &.question {
                position: relative;
                &:before {
                  content: '';
                  display: inline-block;
                  width: 8px;
                  height: 3px;
                  border-radius: 1.5px;
                  background: #bbb;
                  position: absolute;
                  left: -16px;
                  top: 50%;
                  transform: translateY(-50%);
                }
              }

              &.session {
                position: relative;
                &:before {
                  content: '';
                  display: inline-block;
                  width: 8px;
                  height: 3px;
                  border-radius: 1.5px;
                  background: $mainColor;
                  position: absolute;
                  left: -16px;
                  top: 50%;
                  transform: translateY(-50%);
                }
              }
            }
          }
        }
      }


      &-title {
        color: $grey-600;
        font-size: 16px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 20px;

        .count {
          color: #444;
          font-size: 12px;
          font-weight: 400;
          line-height: 12px; /* 100% */

          strong {
            font-weight: 700;
          }
        }
      }

      &-rating {
        display: flex;
        flex-direction: column;
        gap: 16px;
        height: 406px;

        .charts-wrapper {
          display: grid;
          grid-template-columns: repeat(3, 270px);
          justify-content: center;
          grid-column-gap: 56px;
          transition: all .3s;

          div[class^="chart-"] {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 19px;
            height: 298px;

            .chart-title {
              color: #444;
              font-size: 13px;
              font-weight: 400;
            }

            &.chart-received {
              position: relative;
              .label {
                margin-top: 6px;
                display: grid;
                grid-template-columns: repeat(3, 1fr);

                .label-text {
                  min-width: 56px;
                  padding: 4px 8px;
                }
              }
            }

            &.chart-pending, &.chart-in-progress {
              .label {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 9px;

                &-title {
                  color: #2F2F2F;
                  font-size: 12px;
                  font-weight: 600;
                }

                &-text {
                  width: 100%;
                  color: #2F2F2F;
                  font-size: 12px;
                  font-weight: 400;
                  line-height: 100%; /* 12px */
                }
              }
            }

            .pie_chart {
              width: 270px;
              height: 210px;
            }

            .none-data {
              height: 294px;

              .graph {
                position: relative;

                .pie_chart {
                  width: 190px;
                  height: 190px;
                  background-color: #D8D8D8;
                  border-radius: 50%;
                  opacity: 0.3;
                }
              }

              .label {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                opacity: 0.3;
                margin-top: 25px;

                &.delay {
                  margin-top: 20px;
                }

                .marker {
                  width: 10px;
                  height: 10px;
                  border-radius: 100px;
                  background-color: #D7D7D7;
                  padding: 8px;
                }

                .label-text {
                  width: 160px;
                  color: #444;
                  font-size: 12px;
                  font-weight: 400;
                }
              }
            }
          }

          &.en {
            grid-template-columns: repeat(3, 314px);
            grid-column-gap: 20px;

            div[class^="chart-"] {
              height: 310px;
            }
          }

          @media all and (min-width: 1800px) {
            grid-column-gap: 120px;

            &.en {
              grid-column-gap: 76px;
            }
          }
        }
      }

      &-answer {
        position: relative;

        .annotation {
          position: absolute;
          bottom: 24px;
          right: 26px;
          color: #2F2F2F;
          font-size: 12px;
          font-weight: 400;
        }
      }

      &-response-graph {

        .stacked_chart {
          width: 100%;
          height: 302px;
        }
      }

      &-ranking {
        .charts-wrapper {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;

          .none-data {
            position: relative;

            .pie_chart {
              background-color: #D8D8D8;
              border-radius: 50%;
              opacity: 0.3;
            }
          }
        }

        .pie_chart {
          width: 240px;
          height: 240px;
        }
      }
    }
  }
}

</style>
