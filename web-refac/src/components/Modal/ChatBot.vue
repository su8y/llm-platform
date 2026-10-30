<script setup>
import { computed, inject, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useStore } from "vuex";
import { useI18n } from "vue-i18n";
import { useElementSize } from "@vueuse/core"
import AppLogo from "@/components/AppLogo.vue";

import { abortRendering, chatbotAskQuestion } from "@/api/chatbot.js";

import { useChatbotSessionKey } from "@/composables/useChatbotSessionKey.js";

import ChatSideBar from "@/components/ChatBot/ChatSideBar.vue";
import ChartHeader from "@/components/ChatBot/ChatHeader.vue";
import AskContainer from "@/components/Playground/AskContainer.vue";
import MessageContainer from "@/components/Playground/MessageContainer.vue";



const modal = inject('$modal')
const content = inject('modalContent')
const { t, locale } = useI18n()
const store = useStore()
const isMobile = computed(() => store.state.isMobile)
const chatbotRef = ref(null)
const fullScreenMode = ref(false)
const showSideTab = ref(true)
const messages = ref([])
const isLoading = ref(false)
const isAnswering = ref(false)
const lastAiIndex = ref()
const question = ref(null)
const scroller = ref(null)
const askWrapper = ref(null)

const { getChatbotSessionKey } = useChatbotSessionKey()


const aksHeight = computed(() => {
  if (askWrapper.value) {
    const { height } = useElementSize(askWrapper.value)
    return height.value - 72 || 0
  }
  return 0
})

const resetChat = async () => {
  messages.value = []
  isLoading.value = false
  isAnswering.value = false
  await getChatbotSessionKey(false)
}

const handleSubmitQuestion = async (questionData) => {
  const params = {
    question: questionData.prompt,
    chatbotKey: content.value.content.chatbotKey,
    lang: locale.value
  }
  insertMessage('human', questionData.prompt)
  insertMessage('ai', '')
  question.value = questionData.prompt
  isLoading.value = true

  await chatbotAskQuestion(params, startAnswering, onAnswering, endAnswering)
}

const stopAnswering = () => {
  isAnswering.value = false
  abortRendering()
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
  if (messages.value[lastAiIndex.value]?.role === 'ai') {
    messages.value[lastAiIndex.value].id = id
  }
}

