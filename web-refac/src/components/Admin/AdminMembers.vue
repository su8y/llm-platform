<script setup>
import { ref, reactive, inject, computed, onMounted, onBeforeUnmount } from 'vue'

import { MEMBERS_COLUMNS, MEMBERS_STATUS, PAGE_OPTIONS, SEARCH_AUTHORITY, SEND_MAIL_TYPE } from "@/libs/constants.js";
import { dateFormatter } from "@/libs/utils.js";

import DatePicker from "@/components/DatePicker/index.vue";
import MemberStatus from "@/components/Modal/MemberStatus.vue";
import SendMail from "@/components/Modal/SendMail.vue";
import {useI18n} from "vue-i18n";

const modal = inject('$modal')
const emits = defineEmits(['change', 'searchChange', 'dateChange', 'openList', 'search'])
const props = defineProps({
  membersData: Array,
  page: Object,
  searchFilter: Object,
  dateRange: Object,
  authNameList: Array
})

const { locale } = useI18n()
const searchOption = ref(props.searchFilter)
const inviteEmail = ref('')
const isDatePicker = ref(false)
const currentMemberId = ref(null)
const selectMemberAuthority = ref(null)
const dropdownStatus = reactive({
  isStatus: false,
  isAuthority: false,
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

const dateRangeStr = computed(() => {
  return `----.--.-- ~ ----.--.--`
})

const onSearch = () => {
  emits('search')
}

const selectDateRange = (date) => {
  emits('dateChange', date.start, date.end)
  isDatePicker.value = false
}

const toggleDropDown = (type) => {
  switch (type) {
    case 'status':
      dropdownStatus.isStatus = !dropdownStatus.isStatus
      dropdownStatus.isAuthority = false
      dropdownStatus.isPageOption = false
      break
    case 'authority':
      dropdownStatus.isAuthority = !dropdownStatus.isAuthority
      dropdownStatus.isStatus = false
      dropdownStatus.isPageOption = false

      break
    case 'pageOption':
      dropdownStatus.isPageOption = !dropdownStatus.isPageOption
      dropdownStatus.isStatus = false
      dropdownStatus.isAuthority = false
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
  const typesMap = new Map()
      .set('status', (value) => emits('searchChange', 'status', value))
      .set('authority', (value) => emits('searchChange', 'authority', value))
      .set('pageOption', (value) => emits('change', 'pageOption', value))

  const types = typesMap.get(type)

  types(item)
  toggleDropDown(type)
}

const onChangePage = (page) => {
  emits('change', 'current', page)
}

const dateReset = () => {
  emits('dateChange', null, null)
}

const togglePageOptions = () => {
  dropdownStatus.isPageOption = !dropdownStatus.isPageOption
  dropdownStatus.isStatus = false
  dropdownStatus.isAuthority = false
}

const closeDropdown = (e) => {
  dropdownStatus.isPageOption = false
  currentMemberId.value = null
  dropdownStatus.isStatus = false
  dropdownStatus.isAuthority = false

  if (e.target.className === 'be-input' || e.target.tagName === 'TEXTAREA') {
    isDatePicker.value = false
  }
}

const openInfo = (type) => {
  modal.open(MemberStatus, type)
}

const sendInviteMail = async () => {
  emits('change', 'email', {emailAddress: inviteEmail.value , lang : locale.value})
}

const openMemberAuthority = (id) => {
  currentMemberId.value = id
  emits('openList')
}

const selectMemAuthority = async (item, userId) => {
  selectMemberAuthority.value = item
  currentMemberId.value = null
  emits('change', 'authority', {userId: userId, authName: item.toLowerCase()})
}

const manageAccountActions = async (status, email, id) => {
  if (status === 'complete') {
    emits('change', 'delete', {userId: id})
  } else {
    modal.open(SendMail, SEND_MAIL_TYPE.SEND_INVITE)
    emits('change', 'resend', {emailAddress: email, lang : locale.value})
  }
}
</script>

<template>
  <div class="members-wrapper flex flex-column">
    <div class="search-wrapper members">
      <div class="invite-wrapper">
        <h3 class="title be-font text-grey-md bold size-18 flex y-center">
          {{ $t('members.invite.index') }}
        </h3>
        <div class="invite-container">
          <div class="invite">
            <span class="invite-label">{{ $t('register.email') }}</span>
            <textarea v-model="inviteEmail"/>
          </div>
          <div class="invite-desc">
            <span>{{ $t('members.invite.desc1') }}</span>
            <span>{{ $t('members.invite.desc2') }}</span>
            <span>{{ $t('members.invite.desc3') }}</span>
          </div>
          <UiButton :type="'icon primary sm'" @click="sendInviteMail()" class="invite-btn">
            <span class="btn-text">
              {{ $t('common.invite') }}
            </span>
          </UiButton>
        </div>
      </div>
      <div class="members-search-line"></div>
      <div class="search-members">
        <h3 class="title be-font text-grey-md bold size-18 flex y-center">
          {{ $t('common.searchFilter') }}
        </h3>
        <div class="search">
          <div class="search-group">
            <div class="search-group-top">
              <div class="search-group-top--title">
                <UiInput
                    :type="'text'"
                    v-model="searchOption.userId"
                    @enter="onSearch">
                  <template #label>
                    {{ $t('members.search.id') }}
                  </template>
                </UiInput>
              </div>
              <div class="search-group-top--title">
                <UiInput
                    :type="'text'"
                    v-model="searchOption.department"
                    @enter="onSearch">
                  <template #label>
                    {{ $t('members.search.department') }}
                  </template>
                </UiInput>
              </div>
              <div class="search-group-top--disclosure">
                <label>{{ $t('members.search.status') }}</label>
                <div class="be-dropdown flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('status')">
                  <span class="current-type">
                    {{ $t(`members.status.${MEMBERS_STATUS[props.searchFilter.status]}`) }}
                  </span>
                  <span class="be-icon size-20 icon-grey-md icon-dropdown">
                    <i class="font-icon-right-arrow"></i>
                  </span>
                  <Transition name="slide">
                    <temaplte v-if="dropdownStatus.isStatus">
                      <ul class="list" :class="{'is-show': dropdownStatus.isStatus}">
                        <template v-for="(type, key) in MEMBERS_STATUS" :key="type">
                          <li @click.stop="selectDropDown(key, 'status')">
                            {{ $t(`members.status.${type}`) }}
                          </li>
                        </template>
                      </ul>
                    </temaplte>
                  </Transition>
                </div>
              </div>
            </div>
            <div class="search-group-bottom">
              <div class="search-group-bottom--date">
                <UiInput
                    :input-style="'date'"
                    :type="'text'"
                    :value="dateRangeStr"
                    :date-range="props.dateRange"
                    @date-reset="dateReset"
                    @click.stop="toggleDatePicker()">
                  <template #label>
                    {{ $t('members.search.date') }}
                  </template>
                </UiInput>
                <template v-if="isDatePicker">
                  <DatePicker :date-range="props.dateRange" @select-date-range="selectDateRange($event)"/>
                </template>
              </div>
              <div class="search-group-bottom--author">
                <UiInput
                    :type="'text'"
                    v-model="searchOption.emailAddress"
                    @enter="onSearch">
                  <template #label>
                    {{ $t('register.email') }}
                  </template>
                </UiInput>
              </div>
              <div class="search-group-bottom--reference">
                <label>{{ $t('members.search.authority') }}</label>
                <div class="be-dropdown flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('authority')">
                  <span class="current-type">
                    {{ props.searchFilter.authority === 'all' ? $t(`common.${SEARCH_AUTHORITY[props.searchFilter.authority]}`) : SEARCH_AUTHORITY[props.searchFilter.authority] }}
                  </span>
                  <span class="be-icon size-20 icon-grey-md icon-dropdown">
                    <i class="font-icon-right-arrow"></i>
                  </span>
                  <Transition name="slide">
                    <template v-if="dropdownStatus.isAuthority">
                      <ul class="list" :class="{'is-show': dropdownStatus.isAuthority}">
                        <template v-for="(type, key) in SEARCH_AUTHORITY" :key="type">
                          <li @click.stop="selectDropDown(key, 'authority')">
                            <span>
                              {{ type === 'all' ? $t(`common.statusList.${type}`) : type }}
                            </span>
                          </li>
                        </template>
                      </ul>
                    </template>
                  </Transition>
                </div>
              </div>
            </div>
            <UiButton :type="'icon primary sm'" @click="onSearch" class="members-search-btn">
              <i class="font-icon-search"/>
              <span class="btn-text">
                {{ $t('common.search') }}
              </span>
            </UiButton>
          </div>
        </div>
      </div>
    </div>
    <div class="be-list-wrapper">
      <div class="pagination-wrapper reference">
        <div class="pagination">
          <div class="search-group flex flex-column x-center">
            <div class="be-dropdown status flex y-center" ref="dropdown" @click.stop.prevent="togglePageOptions()">
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
                      <li @click.stop="selectDropDown(type, 'pageOption')">
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
              @changePage="onChangePage"/>
        </div>
      </div>
      <table class="be-table">
        <colgroup>
          <col style="width: 96px">
          <col style="width: 102px">
          <col style="width: 96px">
          <col style="width: 162px">
          <col style="width: 200px">
          <col style="width: 76px">
          <col style="width: 77px">
        </colgroup>
        <thead>
          <tr class="thead-row">
            <template v-for="column in MEMBERS_COLUMNS" :key="column.key">
              <th>
                <template v-if="column.key === 'status' || column.key === 'authName'">
                  <div class="title-info">
                    {{ $t(`members.column.${column.title}`) }}
                    <i class="icon icon--info" @click="openInfo(column.key)"/>
                  </div>
                </template>
                <template v-else>
                  <span>
                    {{ $t(`members.column.${column.title}`) }}
                  </span>
                </template>
              </th>
            </template>
          </tr>
        </thead>

        <tbody :class="{noData: !props.membersData || props.membersData.length === 0}">
          <template v-if="props.membersData && props.membersData.length > 0">
            <template v-for="(row, rowIndex) in props.membersData" :key="row.date" >
              <tr class="members-table">
                <template v-for="header in MEMBERS_COLUMNS" :key="header.key">
                  <td :class="header">
                    <template v-if="header.key === 'status'">
                      <span>
                        {{ $t(`members.status.${MEMBERS_STATUS[row[header.key]]}`) }}
                      </span>
                    </template>
                    <template v-else-if="header.key === 'authName'">
                      <div>
                        <div class="be-dropdown members-status flex y-center" ref="dropdown"
                             @click.stop.prevent="openMemberAuthority(rowIndex)">
                            <span class="current-page-option flex xy-center">
                              {{ row[header.key] || '-' }}
                            </span>
                            <span class="be-icon size-20 icon-grey-md icon-dropdown">
                              <i class="font-icon-right-arrow"></i>
                            </span>
                          <Transition name="slide">
                            <template v-if="currentMemberId === rowIndex">
                              <ul class="list" :class="{'is-show': currentMemberId === rowIndex}">
                                <template v-for="type in props.authNameList" :key="type">
                                  <li @click.stop="selectMemAuthority(type, row.userId)">
                                    <span class="status">
                                      {{ type }}
                                    </span>
                                  </li>
                                </template>
                              </ul>
                            </template>
                          </Transition>
                        </div>
                      </div>
                    </template>
                    <template v-else-if="header.key === 'date'">
                      <span>
                        {{ dateFormatter(row[header.key], 'time') }}
                      </span>
                    </template>
                    <template v-else-if="header.key === 'etc'">
                      <div>
                        <template v-if="row.status === 'complete' || row.status === 'expired'">
                          <UiButton :type="'outline'" @click="manageAccountActions(row.status, row.emailAddress, row.userId)">
                            {{ row.status === 'complete' ? $t('members.column.withdrawal') : $t('members.column.resend') }}
                          </UiButton>
                        </template>
                        <template v-else>
                          <span>-</span>
                        </template>
                      </div>
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
.members-wrapper {
  gap: 30px;
  padding: 20px 40px;

}

</style>
