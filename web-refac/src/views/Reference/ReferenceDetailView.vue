<script setup>
import { ref, reactive, onBeforeMount, inject } from "vue";
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { HTTP_CODES, WARNING_TYPE } from "@/libs/constants.js";
import { deleteFileData, deleteReferenceData, getReferenceDetail, updateReferenceData } from "@/api/reference.js";

import ReferenceDetail from "@/components/Reports/ReferenceDetail.vue";
import Loading from '@/components/Modal/Loading.vue';
import Warning from "@/components/Modal/Warning.vue";

const { t } = useI18n()
const modal = inject('$modal')
const route = useRoute()
const router = useRouter()

const postData = ref(null)
const isReference = ref(false)
const editData = reactive({
  title: null,
  isOn: isReference.value,
  content: null
})
const categoryData = reactive({
  is1depthCategory: false,
  is2depthCategory: false,
  is3depthCategory: false,
  categoryDepth1List: [],
  categoryDepth2List: [],
  categoryDepth3List: [],
  select1depthCategory: null,
  select2depthCategory: null,
  select3depthCategory: null
})
const fileData = reactive({
  files: [],
  fileNames: [],
  base64Files: []
})

onBeforeMount(async () => {
  await getReferenceData()
})

const getReferenceData = async () => {
  modal.open(Loading)
  const id = route.params.id
  try {
    const params = {
      id: Number(id)
    }
    const res = await getReferenceDetail(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()

      postData.value = res.data
      isReference.value = postData.value.is_on === 1
      editData.title = postData.value.title || ''
      editData.content = postData.value.content || ''
      editData.isOn = postData.value.is_on
      categoryData.categoryDepth1List = postData.value.categories
      fileData.fileNames = postData.value.filenames

      switch (postData.value.post_category_depth) {
        case 3:
          categoryData.select1depthCategory = {
            id: postData.value.category_depth_1_id,
            name: postData.value.category['1']
          }
          categoryData.select2depthCategory = {
            id: postData.value.category_depth_2_id,
            name: postData.value.category['2']
          }
          categoryData.select3depthCategory = {
            id: postData.value.post_category_id,
            name: postData.value.post_category_name
          }
          break
        case 2:
          categoryData.select1depthCategory = {
            id: postData.value.category_depth_1_id,
            name: postData.value.category['1']
          }
          categoryData.select2depthCategory = {
            id: postData.value.post_category_id,
            name: postData.value.post_category_name
          }
          break
        case 1:
          categoryData.select1depthCategory = {
            id: postData.value.post_category_id,
            name: postData.value.post_category_name
          }
          break
      }

      if (categoryData.select1depthCategory) {
        categoryData.categoryDepth2List = categoryData.categoryDepth1List.filter(item => item.id === categoryData.select1depthCategory.id)[0].children

        if (categoryData.select2depthCategory) {
          categoryData.categoryDepth3List = categoryData.categoryDepth2List.filter(item => item.id === categoryData.select2depthCategory.id)[0].children
        }
      }
    } else {
      modal.close()
      alert(res.message)
      console.log('Error: ', res)
    }
  } catch (e) {
    modal.close()
    alert(e)
    console.error('Error: ', e)
  }
}

const updateReference = async (params) => {
  modal.open(Loading)

  try {
    const res = await updateReferenceData(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      alert(t('modal.updateSuccess'))
      location.reload()
    } else {
      modal.close()
      alert(res.message)
      console.log('Error: ', res)
    }

  } catch (e) {
    modal.close()
    console.error('Error: ', e)
  }
}

const deleteReference = async (params) => {
  try {
    await modal.open(Warning, WARNING_TYPE.REFERENCE_DELETE).then(async () => {
      modal.open(Loading)

      const res = await deleteReferenceData(params)
      if (res.code === HTTP_CODES.SUCCESS) {
        modal.close()
        router.go(-1)
      } else {
        modal.close()
        alert(res.message)
      }
    }).catch(() => {
      modal.close()
    })
  } catch (e) {
    console.error('Error: ', e)
  }
}

const deleteFile = async (data) => {
  try {
    const res = await deleteFileData({id: data.id})

    if (res.code === HTTP_CODES.SUCCESS) {
      fileData.value.fileNames.splice(data.index, 1)
    } else {
      alert(res.message)
      console.log('Error: ', res)
    }
  } catch (e) {
    alert(e)
    console.error('Error: ', e)
  }
}


const change = (type, value) => {
  type === 'reference' ? isReference.value = value : null
}

</script>

<template>
  <ReferenceDetail
      :post-data="postData"
      :category-data="categoryData"
      :edit-data="editData"
      :file-data="fileData"
      :is-reference="isReference"
      @change="change"
      @update="updateReference"
      @delete="deleteReference"
      @deleteFile="deleteFile"
  />
</template>
