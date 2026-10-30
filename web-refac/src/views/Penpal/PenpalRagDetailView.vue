<script setup>
import { ref, onBeforeMount, inject } from 'vue';
import { useRoute } from 'vue-router'

import {fileDownloadForInbox, getEmailRagDetail} from "@/api/penpal.js";
import { HTTP_CODES } from "@/libs/constants.js";

import PenpalRagDetail from "@/components/Panpal/PenpalRagDetail.vue";
import Loading from "@/components/Modal/Loading.vue";

const route = useRoute()
const modal = inject('$modal')

const ragData = ref(null)

onBeforeMount(async() => {
  await loadData()
})

const loadData = async () => {
  modal.open(Loading)
  const id = route.params.id
  const params = {
    id: id
  }
  try {
    const res = await getEmailRagDetail(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      ragData.value = res.data

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

const fileDownload = async (attachment) => {
  modal.open(Loading)

  const params = {
    s3Key: encodeURI(attachment.s3Key)
  }

  try {
    const res = await fileDownloadForInbox(params)

    if (res.status === HTTP_CODES.SUCCESS) {
      modal.close()
      const blob = res.data || res
      const blobUrl = window.URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = blobUrl
      link.download = attachment.filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(blobUrl)
    }
  } catch (e) {
    modal.close()
    console.error(`Error: ${e}`)
  }
}


const changeOption = async (type, value) => {
  switch (type) {
    case 'create':
      break
    case 'send':
      break
    case 'download':
      if (!Array.isArray(value)) {
        await fileDownload(value)
      } else {
        for (let i = 0; i < value.length; i++) {
          const file = value[i]
          await fileDownload(file)
        }
      }
      break
  }
}
</script>

<template>
  <PenpalRagDetail
      :rag-data="ragData"
      @change="changeOption"
  />
</template>

<style lang="scss" scoped>
</style>
