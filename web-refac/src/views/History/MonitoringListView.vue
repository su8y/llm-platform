<script setup>
import { ref, reactive, inject, onBeforeMount } from 'vue'
import { useStore } from 'vuex'
import { useI18n } from 'vue-i18n'

import { dateFormatter } from "@/libs/utils.js";
import { getMonitoringList } from "@/api/monitoring.js";
import { HTTP_CODES, USE_MCP_ID_LIST } from "@/libs/constants.js";

import MonitoringList from "@/components/Reports/MonitoringList.vue";
import Loading from "@/components/Modal/Loading.vue";

const modal = inject('$modal')
const store = useStore()
const { t } = useI18n()

const monitoringData = ref([])
const userData = ref(null)
const isMCP = ref(null)
const isAdmin = ref(false)
const page = reactive({
  totalLength: 0,
  limit: 10,
  currentPage: store.state.currentPage ? parseInt(store.state.currentPage) : 1,
  selectedOption: store.state.limitPage ? parseInt(store.state.limitPage) : 10
})
const dateRange = reactive({
  start: store.state.monitoringSearchData.startDate ? store.state.monitoringSearchData.startDate : null,
  end: store.state.monitoringSearchData.endDate ? store.state.monitoringSearchData.endDate : null,
})
const searchFilter = reactive({
  id: store.state.monitoringSearchData.id ? store.state.monitoringSearchData.id : null,
  manager: store.state.monitoringSearchData.manager ? store.state.monitoringSearchData.manager : null,
  statusType: store.state.monitoringSearchData.statusType ? store.state.monitoringSearchData.statusType : 'all'
})

onBeforeMount(async () => {
  try {
    userData.value = await store.dispatch('storeUserData');
    isAdmin.value = USE_MCP_ID_LIST.includes(userData.value.userId)
  } catch (error) {
    console.error(`${t('common.error.user')}: ${error}`);
    alert(t('common.error.error'));
  }

  await getMonitoringListData()
})

const getMonitoringListData = async () => {
  modal.open(Loading)
  const params = {
    page: page.currentPage,
    per_page: page.selectedOption,
    asker_id: searchFilter.id,
    manager_id: searchFilter.manager,
    issue_status: searchFilter.statusType === 'all' ? '' : searchFilter.statusType,
    start_date: dateRange.start && dateFormatter(dateRange.start),
    end_date: dateRange.end && dateFormatter(dateRange.end)
  }

  if (isAdmin.value && isMCP.value !== null) {
    params.isMCP = isMCP.value
  }

  try {
    const res = await getMonitoringList(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      monitoringData.value = res.data.rows
      page.totalLength = res.data.count
      page.limit = page.selectedOption
      modal.close()
    } else {
      modal.close()
      monitoringData.value = null
      page.totalLength = 0
      alert(res.message)
      console.log('Error: ', res)
    }
  } catch (e) {
    modal.close()
    alert(e)
    console.error('Error: ', e)
  }
}

/**
 *
 * @param {string} type
 * @param {string|number|Object} value
 * @returns {Promise<void>}
 */
const changeOption = async (type, value) => {
  switch (type) {
    case 'current':
      page.currentPage = value
      break
    case 'pageOption':
      page.selectedOption = value
      page.currentPage = 1
      break
    case 'mcp':
      isMCP.value = value
      break
  }

  await getMonitoringListData()
}

const dateOption = (start, end) => {
  dateRange.start = start
  dateRange.end = end
}

const onSearch = async () => {
  store.commit('setPagination', {
    newPage: 1,
    newLimit: page.selectedOption
  })
  page.currentPage = 1
  store.commit('setMonitoringSearchData', {
    id: searchFilter.id,
    status: searchFilter.statusType,
    manager: searchFilter.manager,
    startDate: dateRange.start,
    endDate: dateRange.end
  })

  await getMonitoringListData()
}
</script>

<template>
  <MonitoringList
      :monitoring-data="monitoringData"
      :page="page"
      :date-range="dateRange"
      :search-filter="searchFilter"
      :is-admin="isAdmin"
      @change="changeOption"
      @dateChange="dateOption"
      @search="onSearch"
  />
</template>
