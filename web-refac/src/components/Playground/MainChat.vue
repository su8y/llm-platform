<script setup>
import { defineProps, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AppLogo from "@/components/AppLogo.vue";

import { chatbotAskQuestion, getChatbotConversationHistory, abortRendering } from '@/api/chatbot.js'
import { HTTP_CODES } from "@/libs/constants.js";

import ChatBody from "@/components/Playground/ChatBody.vue";

const emits = defineEmits(['isOffChatbot'])

const props = defineProps({
  chatbotKey: Object
})

const { locale } = useI18n()

const messages = ref([])
const isLoading = ref(false)
const isAnswering = ref(false)
const askDisabled = ref(false)
const lastAiIndex = ref()
const isReference = ref(false)
const userData = ref(null)
const question = ref(null)

const startConnecting = async () => {
  const params = {
    chatbotKey: props.chatbotKey.chatbotKey
  }
  try {
    const res = await getChatbotConversationHistory(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      const messages = res.data
      if (messages.length > 0) {
        setHistoryMessages(messages)
      }
    } else {
      alert(res.message)
      console.log('Error: ', res)
    }
  } catch (e) {
    console.log('Connect Error', e)
  }
}

const handleSubmitQuestion = async (questionData) => {
  const params = {
    question: questionData.prompt,
    chatbotKey: props.chatbotKey.chatbotKey,
    lang: locale.value
  }

  insertMessage('human', questionData.prompt)
  insertMessage('ai', '')
  question.value = questionData.prompt

  isLoading.value = true

  chatbotAskQuestion(params, startAnswering, onAnswering, endAnswering)
}

const insertMessage = (role, message) => {
  if (role === 'ai') {
    lastAiIndex.value = 0
  } else {
    lastAiIndex.value += 1
  }
  messages.value.unshift({ role, message })
}

const startAnswering = () => {
  isLoading.value = false
  isAnswering.value = true
}

const onAnswering = (chunk) => {
  messages.value[lastAiIndex.value].message += chunk
}

const endAnswering = (id) => {
  isLoading.value = false
  isAnswering.value = false
  if (messages.value[lastAiIndex.value].role === 'ai') {
    messages.value[lastAiIndex.value].id = id
  }
}

const stopAnswering = () => {
  isAnswering.value = false
  abortRendering()
}

const setHistoryMessages = (prevMessages) => {
  const reversedMessages = prevMessages.reverse()
  messages.value = [...messages.value, ...reversedMessages]
}

startConnecting()

</script>

<template>
  <div class="chatbot-wrapper">
    <div class="chatbot-header-wrapper">
      <div class="chatbot-header-logo">
        <span class="knit-logo">
          <AppLogo />
        </span>
        <span class="chatbot-header-desc">
          Where Knowledge Connects
        </span>
      </div>
      <div class="chatbot-close-btn" @click="emits('isOffChatbot', false)">
        <span class="be-icon icon-white size-60">
          <i class="font-icon-close-slim" />
        </span>
      </div>
    </div>
    <div class="main-chat-wrapper">
      <ChatBody
          :messages="messages"
          :is-loading="isLoading"
          :is-answering="isAnswering"
          :disabled="askDisabled"
          :onSubmitQuestion="handleSubmitQuestion"
          :stop="stopAnswering"
          :is-reference="isReference"
          :user-data="userData"
          :is-main="true"
      />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.chatbot-wrapper {
  padding: 18px 0;
  position: relative;
  background-color: rgba(0, 0, 0, .5);

  .chatbot-header-wrapper {
    width: 100%;
    min-height: 211px;
    position: absolute;
    top: 29px;
    z-index: 1;
    background: linear-gradient(180deg, #000 79.77%, rgba(255, 255, 255, 0) 100%);

    .chatbot-header-logo {
      display: flex;
      flex-direction: column;
      position: relative;
      left: 52px;

      .knit-logo {
        display: block;
        margin-bottom: 16px;
        .app-logo {
          color: #FFF;
          font-size: 36px;
        }
      }
      .chatbot-header-desc {
        color: #FFF;
        font-size: 52px;
        font-weight: 800;
        line-height: 100%;
      }
    }
    .chatbot-close-btn {
      position: absolute;
      top: 0px;
      right: 24px;
    }
  }

  .main-chat-wrapper {
    margin-top: 200px;
    height: 100%;
    max-height: calc(100dvh - 240px);
    margin-right: 6px;
  }
}
</style>
