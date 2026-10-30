<script setup>
import { ref, reactive, inject, onBeforeMount } from "vue";
import { useI18n } from 'vue-i18n'
import { useStore } from 'vuex'

import { deleteReferenceData, getCategories, getReferenceList } from "@/api/reference.js";
import { dateFormatter } from "@/libs/utils.js";
import { HTTP_CODES, WARNING_TYPE } from "@/libs/constants.js";

import Reference from "@/components/Reports/Reference.vue"
import Loading from "@/components/Modal/Loading.vue";
import Warning from "@/components/Modal/Warning.vue";

const modal = inject('$modal')
const { t }  = useI18n()
const store = useStore()

const referenceData = ref([])
const dataIdArrays = ref([])
const page = reactive({
  totalLength: 0,
  limit: 10,
  currentPage: store.state.currentPage ? parseInt(store.state.currentPage) : 1,
  selectedOption: store.state.limitPage ? parseInt(store.state.limitPage) : 10
})
const selectCategories = reactive({
  select1depthCategory: store.state.referenceSearchData.category ? store.state.referenceSearchData.category.select1depthCategory : {},
  select2depthCategory: store.state.referenceSearchData.category ? store.state.referenceSearchData.category.select2depthCategory : {},
  select3depthCategory: store.state.referenceSearchData.category ? store.state.referenceSearchData.category.select3depthCategory : {},
})
const categoryData = reactive({
  categoryDepth1List: null,
  categoryDepth2List: null,
  categoryDepth3List: null
})
const searchFilter = reactive({
  title: store.state.referenceSearchData.title ? store.state.referenceSearchData.title : '',
  author: store.state.referenceSearchData.author ? store.state.referenceSearchData.author : '',
  isOn: store.state.referenceSearchData.isOn ? store.state.referenceSearchData.isOn : null
})
const dateRange = reactive({
  start: store.state.referenceSearchData.startDate ? store.state.referenceSearchData.startDate : null,
  end: store.state.referenceSearchData.endDate ? store.state.referenceSearchData.endDate : null,
})

onBeforeMount(async () => {
  await getList()
  await getCategoryList()
})

const getList = async () => {
  modal.open(Loading)
  const params = {
    page: page.currentPage,
    per_page: page.selectedOption,
    title: searchFilter.title,
    is_on: searchFilter.isOn,
    author: searchFilter.author,
    start_date: dateRange.start && dateFormatter(dateRange.start),
    end_date: dateRange.end && dateFormatter(dateRange.end)
  }

  const categories = Object.values(selectCategories)

  let categoryFilter
  for (let i = categories.length - 1; i >= 0; i--) {
    if (categories[i] !== null) {
      categoryFilter = categories[i]
      break
    }
  }

  params.category_id = categoryFilter.id || null

  try {
    const res = await getReferenceList(params)
    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      referenceData.value = res.data.post
      page.totalLength = res.data.count || referenceData.value.length
      page.limit = page.selectedOption

      if (!res.data.count) page.currentPage = 1

      const data = referenceData.value.slice(0, page.limit)

      for (let i=0; i < data.length; i++) {
        dataIdArrays.value.push(data[i].id)
      }
    } else {
      modal.close()
      referenceData.value = null
      page.totalLength = 0
      alert(res.message)
      console.error('Error: ', res)
    }
  } catch (e) {
    modal.close()
    alert(e)
    console.error('Error: ', e)
  }
}

const getCategoryList = async () => {
  try {
    const res = await getCategories()

    if (res.code === HTTP_CODES.SUCCESS) {
      const noneCategory = {
        id: null,
        name: t('referenceCategory.depth.depth1'),
        children: [
          {
            id: null,
            name: t('referenceCategory.depth.depth2'),
            children: [
              {
                id: null,
                name: t('referenceCategory.depth.depth3')
              }
            ]
          }
        ]
      }
      categoryData.categoryDepth1List = [noneCategory, ...res.data]

    } else {
      alert(res.message)
      console.log('Error: ', res)
    }
  } catch (e) {
    console.error('Error: ', e)
  }
}

const selectDelete = async (params) => {
  try {
    await modal.open(Warning, WARNING_TYPE.REFERENCE_DELETE).then(async () => {
      modal.open(Loading)

      const res = await deleteReferenceData(params)

      if (res.code === HTTP_CODES.SUCCESS) {
        modal.close()
        await getList()
      } else {
        modal.close()
        alert(res.message)
        console.log('Error: ', res)
      }

    }).catch(() => {
      modal.close()
    })
  } catch (e) {
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
  if (type === 'current') {
    page.currentPage = value
  } else {
    page.selectedOption = value
    page.currentPage = 1
  }

  await getList()
}

/**
 *
 * @param {string} type
 * @param {string|boolean|null} value
 */
const searchOption = (type, value) => {
  switch (type) {
    case 'reference':
      searchFilter.isOn = value
      break
    case '1depth':
      selectCategories.select1depthCategory = value
      selectCategories.select2depthCategory = null
      selectCategories.select3depthCategory = null
      categoryData.categoryDepth2List = value.children || null
      break
    case '2depth':
      selectCategories.select2depthCategory = value
      selectCategories.select3depthCategory = null
      categoryData.categoryDepth3List = value.children || null
      break
    case '3depth':
      selectCategories.select3depthCategory = value
      break
    case 'id':
      searchFilter.userId = value
      break
  }
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

  store.commit('setReferenceSearchData', {
    isOn: searchFilter.isOn,
    author: searchFilter.author,
    title: searchFilter.title,
    startDate: dateRange.start,
    endDate: dateRange.end,
    category: selectCategories
  })

  await getList()
}
</script>

<template>
  <Reference
      :reference-data="referenceData"
      :category-data="categoryData"
      :data-ids="dataIdArrays"
      :page="page"
      :search-filter="searchFilter"
      :select-categories="selectCategories"
      :date-range="dateRange"
      @change="changeOption"
      @searchChange="searchOption"
      @search="onSearch"
      @dateChange="dateOption"
      @delete="selectDelete"
  />
</template>
