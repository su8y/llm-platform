<script setup>
import { ref, computed, onMounted, onBeforeUnmount, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Cookies from 'js-cookie'

import { dateFormatter } from "@/libs/utils.js";
import { REFERENCE_COLUMNS, STATUS, REFERENCE_TYPE, PAGE_OPTIONS } from "@/libs/constants.js";

import DatePicker from "@/components/DatePicker/index.vue";

const cookie = Cookies.get('app-auth')
const router = useRouter()
const { t } = useI18n()

const emits = defineEmits(['change', 'searchChange', 'dateChange', 'delete', 'search'])
const props = defineProps({
  referenceData: Array,
  page: Object,
  dataIds: Array,
  searchFilter: Object,
  selectCategories: Object,
  categoryData: Object,
  dateRange: Object
})

const selectReference = ref('all')
const isDatePicker = ref(false)
const postSelected = ref([])
const isSearchHide = ref(false)
const searchOption = ref(props.searchFilter)
const dropdownStatus = reactive({
  isReference: false,
  isPageOption: false,
  is1depthCategory: false,
  is2depthCategory: false,
  is3depthCategory: false
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

const isAllPostChecked = computed(() => {
  return props.referenceData.length > 0 && props.referenceData.every(item => postSelected.value.includes(item.id));
})

const isDepth = computed(() => {
  return (value) => {
    return Object.keys(value).some(key => key.includes('depth'))
  }
})

const onSelectPost = (id) => {
  if (id === 'all') {
    if (isAllPostChecked.value) {
      return postSelected.value = []
    }
    postSelected.value = []
    for (let i=0; i < props.referenceData.length; i++) {
      postSelected.value.push(props.referenceData[i].id)
    }
  } else {
    if (postSelected.value.includes(id)) {
      for (let i=0; i < postSelected.value.length; i++) {
        if (postSelected.value[i] === id) postSelected.value.splice(i, 1)
      }
    } else {
      postSelected.value.push(id)
    }
  }
}

const selectDateRange = (date) => {
  emits('dateChange', date.start, date.end)
  isDatePicker.value = false
}

const dropdownMap = new Map([
  ['reference', 'isReference'],
  ['1depth', 'is1depthCategory'],
  ['2depth', 'is2depthCategory'],
  ['3depth', 'is3depthCategory'],
  ['page', 'isPageOption'],
])

const resetOtherDropdowns = (current) => {
  const keys = ['reference', '1depth', '2depth', '3depth', 'page']

  for (let i=0; i < keys.length; i++) {
    if (keys[i] !== current) dropdownStatus[dropdownMap.get(keys[i])] = false
  }
}

const toggleDropDown = (type) => {
  if (!dropdownMap.has(type)) return

  const current = dropdownMap.get(type)
  dropdownStatus[current] = !dropdownStatus[current]

  isDatePicker.value = false
  resetOtherDropdowns(type)
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
    case 'reference':
      selectReference.value = item
      emits('searchChange', 'reference', item === 'reference' ? true : item === 'all' ? null : false)
      break
    case '1depth':
      emits('searchChange', '1depth', item)
      break
    case '2depth':
      emits('searchChange', '2depth', item)
      break
    case '3depth':
      emits('searchChange', '3depth', item)
      break
    case 'page':
      emits('change', 'pageOption', item)
      break
  }

  toggleDropDown(type)
}

const goWriting = () => {
  const accessToken = cookie && JSON.parse(cookie).accessToken

  if (!cookie && !accessToken) {
    alert(t('modal.sessionExpired'))
    router.push('/')
  } else {
    router.push({ name: 'Writing' })
  }
}

const onChangePage = (page) => {
  emits('change', 'current', page)
}

const dateReset = () => {
  emits('dateChange', null, null)
}

const closeDropdown = (e) => {
  dropdownStatus.isPageOption = false
  dropdownStatus.isReference = false
  dropdownStatus.is1depthCategory = false
  dropdownStatus.is2depthCategory = false
  dropdownStatus.is3depthCategory = false

  if (e.target.className === 'be-input') {
    isDatePicker.value = false
  }
}

const selectDelete = async () => {
  if (postSelected.value.length !== 0) {
    emits('delete', {id: postSelected.value})
  }
}

const onSearch = () => {
  emits('search')
}
</script>

<template>
  <div class="reference-wrapper flex flex-column">
    <div class="search-wrapper" :class="{ isSearchHide }">
      <template v-if="!isSearchHide">
        <h3 class="title be-font text-grey-md bold size-18 flex y-center">
          {{ $t('common.searchFilter') }}
        </h3>
      </template>
      <div class="search">
        <template v-if="!isSearchHide">
          <div class="search-group">
            <div class="search-group-top reference">
              <div class="search-group-bottom--reference">
                <label>{{ $t('referenceList.search.isReference') }}</label>
                <div class="be-dropdown flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('reference')">
                  <span class="current-type">
                    {{ $t(`common.${REFERENCE_TYPE[selectReference]}`) }}
                  </span>
                  <span class="be-icon size-20 icon-grey-md icon-dropdown">
                    <i class="font-icon-right-arrow"></i>
                  </span>
                  <Transition name="slide">
                    <ul class="list" :class="{'is-show': dropdownStatus.isReference}" v-if="dropdownStatus.isReference">
                      <template v-for="(type, key) in REFERENCE_TYPE" :key="type">
                        <li @click.stop="selectDropDown(key, 'reference')">
                          {{ $t(`common.${type}`) }}
                        </li>
                      </template>
                    </ul>
                  </Transition>
                </div>
              </div>
              <div class="search-group-top--title">
                <UiInput
                    :type="'text'"
                    v-model="searchOption.title"
                    @enter="onSearch">
                  <template #label>
                    {{ $t('referenceList.search.title') }}
                  </template>
                </UiInput>
              </div>
              <div class="search-group-bottom--date">
                <UiInput
                    :input-style="'date'"
                    :type="'text'"
                    v-model="dateRangeStr"
                    :date-range="props.dateRange"
                    @date-reset="dateReset"
                    @click.stop="toggleDatePicker()">
                  <template #label>
                    {{ $t('referenceList.search.createdDate') }}
                  </template>
                </UiInput>
                <template v-if="isDatePicker">
                  <DatePicker @select-date-range="selectDateRange($event)"/>
                </template>
              </div>
              <div class="search-group-top--transparent" style="width: 102px;">
              </div>
            </div>
            <div class="search-group-bottom">
              <div class="search-group-bottom--author">
                <UiInput
                    :type="'text'"
                    v-model="searchOption.author"
                    @enter="onSearch">
                  <template #label>
                    {{ $t('referenceList.search.author') }}
                  </template>
                </UiInput>
              </div>
              <div class="search-group-bottom--category">
                <span class="option-title">
                  {{ $t('referenceList.search.category') }}
                </span>
                <div class="category-dropdown-wrapper">
                  <div class="be-dropdown flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('1depth')">
                    <span class="current-type">
                      {{ props.selectCategories.select1depthCategory && props.selectCategories.select1depthCategory.name || $t('referenceCategory.depth.depth1') }}
                    </span>
                    <span class="be-icon size-20 icon-grey-md icon-dropdown">
                      <i class="font-icon-right-arrow"></i>
                    </span>
                    <Transition name="slide">
                      <ul class="list" :class="{'is-show': dropdownStatus.is1depthCategory}" v-if="dropdownStatus.is1depthCategory">
                        <template v-for="item in props.categoryData.categoryDepth1List" :key="item.depth">
                          <li @click.stop="selectDropDown(item, '1depth')">
                            {{ item.name }}
                          </li>
                        </template>
                      </ul>
                    </Transition>
                  </div>
                  <div class="be-dropdown flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('2depth')">
                    <span class="current-type">
                      {{ props.selectCategories.select2depthCategory && props.selectCategories.select2depthCategory.name || t('referenceCategory.depth.depth2') }}
                    </span>
                    <span class="be-icon size-20 icon-grey-md icon-dropdown">
                      <i class="font-icon-right-arrow"></i>
                    </span>
                    <Transition name="slide">
                      <ul class="list" :class="{'is-show': dropdownStatus.is2depthCategory}" v-if="dropdownStatus.is2depthCategory">
                        <template v-for="item in props.categoryData.categoryDepth2List" :key="item.depth">
                          <li @click.stop="selectDropDown(item, '2depth')">
                            {{ item.name }}
                          </li>
                        </template>
                      </ul>
                    </Transition>
                  </div>
                  <div class="be-dropdown flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('3depth')">
                    <span class="current-type">
                      {{ props.selectCategories.select3depthCategory && props.selectCategories.select3depthCategory.name || $t('referenceCategory.depth.depth3') }}
                    </span>
                    <span class="be-icon size-20 icon-grey-md icon-dropdown">
                      <i class="font-icon-right-arrow"></i>
                    </span>
                    <Transition name="slide">
                      <ul class="list" :class="{'is-show': dropdownStatus.is3depthCategory}" v-if="dropdownStatus.is3depthCategory">
                        <template v-for="item in props.categoryData.categoryDepth3List" :key="item.depth">
                          <li @click.stop="selectDropDown(item, '3depth')">
                            {{ item.name }}
                          </li>
                        </template>
                      </ul>
                    </Transition>
                  </div>
                </div>
              </div>
              <UiButton :type="'icon primary sm'"  @click="onSearch" style="margin-top: 19px;">
                <i class="font-icon-search"/>
                <span class="btn-text">
                  {{ $t('common.search') }}
                </span>
              </UiButton>
            </div>
          </div>
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
        <div class="btn-wrap">
          <UiButton :type="'icon outline'" @click="selectDelete">
            {{ $t('referenceList.selectDelete') }}
            <i class="font-icon-delete" />
          </UiButton>
          <UiButton :type="'icon outline primary'" @click="goWriting">
            {{ $t('referenceList.goWriting') }}
            <i class="font-icon-writing" />
          </UiButton>
        </div>
      </div>
      <table class="be-table">
        <colgroup>
          <col style="width: 96px">
          <col style="width: 96px">
          <col style="width: 96px">
          <col style="width: 96px">
          <col style="width: 96px">
          <col style="width: 441px">
          <col style="width: 136px">
          <col style="width: 76px">
          <col style="width: 77px">
        </colgroup>
        <thead>
          <tr class="thead-row">
            <template v-for="column in REFERENCE_COLUMNS" :key="column.key">
              <th>
                <template v-if="column.key === 'checkbox'">
                  <div class="reference-checkbox">
                      <input id="selectPost" class="post-checkbox" type="checkbox" :checked="isAllPostChecked" v-model="postSelected" :value="'all'" @change="onSelectPost('all')" />
                      <label for="selectPost"></label>
                  </div>
                </template>
                <template v-else-if="column.title.includes('depth')">
                  <span>
                    {{ $t(`referenceCategory.depth.${column.title}`) }}
                  </span>
                </template>
                <template v-else>
                  <span>
                    {{ $t(`referenceList.column.${column.title}`) }}
                  </span>
                </template>
              </th>
            </template>
          </tr>
        </thead>

        <tbody :class="{noData: !props.referenceData || props.referenceData.length === 0}">
          <template v-if="props.referenceData && props.referenceData.length > 0">
            <template v-for="row in props.referenceData" :key="row.id">
              <tr>
                <template v-for="header in REFERENCE_COLUMNS" :key="header.key">
                  <td :class="{category: header.key.includes('depth')}">
                    <template v-if="header.key === 'issue_status'">
                      <span :class="header.key === 'issue_status' && `status-${row[header.key]}`">
                        {{ STATUS[row[header.key]] }}
                      </span>
                    </template>
                    <template v-else-if="header.key === 'checkbox'">
                      <div class="checkbox-container">
                        <input :id="'selectPost' + row.id"
                               class="post-checkbox"
                               type="checkbox"
                               :checked="postSelected.includes(row.id)"
                               @change="onSelectPost(row.id)" />
                        <label :for="'selectPost' + row.id"></label>
                      </div>
                    </template>
                    <template v-else-if="header.key === 'is_on'">
                      <span>
                        {{ row[header.key] ? $t('common.onReference') : $t('common.offReference') }}
                      </span>
                    </template>
                    <template v-else-if="header.key === 'reg_date'">
                      <span>
                        {{ dateFormatter(row[header.key], 'time') }}
                      </span>
                    </template>
                    <template v-else-if="header.key.includes('depth') && isDepth(row)">
                      <span :class="{category: isDepth(row)}"  @click="router.push({ name: 'ReferencePost', params: { id: row.id } })">
                        {{ row[header.key]?.name || '-'}}
                      </span>
                    </template>
                    <template v-else>
                      <span :class="{title: header.key === 'title'}"  @click="router.push({ name: 'ReferencePost', params: { id: row.id } })">
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
.reference-wrapper {
  gap: 30px;
  padding: 20px 40px;
}

</style>
