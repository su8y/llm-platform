<script setup>
import { ref, reactive, onBeforeMount, inject } from 'vue';
import { useRouter } from 'vue-router';
import { useStore } from 'vuex';
import { useI18n } from 'vue-i18n';

import {
  createPost,
  deleteFileData,
  getCategories,
  getTemporaryPost,
  getTokenSize,
  temporaryPost
} from "@/api/reference.js";
import { HTTP_CODES, SUCCESS_TYPE } from "@/libs/constants.js";

import Writing from "@/components/Reports/Writing.vue";
import Loading from "@/components/Modal/Loading.vue";
import Success from "@/components/Modal/Success.vue";

const { t, locale } = useI18n()
const modal = inject('$modal')
const router = useRouter()
const store = useStore()

const isReference = ref(true)
const userData = ref(null)
const temporaryData = ref(null)
const fileNames = ref([])
const uploadAble = ref(true)
const tokenSize = ref(0)
const postData = reactive({
  title: null,
  content: '',
  isOn: isReference.value,
  lang: locale,
  files: [],
  author: null
})
const categoryData = reactive({
  depth1List: [],
  depth2List: [],
  depth3List: [],
  select1depthCategory: null,
  select2depthCategory: null,
  select3depthCategory: null
})

onBeforeMount(async () => {
  userData.value = await store.dispatch('storeUserData')
  postData.author = userData.value.userId

  await load()
})

const load = async () => {
  modal.open(Loading)
  try {
    const res = await getCategories()
    const temporaryRes = await getTemporaryPost()

    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      categoryData.depth1List = res.data
    } else {
      modal.close()
      alert(res.message)
      console.log('Error: ', res)
    }

    if (temporaryRes.code === HTTP_CODES.SUCCESS) {
      modal.close()
      if (temporaryRes.data) {
        temporaryData.value = temporaryRes.data
        postData.title = temporaryData.value.title
        postData.author = temporaryData.value.author
        postData.content = temporaryData.value.content || ''
        postData.isOn = temporaryData.value.is_on

        fileNames.value = temporaryRes.data.filenames

        switch (temporaryData.value.post_category_depth) {
          case 3:
            categoryData.select1depthCategory = {
              id: temporaryData.value.category_depth_1_id,
              name: temporaryData.value.category['1']
            }
            categoryData.select2depthCategory = {
              id: temporaryData.value.category_depth_2_id,
              name: temporaryData.value.category['2']
            }
            categoryData.select3depthCategory = {
              id: temporaryData.value.post_category_id,
              name: temporaryData.value.post_category_name
            }
            break
          case 2:
            categoryData.select1depthCategory = {
              id: temporaryData.value.category_depth_1_id,
              name: temporaryData.value.category_depth_1_name
            }
            categoryData.select2depthCategory = {
              id: temporaryData.value.post_category_id,
              name: temporaryData.value.post_category_name
            }
            break
          case 1:
            categoryData.select1depthCategory = {
              id: temporaryData.value.post_category_id,
              name: temporaryData.value.post_category_name
            }
            break
          default:
            return null
        }

      }
    } else {
      modal.close()
      alert(temporaryRes.message)
      console.log('Error: ', temporaryRes)
    }
  } catch (e) {
    modal.close()
    console.error('Error: ', e)
  }
}

const checkTokenSize = async (params) => {
  try {
    const res = await getTokenSize(params)
    if (res.code === 999 && !res.data.upload_able) {
      alert(t('modal.postCapacity'))
      uploadAble.value = false
      tokenSize.value = res.data.token_size
    } else {
      tokenSize.value = res.data.token_size
      uploadAble.value = true
    }
  } catch (e) {
    alert(e)
    console.error('Error: ', e)
  }
}

const create = async (params) =>{
  modal.open(Loading)

  try {
    const res = await createPost(params)
    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      router.push({ name: 'Board' })
    } else {
      modal.close()
      alert(res.message)
      console.log('Error: ', res)
      if (res.message) {
        if (res.message.indexOf('token limit') > -1) {
          alert(t('modal.postCapacity'))
        }
      }
    }
  } catch (e) {
    modal.close()
    alert(e)
    console.error('Error: ', e)
  }
}

const saveTemporary = async (params) => {
  modal.open(Loading)

  try {
    const res = await temporaryPost(params)
    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      modal.open(Success, SUCCESS_TYPE.TEMPORARY_SAVE).then(() => {
        router.push({ name: 'Board' })
      })
    } else {
      modal.close()
      alert(res.message)
      console.log('Error: ', res)
      if (res.message) {
        if (res.message.indexOf('token limit') > -1) {
          alert(t('modal.postCapacity'))
        }
      }
    }
  } catch (e) {
    modal.close()
    alert(e)
    console.error('Error: ', e)
  }
}

const deleteFile = async (data) => {
  try {
    const res = await deleteFileData({id: data.id})

    if (res.code === HTTP_CODES.SUCCESS) {
      fileNames.value.splice(data.index, 1)
    } else {
      alert(res.message)
      console.log('Error: ', res)
    }
  } catch (e) {
    alert(e)
    console.error('Error: ', e)
  }
}
</script>

<template>
  <Writing
      :user-data="userData"
      :category-data="categoryData"
      :post-data="postData"
      :temporary-data="temporaryData"
      :upload-able="uploadAble"
      :token-size="tokenSize"
      :file-names="fileNames"
      @check="checkTokenSize"
      @create="create"
      @save="saveTemporary"
      @delete="deleteFile"
  />
</template>
