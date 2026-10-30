<script setup>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import {useRoute} from "vue-router";

const route = useRoute()
const store = useStore()
const props = defineProps({
  isLoading: Boolean,
  isAnswering: Boolean,
  disabled: Boolean,
  isBotDisabled: Boolean,
  onSubmitQuestion: Function,
  stop: Function,
  isMain: Boolean,
  isOver: Boolean,
  isOrganization: Boolean
})

const question = ref('')
const textarea = ref(null)
const fileData = ref([])
const parsedFileData = ref([])
const fileId = ref()
const isAskFocus = ref(false)

const isMobile = computed(() => {
  return store.state.isMobile
})

const handleSubmit = () => {
  if (checkIsEmpty()) return

  let data = {
    prompt: question.value,
  }

  props.onSubmitQuestion(data)
  textarea.value.style.height = 'auto'
  question.value = ''
  fileId.value = ''
  fileData.value = []
  parsedFileData.value = []
}

const handleResizeTextArea = () => {
  if (textarea.value.scrollHeight > 180) return
  textarea.value.style.height = 'auto'
  textarea.value.style.height = textarea.value.scrollHeight + 'px'
}

const handlePress = (e) => {
  if (e.keyCode !== 13) return
  if (e.shiftKey) return

  e.preventDefault()
  handleSubmit()
}

const checkIsEmpty = () => {
  return question.value.length === 0 && fileData.value.length === 0
}

const handleClickStop = () => {
  props.stop()
}

</script>

