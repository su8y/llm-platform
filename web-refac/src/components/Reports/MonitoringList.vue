<script setup>
import { MCP_TITLE } from '@/libs/constants.js'
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { INCOMING_LIST, STATUS, MONITORING_COLUMNS, PAGE_OPTIONS } from "@/libs/constants.js";
import { dateFormatter } from "@/libs/utils.js";

import DatePicker from '@/components/DatePicker/index.vue'
import UiSwitch from "@/components/Ui/UiSwitch.vue";

const router = useRouter()
const emits = defineEmits(['change', 'dateChange', 'search'])
const props = defineProps({
  monitoringData: Array,
  page: Object,
  dateRange: Object,
  searchFilter: Object,
  isAdmin: Boolean
})

const { locale } = useI18n()

const incomingType = ref('none')
const isDatePicker = ref(false)
const isSearchHide = ref(false)
const searchOption = ref(props.searchFilter)
const switchKey = ref(0)
const dropdownStatus = reactive({
  isIncomingTypeListStatus: false,
  isStatusListStatus: false,
  isPageOption: false
})

onMounted(() => {
  window.addEventListener('click', closeDropdown)
  window.addEventListener('touchstart', closeDropdown)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', closeDropdown)
  window.removeEventListener('touchstart', closeDropdown)
})

const onSearch = () => {
  emits('search')
}

const dateRangeStr = computed(() => {
  return `----.--.-- ~ ----.--.--`
})

const columns = computed(() => {
  if (props.isAdmin) {
    return MONITORING_COLUMNS
  } else {
    return MONITORING_COLUMNS.filter(item => item.key !== 'isMCP')
  }
})

const toggleDropdown = (type) => {
  switch (type) {
    case 'incoming':
      dropdownStatus.isIncomingTypeListStatus = !dropdownStatus.isIncomingTypeListStatus
      dropdownStatus.isStatusListStatus = false
      dropdownStatus.isPageOption = false
      break
    case 'status':
      dropdownStatus.isStatusListStatus = !dropdownStatus.isStatusListStatus
      dropdownStatus.isIncomingTypeListStatus = false
      dropdownStatus.isPageOption = false
      break
    case 'page':
      dropdownStatus.isStatusListStatus = false
      dropdownStatus.isIncomingTypeListStatus = false
      dropdownStatus.isPageOption = !dropdownStatus.isPageOption
      break
  }

  isDatePicker.value = false
}

const toggleDatePicker = () => {
  if (Object.values(dropdownStatus).some(item => item === true)) {
    isDatePicker.value = true
    Object.keys(dropdownStatus).forEach(item => {
      if (dropdownStatus[item]) dropdownStatus[item] = false
    })
    return
  }
  isDatePicker.value = !isDatePicker.value
}

const closeDropdown = () => {
  dropdownStatus.isPageOption = false
  dropdownStatus.isStatusListStatus = false
  dropdownStatus.isIncomingTypeListStatus = false
}

const selectIncomingType = (item, type) => {
  type === 'incoming'
    ? incomingType.value = item
    : searchOption.value.statusType = item
  toggleDropdown(type)
}

const selectDateRange = (date) => {
  emits('dateChange', date.start, date.end)
  isDatePicker.value = false
}

const onChangePage = (page) => {
  emits('change', 'current', page)
}

const dateReset = () => {
  emits('dateChange', null, null)
}

const selectPageOption = (item) => {
  emits('change', 'pageOption', item)
  toggleDropdown('page')
}

const goDetail = (id) => {
  router.push({name: 'MonitoringPost', params: { id: id }})
}

const getRatingPercent = (average) => {
  const percent = (average / 5) * 100
  return `width: ${percent}%`
}

const resetMCP = () => {
  switchKey.value++
  emits('change', 'mcp', null)
}

</script>

