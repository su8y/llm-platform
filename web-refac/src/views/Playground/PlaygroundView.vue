<script setup>
import { ref, computed, getCurrentInstance, onBeforeMount } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { getGreeting } from "@/api/prompt.js";
import { askQuestion, abortRendering, getHistory, newChat, getChatTitle } from '@/api/playground.js'
import { setAuthToken } from "@/libs/auth-helper.js";
import {HTTP_CODES, USE_MCP_ID_LIST} from "@/libs/constants.js";

import ChatBody from '@/components/Playground/ChatBody.vue'
import ReferenceContainer from '@/components/Playground/ReferenceContainer.vue'

import MobileHeader from "@/components/MobileHeader.vue";
import MobileHistoryDetail from '@/components/Reports/MobileHistoryDetail.vue'

const store = useStore()
const router = useRouter()
const route = useRoute()
const app = getCurrentInstance()
const bus = app?.appContext.config.globalProperties.emitter
const { t, locale } = useI18n()

const messages = ref([])
const isLoading = ref(false)
const isAnswering = ref(false)
const askDisabled = ref(false)
const lastAiIndex = ref()
const isReference = ref(false)
const userData = ref(null)
const question = ref(null)
const messageId = ref(null)
const messageRef = ref(null)
const isHighlight = ref(false)
const highlightId = ref(null)
const highlightIndex = ref(null)
const highlightIndexes = ref(null)
const greeting = ref(null)
const creditData = ref(null)
const creditUpdateInterval = ref(null)
const isAdmin = ref(false)

onBeforeMount(async () => {
  try {
    userData.value = await store.dispatch('storeUserData');
    isAdmin.value = route.name === 'MCP' && USE_MCP_ID_LIST.includes(userData.value.userId)

    await startConnecting()
  } catch (error) {
    console.error(`${t('common.error.user')}: ${error}`);
    alert(t('common.error.error'));
    router.push('/');
  }
});

const isMobile = computed(() =>  store.state.isMobile)

const updateCredit = async (isInterval = false) => {
  const credit = await store.state.creditData
  creditData.value  = await store.dispatch('storeCreditData', {
    currentCredit: isInterval ? credit.data.useAbleCredit : null
  })

  if (creditData.value.code === HTTP_CODES.SUCCESS) {
    if (creditUpdateInterval.value) {
      clearInterval(creditUpdateInterval.value)
      creditUpdateInterval.value = null
    }
  }

}

const startConnecting = async () => {
  try {

    const params = {}

    if (isAdmin.value) {
      params.params = {
        isMCP: 1
      }
    }

    const res = await getHistory(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      const messages = res.data
      if (messages.length > 0) {
        setHistoryMessages(messages)
      }
    } else {
      alert(res)
      console.log(res)
    }
  } catch (e) {
    console.log('Connect Error', e)
  }
}

const handleSubmitQuestion = async (questionData) => {
  const params = {
    question: questionData.prompt,
    info: {
      asker_id: userData.value.userId
    },
    isMCP: isAdmin.value,
    lang: locale.value
  }

  insertMessage('human', questionData.prompt)
  insertMessage('ai', '')
  question.value = questionData.prompt

  if (userData.value?.creditAvailable === 0 || !userData.value?.creditAvailable) store.commit('setPlanAlert', true)

  isLoading.value = true

  await askQuestion(params, startAnswering, onAnswering, endAnswering)
}

const getChatTitleData = async () => {
  try {
    const res = await getChatTitle()

  } catch (e) {
    console.error(`Error ${e}`)
  }
}

const insertMessage = (role, message) => {
  if (role === 'ai') {
    lastAiIndex.value = 0
  } else {
    lastAiIndex.value += 1
  }
  messages.value.unshift({ role, message })
}

const startAnswering = async () => {
  isLoading.value = false
  isAnswering.value = true

  await updateCredit()
}

const onAnswering = (chunk) => {
  messages.value[lastAiIndex.value].message += chunk
}

