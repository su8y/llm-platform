<script setup>
import { ref, reactive, onBeforeMount, inject } from 'vue';
import { useStore } from 'vuex'

import { getInboxList, getManagers } from '@/api/penpal.js'
import { HTTP_CODES } from "@/libs/constants.js";
import { dateFormatter } from "@/libs/utils.js";

import PenpalList from "@/components/Panpal/PenpalList.vue";
import Loading from "@/components/Modal/Loading.vue";

const modal = inject('$modal')
const store = useStore()

const inboxData = ref([])
const managerList = ref([])
const directoriesData = reactive({
  currentId: null,
  directories: []
})
const dateRange = reactive({
  start: store.state.inboxSearchData.startDate ? store.state.inboxSearchData.startDate : null,
  end: store.state.inboxSearchData.endDate ? store.state.inboxSearchData.endDate : null
})
const searchFilter = reactive({
  from: store.state.inboxSearchData.from ? store.state.inboxSearchData.from : '',
  subject: store.state.inboxSearchData.subject ? store.state.inboxSearchData.subject : '',
  status: store.state.inboxSearchData.status ? store.state.inboxSearchData.status : 'all',
  manager: store.state.inboxSearchData.manager ? store.state.inboxSearchData.manager : 'all'
})
const page = reactive({
  totalLength: 0,
  limit: 10,
  currentPage: store.state.currentPage ? parseInt(store.state.currentPage) : 1,
  selectedOption: store.state.limitPage ? parseInt(store.state.limitPage) : 10
})

onBeforeMount(async() => {
  await load()
  await getManagerList()
})

const load = async () => {
  modal.open(Loading)
  try {
    const params = {
      page: page.currentPage,
      perPage: page.selectedOption,
      startDate: dateRange.start && dateFormatter(dateRange.start),
      endDate: dateRange.end && dateFormatter(dateRange.end),
      manager: searchFilter.manager === 'all' ? '' : searchFilter.manager,
      status: searchFilter.status === 'all' ? '' : searchFilter.status,
      from: searchFilter.from,
      subject: searchFilter.subject
    }

    const res = await getInboxList(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      inboxData.value = res.data.rows
      page.totalLength = res.data.count
      page.limit = page.selectedOption
    } else {
      modal.close()
      alert(res.message)
      console.log(`Error: ${res}`)
    }

  } catch (e) {
    modal.close()
    console.error(`Error: ${e}`)
  }
}

const getManagerList = async () => {
  try {
    const res = await getManagers()

    if (res.code === HTTP_CODES.SUCCESS) {
      res.data.userId = ['all', 'none', ...res.data.userId]
      res.data.emailAddress = ['', '', ...res.data.emailAddress]
      managerList.value = res.data
    } else {
      alert(res.message)
      console.log(`Error: ${res}`)
    }

  } catch (e) {
    console.error(`Error: ${e}`)
  }
}

/**
 *
 * @param {string} type
 * @param {string|number} value
 * @returns {Promise<void>}
 */
const changeOption = async (type, value) => {
  if (type === 'current') {
    page.currentPage = value
  } else {
    page.selectedOption = value
    page.currentPage = 1
  }

  await load()
}

const dateOption = (start, end) => {
  dateRange.start = start
  dateRange.end = end
}

const searchOption = async (type, value) => {
  switch (type) {
    case 'status':
      searchFilter.status = value
      break
    case 'manager':
      searchFilter.manager = value
      break
    case 'from':
      searchFilter.from = value
      break
    case 'subject':
      searchFilter.subject = value
      break
  }
}

const onSearch = async () => {
  store.commit('setPagination', {
    newPage: 1,
    newLimit: page.selectedOption
  })
  page.currentPage = 1
  store.commit('setInboxSearchData', {
    from: searchFilter.from,
    subject: searchFilter.subject,
    status: searchFilter.status,
    manager: searchFilter.manager,
    startDate: dateRange.start,
    endDate: dateRange.end,
  })

  await load()
}
</script>

<template>
  <PenpalList
      :inbox-data="inboxData"
      :directories-data="directoriesData"
      :search-filter="searchFilter"
      :date-range="dateRange"
      :page="page"
      :manager-list="managerList"
      @change="changeOption"
      @dateChange="dateOption"
      @searchChange="searchOption"
      @search="onSearch"
      @refresh="load"
  />
</template>
