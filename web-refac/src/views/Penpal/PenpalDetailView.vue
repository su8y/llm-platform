<script setup>
import { ref, onBeforeMount, inject } from 'vue';
import { useRoute, useRouter } from 'vue-router'

import {
  getInboxData,
  createEmailAnswer,
  sendAiEmail,
  fileDownloadForInbox,
  getManagers,
  setManager,
  setMailStatus, editCompany, checkThread,
} from "@/api/penpal.js";
import {HTTP_CODES, SEND_MAIL_TYPE, SUCCESS_TYPE, WARNING_TYPE} from "@/libs/constants.js";
import { convertBase64ToCid } from "@/libs/imageConverter.js";

import PenpalDetail from "@/components/Panpal/PenpalDetail.vue";
import Loading from "@/components/Modal/Loading.vue";
import Success from "@/components/Modal/Success.vue";
import SendMail from "@/components/Modal/SendMail.vue";
import Warning from "@/components/Modal/Warning.vue";

const route = useRoute()
const router = useRouter()
const modal = inject('$modal')

const inboxData = ref(null)
const answerData = ref(null)
const answerStatus = ref(null)
const managerList = ref([])
const managerAddressList = ref([])
const isPass = ref(false)

onBeforeMount(async() => {
  await loadData()
  await getManagerList()
})

const loadData = async () => {
  modal.open(Loading)
  const id = route.params.id
  const params = {
    id: id
  }
  try {
    const res = await getInboxData(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      inboxData.value = res.data.row

      if (inboxData.value.attachments) {
        try {
          inboxData.value.attachments = JSON.parse(inboxData.value.attachments)
        } catch (e) {
          console.error(`attachments parsing error: ${e}`)
        }
      }
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

const createAnswer = async (id) => {
  modal.open(Loading)
  try {
    const res = await createEmailAnswer({id})

    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      answerData.value = res.data.answer
      answerStatus.value = res.data.status
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

const sendMail = async (params) => {
  try {
    await modal.open(SendMail, {type: SEND_MAIL_TYPE.SEND_AI_EMAIL}).then(async () => {
      modal.open(Loading)

      // base64 -> llm-platform cid
      const emailHtml = params.emailHtml
      const div = document.createElement('div')
      div.innerHTML = emailHtml
      const result = await convertBase64ToCid(emailHtml, div)

      if (result.convertImageList) {
        params.emailHtml = result.content
        params.imageInfo = result.convertImageList
      }

      // send mail
      const res = await sendAiEmail(params)

      if (res.code === HTTP_CODES.SUCCESS) {
        modal.close() // Loading 모달을 먼저 닫기
        await modal.open(Success, SUCCESS_TYPE.SEND_MAIL)

      } else {
        modal.close()
        alert('error')
      }
    }).catch(() => {
      modal.close()
      modal.open(Warning, WARNING_TYPE.FAILED_SEND_MAIL)
    })
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

const getManagerList = async () => {
  try {

    const res = await getManagers()

    if (res.code === HTTP_CODES.SUCCESS) {
      managerList.value = res.data.userId
      managerAddressList.value = res.data.emailAddress
    } else {
      alert(res.message)
      console.log(`Error: ${res}`)
    }

  } catch (e) {
    console.error(`Error: ${e}`)
  }
}

const assigningManager = async (params) => {
  try {
    const res = await setManager(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      await loadData()
      router.push({ name: 'PenpalDetail' })
    } else {
      alert(res.message)
     console.log(`Error: ${res}`)
    }

  } catch (e) {
    console.error(`Error: ${e}`)
  }
}

const setStatus = async (params) => {
  try {
    const res = await setMailStatus(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      await loadData()
      router.push({ name: 'PenpalDetail' })
    } else {
      alert(res.message)
     console.log(`Error: ${res}`)
    }

  } catch (e) {
    console.error(`Error: ${e}`)
  }
}

const checkThreadData = async (params) => {
  isPass.value = false
  try {
    const res = await checkThread(params)

    if (res.code === HTTP_CODES.HAS_THREAD) {
      modal.open(Warning, WARNING_TYPE.HAS_THREAD).then(async () => {
        isPass.value = true
      }).catch(() => {
        modal.close()
        isPass.value = false
      })

    } else if (res.code === HTTP_CODES.SUCCESS) {
      isPass.value = true
      await loadData()
    }

  } catch (e) {
    console.error(`Error: ${e}`)
  }
}

const editCompanyData = async (params) => {
  try {

    const res = await editCompany(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      await loadData()
      router.push({ name: 'PenpalDetail' })
    } else {
      alert(res.message)
     console.log(`Error: ${res}`)
    }

  } catch (e) {
    console.error(`Error: ${e}`)
  }
}

const changeOption = async (type, value) => {
  switch (type) {
    case 'create':
      await createAnswer(value)
      break
    case 'send':
      await sendMail(value)
      break
    case 'fileDownload':
      await fileDownload(value)
      break
    case 'setManager':
      await assigningManager(value)
      break
    case 'setStatus':
      await setStatus(value)
      break
    case 'editCompany':
      await editCompanyData(value)
      break
    case 'checkThread':
      await checkThreadData(value)
  }
}
</script>

<template>
  <PenpalDetail
      :inbox-data="inboxData"
      :answer="answerData"
      :status="answerStatus"
      :manager-list="managerList"
      :manager-address-list="managerAddressList"
      :is-pass="isPass"
      @change="changeOption"

  />
</template>

<style lang="scss" scoped>
</style>
