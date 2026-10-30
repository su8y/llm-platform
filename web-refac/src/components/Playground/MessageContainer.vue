<script setup>
import { MCP_TITLE } from '@/libs/constants.js'
import {computed, getCurrentInstance, onMounted, ref} from 'vue'
import { useI18n } from "vue-i18n";
import { useStore } from 'vuex';

import { convertMarkdownToHtml } from '@/libs/parse'
import { updateComment } from "@/api/playground.js";
import {useRoute} from "vue-router";

const app = getCurrentInstance()
const bus = app?.appContext.config.globalProperties.emitter
const { t } = useI18n()
const store = useStore()
const route = useRoute()

const emits = defineEmits(['onMessageRating', 'isOver'])
const props = defineProps({
  message: Object,
  isLoadingItem: Boolean,
  messageIndex: Number,
  userData: Object,
  isMain: Boolean,
  isHighlight: Boolean,
  highlightId: String,
  highlightIndexes: Array,
  isSideBar: Boolean,
  isFullScreen: Boolean,
  isOrganization: Boolean
})

const ratingValues = ref([1, 2, 3, 4, 5])
const currentRating = ref(0)
const ratingHover = ref(null)
const hoverIndex = ref(null)
const comment = ref(props.message.comment || null)
const textarea = ref(null)
const messageContainer = ref(null)

const isMobile = computed(() => {
  return store.state.isMobile
})

onMounted(() => {
  if (!messageContainer.value.classList.contains('intro')) {
    emits('isOver', true)
  }
})

const isAssistantMessage = () => {
  return props.message.role === 'ai'
}

const author = computed(() => {
  if (isAssistantMessage()) {
    return MCP_TITLE
  } else {
    return t('playground.me')
  }
})

const copy = () => {
  navigator.clipboard.writeText(props.message.message).then(() => alert(t('common.copy')))
}

const selectRating = (value, type) => {
  if (type === 'click') {
    currentRating.value = value
    emits('onMessageRating', currentRating.value, props.message.id)
  } else {
    ratingHover.value = value
  }
}

const onReferenceTooltip = (index) => {
  if (isAssistantMessage() && index !== undefined) {
    hoverIndex.value = index
  }
}

const toggleReference = (id, index) => {
  getReferenceData(id)
  bus.emit('onReferenceData', {isShow: true, element:  messageContainer.value, index: index})
}

const getReferenceData = (id) => {
  bus.emit('getReferenceData', id)
}

const handleResizeTextArea = () => {
  if (textarea.value.scrollHeight > 79) return
  textarea.value.style.height = 'auto'
  textarea.value.style.height = textarea.value.scrollHeight + 'px'
  textarea.value.style.lineHeight = '130%'
}

const saveComment = async (id) => {
  const params = {
    id: id,
    comment: comment.value
  }

  try {
    await updateComment(params).then(res => {
      if (res.code === 200) {
        comment.value = res.data.comment
      } else{
        alert(res.message)
      }
    })
  } catch (e) {
    console.log(e)
  }
}

const convertHtml = (content) => {
  const html = convertMarkdownToHtml(content)
  const dom = document.createElement('div')
  dom.innerHTML = html
  const aTags = dom.querySelectorAll('a')

  if (aTags.length) {
    for (let i = 0; i < aTags.length; i++) {
      if (!aTags[i].href.includes('mailto')) {
        aTags[i].setAttribute('target', '_blank')
      }
      aTags[i].style.color = '#0074FF'
    }
  }

  return dom.innerHTML
}

const getGreetingMsg = computed(() => {
  if (props.isOrganization) {
    return '도정 각 분야의 정책 및 사업 관련 내용을 질문해주세요.'
  } else if (props.isMain) {
    return t('chatBot.greetingMsg')
  } else {
    return props.message.message
  }
})
</script>

