<script setup>
import {ref, computed, watch, onMounted} from 'vue'
import { useStore } from 'vuex'
import { useElementSize } from "@vueuse/core"

import { updateRating } from "@/api/playground.js";

import AskContainer from './AskContainer.vue'
import MessageContainer from './MessageContainer.vue'

const store = useStore()
const emits = defineEmits(['newSession'])
const props = defineProps({
  messages: Array,
  isLoading: Boolean,
  isAnswering: Boolean,
  disabled: Boolean,
  onSubmitQuestion: Function,
  stop: Function,
  isReference: Boolean,
  userData: Object,
  isMain: Boolean,
  isHighlight: Boolean,
  highlightId: String,
  highlightIndexes: Array,
  greeting: String
})


const scroller = ref(null)
const wrapRef = ref(null)
const isOver = ref(false)
const askWrapper = ref(null)

const isMobile = computed(() => {
  return store.state.isMobile
})

const aksHeight = computed(() => {
  if (askWrapper.value) {
    const { height } = useElementSize(askWrapper.value)
    return height.value || 0
  }
  return 0
})


watch(() => props.isAnswering, () => {
  checkOver()
})

onMounted(() => {
  const messageContainer = document.querySelectorAll('.message-container')
  isOver.value = window.innerHeight <  document.querySelectorAll('.message-container')[0].clientHeight
})

const getWelcomeMessage = () => {
  return {
    role: 'ai',
    type: 'welcome',
    message: props.greeting,
  }
}

const checkLoadingComponents = (index) => {
  if (!props.isLoading) return
  isOver.value = wrapRef.value?.clientHeight < scroller.value.scrollHeight

  return index === 0
}

const onMessageRating = async (rating, id) => {
  const param = {
    id: id,
    rating: rating
  }

  try {
    await updateRating(param).then(res => {
      console.log(res)
    })
  } catch (e) {
    console.error(e)
  }
}

const newSessionEmit = () => {
  emits('newSession')
}

const checkOver = () => {
  if (isMobile.value) {
    setTimeout(() => {
      isOver.value = wrapRef.value.clientHeight < scroller.value.scrollHeight
    }, 0)
  }
}

</script>

<template>
  <template v-if="!isMain">
    <div class="chat-body" :class="{ 'is-not-reference': !isReference, isMobile }" ref="wrapRef">
      <UiButton v-if="!isMobile" class="new-chat-btn" :type="'icon outline primary shadow'"
                @click.stop="newSessionEmit">
        {{ $t('playground.reset') }}
        <span class="be-icon size-24 icon-primary">
          <i class="font-icon-refresh"/>
        </span>
      </UiButton>
      <div class="chat-body-container" :class="{over: isOver}" :style="{paddingBottom: `${aksHeight}px`}">
        <div ref="scroller" class="chat-body-wrapper" :class="{chatStart: messages.length !== 0}">
          <template v-for="(item, index) in messages" v-bind:key="item.id">
            <MessageContainer
                :message="item"
                :message-index="index"
                :is-loading-item="checkLoadingComponents(index)"
                :user-data="userData"
                :is-highlight="isHighlight"
                :highlight-id="highlightId"
                :highlight-indexes="highlightIndexes"
                @onMessageRating="onMessageRating"
                @isOver="isOver = true"
            />
          </template>
          <MessageContainer class="intro" :message="getWelcomeMessage()"/>
        </div>
      </div>
      <div class="ask-wrapper" ref="askWrapper">
        <AskContainer
            :is-loading="isLoading"
            :is-answering="isAnswering"
            :disabled="disabled"
            :onSubmitQuestion="onSubmitQuestion"
            :stop="stop"
            :is-over="isOver"
        />
      </div>
    </div>
  </template>
  <template v-else>
    <div class="main-chat-body">
      <div ref="scroller" class="main-chat-body-wrapper">
        <template v-for="(item, index) in messages" :key="item.id">
          <div>
            <MessageContainer
                :message="item"
                :message-index="index"
                :is-loading-item="checkLoadingComponents(index)"
                :user-data="userData"
                :is-main="isMain"
                @onMessageRating="onMessageRating"
            />
          </div>
        </template>
        <MessageContainer :is-main="isMain" :message="getWelcomeMessage()" :is-welcome-message="true"/>
      </div>
      <div class="main-ask-wrapper">
        <AskContainer
            :is-loading="isLoading"
            :is-answering="isAnswering"
            :disabled="disabled"
            :onSubmitQuestion="onSubmitQuestion"
            :stop="stop"
            :is-main="isMain"
        />
      </div>
    </div>
  </template>
