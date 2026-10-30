<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { getMonitoringDetail, getMonitoringDetailChat } from "@/api/monitoring.js";
import { HTTP_CODES } from "@/libs/constants.js";

import { dateFormatter } from "@/libs/utils.js";
import { convertMarkdownToHtml } from "@/libs/parse.js";

import PencilIcon from "@/assets/img/icon-pencil.svg"

const props = defineProps({
  id: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['new-chat'])
const { t } = useI18n()

const postData = ref({})
const chatData = ref(null)

const wrapRef = ref(null)
const listRef = ref(null)
const isOver = ref(false)

watch(() => props.id, async() => {
  await getHistoryPost()
  await getHistoryChat()
  await checkOver()
})

const getHistoryDetail = async () => {
  await getHistoryPost()
  await getHistoryChat()
  await checkOver()
}

const getHistoryPost = async () => {
  try {
    const params = {
      sessionKey: props.id
    }
    const res = await getMonitoringDetail(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      res.data.idList = [t('historyDetail.noManager'), ...res.data.idList]
      postData.value = res.data
    } else {
      alert(res)
      console.log('Error: ', res.message)
    }

  } catch (err) {
    console.error('Error: ', err)
  }
}

const getHistoryChat = async () => {
  const params = {
    sessionKey: props.id,
    pageMode: false,
    page: 1
  }

  try {
    const res = await getMonitoringDetailChat(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      chatData.value = res.data.rows
    } else {
      alert(res)
      console.log('Error: ', res.message)
    }
  } catch (e) {
    console.error('Error: ', e)
  }
}

getHistoryDetail()

const checkOver = () => {
  setTimeout(() => {
    isOver.value = wrapRef.value.clientHeight < listRef.value.scrollHeight
  }, 0)
}


</script>

<template>
  <div class="history-detail-container" :class="{over: isOver}" ref="wrapRef">
    <div class="history-detail-wrapper" ref="listRef">
      <div class="history-detail-header">
        <div>
          <div>{{ dateFormatter(postData.regDate, 'time') }}</div>
          <div>{{ postData.askerId || '-' }}의 채팅 기록</div>
        </div>
        <img class="pencil-icon" :src="PencilIcon" alt="pancil">
      </div>
      <div class="history-detail-chat">
        <template v-for="(item) in chatData" :key="item.regDate">
          <div class="messages">
            <template v-if="item.role === 'ai'">
              <div class="ai be-font size-14 flex">
                <div class="message-wrap">
                  <div class="message">
                    <span v-html="convertMarkdownToHtml(item.message)"></span>
                  </div>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="human be-font size-14 flex">
                <span class="message-wrap">
                  <span class="message">
                    <svg class="chat-arrow" width="37" height="25" viewBox="0 0 37 25" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path id="Vector 215" d="M0 0H36.5C31 9.63422 17 31.7929 17 21.677C17 3.01069 4.5 1.20428 0 0Z" fill="white"/>
                    </svg>
                    {{ item.message }}
                  </span>
                </span>
              </div>
            </template>
          </div>
        </template>
      </div>
    </div>
  </div>
  <div class="chat-new-wrap" @click="emit('new-chat')">
    <UiButton :type="'icon primary widthFull'">
      <i class="font-icon-ask" />
      새 질문하기
    </UiButton>
  </div>
</template>

<style lang="scss" scoped>
.history-detail-container {
  position: relative;
  height: calc(100dvh - 56px - 68px);
  z-index: 1000;
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 12px;
    background: linear-gradient(0, rgba(255, 255, 255, 0.00) 0%, rgba(0, 0, 0, 0.06) 100%);
    z-index: 10;
  }
  &.over {
    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      width: 100%;
      height: 12px;
      background: linear-gradient(180deg, rgba(0, 0, 0, 0.00) 0%, #ECECEC 100%);
      z-index: 10;
    }
  }
  .history-detail-wrapper {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: #ECECEC;
    padding: 24px;
    overflow-y: auto;

    .history-detail-header {
      width: 100%;
      font-weight: 600;
      line-height: 1.5;
      margin-bottom: 14px;
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
    }
    .history-detail-chat {
      .messages {
        width: 100%;
        .ai, .human {
          padding: 10px 0;
          gap: 10px;
          line-height: 13px; /* 86.667% */
          .icon-wrap {
            gap: 12px;
          }
        }

        .human {
          flex-direction: row-reverse;
          justify-content: flex-start;
          gap: 26px;
          .message-wrap {
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 12px;
            position: relative;
            margin-right: 17px;
            .chat-arrow {
              position: absolute;
              top: 0;
              right: -15px;
              transform: scale(-1, 1);
              z-index: 2;
            }
          }

          .message {
            position: relative;
            width: 100%;
            padding: 14px;
            background: #fff;
            border-radius: 8px 0 8px 8px;
            box-shadow: 0 1px 3px #00000029;
            line-height: 1.5;
          }
        }

        .ai {
          display: flex;
          gap: 26px;

          .message-wrap {
            max-width: 500px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            position: relative;

            .chat-arrow {
              position: absolute;
              top: 0;
              left: -15px;
              z-index: 2;
            }

            .message {
              position: relative;
              background: transparent;
              padding: 0;
              white-space: break-spaces;
              line-height: 1.5;
            }

            :deep(.message p > a) {
              color: #0074FF;
            }
          }

        }
      }
    }
  }
}

.chat-new-wrap {
  position: absolute;
  width: 100%;
  height: 68px;
  bottom: 0;
  z-index: 100;
  background-color: #ECECEC;
  padding: 4px 24px;

  .be-btn {
    font-size: 16px;
    font-weight: 600;
    border-radius: 6px;
    .font-icon-ask {
      font-size: 20px;
    }
  }

}
</style>
