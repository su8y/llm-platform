<script setup>
import { reactive, inject, onMounted, onBeforeUnmount, computed, ref } from 'vue'

import { PAGE_OPTIONS, PLAN_COLUMNS, WARNING_TYPE, PLAN_LIST } from "@/libs/constants.js";
import { dateFormatter, thousand } from "@/libs/utils.js";

import Warning from "@/components/Modal/Warning.vue";
// import SubscribePlan from "@/components/Modal/SubscribePlan.vue";

const modal = inject('$modal')
const emits = defineEmits(['change'])
const props = defineProps({
  historyData: Array,
  planData: Object,
  page: Object
})

const pageInfo = ref(props.page)
const plans = reactive({
  isPlanDropdown: false,
  selectPlanOption: 'all'
})

onMounted(() => {
  window.addEventListener('click', closeDropdown)
  window.addEventListener('touchstart', closeDropdown)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', closeDropdown)
  window.removeEventListener('touchstart', closeDropdown)
})

// plan battery 계산
const battery = computed(() => {
  const ratio = (props.planData.useAbleCredit / props.planData.totalCredit) * 100

  return ratio >= 70 ? 'full' : ratio >= 30 ? 'half' : 'handful';
})

const toggleDropdown = (type = '') => {
  if (type === 'page') {
    pageInfo.value.isPageOption = !pageInfo.value.isPageOption
    plans.isPlanDropdown = false
    return
  }

  pageInfo.value.isPageOption = false
  plans.isPlanDropdown = !plans.isPlanDropdown
}

const selectPageOption = (item, type = '') => {
  toggleDropdown(type)

  if (type === 'page') {
    emits('change', 'pageOption', item)
  }

  emits('change', 'plan', item)
}

const closeDropdown = () => {
  pageInfo.value.isPageOption = false
  plans.isPlanDropdown = false
}

const onChangePage = (current) => {
  pageInfo.value.currentPage = current
  emits('change', 'current', current)
}

const onPlanCancel = async () => {
  try {
    await modal.open(Warning, WARNING_TYPE.PLAN_CANCEL).then(async () => {
      modal.close()
    }).catch(() => {
      modal.close()
    })
  } catch (e) {
    alert(e)
    console.error('Error: ', e)
  }
}
</script>

<template>
  <div class="plan--wrapper">
    <div class="current-plan--wrapper">
      <span class="title">{{ $t('plan.usingPlan') }}</span>
      <div class="current-plan">
        <div class="current-plan-name">
          <span class="plan-name" :class="{none: !planData?.planName }">
            {{ planData.planName || $t('plan.none') }}
          </span>
          <span class="icon-wrap">
            <i class="icon" :class="`icon--battery-${battery}`" />
          </span>
        </div>
<!--        <div class="line middle"></div>-->
<!--        <div class="plan-btn-wrap">-->
<!--          <UiButton :type="'outline'" @click="modal.open(SubscribePlan)">-->
<!--            {{ t('plan.planChange') }}-->
<!--          </UiButton>-->
<!--          <UiButton :type="'outline'" @click="onPlanCancel">-->
<!--            {{ t('plan.planCancel') }}-->
<!--          </UiButton>-->
<!--        </div>-->
      </div>
      <div class="current-plan-desc">
        <div class="desc-wrapper">
          <span class="desc">{{ $t('plan.remainingQuestion') }}</span>
          <span class="plan-data">
            {{
              planData.planName
                ? `${thousand(planData.useAbleCredit)}/${thousand(planData.totalCredit)}`
                : 0
            }}{{ $t('plan.questionCount') }}
          </span>
        </div>
        <div class="desc-wrapper">
          <span class="desc">{{ $t('plan.usePeriod') }}</span>
          <span class="plan-data">
            {{
              planData.startDate && planData.endDate
              ? `${dateFormatter(planData.startDate)} ~ ${dateFormatter(planData.endDate)}`
              : '-'
            }}
          </span>
        </div>
        <div class="desc-wrapper">
          <span class="desc">{{ $t('plan.nextPlan.title') }}</span>
          <span class="plan-data">
            {{
              planData.nextDate
                ? $t('plan.nextPlan.desc', { date: dateFormatter(planData.nextDate), plan: planData.nextPlanName })
                : $t('plan.nextPlan.nonPlan')
            }}
          </span>
        </div>
      </div>
    </div>
    <div class="be-list-wrapper">
      <div class="pagination-wrapper reference">
        <div class="plan-usage-status">
          <span class="title">{{ $t('plan.planUsageStatus') }}</span>
          <div class="search-group flex flex-column x-center">
            <div class="be-dropdown status flex y-center" ref="dropdown" @click.stop.prevent="toggleDropdown()">
              <span class="current-page-option flex y-center">
                {{
                  plans.selectPlanOption === 'all'
                    ? $t(`common.statusList.${plans.selectPlanOption}`)
                    : plans.selectPlanOption
                }}
              </span>
              <span class="be-icon size-20 icon-grey-md icon-dropdown">
                  <i class="font-icon-right-arrow"></i>
                </span>
              <Transition name="slide">
                <ul class="list" :class="{'is-show': pageInfo.isPageOption}" v-if="plans.isPlanDropdown">
                  <template v-for="type in PLAN_LIST" :key="type">
                    <li @click.stop="selectPageOption(type)">
                      <span class="status">
                        {{
                          type === 'all'
                            ? $t(`common.statusList.${type}`)
                            : type
                        }}
                      </span>
                    </li>
                  </template>
                </ul>
              </Transition>
            </div>
          </div>
        </div>
        <div class="pagination plan">
          <div class="search-group flex flex-column x-center">
            <div class="be-dropdown status flex y-center" ref="dropdown" @click.stop.prevent="toggleDropdown('page')">
              <span class="current-page-option flex y-center">
                {{ $t('common.pageCount', { count: pageInfo.selectedOption }) }}
              </span>
              <span class="be-icon size-20 icon-grey-md icon-dropdown">
                <i class="font-icon-right-arrow"></i>
              </span>
              <Transition name="slide">
                <ul class="list" :class="{'is-show': pageInfo.isPageOption}" v-if="pageInfo.isPageOption">
                  <template v-for="type in PAGE_OPTIONS" :key="type">
                    <li @click.stop="selectPageOption(type, 'page')">
                      <span class="status">
                        {{ $t('common.pageCount', { count: type }) }}
                      </span>
                    </li>
                  </template>
                </ul>
              </Transition>
            </div>
          </div>
          <div class="line xs"></div>
          <UiPagination
              :total="props.page.totalLength"
              :limit="pageInfo.limit"
              :currentPage="pageInfo.currentPage"
              @changePage="onChangePage" />
        </div>
      </div>
      <table class="be-table">
        <colgroup>
          <col style="width: 116px">
          <col style="width: 271px">
          <col style="width: 121px">
          <col style="width: 121px">
