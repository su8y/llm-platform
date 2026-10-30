<script setup>
import { ref, computed, onMounted, onBeforeUnmount, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router';

import { dateFormatter } from "@/libs/utils.js";
import { PAGE_OPTIONS, PENPAL_LIST_COLUMNS, PENPAL_STATUS } from "@/libs/constants.js";

import DatePicker from "@/components/DatePicker/index.vue";

const router = useRouter()

const emits = defineEmits(['change', 'dateChange', 'searchChange'])
const props = defineProps({
  inboxData: Array,
  searchFilter: Object,
  dateRange: Object,
  page: Object,
  managerList: Array,
})

const isDatePicker = ref(false)
const isSearchHide = ref(false)
const searchOption = ref(props.searchFilter)
const dropdownStatus = reactive({
  isPageOption: false,
  isManagerList: false,
  isStatusList: false
})

onMounted(() => {
  window.addEventListener('click', closeDropdown)
  window.addEventListener('touchstart', closeDropdown)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', closeDropdown)
  window.removeEventListener('touchstart', closeDropdown)
})

const dateRangeStr = computed(() => {
  return `----.--.-- ~ ----.--.--`
})

const selectDateRange = (date) => {
  emits('dateChange', date.start, date.end)
  isDatePicker.value = false
}

const toggleDropDown = (type) => {
  switch (type) {
    case 'manager':
      dropdownStatus.isManagerList = !dropdownStatus.isManagerList
      dropdownStatus.isPageOption = false
      dropdownStatus.isStatusList = false
      break
    case 'status':
      dropdownStatus.isStatusList = !dropdownStatus.isStatusList
      dropdownStatus.isManagerList = false
      dropdownStatus.isPageOption = false
      break
    case 'page':
      dropdownStatus.isPageOption = !dropdownStatus.isPageOption
      dropdownStatus.isManagerList = false
      dropdownStatus.isStatusList = false
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

const selectDropDown = (item, type) => {
  switch (type) {
    case 'manager':
      searchOption.value.manager = item
      emits('searchChange', 'manager', item)
      break
    case 'status':
      searchOption.value.statusType = item
      emits('searchChange', 'status', item)
      break
    case 'page':
      emits('change', 'pageOption', item)
      break
  }

  toggleDropDown(type)
}

const onChangePage = (page) => {
  emits('change', 'current', page)
}

const dateReset = () => {
  emits('dateChange', null, null)
}

const closeDropdown = () => {
  dropdownStatus.isPageOption = false
  dropdownStatus.isManagerList = false
  dropdownStatus.isStatusList = false
}

const onSearch = () => {
  emits('search')
}
</script>

<template>
  <div class="penpal-wrapper flex flex-column">
    <div class="search-wrapper" :class="{ isSearchHide }">
      <template v-if="!isSearchHide">
        <h3 class="title be-font text-grey-md bold size-18 flex y-center">
          {{ $t('common.searchFilter') }}
        </h3>
      </template>
      <div class="search">
        <template v-if="!isSearchHide">
          <div class="search-group">
            <div class="search-group-top email">
              <div class="search-group-top--date">
                <UiInput
                    :input-style="'date'"
                    :type="'text'"
                    :date-range="dateRange"
                    v-model="dateRangeStr"
                    @date-reset="dateReset"
                    @click.stop="toggleDatePicker()">
                  <template #label>
                    {{ $t('penpal.search.receivedDate') }}
                  </template>
                </UiInput>
                <template v-if="isDatePicker">
                  <DatePicker @select-date-range="selectDateRange($event)" :date-range="dateRange"/>
                </template>
              </div>
              <div class="search-group-top--from">
                <UiInput
                    v-model="searchOption.from"
                    :type="'text'"
                    @enter="onSearch">
                  <template #label>
                    {{ $t('penpal.search.sender') }}
                  </template>
                </UiInput>
              </div>
              <div class="search-group-top--transparent">
              </div>
            </div>
            <div class="search-group-bottom email">
              <div class="search-group-bottom--subject">
                <UiInput
                    v-model="searchOption.subject"
                    :type="'text'"
                    @enter="onSearch">
                  <template #label>
                    {{ $t('penpal.search.subject') }}
                  </template>
                </UiInput>
              </div>
              <div class="search-group-bottom--status">
                <label>{{ $t('penpal.search.status') }}</label>
                <div class="be-dropdown status flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('status')">
                  <span class="current-status flex y-center" :class="`status-${searchOption.status}`">
                    {{ PENPAL_STATUS[searchOption.status] ? $t(`penpal.statusList.${PENPAL_STATUS[searchOption.status]}`) : searchOption.status }}
                  </span>
                  <span class="be-icon size-20 icon-grey-md icon-dropdown">
                    <i class="font-icon-right-arrow"></i>
                  </span>
                  <Transition name="slide">
                    <template v-if="dropdownStatus.isStatusList">
                      <ul class="list" :class="{'is-show': dropdownStatus.isStatusList}">
                        <template v-for="type in PENPAL_STATUS" :key="type">
                          <li @click.stop="selectDropDown(type, 'status')">
                            <span class="status" :class="`status-${type}`">
                              {{ $t(`penpal.statusList.${type}`) }}
                            </span>
                          </li>
                        </template>
                      </ul>
                    </template>
                  </Transition>
                </div>
              </div>
              <div class="search-group-bottom--manager">
                <label>{{ $t('penpal.column.manager') }}</label>
                <div class="be-dropdown status flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('manager')">
                  <span class="current-status flex y-center">
                    {{ searchOption.manager === 'all'
                        ? $t('penpal.statusList.all')
                        : searchOption.manager === 'none'
                          ? $t('penpal.detail.noneManager')
                          : searchOption.manager
                    }}
                  </span>
                  <span class="be-icon size-20 icon-grey-md icon-dropdown">
                    <i class="font-icon-right-arrow"></i>
                  </span>
                  <Transition name="slide">
                    <template v-if="dropdownStatus.isManagerList">
                      <ul class="list" :class="{'is-show': dropdownStatus.isManagerList}">
                        <template v-for="(type, i) in props.managerList.userId" :key="type">
                          <li @click.stop="selectDropDown(type, 'manager')">
                            <span class="manager">
                            {{ type === 'all'
                                ? $t('penpal.statusList.all')
                                : type === 'none'
                                    ? $t('penpal.detail.noneManager')
                                    : type
                              }}
                              <span>{{ props.managerList.emailAddress[i] }}</span>
                            </span>
                          </li>
                        </template>
                      </ul>
                    </template>
                  </Transition>
                </div>
              </div>
              <UiButton :type="'icon primary sm'" @click="onSearch" style="margin-top: 19px;">
                <i class="font-icon-search"/>
                <span class="btn-text">
                  {{ $t('common.search') }}
                </span>
              </UiButton>
            </div>
          </div>
          <div class="transparent"></div>
        </template>
        <div class="search-hide" @click="isSearchHide = !isSearchHide">
          <i class="font-icon-left-arrow" />
        </div>
      </div>
    </div>
    <div class="be-list-wrapper">
      <div class="pagination-wrapper reference">
        <div class="pagination">
          <div class="search-group flex flex-column x-center">
            <div class="be-dropdown status flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('page')">
              <span class="current-page-option flex y-center">
                {{ $t('common.pageCount', { count: props.page.selectedOption }) }}
              </span>
              <span class="be-icon size-20 icon-grey-md icon-dropdown">
                <i class="font-icon-right-arrow"></i>
              </span>
              <Transition name="slide">
                <ul class="list" :class="{'is-show': dropdownStatus.isPageOption}" v-if="dropdownStatus.isPageOption">
                  <template v-for="type in PAGE_OPTIONS" :key="type">
                    <li @click.stop="selectDropDown(type, 'page')">
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
              :limit="props.page.limit"
              :currentPage="props.page.currentPage"
              @changePage="onChangePage" />
        </div>
      </div>
      <table class="be-table">
        <colgroup>
          <col style="width: 20%">
          <col style="width: 20%">
          <col style="width: 40%">
          <col style="width: 10%">
          <col style="width: 10%">
        </colgroup>
        <thead>
        <tr class="thead-row">
          <template v-for="column in PENPAL_LIST_COLUMNS" :key="column.key">
            <th>
              <span>
                {{ $t(`penpal.column.${column.title}`) }}
              </span>
            </th>
          </template>
        </tr>
        </thead>

        <tbody :class="{noData: !props.inboxData || props.inboxData.length === 0}">
          <template v-if="props.inboxData && props.inboxData.length > 0">
            <template v-for="row in props.inboxData" :key="row.id">
              <tr class="inbox-list">
                <template v-for="header in PENPAL_LIST_COLUMNS" :key="header.key">
                  <td :class="{subject: header.key.includes('subject'), fromMail: header.key.includes('fromMail'), receivedAt: header.key.includes('receivedAt')}" @click="router.push({ name: 'PenpalDetail', params: { id: row.id } })">
                    <template v-if="header.key === 'receivedAt'">
                      <span>
                        {{ dateFormatter(row[header.key], 'time') }}
                      </span>
                    </template>
                    <template v-else-if="header.key === 'status'">
                      <span :class="`status-${row[header.key] === 'received' ? 'parsed' : row[header.key]}`">
                        {{ $t(`penpal.statusList.${row[header.key] === 'received' ? 'parsed' : row[header.key]}`) || '-' }}
                      </span>
                    </template>

                    <template v-else-if="header.key === 'fromMail'">
                      <span>
                        {{ row.fromName || '-' }} <br>
                        {{ `<${row.fromMail || '-'}>` }}
                      </span>
                    </template>
                    <template v-else-if="header.key === 'manager'">
                      <span>
                        {{ row[header.key] === 'none' || !row[header.key] ? $t('penpal.detail.noneManager') : row[header.key] }}
                      </span>
                    </template>
                    <template v-else>
                      <span>
                        {{ row[header.key] || '-' }}
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
.penpal-wrapper {
  gap: 30px;
  padding: 20px 40px;

  .search-wrapper {
    position: relative;
    .search {
      .search-group {
        &-top {
          gap: 12px;

          .search-group-top {
            &--date {
              width: 236px;
              transition: all .3s;
            }

            &--from {
              width: 236px;
              transition: all .3s;
            }
          }

          &--transparent {
            min-width: 350px;
            max-width: 350px;
            height: 48px;
            width: 100%;
          }
        }

        &-bottom {
          &--subject{
            width: 236px;
            transition: all .3s;
          }

          &--status {
            width: 236px;
            transition: all .3s;
            margin-right: 0;
            label {
              font-size: 13px;
              color: #454545;
              font-weight: 600;
              line-height: 120%;
              margin-left: 4px;
            }
          }

          &--manager {
            width: 236px;
            transition: all .3s;
            .be-dropdown {
              .list {
                .manager {
                  display: flex;
                  flex-direction: column;
                  color: #2F2F2F;
                  font-size: 13px;
                  font-weight: 600;
                  line-height: 150%;

                  > span {
                    color: #888;
                    font-size: 12px;
                    font-weight: 400;
                    line-height: 150%;
                  }
                }
              }
            }
            label {
              font-size: 13px;
              color: #454545;
              font-weight: 600;
              line-height: 120%;
              margin-left: 4px;
            }
          }
        }
      }

      .transparent {
        width: 225px;
        height: 149px;
      }

      .icon-wrap {
      }
    }
  }

  .drive-status {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;

    .restart-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 14px;
      height: 14px;
      cursor: pointer;

      .font-icon-refresh {
        transform: scaleY(-1) rotate(270deg);
      }
    }
  }
}

@media all and (max-width: 1400px) {
  .penpal-wrapper {
    .search-wrapper {
      position: relative;
      .search {
        .search-group {
          &-top {
            .search-group-top {
              &--date {
                width: 210px;
              }

              &--from {
                width: 210px;
              }
            }

            &--transparent {
              width: 350px;
              height: 48px;
            }
          }

          &-bottom {
            &--subject{
              width: 210px;
            }

            &--status {
              width: 210px;
            }

            &--manager {
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
  .penpal-wrapper {
    .search-wrapper {
      .search {
        .icon-wrap {
        }
      }
    }
  }
}

</style>
