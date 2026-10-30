```vue
<script setup>
import { ref, defineAsyncComponent, nextTick, inject, reactive, onMounted, watch } from 'vue'
import { useStore } from 'vuex'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { getInitAnswer, getSendInfo, saveAttachment, saveTemporaryMail } from "@/api/penpal.js";
import { HTTP_CODES, INTERNAL_COMPANY_NAMES, WARNING_TYPE } from "@/libs/constants.js";
import {addResponsiveImageStyles, convertBase64ToCid, convertCidToS3, convertS3ToCid} from "@/libs/imageConverter.js";
import { bytesToMB } from '@/libs/utils.js'

import Warning from "@/components/Modal/Warning.vue";
import Loading from "@/components/Modal/Loading.vue";

const CKEditor = defineAsyncComponent(() =>
    import('@/components/Editor/CKEditor.vue')
)

const emits = defineEmits(['edit', 'create', 'send', 'download'])
const props = defineProps({
  data: Object,
  answerData: String,
  answerStatus: String,
})

const modal = inject('$modal')
const store = useStore()
const route = useRoute()
const { t } = useI18n()

const initAnswerData = ref(null)
const isReplyEdit = ref(false)
const editFocus = ref(false)
const answer = ref('')
const templateRef = ref(null)
const userData = ref(null)
const fileNames = ref([])
const files = ref([])
const base64Files = ref([])
const toTags = ref([])
const ccTags = ref([])
const hiddenCcTags = ref([])
const toInputValue = ref('')
const ccInputValue = ref('')
const hiddenCcInputValue = ref('')
const isHiddenCcOpen = ref(false)
const commentRef = ref(null)
const attachments = ref([])
const isAttachmentOpen = ref(true)
const isFocus = reactive({
  to: false,
  cc: false,
  hiddenCc: false
})
const inputError = reactive({
  comment: false
})
const editDataState = reactive({
  subject: '',
  answerText: '',
  hiddenCc: '',
  cc: null,
  replyTo: props.inboxData?.replyTo,
  comment: ''
})

watch(() => props.answerStatus, async (newVal) => {
  await getInfo({id: route.params.id})
})

onMounted(async () => {
  const id = route.params.id
  await getInitAnswerData({id: id})

  if (hiddenCcTags.value.length) {
    isHiddenCcOpen.value = true
  } else {
    isHiddenCcOpen.value = false
  }
})

const isInternalCompany = () => {
  userData.value = store.state.userData
  return INTERNAL_COMPANY_NAMES.includes(userData?.value.companyName)
}

const formatEmailDate = (dateString) => {
  if (!dateString) return ''

  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()

  const weekdays = ['일', '월', '화', '수', '목', '금', '토']
  const weekday = weekdays[date.getDay()]

  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${year}. ${month}. ${day}. (${weekday}) ${hours}:${minutes} (GMT+09:00)`
}

const isValidEmail = (email) => {
  const emailRegex = /^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/

  return emailRegex.test(email.trim())
}

const isValidName = (name) => {
  if (!name) return true

  const nameRegex = /^[^<]+$/

  const normalizedName = name.replace(/\s+/g, ' ').trim()

  return nameRegex.test(normalizedName) && normalizedName.length > 0
}

const normalizeSpaces = (text) => {
  return text.replace(/\s+/g, ' ').trim()
}

const emailToTag = (email) => {
  if (!email) return ''
  const emailArr = email.split('@')
  const tag = emailArr[0].replace(/[^a-zA-Z0-9]/g, '')
  return tag
}

const parseMultipleEmails = (emailString) => {
  if (!emailString) return []

  const emails = emailString.split(/[,;]/)
  const results = []

  emails.forEach(email => {
    const trimmed = email.trim()
    if (trimmed) {
      const parsed = parseSingleEmail(trimmed)
      if (parsed) {
        results.push(parsed)
      }
    }
  })

  return results
}

const parseSingleEmail = (emailString) => {
  if (!emailString) return null

  const trimmed = emailString.trim()

  const nameEmailMatch = trimmed.match(/^(.+?)\s*<([^>]+)>\s*$/)

  if (nameEmailMatch) {
    const name = normalizeSpaces(nameEmailMatch[1])
    const email = nameEmailMatch[2].trim()

    if (isValidName(name) && isValidEmail(email)) {
      return {
        name: name,
        email: email,
        isValid: true
      }
    } else {
      return {
        name: name,
        email: email,
        isValid: false,
        error: !isValidName(name) ? 'invalid_name' : 'invalid_email'
      }
    }
  }

  if (isValidEmail(trimmed)) {
    return {
      name: '',
      email: trimmed,
      isValid: true
    }
  }

  return {
    name: '',
    email: trimmed,
    isValid: false,
    error: 'invalid_format'
  }
}