</template>

<style lang="scss" scoped>
.chat-body {
  width: 72%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border-right: 1px solid #c3c3c3;
  overflow: hidden;
  position: relative;
  transition: all .3s;
  padding-top: 43px;

  &.isMobile {
    border-right: none;
  }

  &.is-not-reference {
    width: 100%;
  }

  .new-chat-btn {
    position: absolute;
    top: 19px;
    right: 40px;
    z-index: 2;
    box-sizing: border-box;
    transition: all .3s;

    > span.be-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      transform: rotate(-90deg) scaleX(-1);
    }

    &:hover {
      span {
        color: $whiteColor;
      }
    }
  }
}
.chat-body-container {
  max-height: 100%;
  padding-bottom: 103px;
}
.chat-body-wrapper {
  display: flex;
  flex-direction: column-reverse;
  overflow-y: auto;
  height: 100%;
}

@media all and (min-width: 1441px) {
  .chat-body-container {
    overflow-y: auto;

    .chat-body-wrapper {
      margin: 0 auto;
      max-width: 1077px;
      overflow-y: initial;
      height: initial;
    }
  }
}

.ask-wrapper {
  position: absolute;
  width: 100%;
  bottom: 0;
  background: linear-gradient(360deg, $backgroundColor 89.77%, rgba(255, 255, 255, 0) 100%);
  z-index: 2;
}

.auto-scroll-button {
  position: absolute;
  bottom: 40px;
  right: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 35px;
  height: 35px;
  background: #fff;
  border-radius: 100%;
  box-shadow: 0 0 2px 1.5px rgba(0, 0, 0, 0.16);
  cursor: pointer;

  .icon {
    background-size: 20px;
    opacity: 0.7;
  }
}

// main chatbot css
.main-chat-body {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
  position: relative;
  transition: all .3s;

  .main-chat-body-wrapper {
    width: 100%;
    display: flex;
    flex-direction: column-reverse;
    margin-bottom: 60px;
    overflow-y: auto;
    box-sizing: border-box;

    // 스크롤 바 커스텀 - WebKit 기반 브라우저 (Chrome, Edge, Opera, Safari, ios)
    &::-webkit-scrollbar {
      width: 8px;
    }

    &::-webkit-scrollbar-thumb {
      height: 30%;
      background: #767676;
      border-radius: 10px;
      margin-right: 8px;
    }

    &::-webkit-scrollbar-track {
      background: none;
    }
  }

  .main-ask-wrapper {
    width: 100%;
    padding-left: 48px;
    padding-right: 68px;
    position: absolute;
    bottom: 0;
    background: linear-gradient(360deg, #000 69.77%, rgba(255, 255, 255, 0) 100%);
  }
}

.mobile {
  .chat-body {
    width: 100%;
    padding-top: 0px;
    .chat-body-container {
      padding-top: 12px;
      padding-bottom: 75px;
      &::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 12px;
          background: linear-gradient(0, rgba(255, 255, 255, 0.00) 0%, rgba(0, 0, 0, 0.06) 100%);
          z-index: 100;
        }
      &.over {

        &::after {
          content: '';
          position: absolute;
          bottom: 56px;
          left: 0;
          width: 100%;
          height: 12px;
          background: linear-gradient(180deg, rgba(0, 0, 0, 0.00) 0%, #fff 100%);
          z-index: 100;
        }
      }
      .chat-body-wrapper {
        height: 100%;
      }
    }
  }
}
// @media all and (max-width: 768px) {
// }
</style>
