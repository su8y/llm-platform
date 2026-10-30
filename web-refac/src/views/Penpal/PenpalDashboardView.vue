<script setup>
import { ref, reactive } from 'vue'
import { addDays } from "date-fns";

import { getAskRanking } from "@/api/monitoring.js";
import {getDashboardChart, getDashboardLine, getDashboardManager} from "@/api/penpal.js";
import { dateFormatter } from "@/libs/utils.js";
import { HTTP_CODES } from "@/libs/constants.js";

import PenpalDashboard from "@/components/Panpal/PenpalDashboard.vue";

const today = new Date()
const startDate = addDays(today, -6)

const workStatusData = ref(null)
const managerData = ref(null)
const lineChartData = ref(null)
const timezone = ref(Intl.DateTimeFormat().resolvedOptions().timeZone)
const dateRange = reactive({
  start: startDate,
  end: today
})

const getDashboardManagerData = async () => {
  const param = {
    startDate: dateRange.start && dateFormatter(dateRange.start),
    endDate: dateRange.end && dateFormatter(dateRange.end),
    timezone: timezone.value
  }

  try {
    const res = await getDashboardManager(param)

    if (res.code === HTTP_CODES.SUCCESS) {
      managerData.value = res.data
    } else {
      alert(res.message)
      console.log(`Get Dashboard Manager Count Error: ${res}`)
    }
  } catch (e) {
    console.error(`Get Dashboard Manager Count Error: ${e}`)
  }
}

const getDashboardChartData = async () => {
  const param = {
    startDate: dateRange.start && dateFormatter(dateRange.start),
    endDate: dateRange.end && dateFormatter(dateRange.end),
    timezone: timezone.value
  }
  try {
    const res = await getDashboardChart(param)

    if (res.code === HTTP_CODES.SUCCESS) {
      workStatusData.value = res.data
    } else {
      alert(res.message)
      console.log(`Get Dashboard Chart Error: ${res}`)
    }

  } catch (e) {
    console.error(`Get Dashboard Chart Error: ${e}`)
  }
}

const getDashboardLineData = async () => {
  const param = {
    startDate: dateRange.start && dateFormatter(dateRange.start),
    endDate: dateRange.end && dateFormatter(dateRange.end),
    timezone: timezone.value
  }

  try {
    const res = await getDashboardLine(param)

    if (res.code === HTTP_CODES.SUCCESS) {
      lineChartData.value = res.data
    } else {
      alert(res.message)
      console.log(`Get Dashboard Line Data Error: ${res}`)
    }
  } catch (e) {
    console.error(`Get Dashboard Line Data Error: ${e}`)
  }
}

const dateChange = async (start, end) => {
  dateRange.start = start
  dateRange.end = end
  await getDashboardManagerData()
  await getDashboardChartData()
  await getDashboardLineData()
}


getDashboardManagerData()
getDashboardChartData()
getDashboardLineData()
</script>

<template>
  <PenpalDashboard
      :work-status-data="workStatusData"
      :line-chart-data="lineChartData"
      :manager-data="managerData"
      :date-range="dateRange"
      @change="dateChange"/>
</template>
