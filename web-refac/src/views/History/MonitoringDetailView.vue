<script setup>
import { ref, reactive, onBeforeMount, inject } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from 'vue-i18n'

import { getMonitoringDetail, getMonitoringDetailChat, updateMonitoringData } from "@/api/monitoring.js";
import { HTTP_CODES } from "@/libs/constants.js";

import MonitoringDetail from "@/components/Reports/MonitoringDetail.vue";
import Loading from "@/components/Modal/Loading.vue";

const modal = inject('$modal')
const { t } = useI18n()
const route = useRoute()

const postData = ref({})
const chatData = ref(null)
const page = reactive({
  totalLength: 0,
  limit: 1,
  currentPage: 1,
  isAllPage: false
})

onBeforeMount(async () => {
  await getMonitoringData()
  await getChatData()
})

const getMonitoringData = async () => {
  modal.open(Loading)
  try {
    const params = {
      sessionKey: route.params.id
    }

    const res = await getMonitoringDetail(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      res.data.idList = [t('historyDetail.noManager'), ...res.data.idList]
      postData.value = res.data
    } else {
      modal.close()
      alert(res)
      console.log('Error: ', res.message)
    }
  } catch (e) {
    modal.close()
    console.error('Error: ', e)
  }
}

const getChatData = async () => {
  const params = {
    sessionKey: route.params.id,
    pageMode: !page.isAllPage,
    page: page.currentPage
  }

  try {
    const res = await getMonitoringDetailChat(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      chatData.value = res.data.rows
      page.totalLength = res.data.count
      page.limit = page.isAllPage ? res.data.count : 1
    } else {
      alert(res)
      console.log('Error: ', res.message)
    }
  } catch (e) {
    console.error('Error: ', e)
  }
}

const updateMonitoring = async (params) => {
  modal.open(Loading)

  try {
    const res = await updateMonitoringData(params)
    if (res.code === HTTP_CODES.SUCCESS) {
      modal.open(Loading)
      location.reload()
    } else {
      modal.open(Loading)
      alert(res.message)
    }

  } catch (e) {
    modal.open(Loading)
    console.error(e)
  }
}

/**
 *
 * @param {string} type
 * @param {string|number|Boolean} value
 * @returns {Promise<void>}
 */
const changeOption = async (type, value) => {
  type === 'current'
      ? page.currentPage = value
      : page.isAllPage = value

  page.isAllPage ? page.currentPage = 1 : null

  await getChatData()
}

</script>

<template>
  <MonitoringDetail
      :post-data="postData"
      :chat-data="chatData"
      :page="page"
      @change="changeOption"
      @update="updateMonitoring" />
</template>