const handleEnterKey = (event = null, field) => {
  if (event.key === 'Enter') {
    event.preventDefault()
    addEmailTag(field)
    return
  }
  addEmailTag(field)
}

const addEmailTag = (field, value = null) => {
  let inputValue = ''
  let tagsArray = null

  switch (field) {
    case 'to':
      inputValue = value || toInputValue.value.trim()
      tagsArray = toTags.value
      break
    case 'cc':
      inputValue = value || ccInputValue.value.trim()
      tagsArray = ccTags.value
      break
    case 'hiddenCc':
      inputValue = value || hiddenCcInputValue.value.trim()
      tagsArray = hiddenCcTags.value
      break
  }

  if (inputValue) {
    const parsedEmails = parseMultipleEmails(inputValue)

    parsedEmails.forEach(emailData => {
      const tag = emailToTag(emailData.email)

      tagsArray.push({
        name: emailData.name,
        email: emailData.email,
        tag: tag,
        error: !emailData.isValid,
        errorType: emailData.error || null
      })
    })

    switch (field) {
      case 'to':
        toInputValue.value = ''
        break
      case 'cc':
        ccInputValue.value = ''
        break
      case 'hiddenCc':
        hiddenCcInputValue.value = ''
        break
    }
  }
}

const createEmailString = (name, email) => {
  if (!email) return ''

  if (name && name.trim() && name.trim() !== '') {
    return `${name.trim()} <${email.trim()}>`
  } else {
    return email.trim()
  }
}

const removeEmailTag = (field, index) => {
  switch (field) {
    case 'to':
      toTags.value.splice(index, 1)
      break
    case 'cc':
      ccTags.value.splice(index, 1)
      break
    case 'hiddenCc':
      hiddenCcTags.value.splice(index, 1)
      break
  }
}

const handleBackspace = (event, field) => {
  let inputValue = ''
  let tagsArray = null

  switch (field) {
    case 'to':
      inputValue = toInputValue.value
      tagsArray = toTags.value
      break
    case 'cc':
      inputValue = ccInputValue.value
      tagsArray = ccTags.value
      break
    case 'hiddenCc':
      inputValue = hiddenCcInputValue.value
      tagsArray = hiddenCcTags.value
      break
  }

  if (event.key === 'Backspace' && inputValue === '' && tagsArray.length) {
    tagsArray.pop()
  }
}

const onEditing = () => {
  isReplyEdit.value = !isReplyEdit.value

  if (hiddenCcTags.value.length) {
    isHiddenCcOpen.value = true
  } else {
    isHiddenCcOpen.value = false
  }
}

const onFileChange = (e) => {
  files.value = e.target.files
  const maxSize = 20 * 1024 * 1024
  let totalFileSize = 0

  if (files.value.length > 0) {
    if (fileNames.value.length) {
      fileNames.value.forEach((file) => {
        totalFileSize += file.size
      })
    }

    Array.from(files.value).forEach((file) => {
      totalFileSize += file.size
    })

    if (totalFileSize > maxSize) {
      files.value = null
      e.target.value = ''
      return modal.open(Warning, WARNING_TYPE.ATTACHMENT_ERROR)
    }

    Array.from(files.value).forEach((file) => {
      const fileSize = file.size
      const reader = new FileReader()

      if (fileSize > maxSize) {
        return modal.open(Warning, WARNING_TYPE.FILE_UPLOAD_ERROR)
      }

      reader.onload = () => {
        base64Files.value.push(file)
      }
      reader.readAsDataURL(file)
      fileNames.value.push(file)
    })
  }
}

const deleteFile = async (index, type = null) => {
  if (type === 'all') {
    base64Files.value = []
    fileNames.value = []
    return
  }

  const file = fileNames.value[index]
  for (let i=0; i < base64Files.value.length; i++) {
    if (base64Files.value[i].name === (file.filename || file.name)) base64Files.value.splice(i, 1)
  }
  fileNames.value.splice(index, 1)
}