<template>
  <div class="monitoring-wrapper flex flex-column">
    <div class="search-wrapper" :class="{ isSearchHide }">
      <template v-if="!isSearchHide">
        <h3 class="search-title">
          {{ $t('common.searchFilter') }}
        </h3>
      </template>
      <div class="search">
        <template v-if="!isSearchHide">
         <div class="search-group">
            <div class="search-group-top history">
              <div class="search-group-top--date">
                <UiInput
                    :input-style="'date'"
                    :type="'text'"
                    :date-range="dateRange"
                    v-model="dateRangeStr"
                    @date-reset="dateReset"
                    @click.stop="toggleDatePicker()">
                  <template #label>
                    {{ $t('historyList.search.chatDate') }}
                  </template>
                </UiInput>
                <template v-if="isDatePicker">
                  <DatePicker @select-date-range="selectDateRange($event)" :date-range="dateRange"/>
                </template>
              </div>
              <div class="search-group-top--transparent" style="width: 102px;">
              </div>
            </div>
            <div class="search-group-bottom">
              <div class="search-group-bottom--status">
                <label>{{ $t('historyList.search.statusFilter') }}</label>
                <div class="be-dropdown status flex y-center" ref="dropdown" @click.stop.prevent="toggleDropdown('status')">
                  <span class="current-status flex y-center" :class="`status-${searchOption.statusType}`">
                    {{ STATUS[searchOption.statusType] ? $t(`common.statusList.${STATUS[searchOption.statusType]}`) : searchOption.statusType }}
                  </span>
                  <span class="be-icon size-20 icon-grey-md icon-dropdown">
                    <i class="font-icon-right-arrow"></i>
                  </span>
                  <Transition name="slide">
                    <template v-if="dropdownStatus.isStatusListStatus">
                      <ul class="list" :class="{'is-show': dropdownStatus.isStatusListStatus}">
                        <template v-for="type in STATUS" :key="type">
                          <li @click.stop="selectIncomingType(type, 'status')">
                            <span class="status" :class="`status-${type}`">
                              {{ $t(`common.statusList.${type}`) }}
                            </span>
                          </li>
                        </template>
                      </ul>
                    </template>
                  </Transition>
                </div>
              </div>
              <div class="search-group-bottom--id">
                <UiInput
                    :type="'text'"
                    v-model="searchOption.id"
                    @enter="onSearch">
                  <template #label>
                    {{ $t('historyList.search.id') }}
                  </template>
                </UiInput>
              </div>
              <div class="search-group-bottom--manager">
                <UiInput
                    :type="'text'"
                    v-model="searchOption.manager"
                    @enter="onSearch">
                  <template #label>
                    {{ $t('historyList.search.manager') }}
                  </template>
                </UiInput>
              </div>
              <UiButton :type="'icon primary sm'"  @click="onSearch" style="margin-top: 19px;">
                <i class="font-icon-search"/>
                <span class="btn-text">
                  {{ $t('common.search') }}
                </span>
              </UiButton>
            </div>
          </div>
        </template>
        <div class="search-hide" @click="isSearchHide = !isSearchHide">
          <i class="font-icon-left-arrow" />
        </div>
      </div>
    </div>
    <div class="be-list-wrapper">
      <div class="pagination-wrapper">
        <div class="search-group flex flex-column x-center">
          <div class="be-dropdown status flex y-center" ref="dropdown" @click.stop.prevent="toggleDropdown('page')">
            <span class="current-page-option flex y-center">
              {{ $t('common.pageCount', { count: props.page.selectedOption }) }}
            </span>
            <span class="be-icon size-20 icon-grey-md icon-dropdown">
              <i class="font-icon-right-arrow"></i>
            </span>
            <Transition name="slide">
              <template v-if="dropdownStatus.isPageOption">
                <ul class="list" :class="{'is-show': dropdownStatus.isPageOption}">
                  <template v-for="type in PAGE_OPTIONS" :key="type">
                    <li @click.stop="selectPageOption(type)">
                      <span class="status">
                        {{ $t('common.pageCount', { count: type }) }}
                      </span>
                    </li>
                  </template>
                </ul>
              </template>
            </Transition>
          </div>
        </div>
        <div class="line xs"></div>
        <UiPagination
            :total="props.page.totalLength"
            :limit="props.page.limit"
            :currentPage="props.page.currentPage"
            @changePage="onChangePage" />
        <template v-if="props.isAdmin">
          <div class="playground-toolbar">
            <div class="line xs"></div>
            <div class="toolbar-toggle">
              <span class="toolbar-text">{{ MCP_TITLE }}</span>
              <UiSwitch :key="switchKey"
                        :default="false"
                        :off-color="'#d7d7d7'"
                        :on-color="'#64b950'"
                        :off-label="''"
                        :on-label="''"
                        :size="'xsmall'"
                        :width="30"
                        :on-value="true"
                        :off-value="false"
                        @change="emits('change', 'mcp', $event)"/>
            </div>
            <div class="mcp-reset" title="Reset MCP Option">
              <i class="font-icon-refresh" @click="resetMCP"/>
            </div>
          </div>
        </template>
      </div>
      <table class="be-table">
        <colgroup>
          <template v-if="props.isAdmin">
            <col style="width: 100px">
          </template>
          <col style="width: 250px">
          <col style="width: 150px">
          <col style="width: 120px">
          <col style="width: 130px">
          <col style="width: 109px">
          <col style="width: 100px">
        </colgroup>
        <thead>
          <tr class="thead-row">
            <template v-for="column in columns" :key="column.key">
              <th :class="column">
                <template v-if="column.title === MCP_TITLE && props.isAdmin">
                  {{ column.title }}
                </template>
                <template v-else>
                  {{ $t(`historyList.column.${column.title}`) }}
                </template>
              </th>
            </template>
          </tr>
        </thead>
        <tbody :class="{noData: !props.monitoringData || props.monitoringData.length === 0}">
          <template v-if="props.monitoringData && props.monitoringData.length > 0">
            <template v-for="row in props.monitoringData" :key="row.sessionKey">
              <tr @click="goDetail(row.sessionKey)">
                <template v-for="header in columns" :key="header.key">
                  <td class="monitoring-list" >
                    <template v-if="header.key === 'issueStatus'">
                      <span :class="header.key === 'issueStatus' && `status-${row[header.key]}`">
                        {{ $t(`common.statusList.${STATUS[row[header.key]]}`) }}
                      </span>
                    </template>
                    <template v-else-if="header.key === 'regDate'">
                      <span>
                        {{ dateFormatter(row[header.key], 'time') }}
                      </span>
                    </template>
                    <template v-else-if="header.key === 'rating'">
                      <span class="rating-wrapper">
                        <span class="rating">
                          <span :style="getRatingPercent(row[header.key])"></span>
                        </span>
                      </span>
                    </template>
                    <template v-else>
                      <span>
                        {{ row[header.key] ? row[header.key] : '-' }}
                      </span>
                    </template>
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
.rating-wrapper {
  display: flex;
  justify-content: center;
}

