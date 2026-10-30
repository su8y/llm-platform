<script setup>
import {computed, defineAsyncComponent, onBeforeUnmount, onMounted, ref} from "vue";

import { dateFormatter } from '@/libs/utils.js'

import DatePicker from '@/components/DatePicker/index.vue'

const BarChart = defineAsyncComponent(() =>
    import('@/components/Chart/BarChart.vue')
)
const LineChart = defineAsyncComponent(() =>
    import('@/components/Chart/LineChart.vue')
)
const StackedChart = defineAsyncComponent(() =>
    import('@/components/Chart/StackedChart.vue')
)

const emits = defineEmits(['change'])
const props = defineProps({
  ratingGraphData: Object,
  responseCountData: Object,
  askRanking: Array,
  dateRange: Object
})

const isDatePicker = ref(false)

onMounted(() => {
  window.addEventListener('click', (e) => {
    const className = e.target.className
    if (!className.includes('vc')) {
      isDatePicker.value = false
    }
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('click', () => {
    isDatePicker.value = false
  })
})

const dateRangeStr = computed(() => {
  return `${dateFormatter(props.dateRange.start)} ~ ${dateFormatter(props.dateRange.end)}`
})

const selectDateRange = (date) => {
  emits('change', date.start, date.end)
  isDatePicker.value = false
}

const getRatingPercent = (average) => {
  const percent = (average / 5) * 100
  return `width: ${percent}%`
}
</script>

<template>
  <div class="dashboard" ref="dashboard">
    <template v-if="props.ratingGraphData && props.responseCountData">
      <div class="dashboard--period-wrapper">
        <span class="period-label">{{ $t('dashboard.dateRange') }}</span>
        <div class="period">
          <span class="period-date">{{ dateRangeStr }}</span>
          <UiButton :type="'icon outline primary'" @click.stop="isDatePicker = !isDatePicker">
            {{ $t('common.edit') }}
            <i class="font-icon-write" />
          </UiButton>
          <template v-if="isDatePicker">
            <DatePicker :date-range="dateRange" @select-date-range="selectDateRange($event)" />
          </template>
        </div>
      </div>
      <div class="dashboard--analyzed-wrapper">
        <div class="analyzed">
          <div class="analyzed-rating">
            <span class="analyzed-title">{{ $t('dashboard.rating') }}</span>
            <div class="analyzed-rating-average">
              <div class="analyzed-rating-average-left">
                <div class="average">
                  <span>{{ props.ratingGraphData.average ? props.ratingGraphData.average : '0' }}</span>
                </div>
                <span class="slash">/</span>
                <span class="total">5</span>
              </div>
              <div class="analyzed-rating-average-right">
                <span class="rating">
                  <span :style="getRatingPercent(props.ratingGraphData.average)"></span>
                </span>
              </div>
            </div>
            <div class="analyzed-rating-count-graph">
              <template v-if="props.ratingGraphData">
                <BarChart :rating-graph-data="props.ratingGraphData" :x="props.ratingGraphData.askGraph.X" :data="props.ratingGraphData.askGraph.data" />
              </template>
            </div>
            <span class="analyzed-rating-target">
              {{ $t('dashboard.ratingTarget') }} :
              {{ $t('dashboard.ratingDesc', {
                  average: ratingGraphData.target.targetCount,
                  total: ratingGraphData.target.total,
                  percent: ratingGraphData.target.targetRatio
                })
              }}
            </span>
          </div>
          <div class="analyzed-rating-graph">
            <span class="analyzed-title">{{ $t('dashboard.ratingGraph') }}</span>
            <div class="analyzed-rating-graph">
              <template v-if="props.ratingGraphData">
                <LineChart :x="props.ratingGraphData.ratingGraph.X" :data="props.ratingGraphData.ratingGraph.data" />
              </template>
            </div>
          </div>
        </div>
        <div class="analyzed reverse">
          <div class="analyzed-ranking">
            <span class="analyzed-title">ASK Top3</span>
            <div class="analyzed-ranking-wrap" :class="{'none-data': !props.askRanking}">
              <template v-if="props.askRanking && props.askRanking.length !== 0">
                <template v-for="(item, index) in props.askRanking" :key="item">
                  <div class="ranking">
                    <span class="number">{{ index + 1 }}</span>
                    <span class="ranking-text">{{ item || '-' }}</span>
                  </div>
                </template>
              </template>
              <div v-else>
                <p>{{ $t('dashboard.comingSoon') }}</p>
              </div>
            </div>
          </div>
          <div class="analyzed-answer">
            <div class="analyzed-answer-header">
              <span class="analyzed-title">
                {{ $t('dashboard.answerCount') }}
                <span class="count">
                  {{ $t('dashboard.answerCountDesc', {
                      average: props.responseCountData.average,
                      total: props.responseCountData.total
                    })
                  }}
                </span>
              </span>
              <div class="legend">
                <span class="question">
                  {{ $t('dashboard.askQuestion') }}
                </span>
                <span class="session">
                  {{ $t('dashboard.askSession') }}
                </span>
              </div>
            </div>
            <div class="analyzed-response-graph">
              <template v-if="props.responseCountData">
                <StackedChart
                    :x="props.responseCountData.chat.X"
                    :data="props.responseCountData.chat.data"
                    :session-data="props.responseCountData.session.data"
                    :color="['#64B4C6', '#ec0047']"
                    :name="[$t('dashboard.askQuestion'), $t('dashboard.askSession')]"
                />
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.dashboard {
  padding: 32px 40px;
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
        &:first-child {
          width: 420px;
          height: 390px;
        }
        &:last-child {
          flex: 1;
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
        &-average {
          display: flex;
          align-items: center;
          gap: 34px;

          &-left {
            display: flex;
            align-items: center;
            gap: 12px;

            .average {
              height: 80px;
              box-sizing: border-box;
              color: #EC0047;
              font-size: 60px;
              font-weight: 700;
              line-height: 100%;
              border-radius: $radius-12;
              background: $grey-50;
              box-shadow: 0px 1px 4px 0px rgba(0, 0, 0, 0.12) inset;
              padding: 10px 12px;
            }

            .slash {
              color: $grey-600;
              font-size: 28px;
              font-weight: 700;
            }

            .total {
              margin-left: 2px;
              width: 52px;
              height: 52px;
              display: flex;
              align-items: center;
              justify-content: center;
              border-radius: $radius-12;
              background: $grey-700;
              color: $whiteColor;
              text-align: center;
              font-size: 36px;
              font-weight: 700;
            }
          }

          &-right {
            display: flex;
            gap: 4px;
            align-items: center;

            .rating, .rating > span {
              display: inline-block;
              height: 20px;
              overflow: hidden;
              background: url('../../assets/img/icon-star-rating.svg') no-repeat;
            }

            .rating {
              width: 109px;

              span {
                background-position: left bottom;
                line-height: 0;
                vertical-align: top;
              }
            }
          }
        }


        &-target {
          color: $grey-500;
          font-size: 13px;
          font-weight: 400;
          text-align: center;
        }

        &-graph {
          display: flex;
          flex-direction: column;
          gap: 24px;
          .line_chart {
            width: 100%;
            height: 285px;
          }
        }

        &-count-graph {
          margin-top: 11px;
          width: 100%;

          .bar_chart {
            width: 100%;
            height: 162px;
          }
        }
      }

      &.reverse {
        flex-direction: row-reverse;

        .analyzed {

          &-answer {
            display: flex;
            flex-direction: column;
            gap: 24px;
            height: 408px;
            &-header {
              display: flex;
              justify-content: space-between;

              .legend {
                display: flex;
                gap: 24px;
                span {
                  display: flex;
                  align-items: center;
                  gap: 8px;
                  &:before {
                    display: inline-block;
                    content: '';
                    width: 8px;
                    height: 3px;
                    border-radius: 1.5px;
                  }

                  &.question {
                    &:before {
                      background-color: #64b4c6;
                    }
                  }
                  &.session {
                    &:before {
                      background-color: #ec0047;
                    }
                  }
                }
              }
            }
          }
          &-ranking {
            display: flex;
            flex-direction: column;
            gap: 24px;
            height: 408px;

            &-wrap {
              height: 312px;
              padding: 20px 16px 96px 16px;
              border-radius: $radius-8;
              background: #F3F3F3;

              .ranking {
                display: flex;
                align-items: center;
                gap: 12px;
                border-bottom: 1px dashed $line-sm;
                padding: 20px 0;

                &:first-child {
                  padding-top: 0;
                }

                &:last-child {
                  border: none;
                }

                .number {
                  display: flex;
                  min-width: 32px;
                  min-height: 32px;
                  flex-direction: column;
                  justify-content: center;
                  align-items: center;
                  color: $whiteColor;
                  text-align: center;
                  font-size: 18px;
                  font-weight: 700;
                  border-radius: $radius-8;
                  background: $grey-700;
                }

                &-text {
                  color: #444;
                  font-size: 14px;
                  font-weight: 400;
                  line-height: 150%; /* 21px */
                }
              }

              &.none-data {
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: $grey-600;
                font-size: 20px;
                font-weight: bold;
                padding: 90px;
              }

            }
          }
          &-response-graph {

            .stacked_chart {
              width: 100%;
              height: 302px;
            }
          }
        }
      }
    }
  }
}

</style>