const getWelcomeMessage = () => {
  return {
    role: 'ai',
    type: 'welcome'
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

const checkLoadingComponents = (index) => {
  if (!isLoading.value) return

  return index === 0
}

const handleChatPopup = (mode) => {
  fullScreenMode.value = mode;
  const parent = chatbotRef.value?.parentElement;
  fullScreenMode.value ? parent.classList.add('full-screen') : parent.classList.remove('full-screen')
}

const closeChatPopup = () => {
  modal.close()
}

const getPausePosition = () => {
  const containerRect = chatbotRef.value.getBoundingClientRect()
  const messageRect = chatbotRef.value?.querySelector('.chat-bot-content').getBoundingClientRect()
  const stopButton = chatbotRef.value?.querySelector('.pause')

  if(!containerRect || !messageRect || !stopButton) return
  const offsetRight = containerRect.right - messageRect.right

  stopButton.style.right = `${offsetRight}px`
}

watch(
    () => [isLoading.value, isAnswering.value],
    async (newValue) => {
      const [loadingValue, answeringValue] = newValue
      if (loadingValue || answeringValue) {
        await nextTick()
        getPausePosition()
      }
    }
)

const resizeObserver = new ResizeObserver(() => {
  getPausePosition()
})

onMounted(async () => {
  window.addEventListener('resize', getPausePosition)
  const parent = chatbotRef.value?.parentElement
  parent.classList.add('chat-bot-modal')

  if (chatbotRef.value?.querySelector('.chat-bot-content')) {
    resizeObserver.observe(chatbotRef.value?.querySelector('.chat-bot-content'))
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', getPausePosition)
  resizeObserver.disconnect()
})
</script>

<template>
<div class="chat-bot-container" ref="chatbotRef">
  <ChartHeader @expand="handleChatPopup" @close="closeChatPopup"/>
  <div class="chat-bot-body" :class="{ 'side-tab-open': showSideTab }">
    <div class="chat-bot-content" :style="{marginBottom: `${aksHeight}px`}">
      <div class="chat-bot-scroll">
        <div ref="scroller" class="chat-bot-wrapper" :class="{chatStart: messages.length !== 0}">
          <template v-for="(item, index) in messages" v-bind:key="item.id">
            <MessageContainer
                :isFullScreen="fullScreenMode"
                :isSideBar="showSideTab"
                :is-main="true"
                :message="item"
                :message-index="index"
                :is-loading-item="checkLoadingComponents(index)"
            />
          </template>
          <MessageContainer :isFullScreen="fullScreenMode" :isSideBar="showSideTab" class="intro" :message="getWelcomeMessage()" :is-main="true" />
          <div class="message-list-header">
            <div class="list-header-inner">
              <div class="intro-text">
                <AppLogo />
                <p class="description">Where knowledge connects</p>
              </div>
              <i v-if="!isMobile" class="icon icon--chat-bot"></i>
            </div>
          </div>
        </div>
      </div>
      <div class="button-wrapper" v-if="!isMobile">
        <button v-if="!showSideTab" class="guide-button" @click="showSideTab = true">
          <span>{{ t('chatBot.questionGuide') }}</span>
        </button>
        <button v-if="messages.length" class="reset-button" @click="resetChat">
          <span>{{ t('chatBot.reset') }}</span>
          <i class="icon icon--reset-red"></i>
        </button>
      </div>
    </div>
    <Transition name="slide-width" v-if="!isMobile">
      <ChatSideBar @close="showSideTab = false" v-if="showSideTab" @submitQuestion="handleSubmitQuestion"/>
    </Transition>
  </div>
  <AskContainer
      :is-main="true"
      :is-answering="isAnswering"
      :is-loading="isLoading"
      :is-bot-disabled="isAnswering||isLoading"
      :onSubmitQuestion="handleSubmitQuestion"
      :stop="stopAnswering"
      ref="askWrapper"
  />
</div>
</template>

<style scoped lang="scss">
.slide-width-enter-active,
.slide-width-leave-active {
  transition: flex 0.3s ease-in-out;
  overflow: hidden;
}

.slide-width-enter-from,
.slide-width-leave-to {
  flex: 0;
}

.slide-width-enter-to,
.slide-width-leave-from {
  flex:0 0 384px
}

.chat-bot {
  &-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 16px;
    //padding-bottom: 45px;
  }
  &-wrapper {
    display: flex;
    flex-direction: column-reverse;
    justify-content: flex-end;
  }
  &-body {
    position: relative;
    display: flex;
    height: 100%;
    width: 100%;
    border: 1px solid #C3C3C3;
    border-radius: 6px;
    filter: drop-shadow(0px 3px 6px rgba(0, 0, 0, 0.12));
    background-color: #ECECEC;
    box-sizing: border-box;
    overflow: hidden;

    &:deep {
      .ask-wrapper {
        position: absolute;
        width:100%;
        bottom:0;
        right: 0;
      }
    }
  }

  &-content {
    flex: auto;
    width: calc(100% - 384px);
    position: relative;
    .button-wrapper {
      position: absolute;
      top: 20px;
      right: 25px;
      display: flex;
      gap: 10px;
      z-index: 1;
      button {
        display: flex;
        align-items: center;
        gap: 8px;
        border-radius: 5px;
        font-size: 14px;
        font-weight: 600;
        line-height: 1;
      }
      .guide-button {
        background-color: #EC0047;
        color: #fff;
        padding: 12px 14px 12px 12px;
      }
      .reset-button {
        padding: 11px 12px;
        background-color: #fff;
        box-shadow: 0px 1px 2px 0px rgba(0, 0, 0, 0.25);
        color: $mainColor;
      }
    }

  }
  &-scroll {
    overflow: auto;
    max-height: calc(100% - 72px);
    display: flex;
    flex-direction: column-reverse;
    &::-webkit-scrollbar {
      width: 22px;
    }

    &::-webkit-scrollbar-thumb {
      height: 30%;
      background: #C3C3C3;
      border-radius: 16px;
      border: 7px solid #ECECEC;
    }

    &::-webkit-scrollbar-track {
      background: none;
    }
  }
}

.message-list-header {
  padding: 21px 40px 28px;
  .list-header-inner {
    display: flex;
    gap: 14px;
    align-items: flex-end;
    border-bottom: 1px solid #BDBDBD;
    padding-bottom: 27px;
  }
  .intro-text {
    position: relative;
    .app-logo {
      display: block;
      font-size: 32px;
      color: $mainColor;
      margin-bottom: 10px;
    }
    .description {
      color: $n-gray-600;
      font-size: 26px;
      font-weight: $semiBold;
      line-height: 1;
    }
  }
}

@media all and (max-width: 768px) {
  .chat-bot-container {

    &:deep {
      //.button-container, .icon--chat-bot, .guide-button{
      //  display: none;
      //}

      .message-list-header {
        padding: 25px 0 20px;
        margin: 0 20px 4px;
      }

      .message-container {
        &:not(.intro) {
          .message-wrapper {
            &.isAssistant {
              .message-profile {
                display: none;
              }
            }
          }
        }
        .message-wrapper {
          &:not(.isAssistant) {
            .message-detail {
              .message-text-container {
                margin: 0;

                .message-text {
                  font-size: 14px;
                }
              }
            }
          }
        }
      }

      .ask-wrapper {
        height: 56px;
        width: 100%;
        border-radius: 0;

        .textarea-wrapper {
          .ask-input {
            width: 100%;
            height: 23px;
            border: none;
            outline: none;
            background: none;
            font-size: 16px;
            line-height: 150%;
            resize: none;
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
            color: $whiteColor;

          }
        }
      }
    }
  }

}
</style>
