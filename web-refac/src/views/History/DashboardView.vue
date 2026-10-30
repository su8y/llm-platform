<script setup>
import {ref, reactive, computed} from 'vue'
import { addDays } from "date-fns";

import { getAskRanking, getRating, getResponseCount } from "@/api/monitoring.js";
import { dateFormatter } from "@/libs/utils.js";

import Dashboard from "@/components/Reports/Dashboard.vue";
import {useStore} from "vuex";
import {useRouter} from "vue-router";

const router = useRouter()
const today = new Date()
const startDate = addDays(today, -6)
const store = useStore()
const isMobile = computed(() => store.state.isMobile)

if (isMobile.value) {
  router.replace({ name: 'Playground' })
}

const ratingGraphData = ref(null)
const responseCountData = ref(null)
const askRanking = ref(null)
const timezone = ref(Intl.DateTimeFormat().resolvedOptions().timeZone)
const dateRange = reactive({
  start: startDate,
  end: today
})

const getRatingData = async () => {
  const param = {
    start_date: dateRange.start && dateFormatter(dateRange.start),
    end_date: dateRange.end && dateFormatter(dateRange.end),
    timezone: timezone.value
  }
  try {
    await getRating(param).then(res => {
      ratingGraphData.value = res
    })
  } catch (e) {
    console.error(e)
  }
}

const dateChange = async (start, end) => {
  dateRange.start = start
  dateRange.end = end
  await getRatingData()
  await getResponseCountData()
  await getAskRankingData()
}

const getResponseCountData = async () => {
  const param = {
    start_date: dateRange.start && dateFormatter(dateRange.start),
    end_date: dateRange.end && dateFormatter(dateRange.end),
    timezone: timezone.value
  }
  try {
    await getResponseCount(param).then(res => {
      responseCountData.value = res
    })
  } catch (e) {
    console.error(e)
  }
}

const getAskRankingData = async () => {
  const param = {
    start_date: dateRange.start && dateFormatter(dateRange.start),
    end_date: dateRange.end && dateFormatter(dateRange.end),
    timezone: timezone.value
  }

  try {
    await getAskRanking(param).then(res => {
      askRanking.value = res
    })
  } catch (e) {
    console.error(e)
  }
}

getRatingData()
getResponseCountData()
getAskRankingData()
</script>

<template>
  <Dashboard
      :rating-graph-data="ratingGraphData"
      :response-count-data="responseCountData"
      :ask-ranking="askRanking"
      :date-range="dateRange"
      @change="dateChange"/>
</template>