<template>
  <div class="ask-container-wrapper" :class="{ disabled, isMain, isOrganization, 'bot-disabled': isBotDisabled }">
    <div class="shadow" v-if="isMain"></div>
    <div class="ask-container flex flex-column xy-center">
      <div class="ask-container-header flex y-center x-end" >
        <template v-if="isLoading || isAnswering">
          <button class="pause flex xy-center" @click="handleClickStop" ref="pauseRef">
            <i class="icon icon--pause-answering" />
            <span>{{ $t('playground.stop') }}</span>
          </button>
        </template>
        <template v-else-if="isAskFocus || props.isOver">
          <div class="fade"></div>
        </template>
      </div>
      <div class="ask-wrapper flex y-center">
        <div class="textarea-wrapper" :class="{'flex xy-center': !isMobile}">
          <template v-if="!isMobile">
            <textarea
                ref="textarea"
                rows="1"
                v-model="question"
                :placeholder="isOrganization ? '궁금한 내용을 여기에 입력하세요. 1,326건의 2025년 보도자료를 기반으로 답변해드립니다.' : $t('playground.question')"
                :disabled="disabled || isBotDisabled"
                @input="handleResizeTextArea"
                @focus="isAskFocus = true"
                @blur="isAskFocus = false"
                @keypress="handlePress"
            />
          </template>
          <template v-else>
            <input ref="textarea"
                   class="ask-input"
                   type="text"
                   v-model="question"
                   :placeholder="$t('playground.question')"
                   :disabled="disabled"
                   @input="handleResizeTextArea"
                   @focus="isAskFocus = true"
                   @blur="isAskFocus = false"
                   @keypress="handlePress"
            />
          </template>
        </div>
        <div class="button-wrapper">
          <UiButton
              :type="'only-icon'"
              :class="[{ empty: checkIsEmpty() }, { answering: isAnswering || (isMain && isLoading) }]"
              @click="handleSubmit"
          >
            <span :class="`be-icon icon-white ${isMain ? 'size-24' : 'size-28'}`">
              <i class="font-icon-send" />
            </span>
            <div class="droplet_spinner flex xy-center">
              <div class="droplet"></div>
              <div class="droplet"></div>
              <div class="droplet"></div>
            </div>
          </UiButton>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.ask-container-wrapper {
  .ask-container {
    width: 100%;
    margin: auto;
    padding-bottom: 32px;


    .ask-container-header {
      width: 100%;
      padding: 12px 30px;

      .pause {
        gap: 5px;
        cursor: pointer;
        span {
          color: #79797f;
          font-weight: 400;
          &:hover {
            color: #e5476e;
          }
        }
      }
    }

    .ask-wrapper {
      gap: 5px;
      width: calc(100% - 60px);
      padding: 5px 8px;
      border-radius: 8px;
      background-color: $grey-800;
      box-sizing: border-box;
      box-shadow: 0 4px 5px 0 rgba(0, 0, 0, 0.12);
      position: relative;

      .textarea-wrapper {
        position: relative;
        width: 100%;
        box-sizing: border-box;
        color: $placeholderColor;
        margin: 8px 0;

        textarea {
          width: calc(100% - 70px);
          height: 23px;
          padding-right: 37px;
          padding-left: 12px;
          border: none;
          outline: none;
          background: none;
          font-size: 20px;
          resize: none;
          -webkit-appearance: none;
          -moz-appearance: none;
          appearance: none;
          color: $whiteColor;
          border-radius: 8px;

          &::placeholder {
            color: $placeholderColor;
            font-size: 20px;
            font-weight: $semiBold;
            line-height: 1.2;
          }
        }
      }

      .button-wrapper {
        position: absolute;
        top: 50%;
        right: 8px;
        transform: translate(0, -50%);
        z-index: 1;
        button {
          &.empty {
            background: #999;
          }
          &.answering {
            background: none;
            .be-icon {
              display: none;
            }
            .droplet_spinner {
              margin: 5px;
              gap: 4px;
            }

            .droplet_spinner .droplet {
              width: 5px;
              height: 5px;
              background-color: #ec0047;
              border-radius: 50em;
              transform-origin: center bottom;

              animation: bounce 1.2s cubic-bezier(0.3, 0.01, 0.4, 1) infinite;
            }

            .droplet_spinner .droplet:nth-child(1) {
              animation-delay: -0.4s;
            }

            .droplet_spinner .droplet:nth-child(2) {
              animation-delay: -0.2s;
            }

            .droplet_spinner .droplet:nth-child(3) {
              animation-delay: 0s;
            }
          }
        }
      }
    }
  }
  &.disabled {
    .ask-container {
      opacity: 60%;
      .ask-container-header {
        .file-input-container {
          .file-name-container {
            display: none;
          }
          .file-input-label {
            background: #e6e6e6;
            cursor: not-allowed;
          }
        }
      }
      .ask-wrapper {
        background: #e6e6e6;
        .button-wrapper {
          button {
            cursor: not-allowed;
          }
        }
      }
    }
  }

  // Main Chatbot
  &.isMain {
    padding: 0 14px 14px 14px;
    position: absolute;
    bottom:18px;
    border-radius: 0 0 6px 6px;
    left:50%;
    transform: translateX(-50%);
    width: calc(100% - 34px);
    background: #ECECEC;
    z-index: 1;
    .shadow {
      z-index: 1;
      position: absolute;
      top: -23px;
      left: 0;
      width: 100%;
      height: 23px;
      background: linear-gradient(180deg, rgba(236, 236, 236, 0) 0%, #ECECEC 100%);
    }
    .ask-container {
      width: 100%;
      margin: auto;
      padding-bottom: 0;
      .ask-container-header {
        position: relative;
        padding: 0;
        z-index: 1;
        .pause {
          display: flex;
          align-items: center;
          gap: 4px;
          position: absolute;
          bottom: 10px;
          span {
            color: #7D7D7D;
            font-size: 14px;
            font-weight: 600;
          }
        }
      }
      .ask-wrapper {
        width: 100%;
        background: $n-gray-990;
        gap: 19px;
        align-items: center;
        padding: 11px 11px 11px 20px;
        .textarea-wrapper {
          margin: 0;
          textarea {
            width: 100%;
            padding: 0;
            font-size: $font-18;
            font-weight: $semiBold;
            line-height: normal;
            overflow: hidden;
            border-radius: 0;
            &::placeholder {
              color: #bfbfbf;
            }
          }
        }
        .button-wrapper {
          position: unset;
          transform: initial;
          align-self: flex-end;
          &.answering {
            pointer-events: none;
          }
          .be-btn.only-icon {
            margin: 0;
            width: 34px;
            height: 34px;
            min-width: initial;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
          }
        }
      }
    }
  }

  &.isOrganization {
    .ask-container .ask-wrapper .textarea-wrapper textarea {
      &::placeholder {
        color: #FFFF00;
      }
    }
  }
}

@keyframes bounce {
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

// Mobile
.mobile {
  .ask-wrapper {
    z-index: 100;
    .ask-container-wrapper {
      width: 100%;
      .ask-container {
        padding-bottom: 0;
        margin: 0;
        .ask-container-header {
          position: absolute;
          bottom: 100%;
          right: 0;
          z-index: 100;
          padding: 0;
          .pause {
            background-color: #ECECEC;
            padding: 12px 30px;
          }
          .fade {
            width: 100%;
            height: 12px;
            background: linear-gradient(180deg, rgba(236, 236, 236, 0.00) 0%, #ECECEC 100%);
          }
        }

        .ask-wrapper {
          height: 56px;
          width: 100%;
          border-radius: 0;

          .textarea-wrapper {
            .ask-input {
              width: calc(100% - 60px);
              height: 23px;
              padding-right: 37px;
              padding-left: 12px;
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
              border-radius: 8px;


              &::placeholder {
                color: $placeholderColor;
                font-size: 16px;
                line-height: 150%; /* 24px */
                font-weight: $semiBold;
              }
            }
          }

          .button-wrapper {
            .be-btn {
              height: 34px;
              min-width: 34px;
              padding: 5px;
              border-radius: 4.25px;

              .be-icon {
                width: 23px;
                height: 23px;
                font-size: 23px;
              }
            }
          }
        }
      }
    }
  }
}
// @media all and (max-width: 768px) {
// }
</style>
