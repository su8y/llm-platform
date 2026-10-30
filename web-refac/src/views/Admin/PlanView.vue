<script setup>
import { onBeforeMount, reactive, ref } from 'vue'
import { useStore } from "vuex";

import { getPlanList } from "@/api/plan.js";
import { HTTP_CODES } from "@/libs/constants.js";

import AdminPlan from "@/components/Admin/AdminPlan.vue";

const store = useStore()

const historyData = ref(null)
const planData = ref({})
const selectPlanOption = ref(null)
const page = reactive({
  isPageOption: false,
  totalLength: 0,
  limit: 10,
  currentPage: store.state.currentPage ? parseInt(store.state.currentPage) : 1,
  selectedOption: store.state.limitPage ? parseInt(store.state.limitPage) : 10
})

onBeforeMount(async () => {
  await getPlanHistory()
  await getCurrentPlanData()
})

const getPlanHistory = async () => {
  const params = {
    page: page.currentPage,
    perPage: page.selectedOption
  }

  try {
    const res = await getPlanList(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      historyData.value = res.data.post
      page.totalLength = res.data.count
    } else {
      alert(res.message)
      console.log('Error: ', res)
    }

  } catch (e) {
    alert(e)
    console.error('Error: ', e)
  }
}

const getCurrentPlanData = async () => {
  planData.value = await store.dispatch('storePlanData')
}

/**
 * @param {string} type
 * @param {string|number} value
 * @returns {Promise<void>}
 */
const changeOption = async (type, value) => {
  switch (type) {
    case 'current':
      page.currentPage = value
      break
    case 'pageOption':
      page.selectedOption = value
      break
    case 'plan':
      selectPlanOption.value = value
  }

  await getPlanHistory()
}

</script>

<template>
  <AdminPlan
      :history-data="historyData"
      :plan-data="planData"
      :page="page"
      @change="changeOption"
  />
</template>