const endAnswering = async (id, isInterval = false) => {
  isLoading.value = false
  isAnswering.value = false
  if (messages.value[lastAiIndex.value].role === 'ai') {
    messages.value[lastAiIndex.value].id = id
  }

  if (isInterval) {
    await updateCredit(true)

    if (creditData.value.code === 9004) {
      creditUpdateInterval.value = setInterval(() => {
        updateCredit(true)
      }, 3000)
    }
  }

  getChatTitleData()
}

const stopAnswering = () => {
  isAnswering.value = false
  messages.value[lastAiIndex.value].message = t('playground.askStop')
  abortRendering()
}

const setHistoryMessages = (prevMessages) => {
  const reversedMessages = prevMessages.reverse()
  messages.value = [...messages.value, ...reversedMessages]
}

const newSession = async () => {
  try {
    const res = await newChat()

    if (res.code === HTTP_CODES.SUCCESS) {
      messages.value = []
      setAuthToken(res.data)
      selectedHistory.value = null
    } else {
      alert(res.message)
      console.log(res)
    }
  } catch (e) {
    console.error(e)
    alert(e.response.data.message)
  }
}

const elementHighlight = (isShow, id) => {
  isHighlight.value = isShow
  highlightId.value = id
  highlightIndexes.value = [highlightIndex.value, highlightIndex.value + 1]

  setTimeout(() => {
    isHighlight.value = false
  }, 3000)
}

const getGreetingData = async () => {
  try {
    const res = await getGreeting()

    if (res.code === HTTP_CODES.SUCCESS) {
      greeting.value = res.data || t('playground.defaultGreeting')
    } else {
      alert(res.message)
      console.log('Error: ', res)
    }
  } catch (e) {
    console.log('Error: ', e)
  }
}


bus.on('onReferenceData', (params) => {
  if (params.isShow) {
    isReference.value = true
    messageRef.value = params.element
    highlightIndex.value = params.index
  } else {
    isReference.value = false
  }
})

bus.on('getReferenceData', (id) => {
  messageId.value = id
})

getGreetingData()

const selectedHistory = ref(null)
const selectHistory = (payload) => {
  selectedHistory.value = payload
}
</script>

<template>
  <template v-if="isMobile">
    <MobileHeader :user-data="userData" @new-chat="newSession" @select="selectHistory"/>
  </template>
  <template v-if="isMobile && selectedHistory">
    <MobileHistoryDetail :id="selectedHistory" @new-chat="newSession" />
  </template>
  <template v-else>
    <div class="chat-container flex flex-column gap-8 border-box">
      <div class="chat-section-layout flex">
        <ChatBody
            :messages="messages"
            :is-loading="isLoading"
            :is-answering="isAnswering"
            :disabled="askDisabled"
            :onSubmitQuestion="handleSubmitQuestion"
            :stop="stopAnswering"
            :is-reference="isReference"
            :user-data="userData"
            :is-highlight="isHighlight"
            :highlight-id="highlightId"
            :highlight-indexes="highlightIndexes"
            :greeting="greeting"
            @newSession="newSession"
        />
        <template v-if="!isMobile">
          <ReferenceContainer
              :is-reference="isReference"
              :message-id="messageId"
              :question="question"
              :message-ref="messageRef"
              @elementHighlight="elementHighlight"
          />
        </template>
      </div>
    </div>
  </template>
</template>

<style lang="scss">
.chat-container {
  overflow: hidden;

  .chat-section-layout {
    height: calc(100dvh - 58px);
    position: relative;
  }
}


.mobile {
  .chat-container {
    .chat-section-layout {
      height: calc(100dvh - 56px);
    }
    .message-container:not(.intro) {
      .message-wrapper.isAssistant {
        .message-profile {
          display: none;
        }
      }
    }
    .reference-container {
      position: absolute;
      width: 85%;
      right: 0;
      z-index: 9999;
      transition: margin 250ms, opacity 250ms;
      &.isReference {
        margin-right: -100%;
        opacity: 0;
      }
    }
  }
}
// @media all and (max-width: 768px) {
// }
</style>