.rating, .rating > span {
  display: flex;
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

.monitoring-wrapper {
  gap: 30px;
  padding: 20px 40px;

  .number {
    line-height: 75%; /* 60px */
  }

  .search-wrapper {
    positoin: relative;
    .search {
      .search-group {
        &-top {
          &--date {
            width: 240px;
            transition: all .3s;
          }
        }

        &-bottom {
          &--status {
            width: 240px;
            margin-right: 0;
            transition: all .3s;
          }

          &--id {
            width: 250px;
            transition: all .3s;
          }

          &--manager {
            width: 192px;
            transition: all .3s;
          }
        }
      }
    }

    .icon-wrap {
    }
  }
}

@media all and (max-width: 1400px) {
  .monitoring-wrapper {
    .search-wrapper {
      position: relative;
      .search {
        .search-group {
          &-top {
            .search-group-top {
              &--date {
                width: 210px;
              }
            }
          }

          &-bottom {
            &--status{
              min-width: 210px;
              width: 210px;
            }

            &--id {
              width: 210px;
            }
          }
        }

        .transparent {
          width: 225px;
          height: 149px;
        }
      }
    }
  }
}

@media all and (max-width: 1390px) {
  .monitoring-wrapper {
    .search-wrapper {
      .search {
        .icon-wrap {
        }
      }
    }
  }
}

</style>