<template>
  <div :class="['message-container', {isMain}, {isOrganization} , {'side-open' : isSideBar}, {'full-screen' : isFullScreen}]" ref="messageContainer">
    <div class="flex y-start row-reverse" :class="['message-wrapper', message.type, {isAssistant: isAssistantMessage(), isMobile: isMobile, isMain}]">
      <template v-if="!isMobile">
        <div class="message-profile">
          <template v-if="isAssistantMessage()">
            <span>
              <i class="icon icon--ai-assistant"/>
            </span>
          </template>
          <template v-else>
            <span class="user-profile be-font size-22 text-white bold">
              {{ isMain
                ? 'C'
                : userData && userData.userId.charAt(0).toUpperCase()
              }}
            </span>
          </template>
        </div>
      </template>
      <template v-else>
        <template v-if="isAssistantMessage()">
          <div class="message-profile">
            <span>
              <i class="icon icon--ai-assistant"/>
            </span>
            <p class="message-author">{{ author }}</p>
          </div>
        </template>
      </template>
      <div class="message-detail flex flex-column" :class="[author === '나' ? 'y-end' : 'y-start',{ isHuman : !isAssistantMessage() }]">
        <template v-if="!isMobile && !isAssistantMessage()">
          <p class="message-author" v-if="!isOrganization && !isMain">{{ author }}</p>
          <svg class="chat-arrow" :class="{'highlight': isHighlight && highlightIndexes&& highlightIndexes.includes(messageIndex)}" width="37" height="25" viewBox="0 0 37 25" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path id="Vector 215" d="M0 0H36.5C31 9.63422 17 31.7929 17 21.677C17 3.01069 4.5 1.20428 0 0Z" :fill="isAssistantMessage() ? 'white' : isMain ? '#fff' : '#fff'"/>
          </svg>
        </template>
        <div class="message-text-container" :class="{'highlight': isHighlight && highlightIndexes&& highlightIndexes.includes(messageIndex), 'isHuman': !isAssistantMessage()} " @mouseenter="onReferenceTooltip(messageIndex)" @mouseleave="hoverIndex = null">
          <template v-if="isAssistantMessage()">
            <template v-if="message.type && message.type === 'welcome'">
              <div
                  class="be-font size-16 line-height-150 flex-column"
                  :class="['message-text', { loading: isLoadingItem }, message.type]"
                  v-html="getGreetingMsg"
              ></div>
            </template>
            <template v-else>
              <div
                  class="be-font size-16 line-height-150 flex-column"
                  :class="['message-text', { loading: isLoadingItem, playground: !isMain && !isOrganization }]"
                  v-html="convertHtml(message.message)"
              ></div>
            </template>
          </template>
          <template v-else>
            <p class="be-font size-16 line-height-150 flex-column" :class="['message-text', { loading: isLoadingItem }]">
              {{ message.message }}
            </p>
          </template>
          <template v-if="!isLoadingItem && isAssistantMessage() && messageIndex !== undefined && !isMain && !isMobile">
            <div class="button-container" :style="{justifyContent: 'space-between'}">
              <template v-if="messageIndex === hoverIndex">
                <div class="reference-tooltip" @click="toggleReference(message.id, messageIndex)">
                  <div class="tooltip-wrap">
                    <i class="font-icon-reference-data" />
                    {{ $t('playground.reference') }}
                  </div>
                </div>
              </template>
              <div class="rating-wrapper">
                <div class="rating-container flex y-center x-start">
                  <span class="rating-text">
                    {{ $t('playground.rating') }}
                  </span>
                  <div class="rating">
                    <template v-for="value in ratingValues" :key="value">
                      <div class="circle-container flex y-center" @mouseenter="selectRating(value, 'hover')" @mouseleave="ratingHover = null">
                        <template v-if="ratingHover !== null">
                          <!-- 호버 상태일 때는 호버 값을 기준으로 표시 -->
                          <template v-if="value <= ratingHover">
                            <i class="icon icon--star-fill" @click="selectRating(value, 'click')" />
                          </template>
                          <template v-else>
                            <i class="icon icon--star-transparent" @click="selectRating(value, 'click')" />
                          </template>
                        </template>
                        <template v-else>
                          <!-- 호버 상태가 아닐 때는 현재 평점이나 메시지 평점을 기준으로 표시 -->
                          <template v-if="value <= currentRating || value <= message.rating">
                            <i class="icon icon--star-fill" @click="selectRating(value, 'click')" />
                          </template>
                          <template v-else>
                            <i class="icon icon--star-transparent" @click="selectRating(value, 'click')" />
                          </template>
                        </template>

                      </div>
                    </template>
                  </div>
                </div>
                <button class="copy-button flex xy-center" @click="copy">
                  <span class="be-icon icon-grey-sm size-20">
                    <i class="icon icon--copy-white" />
                  </span>
                </button>
              </div>
              <div class="dash-line"></div>
              <div class="comment-wrapper">
                <p>{{ $t('playground.comment') }}</p>
                <div class="comment-container">
                  <textarea :placeholder="t('playground.commentPlaceholder')"
                            ref="textarea"
                            rows="1"
                            v-model="comment"
                            maxlength="100"
                            @input="handleResizeTextArea" />
                  <UiButton :type="'icon outline primary'" @click="saveComment(message.id)">
                    <i class="font-icon-save"></i>
                    {{ $t('common.save2') }}
                  </UiButton>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.message-container {
  width: 100%;
  padding-left: 40px;
  padding-right: 40px;
  padding-bottom: 37px;

  &.isOrganization {
    max-width: 1056px;
    margin: 0 auto;
  }

  .message-wrapper {
    gap: 10px;
    .message-profile {
      margin-left: 20px;

      .user-profile {
        display: block;
        width: 36px;
        height: 36px;
        padding: 5px 9px;
        background: $deepyellow-500;
        border-radius: $radius-4;
      }
    }

    .message-detail {
      gap: 4px;
      width: calc(100% - 100px);
      position: relative;
      align-items: flex-end;

      @media all and (min-width: 1440px) {
        .message-text {
          max-width: 980px;
        }
      }

      .message-text-container {
        max-width: 100%;
        background: $whiteColor;
        border-radius: 16px 0 16px 16px;
        box-shadow: $shadow-panel-sm;
        padding: 20px 24px;
        z-index: 1;

        :deep(img) {
          width: 100%;
        }

        &.highlight {
          box-shadow: 0px 4px 30px 0px #00000040;

        }

        .message-text {
          position: relative;
          gap: 10px;
          min-width: 2px;
          min-height: 19px;
          white-space: break-spaces;
          word-wrap: break-word;

          &.loading::before {
            content: '';
            display: block;
            position: absolute;
            top: 0;
            left: 0;
            width: 2px;
            height: 100%;
            background-color: #e5476e;
            animation: blick-effect 1s step-end infinite;
          }
        }
      }

      .chat-arrow {
        position: absolute;
        top: 21px;
        right: -17px;
        z-index: 2;
        transform: scale(-1, 1);
      }
    }

    &.isAssistant {
      flex-direction: row;
      gap: 14px;

      &.welcome {
        align-items: center;

        &.isMobile, &.isMain {
          align-items: initial;
        }
      }

      .message-profile {
        margin-left: 0;

        @media (max-width: 768px) {
          margin-right: 15px;
        }
      }

      .message-detail {
        align-items: flex-start;
        .message-author {
          padding-bottom: 6px;
        }

        .message-text-container {
          width: 100%;
          background: transparent;
          box-shadow: none;
          padding: 0;

          &::after {
            border-left: none;
          }

          .message-text {
            color: #262626;
            font-size: 18px;
            font-weight: 400;
            line-height: 150%;

            &.playground {
              margin-top: 10px;
            }

            &.welcome {
              margin-top: 0;
              font-weight: $semiBold;
            }
          }

          .button-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
            width: 100%;
            position: relative;

            .reference-tooltip {
              position: absolute;
              z-index: 99;
              top: 15px;
              right: 36px;

              .tooltip-wrap {
                display: flex;
                height: 34px;
                min-width: 80px;
                padding: 9px 13px 9px 11px;
                align-items: center;
                gap: 6px;
                border-radius: 4px;
                background: #EC0047;
                color: $whiteColor;
                cursor: pointer;

                .font-icon-reference-data {
                  font-size: 16px;
                }
              }
            }

            .rating-wrapper {
              display: flex;
              justify-content: space-between;
              margin-top: 11px;

              .rating-container {
                border-radius: $radius-8;
                min-width: 192px;
                border: 1px solid $line-sm;
                background: $whiteColor;
                padding: 11px;
                display: flex;
                align-items: center;
                gap: 10px;

                .rating-text{
                  color: $grey-600;
                  font-size: 13px;
                  font-weight: 400;
                }

                .rating {
                  display: flex;
                  align-items: center;
                  gap: 3px;

                  .circle-container {
                    .icon {
                      cursor: pointer;
                    }
                  }

                  &.disabled {
                    .circle {
                      border-color: $grey-100;
                      cursor: not-allowed;
                      pointer-events: none;
                    }

                    .line {
                      background-color: $grey-100;
                    }
                  }
                }
              }
            }

            .dash-line {
              width: 100%;
              height: 2px;
              border: 1px solid transparent;
              border-image: url('../../assets/img/icon-dashed-border.svg') 1 repeat;
            }

            .comment-wrapper {
              display: flex;
              flex-direction: column;
              gap: 4px;

              p {
                color: $grey-400;
                font-size: 13px;
                font-weight: 600;
                line-height: 120%; /* 15.6px */
                margin-left: 5px;
              }

              .comment-container {
                display: flex;
                align-items: flex-start;
                gap: 10px;

                textarea {
                  max-width: 445px;
                  width: 100%;
                  height: 38px;
                  font-size: 14px;
                  color: #1f1f1f;
                  font-weight: 400;
                  line-height: 100%;
                  text-align: left;
                  padding: 9px;
                  box-sizing: border-box;
                  border-radius: 5px;
                  background-color: #fff;
                  border: 1px solid #bfbfbf;
                  resize: none;
                  overflow: hidden;

                  &:focus {
                    border: 1px solid #289eef;
                    outline: none;
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  // Main Chatbot
  &.isMain:not(.isOrganization) {
    padding: 0 120px 20px 120px;
    .message-wrapper {
      gap: 23px;
      &.isAssistant {
        gap: 14px;
      }
      .message-profile {
        margin-right: 0;
        margin-left: 0;
        .user-profile {
          display: inline-block;
        }
      }
      .message-detail {
        max-width: 800px;
        &.isHuman {
          filter: drop-shadow(0px 1px 3px rgba(0, 0, 0, 0.16));
        }
        .chat-arrow{
          top: 9px;
        }
        .message-text-container {
          max-width: initial;
          padding: 0;
          margin: 9px 0 0 0;
          background: initial;
          box-shadow: none;
          &.isHuman {
            background: #fff;
            padding: 20px 24px;
            &::after {
              border-top: 0 solid transparent;
              border-left: 15px solid $grey-500;
              border-bottom: 30px solid transparent;
            }
          }

          .message-text {
            &.welcome {
              font-weight: $semiBold;
            }
            white-space: normal;
            font-size: $font-18;
          }
        }
      }
    }
  }

  &.isOrganization {
    .message-wrapper {
      .message-detail {
        .chat-arrow {
          top: 21px;
          path {
            fill: #fff;
          }
        }

        .message-text-container {
          margin-top: 21px;
        }
      }
    }
  }

  &.side-open {
    padding: 0 40px 20px 40px;
  }
  &.full-screen {
    padding: 20px 40px;
    max-width: 1157px;
    margin: 0 auto;
  }
}

@keyframes blick-effect {
  50% {
    opacity: 0;
  }
}

.mobile {
  .message-container:not(.isOrganization) {
    padding: 12px 24px;

    .message-wrapper.isAssistant {
      flex-direction: column;
      gap: 12px;

      .message-profile {
        display: flex;
        align-items: center;
        gap: 16px;

        .message-author {
          color: #111;
          font-size: 13px;
          font-weight: 600;
        }
      }

      .message-detail {
        width: 100%;
        max-width: 100%;
        .message-text-container {
          background-color: transparent;
          box-shadow: none;
          padding: 0;

          .message-text {
            color: #444;
            font-size: 14px;
            font-weight: 400;
            line-height: 150%; /* 21px */
          }

          :deep(.message-text p > a) {
            color: #0074FF;
          }
        }
      }
    }

    .message-wrapper:not(.isAssistant) {
      flex-direction: row;
      align-items: center;
      .message-profile {
        margin-left: 0;
      }
      .message-detail {
        max-width: 100%;
        width: 100%;
        align-items: flex-start;
        .chat-arrow {
          top: 0;
          right: 0;
        }

        .message-text-container {
          width: 100%;
          border-radius: 8px;
          padding: 14px;
          &.isHuman {
            width: calc(100% - 17px);
          }
        }
      }
    }
  }
}
// @media all and (max-width: 768px) {
// }
</style>