const temporarySave = async () => {
  modal.open(Loading)
  if (!editDataState.comment) {
    inputError.comment = true
    commentRef.value.scrollIntoView({ behavior: 'smooth' })
    return modal.open(Warning, WARNING_TYPE.REQUIRED_COMMENT)
  }

  const emailCount = toTags.value.length + ccTags.value.length + hiddenCcTags.value.length

  if (emailCount > 50) {
    return modal.open(Warning, WARNING_TYPE.EMAIL_COUNT_ERROR)
  }

  answer.value = addResponsiveImageStyles(answer.value)

  try {
    let res = null
    const params = {
      id: route.params.id,
      lastEditUserId: initAnswerData.value.lastEditUserId,
      fromMail: initAnswerData.value.fromMail || '',
      fromName: initAnswerData.value.fromName || '',
      toMail: toTags.value.map(tag => tag.email),
      toName: toTags.value.map(tag => tag.name),
      ccMail: ccTags.value.map(tag => tag.email),
      ccName: ccTags.value.map(tag => tag.name),
      bccMail: hiddenCcTags.value.map(tag => tag.email),
      bccName: hiddenCcTags.value.map(tag => tag.name),
      answeringContent: answer.value,
      subject: editDataState.subject,
      comment: editDataState.comment,
    }

    const remainingAttachments = attachments.value.filter(attachment =>
      fileNames.value.some(file => (file.filename || file.name) === attachment.filename)
    )

    const newFiles = fileNames.value.filter(file =>
      !attachments.value.some(attachment => attachment.filename === (file.filename || file.name))
    )

    if (newFiles.length > 0) {
      const formData = new FormData()

      for(let i = 0; i < base64Files.value.length; i++) {
        const file = base64Files.value[i]
        const isNewFile = newFiles.some(newFile => (newFile.name || newFile.filename) === file.name)

        if (isNewFile) {
          formData.append('files', file)
        }
      }

      await saveAttachments(formData)

      params.attachments = [...remainingAttachments, ...attachments.value.slice(-newFiles.length)]
    } else {
      params.attachments = remainingAttachments
    }

    res = await saveTemporaryMail(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      await getInfo({id: route.params.id})
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

const checkValidEmails = (tags) => {
  return tags.every(tag => {
    return isValidEmail(tag.email)
  })
}

const onCreateAnswer = () => {
  emits('create')
}

const mergeThread = () => {
  const receivedAt = formatEmailDate(props.data.receivedAt)
  const cc = initAnswerData.value.ccName.map((name, index) => {
    return `${name}<${initAnswerData.value.ccMail[index]}>`
  }).join(', ')
  const mailInfo = `
      <br>
      <p>-----Original Message-----</p>
      <p><strong>From:</strong> ${props.data?.fromName}&lt;${props.data?.fromMail}&gt;</p>
      <p><strong>To:</strong> ${props.data?.toName || ''}&lt;${props.data?.toMail || ''}&gt;</p>
      ${cc ? `<p><strong>Cc:</strong> ${cc}</p>` : ''}
      <p><strong>Sent:</strong> ${receivedAt}</p>
      <p><strong>Subject:</strong> ${props.data?.subject}</p>
      <br>
    `

  let thread = props.data?.thread
  if (props.data?.imageInfo) {
    thread = convertCidToS3(props.data?.imageInfo, thread)
  }

  return '<br><hr>' + mailInfo + thread
}

const sendMail = async () => {
  const isToValid = toTags.value.length === 0 || checkValidEmails(toTags.value)
  const isCcValid = ccTags.value.length === 0 || checkValidEmails(ccTags.value)
  const isHiddenCcValid = hiddenCcTags.value.length === 0 || checkValidEmails(hiddenCcTags.value)

  const validations = [
    {
      condition: !editDataState.replyTo.length || !isToValid,
      error: { type: WARNING_TYPE.SEND_MAIL_ERROR, required: t('penpal.search.to') }
    },
    {
      condition: !isCcValid,
      error: { type: WARNING_TYPE.SEND_MAIL_ERROR, required: t('penpal.detail.cc') }
    },
    {
      condition: !isHiddenCcValid,
      error: { type: WARNING_TYPE.SEND_MAIL_ERROR, required: t('penpal.detail.hiddenCc') }
    },
    {
      condition: !editDataState.subject,
      error: { type: WARNING_TYPE.SEND_MAIL_ERROR, required: t('penpal.column.subject') }
    },
    {
      condition: !answer.value,
      error: { type: WARNING_TYPE.SEND_MAIL_ERROR, required: t('penpal.search.content') }
    }
  ]

  const failedValidation = validations.filter(validation => validation.condition)

  if (failedValidation.length) {
    const error = []
    for (let i=0; i < failedValidation.length; i++) {
      error.push(failedValidation[i].error.required)
    }

    modal.open(Warning, { type: WARNING_TYPE.SEND_MAIL_ERROR, required: error }).then(() => {
    }).catch(() => {
      isReplyEdit.value = true
    })
    return
  } else {
    modal.open()
  }

  // change img src s3 url -> cid
  let emailHtml = convertS3ToCid(props.data?.imageInfo, answer.value)

  // edit img style
  emailHtml = addResponsiveImageStyles(emailHtml)

  const params = {
    id: route.params.id,
    emailHtml: emailHtml
  }

  emits('send', params)
}

const getInfo = async (params) => {
  modal.open(Loading)
  isReplyEdit.value = false
  toTags.value = []
  ccTags.value = []
  hiddenCcTags.value = []
  try {
    const res = await getSendInfo(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      initAnswerData.value = res.data
      editDataState.answerText = res.data.answeringContent
      editDataState.comment = res.data.comment
      editDataState.subject = res.data.subject
      editDataState.replyTo = res.data.toMail
      editDataState.cc = res.data.ccMail
      editDataState.hiddenCc = res.data.bccMail

      fileNames.value = [...res.data.attachments]
      attachments.value = [...res.data.attachments]

      for (let i=0; i < res.data.toMail.length; i++) {
        const emailString = createEmailString(res.data.toName[i], res.data.toMail[i])
        addEmailTag('to', emailString)

      }

      for (let i=0; i < editDataState.cc.length; i++) {
        const emailString = createEmailString(res.data.ccName[i], res.data.ccMail[i])
        addEmailTag('cc', emailString)
      }

      if (editDataState.hiddenCc) {
        isHiddenCcOpen.value = true
        for (let i=0; i < editDataState.hiddenCc.length; i++) {
          const emailString = createEmailString(res.data.bccName[i], res.data.bccMail[i])
          addEmailTag('hiddenCc', emailString)
        }
      }

      if (editDataState.answerText && editDataState.answerText.includes('Pangyoyeok-ro')) {
        answer.value = editDataState.answerText
      } else if (templateRef.value) {
        await nextTick()

        if (!isInternalCompany()) {
          answer.value = editDataState.answerText + mergeThread()
        } else {
          if (!res.data.isCreate) {
            answer.value = templateRef.value.$el.outerHTML
          } else {
            if (editDataState.answerText) {
              answer.value = templateRef.value.$el.outerHTML + mergeThread()
            } else {
              answer.value = editDataState.answerText + mergeThread()
            }
          }
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

const getInitAnswerData = async (params) => {
  try {
    const res = await getInitAnswer(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      await getInfo(params)
    } else {
      alert(res.message)
      console.log(`Error: ${res}`)
    }

  } catch (e) {
    console.error(`Error: ${e}`)
  }
}

const saveAttachments = async (params) => {
  try {
    const res = await saveAttachment(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      attachments.value = res.data
    } else {
      alert(res.message)
      console.log(`Error: ${res}`)
    }

  } catch (e) {
    console.error(`Error: ${e}`)
  }
}

</script>

<template>
  <div class="reference-detail-wrapper">

    <div class="monitoring-detail-header">
      <div class="back-list">
        <UiButton :type="'only-icon outline'" @click="isReplyEdit ? onEditing() : emits('edit')">
          <i class="font-icon-left-arrow" />
        </UiButton>
        <span>
          {{ $t('penpal.detail.out') }}
       </span>
      </div>
      <div class="edit-btn-wrap flex y-center gap-8">
        <template v-if="!initAnswerData?.isCreate">
          <UiButton :type="'outline'" @click="onCreateAnswer">
            {{ $t('penpal.detail.create') }}
          </UiButton>
        </template>
        <template v-else-if="isReplyEdit">
          <UiButton :type="'outline'" @click="temporarySave">
            {{ $t('penpal.detail.temporarySave') }}
          </UiButton>
        </template>
        <template v-else>
          <UiButton :type="'outline primary border'" @click="onEditing">
            {{ $t('common.edit2') }}
            <i class="font-icon-write"></i>
          </UiButton>
          <UiButton :type="'primary'" @click="sendMail">
            <i class="font-icon-save"></i>
            {{ $t('penpal.detail.send') }}
          </UiButton>
        </template>
      </div>
    </div>
    <div class="penpal-answer-container">
      <div class="detail-wrapper">
        <div class="detail flex">
          <div class="detail-group flex title">
            <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('penpal.detail.from') }}</p>
            <div class="from-mail right flex flex-column x-center title">
              <template v-if="initAnswerData?.fromMail">
                <p>
                  {{ `${initAnswerData?.fromName}<${initAnswerData?.fromMail}>` }}
                </p>
              </template>
            </div>
          </div>
          <div class="detail-group flex title" :class="{email: !isReplyEdit}">
            <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('penpal.search.to') }}</p>
            <div class="to-mail right title">
              <template v-if="!isReplyEdit">
                <template v-for="(mail, i) in initAnswerData?.toMail" :key="mail">
                  <span>
                    {{ initAnswerData.toName[i] }}{{ `<${mail}>` }}<template v-if="i !== initAnswerData.toMail.length - 1">, </template>
                  </span>
                </template>
              </template>
              <template v-else>
                <div class="email-input-container">
                  <div class="email-tags-wrapper" :class="{error: !toInputValue && !toTags.length, focus: isFocus.to}">
                    <div v-for="(tagObj, index) in toTags" :key="index" class="email-tag" :class="{error: tagObj.error}">
                      <span class="tag-name">{{ `${tagObj.name}<${tagObj.email}>` }}</span>
                      <button @click="removeEmailTag('to', index)" class="tag-remove">
                        <i class="font-icon-close" />
                      </button>
                    </div>
                    <input
                        class="email-input"
                        v-model="toInputValue"
                        :type="'email'"
                        @keydown="handleBackspace($event, 'to')"
                        @keydown.enter="handleEnterKey($event, 'to')"
                        @focus="isFocus.to = true"
                        @focusout="handleEnterKey($event, 'to'), isFocus.to = false"
                    />
                  </div>
                </div>
              </template>
            </div>
          </div>
          <div class="detail-group flex title" :class="{email: !isReplyEdit}">
            <p class="cc-label left be-font text-grey-sm size-13 bold flex y-center">
              {{ $t('penpal.detail.cc') }}
              <template v-if="editDataState.hiddenCc.length || isReplyEdit">
                <span class="icon-wrap" :class="{'open': isHiddenCcOpen}" @click="isHiddenCcOpen = !isHiddenCcOpen">
                  <i class="icon icon--arrow-down" />
                </span>
              </template>
            </p>
            <div class="cc-mail right">
              <template v-if="!isReplyEdit">
                <template v-if="initAnswerData?.ccMail.length">
                  <template v-for="(mail, index) in initAnswerData.ccMail" :key="index">
                    <span>
                      {{ initAnswerData.ccName[index] }}{{ `<${mail}>` }}<template v-if="index !== initAnswerData.ccMail.length - 1">, </template>
                    </span>
                  </template>
                </template>
              </template>
              <template v-else>
                <div class="email-input-container">
                  <div class="email-tags-wrapper" :class="{focus: isFocus.cc}">
                    <div v-for="(tagObj, index) in ccTags" :key="index" class="email-tag" :class="{error: tagObj.error}">
                      <span class="tag-name">{{ `${tagObj.name}<${tagObj.email}>` }}</span>
                      <button @click="removeEmailTag('cc', index)" class="tag-remove">
                        <i class="font-icon-close" />
                      </button>
                    </div>
                    <input
                        class="email-input"
                        v-model="ccInputValue"
                        :type="'email'"
                        @keydown="handleBackspace($event, 'cc')"
                        @keydown.enter="handleEnterKey($event, 'cc')"
                        @focus="isFocus.cc = true"
                        @focusout="handleEnterKey($event, 'cc'), isFocus.cc = false"
                    />
                  </div>
                </div>
              </template>
            </div>
          </div>
          <template v-if="(editDataState.hiddenCc.length && isHiddenCcOpen) || isReplyEdit && isHiddenCcOpen">
            <div class="detail-group flex title" :class="{email: !isReplyEdit}">
              <p class="cc-label left be-font text-grey-sm size-13 bold flex y-center">
                {{ $t('penpal.detail.hiddenCc') }}
              </p>
              <div class="cc-mail right">
                <template v-if="!isReplyEdit">
                  <template v-if="initAnswerData.bccMail.length">
                    <template v-for="(mail, index) in initAnswerData.bccMail" :key="index">
                      <span>
                        {{ initAnswerData.bccName[index] }}{{ `<${mail}>` }}<template v-if="index !== initAnswerData.bccMail.length - 1">, </template>
                      </span>
                    </template>
                  </template>
                  <template v-else>
                    -
                  </template>
                </template>
                <template v-else>
                  <div class="email-input-container">
                    <div class="email-tags-wrapper" :class="{focus: isFocus.hiddenCc}">
                      <div v-for="(tagObj, index) in hiddenCcTags" :key="index" class="email-tag" :class="{error: tagObj.error}">
                        <span class="tag-name">{{ `${tagObj.name}<${tagObj.email}>` }}</span>
                        <button @click="removeEmailTag('hiddenCc', index)" class="tag-remove">
                          <i class="font-icon-close" />
                        </button>
                      </div>
                      <input
                          class="email-input"
                          v-model="hiddenCcInputValue"
                          :type="'email'"
                          @keydown="handleBackspace($event, 'hiddenCc')"
                          @keydown.enter="handleEnterKey($event, 'hiddenCc')"
                          @focus="isFocus.hiddenCc = true"
                          @focusout="handleEnterKey($event, 'hiddenCc'), isFocus.hiddenCc = false"
                      />
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </template>
        </div>
      </div>
      <div class="answer-container">
        <div class="detail-group flex title">
          <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('penpal.column.subject') }}</p>
          <div class="answer-subject right flex flex-column x-center">
            <template v-if="!isReplyEdit">
              <p>{{ initAnswerData?.subject || editDataState.subject }}</p>
            </template>
            <template v-else>
              <UiInput
                  :type="'text'"
                  :input-style="!editDataState.subject ? 'error' : ''"
                  v-model="editDataState.subject"
              />
            </template>
          </div>
        </div>
        <template v-if="isReplyEdit">
          <div class="flex flex-column gap-16 file-wrapper">
            <div class="flex y-center file-upload">
              <p class="title left be-font text-grey-sm size-13 bold flex y-center">{{ $t('writing.fileUpload') }}</p>
              <label for="file_upload" class="file-upload-btn">{{ $t('writing.fileRegister') }}</label>
              <input
                  id="file_upload"
                  ref="fileUpload"
                  :type="'file'"
                  :hidden="true"
                  multiple
                  @change="onFileChange"
              />
            </div>
            <template v-if="fileNames.length !== 0">
              <div class="file-header">
                <span class="file-header-text">{{ $t('penpal.detail.attachments') }} {{ fileNames.length }}{{ $t('penpal.detail.count') }}</span>
                <button class="delete-btn" @click="deleteFile(fileNames, 'all')">{{ $t('penpal.detail.allDelete') }}</button>
              </div>
              <template v-for="(file, index) in fileNames" :key="file.name">
                <div class="file-list">
                  <p>{{ file.filename || file.name }}</p>
                  <span>{{ bytesToMB(file.size) }} MB</span>
                  <span class="icon-wrap" @click="deleteFile(index)">
                    <i class="font-icon-close" />
                  </span>
                </div>
              </template>
            </template>
          </div>
        </template>
        <template v-else-if="initAnswerData?.attachments && initAnswerData?.attachments.length">
          <div class="detail-attachment">
            <div class="attachment-header">
              <button class="toggle-btn" :class="{close: !isAttachmentOpen}" @click="isAttachmentOpen = !isAttachmentOpen">
                <i class="font-icon-down-arrow" />
              </button>
              <span class="count">{{ $t('penpal.detail.attachments') }}
                <span>{{ initAnswerData?.attachments.length }}</span>{{ $t('penpal.detail.count') }}
              </span>
              <button class="save-btn" @click="emits('download', initAnswerData?.attachments)">{{ $t('penpal.detail.allSave') }}</button>
            </div>
            <template v-if="isAttachmentOpen">
              <div class="attachments">
                <template v-for="(file, index) in initAnswerData?.attachments" :key="index">
                  <div class="flex y-center x-between">
                    <div class="flex y-center">
<!--                      <i class="icon" :class="`icon&#45;&#45;${file.contentType?.split('/')[1]}`" />-->
                      <span class="file-name">{{ file.filename }} </span>
                      <span class="file-size">{{ bytesToMB(file.size) }}MB</span>
                    </div>
                    <button class="file-download" @click="emits('download', file)">
                      <i class="icon icon--download-black" />
                    </button>
                  </div>

                </template>
              </div>
            </template>
          </div>
        </template>
        <div class="detail-desc flex">
          <template v-if="!isReplyEdit">
            <div class="detail">
              <div v-html="answer"></div>
            </div>
          </template>
          <template v-else>
            <div class="writing-desc" @click.stop="editFocus = true">
              <CKEditor
                  v-model="answer"
                  class="board-write-block content"
                  :class="['write-tiptap', { 'error': !answer || answer.trim() === '' }]"
                  :placeholder="$t('common.content')"
                  :limit="60000"
                  :type="'post'"
                  :active="editFocus"
              />
            </div>
          </template>
        </div>
      </div>
    </div>
    <div class="detail-bottom">
      <div class="comment-container flex y-center" :class="{'edit': isReplyEdit}" ref="commentRef">
        <span class="label">{{ $t('penpal.detail.editComment') }}</span>
        <template v-if="!isReplyEdit">
          <span class="comment">{{ initAnswerData?.comment }}</span>
        </template>
        <template v-else>
          <UiInput
              :type="'text'"
              :input-style="inputError.comment || !editDataState.comment ? 'error' : ''"
              v-model="editDataState.comment"
          />
        </template>
      </div>
    </div>
  </div>

</template>

<style lang="scss" scoped>
.template {
  display: none;
}

.reference-detail-wrapper {
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;

  .monitoring-detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .back-list {
      display: flex;
      gap: 12px;
      align-items: center;
      span {
        color: $grey-400;
        font-size: 16px;
        font-weight: 700;
      }
    }

    .edit-btn-wrap {
      position: relative;
      display: flex;
      align-items: center;

      .mail-info-id {
        color: #A3A3A3;
        font-size: 12px;
        font-weight: 500;
        margin-right: 20px;
      }


      :deep(.be-btn) {
        max-width: initial;
      }
    }
  }
  .penpal-answer-container {
    border-radius: $radius-16;
    background: $whiteColor;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.16);
    padding: 28px 32px;

    .detail-wrapper {
      width: 100%;
      height: 100%;

      .detail {
        flex-wrap: wrap;

        .detail-group {
          flex: 1 1 calc(50% - 10px);

          :deep(.be-input-wrapper) {
            label {
              display: none;
            }
          }

          &.category {
            flex: 0 0 100%;

            .category-dropdown-wrapper {
              width: 50%;
              display: flex;
              align-items: center;
              gap: 12px;
            }
          }

          &.title {
            flex: 0 0 100%;
            align-items: center;

            &.email {
              align-items: flex-start;

              .left {
                padding-top: 10px;
              }
            }

            .answer-subject.right, .from-mail.right, .to-mail.right, .cc-mail.right, .hidden-cc.right {
              width: 100%;
              padding: 10px 0;

              :deep(.be-input-wrapper) {
                margin: 5px 0;
                display: initial;

                .delete-text {
                  top: 50%;
                  transform: translateY(-50%);
                }
              }
            }

            .to-mail, .cc-mail {
              word-break: break-word;
              .email-input-container {
                width: 100%;

                .email-tags-wrapper {
                  display: flex;
                  flex-wrap: wrap;
                  align-items: center;
                  gap: 4px;
                  padding: 5px;
                  border-radius: 5px;
                  border: 1px solid #BBB;
                  min-height: 38px;
                  background-color: white;
                  transition: all .3s;

                  &.error {
                    border: 1px solid $common-red;

                    &.focus {
                      border: solid 1px #289eef;
                    }
                  }

                  &.focus {
                    border: solid 1px #289eef;
                  }

                  .email-tag {
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    border-radius: 28px;
                    background: #EBEBEB;
                    padding: 7.5px 10px 7.5px 12px;
                    color: #2F2F2F;
                    font-size: 13px;
                    font-weight: 600;
                    box-sizing: border-box;
                    height: 28px;

                    &.error {
                      background-color: #FFCCD2;
                      color: #D9001D;

                      .tag-remove {
                        color: #F56C6F;
                      }
                    }

                    .tag-remove {
                      display: flex;
                      align-items: center;
                      font-size: 10px;
                      color: #888;
                    }
                  }

                  .email-input {
                    flex: 1;
                    min-width: 120px;
                    border: none;
                    outline: none;
                    color: #2F2F2F;
                    font-size: 14px;
                    font-weight: 400;

                    &::placeholder {
                      color: #999;
                    }
                  }
                }
              }
            }
          }

          .left {
            min-width: 122px;
            padding: 10px 15px;

            &.cc-label {
              justify-content: space-between;
              .icon-wrap {
                display: inline-block;
                width: 20px;
                height: 20px;
                cursor: pointer;

                &.open {
                  transform: rotate(180deg);
                }
              }
            }
          }

          .right {
            &.cc-mail {
              word-break: break-word;
              padding: 10px 0;
            }

            &.disabled {
              span {
                color: $grey-100;
              }
            }

            span {
              padding: 10px 0;

              &.penpal-status {
                padding: 3px 8px;
              }
            }


            &.disabled {
              color: $grey-100;
            }

          }
        }
      }

      .detail-author {
        display: flex;
        border-bottom: 1px solid $line-sm;

        .left {
          width: 122px;
          padding: 10px 15px;
        }

        .right {

          &.disabled {
            p {
              color: $grey-100;
            }
          }

          p {
            padding: 10px 0;
          }

          &.disabled {
            color: $grey-100;
          }
        }
      }
    }

    .answer-container {
      border-top: 1px solid $line-sm;
      padding-top: 20px;
      margin-top: 18px;

      .detail-group {
        .left {
          min-width: 122px;
          padding: 10px 15px;
        }
        .right {
          width: 100%;
          color: #2F2F2F;
          font-size: 16px;
          font-weight: 700;

          &.answer-subject {
            :deep(.be-input-wrapper) {
              .delete-text {
                top: 50%;
                transform: translateY(-30%);
              }
            }
          }
        }
      }

      .detail-attachment {
        border: 1px solid #E0E0E0;
        border-radius: 5px;
        padding: 10px 22px 15px 13px;
        max-width: 540px;
        margin-bottom: 20px;
        margin-top: 40px;

        .attachment-header {
          display: flex;
          align-items: center;
          gap: 15px;

          .toggle-btn {
            &.close {
              transform: rotate(180deg);
            }
          }

          .count {
            color: #2f2f2f;
            font-size: 13px;
            font-weight: 400;

            > span {
              font-weight: 600;
            }
          }

          .save-btn {
            margin-left: 13px;
            color: #777;
            font-size: 12px;
            font-weight: 400;
            position: relative;

            &::before {
              content: '';
              position: absolute;
              top: 50%;
              left: -13px;
              transform: translateY(-50%);
              width: 1px;
              height: 8px;
              background: #D9D9D9;
            }
          }
        }

        .attachments {
          margin-top: 15px;
          height: 100%;
          display: flex;
          flex-direction: column;
          gap: 8px;

          .file-name {
            margin-left: 14px;
            color: #2F2F2F;
            font-size: 13px;
            font-weight: 400;
          }

          .file-size {
            color: #909090;
            font-size: 12px;
            font-weight: 400;
            margin-left: 6px;
          }
        }
      }

      .file-wrapper {
        width: 100%;
        padding: 4px 0;
        .file-upload {
          padding: 12px 0 ;
          .title {
            min-width: 122px;
            padding: 10px 15px;
          }
        }

        .file-header {
          margin-left: 122px;

          .file-header-text {
            margin-right: 10px;
          }

          .delete-btn {
            margin-left: 10px;
            position: relative;
            &:before {
              content: '';
              display: block;
              width: 1px;
              height: 10px;
              background-color: $line-sm;
              position: absolute;
              top: 50%;
              left: -10px;
              transform: translateY(-50%);
            }
          }
        }

        .file-list {
          margin-left: 107px;
          width: calc(100% - 450px);
          padding-left: 15px;
          display: grid;
          grid-template-columns: 1fr auto auto;
          justify-content: space-between;
          gap: 10px; /* 아이템 간 간격 */
          justify-items: start;
          align-content: center;


          p {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }

          .icon-wrap {
            display: flex;
            align-items: center;
            justify-items: center;
            width: 16px;
            height: 16px;
            cursor: pointer;
          }
        }

        .file-upload-btn {
          color: $whiteColor;
          background-color: $mainColor;
          border-radius: 5px;
          padding: 11px;
          text-align: center;
          font-size: $font-14;
          font-weight: $bold;
          min-width: 73px;
          max-width: 118px;
          transition: all .3s;
          line-height: 1;
          cursor: pointer;
        }
      }

      .detail-desc {
        margin-top: 40px;
        .detail-desc-title {
          width: 122px;
          padding: 16px 15px;
        }

        .detail {
          white-space: normal;
          word-break: keep-all;
          flex: 1;
          width: 100%;
          min-height: 200px;
          max-height: 800px;
          padding: 16px 0;
          border: none;
          resize: none;
          overflow-y: scroll;

          &:focus {
            outline: none;
          }


          .files {
            margin-bottom: 12px;
          }
        }

        .writing-desc {
          margin-top: 16px;
          width: 100%;
          height: 800px;

          :deep(.write-tiptap.error) {
            .ck.ck-editor {
              .ck-editor__main {
                .ck-editor__editable:not(.ck-focused) {
                  border: 1px solid $common-red;
                }
              }
            }
          }

        }
      }
    }
  }

  .detail-bottom {
    padding: 0 28px;
    .comment-container {
      padding-top: 24px;
      padding-bottom: 21px;
      gap: 32px;
      border-bottom: 1px solid $line-sm;

      &.edit {
        gap: 20px;
        border-bottom: none;

        span {
          min-width: 60px;
        }

        :deep(.be-input-wrapper) {
          width: calc(100% - 90px);
        }
      }

      span {
        color: #2F2F2F;
        font-size: 13px;
        font-weight: 400;

        &.label {
          padding-left: 4px;
        }
      }

      :deep(.be-input-wrapper) {
        .delete-text {
          top: 50%;
          transform: translateY(-30%);
        }
      }
    }
  }

}



</style>
