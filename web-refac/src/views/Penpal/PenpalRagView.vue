<script setup>
import { ref, reactive, onBeforeMount, inject } from 'vue';
import { useStore } from 'vuex'

import { getEmailRag, getManagers } from '@/api/penpal.js'
import { HTTP_CODES } from "@/libs/constants.js";
import { dateFormatter } from "@/libs/utils.js";

import PenpalRag from "@/components/Panpal/PenpalRag.vue";
import Loading from "@/components/Modal/Loading.vue";

const modal = inject('$modal')
const store = useStore()

const ragData = ref([])
const managerList = ref(null)
const toMailList = ref(null)
const dateRange = reactive({
  start: store.state.ragSearchData.startDate ? store.state.ragSearchData.startDate : null,
  end: store.state.ragSearchData.endDate ? store.state.ragSearchData.endDate : null,
})
const searchFilter = reactive({
  to: store.state.ragSearchData.to ? store.state.ragSearchData.to : '',
  manager: store.state.ragSearchData.manager ? store.state.ragSearchData.manager : 'all',
  subject: store.state.ragSearchData.subject ? store.state.ragSearchData.subject : '',
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
      to: searchFilter.to,
      subject: searchFilter.subject,
      manager: searchFilter.manager === 'all' ? '' : searchFilter.manager,
      startDate: dateRange.start && dateFormatter(dateRange.start),
      endDate: dateRange.end && dateFormatter(dateRange.end),
    }
    const res = await getEmailRag(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      ragData.value = res.data.email
      toMailList.value = {
        toMail: res.data.email.map(item => item.toMail),
        toName: res.data.email.map(item => item.toName)
      }
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

const onSearch = async () => {
  store.commit('setPagination', {
    newPage: 1,
    newLimit: page.selectedOption
  })
  page.currentPage = 1
  store.commit('setRagSearchData', {
    to: searchFilter.to,
    subject: searchFilter.subject,
    manager: searchFilter.manager,
    startDate: dateRange.start,
    endDate: dateRange.end,
  })

  await load()
}
</script>

<template>
  <PenpalRag
      :rag-data="ragData"
      :manager-list="managerList"
      :to-mail-list="toMailList"
      :search-filter="searchFilter"
      :date-range="dateRange"
      :page="page"
      @change="changeOption"
      @dateChange="dateOption"
      @search="onSearch"
      @refresh="load"
  />
</template>
