<script setup>
import { reactive, onBeforeMount, inject } from "vue"

import { getCategories, saveCategories } from "@/api/reference.js"
import { HTTP_CODES, WARNING_TYPE } from "@/libs/constants.js"

import ReferenceCategory from "@/components/Reports/ReferenceCategory.vue"
import Warning from "@/components/Modal/Warning.vue";

const modal = inject('$modal')

const depthList = reactive({
  depth1List: [],
  depth2List: [],
  depth3List: []
})

onBeforeMount(async () => {
  await loadList()
})

const loadList = async () => {
  try {
    const res = await getCategories()

    if (res.code === HTTP_CODES.SUCCESS) {
      depthList.depth1List = res.data
    } else {
      alert(res.message)
      console.log('Error: ', res)
    }

  } catch (e) {
    alert(e)
    console.error('Error: ', e)
  }
}

const onSave = async (params) => {
  try {
    await modal.open(Warning, WARNING_TYPE.CATEGORY_SAVE).then(async () => {
      modal.close()

      const res = await saveCategories(params)

      if (res.code === HTTP_CODES.SUCCESS) {
        location.reload()
      } else {
        alert(res.message)
        console.log('Error: ', res)
      }
    }).catch(() => {
      modal.close()
    })
  } catch (e) {
    console.error('Error: ', e)
  }
}

</script>

<template>
  <ReferenceCategory :list="depthList" @save="onSave" />
</template>