<!--          <col style="width: 121px">-->
<!--          <col style="width: 121px">-->
        </colgroup>
        <thead>
          <tr class="thead-row">
            <template v-for="column in PLAN_COLUMNS" :key="column.key">
              <th>
                <span>
                  {{ $t(`plan.column.${column.title}`) }}
                </span>
              </th>
            </template>
          </tr>
        </thead>
        <tbody :class="{noData: !props.historyData || props.historyData.length === 0}">
          <template v-if="props.historyData && props.historyData.length > 0">
            <template v-for="row in props.historyData" :key="row.endDate">
              <tr>
                <template v-for="header in PLAN_COLUMNS" :key="header.key">
                  <td>
                    <span v-if="header.key === 'usePeriod'">
                      {{ `${dateFormatter(row.startDate)} ~ ${dateFormatter(row.endDate)}` }}
                    </span>
                    <span v-else-if="header.key === 'initCredit'">
                      {{ thousand(row.initCredit) }}
                    </span>
                    <span v-else-if="header.key === 'useCredit'">
                      {{ thousand(row.useCredit) }}
                    </span>
                    <span v-else :class="{title: header.key === 'title'}" >
                      {{ row[header.key] ? row[header.key] : '-' }}
                    </span>
                  </td>
                </template>
              </tr>
            </template>
          </template>
          <template v-else>
            <tr class="none-data">
              <td colspan="8">
                {{ $t('common.noData') }}
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.plan {
  &--wrapper {
    display: flex;
    flex-direction: column;
    gap: 24px;
    padding: 32px;

    .current-plan {
      &--wrapper {
        width: 100%;
        height: 260px;
        background-color: $whiteColor;
        border-radius: $radius-16;
        box-shadow: 0px 1px 3px 0px rgba(0, 0, 0, 0.16);
        padding: 28px;
        display: flex;
        flex-direction: column;
        gap: 27px;
        position: relative;

        .title {
          color: $grey-600;
          font-size: 16px;
          font-weight: 700;
        }

        .current-plan {
          display: flex;
          place-items: center;
          gap: 25px;
          margin-top: 9px;

          .current-plan-name {
            display: flex;
            place-items: center;
            gap: 15px;

            .plan-name {
              color: $mainColor;
              font-size: 40px;
              font-weight: 600;
              margin-top: -5px;
            }
          }

          .plan-btn-wrap {
            display: flex;
            place-items: center;
            gap: 8px;
          }
        }

        .current-plan-desc {
          display: flex;
          flex-direction: column;
          gap: 12px;

          .desc-wrapper {
            display: flex;
            align-items: center;
            gap: 20px;

            .desc {
              color: #767676;
              font-size: 13px;
              font-weight: 600;
            }

            .plan-data {
              color: $grey-600;
              font-size: 15px;
              font-weight: 400;
            }
          }
        }
      }

    }
  }
}

</style>
