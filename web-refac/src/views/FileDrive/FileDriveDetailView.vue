<script setup>
import { ref, onBeforeMount, inject } from 'vue';
import { useRoute, useRouter } from 'vue-router'

import { getFileData, deleteFile, getFileDetailData, updateFileDetail } from '@/api/drive.js';
import { HTTP_CODES, WARNING_TYPE } from "@/libs/constants.js";

import FileDriveDetail from "@/components/FileDrive/FileDriveDetail.vue";
import Loading from "@/components/Modal/Loading.vue";
import Warning from "@/components/Modal/Warning.vue";

const route = useRoute()
const router = useRouter()
const modal = inject('$modal')

const fileData = ref(null)
const fileDetailData = ref(null)
const currentPage = ref(1)
const isEditing = ref(true)

onBeforeMount(async() => {
  await loadData()
  await getDetailData()
})

const loadData = async () => {
  modal.open(Loading)
  const id = route.params.fileId
  const params = {
    params: {
      fileId: id
    }
  }
  try {
    const res = await getFileData(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      fileData.value = res.data
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

const getDetailData = async (page = null) => {
  try {
    const params = {
      params: {
        fileId: route.params.fileId,
        page: currentPage.value
      }
    }

    if (page) {
      params.params.page = page
    }

    const res = await getFileDetailData(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      fileDetailData.value = res.data
    } else {
      alert(res.message)
      console.log(`Error: ${res}`)
    }
  } catch (e) {
    console.error(`Error: ${e}`)
  }
}

const deleteFileData = async (params) => {
  try {
    await modal.open(Warning, WARNING_TYPE.DELETE_PDF_FILE).then(async () => {
      modal.open(Loading)
      const res = await deleteFile(params)

      if (res.code === HTTP_CODES.SUCCESS) {
        // delete success
        modal.close()
        router.push({ name: 'FileDrive' })
      } else {
        // delete fail
        modal.close()
        alert(res.message)
        console.log(`Error: ${res}`)
      }
    }).catch(() => {
      modal.close()
    })
  } catch (e) {
    modal.close()
    console.error(`Error: ${e}`)
  }
}

const updateFileData = async (params) => {
  isEditing.value = true
  const pageSort = [...params.currentPage].sort((a, b) => a - b)
  try {
    await modal.open(Warning, {type: WARNING_TYPE.UPDATE_PDF_FILE, pages: pageSort}).then(async () => {
      modal.open(Loading)
      const res = await updateFileDetail({ fileId: params.fileId, currentPage: params.currentPage, content: params.content})

      if (res.code === HTTP_CODES.SUCCESS) {
        modal.close()
        await getDetailData(params.currentPage[params.currentPage.length - 1])
        isEditing.value = false
      } else {
        modal.close()
        alert(res.message)
        console.log(`Error: ${res}`)
      }
    }).catch(() => {
      modal.close()
    })
  } catch (e) {
    modal.close()
    console.error(`Error: ${e}`)
  }
}

const changeOption = async (value) => {
  currentPage.value = value

  await getDetailData()
}
</script>

<template>
  <FileDriveDetail
      :file-data="fileData"
      :file-detail-data="fileDetailData"
      :current-page="currentPage"
      :editing="isEditing"
      @delete="deleteFileData"
      @change="changeOption"
      @update="updateFileData"
  />
</template>

<style lang="scss" scoped>
</style>
