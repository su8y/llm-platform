<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import AppLogo from "@/components/AppLogo.vue";

import { removeAuthData } from "@/libs/auth-helper.js";
import { HTTP_CODES } from "@/libs/constants.js";
import { getChatTitleList } from "@/api/playground.js";

const props = defineProps({
  userData: {
    type: Object,
    default: () => {}
  },
})

const emit = defineEmits(['new-chat', 'select'])

const store = useStore()
const router = useRouter()

const isHistoryList = ref(false)
const historyData = ref(null)
const wrapRef = ref(null)
const listRef = ref(null)
const isOver = ref(false)
const isScroll = ref(false)
const isLoading = ref(false)
const page = reactive({
  current: 1,
  perPage: 15
})

const onScroll = () => {
  const heightGap = wrapRef.value.scrollHeight - wrapRef.value.clientHeight

  if (isLoading.value) return


  if (heightGap === wrapRef.value.scrollTop) {
    isScroll.value = true
    page.current += 1
    getChatHistory(true)
  } else {
    isScroll.value = false
  }
}

const signOut = () => {
  store.commit('clearAllUserData')
  removeAuthData()
  router.push('/')
}

const getChatHistory = async (isNext) => {
  if (!isNext) page.current = 1

  try {
    const params = {
      params: {
        page: page.current,
        perPage: page.perPage
      }
    }

    isLoading.value = true
    const res = await getChatTitleList(params)

    if (res.code === HTTP_CODES.SUCCESS) {
      if (isNext) {
        isLoading.value = false
        historyData.value = historyData.value.concat(res.data.rows)
        checkOver()
        return
      }
      isLoading.value = false
      historyData.value = res.data.rows
      isHistoryList.value = true
      checkOver()
    } else {
      isLoading.value = false
      historyData.value = null
      alert(res.message)
      console.log('Error: ', res)
    }
  } catch (e) {
    alert(e)
    isLoading.value = false
    console.error('Error: ', e)
  }
}

const checkOver = () => {
  setTimeout(() => {
    isOver.value = wrapRef.value.clientHeight < listRef.value.scrollHeight
  }, 0)
}

const newSession = () => {
  isHistoryList.value = false
  emit('new-chat')
}

const showDetail = (id) => {
  if (id) isHistoryList.value = false
  emit('select', id)
}
</script>

<template>
  <div class="mo-header-container">
    <div class="hamburger-wrapper" @click="getChatHistory(false)">
      <span class="hamburger">
        <i class="icon icon--hamburger" />
      </span>
    </div>
    <div class="logo">
      <span class="knit-logo">
        <AppLogo />
      </span>
    </div>
    <Transition name="slide-left">
      <div v-if="isHistoryList" class="chat-history-container">
        <div class="chat-history-wrapper">
          <div class="chat-history-header">
            <div class="new-chat-wrapper">
              <button class="new-chat-btn" @click="newSession">
                <i class="font-icon-ask" />
                새 질문 하기
              </button>
            </div>
            <button class="chat-history-close" @click="isHistoryList = false">
              <i class="icon icon-close"/>
            </button>
          </div>
          <div class="chat-history-content">
            <div class="content-wrapper">
              <div class="title">ASK History</div>
              <div class="contents"  :class="{show: isHistoryList, over: isOver}">
                <div class="list-wrapper" ref="wrapRef" @scroll="onScroll">
                  <ul ref="listRef">
                    <template v-for="data in historyData" :key="data.date">
                      <li class="ellipsis" @click="showDetail(data.sessionKey)">{{ data.title }}</li>
                    </template>
                  </ul>
                  <template v-if="isLoading">
                    <div class="section-body-loading">
                      <i class="icon icon--loading-animated"/>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
          <div class="chat-history-footer">
            <div class="user-info">
              <span class="email">{{ props.userData.emailAddress }}</span>
            </div>
            <UiButton :type="'only-icon outline'" @click="signOut">
              <i class="font-icon-logout" />
            </UiButton>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>


<style lang="scss" scoped>
.mo-header-container {
  position: relative;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #fff;
  padding: 16px;
  box-sizing: border-box;

  .hamburger-wrapper {
    position: absolute;
    left: 16px;
    .hamburger {
      display: inline-block;
      width: 24px;
      height: 24px;
      cursor: pointer;
    }
  }

  .chat-history-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100dvh;
    z-index: 9999;
    transition: all 0.3s ease;
    background-color: rgba(0, 0, 0, 0.75);
    margin: 0;

    &.slide-left-enter-active,
    &.slide-left-leave-active {
      transition: background-color 1s ease; // Longer transition for bg
    }

    &.slide-left-enter-to,
    &.slide-left-leave-from {
      background-color: rgba(0, 0, 0, 0.75); // Fully opaque black
    }

    &.slide-left-enter-from,
    &.slide-left-leave-to {
      background-color: rgba(0, 0, 0, 0); // Transparent
    }

    .chat-history-wrapper {
      position: absolute;
      top: 0;
      left: 0;
      width: calc(100% - 55px);
      max-width: 500px;
      height: 100%;
      display: flex;
      flex-direction: column;
      background-color: #fff;

      .chat-history-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        border-bottom: 1px solid #ebebeb;
        padding: 12px;

        .new-chat-wrapper {
          padding: 10px 12px;
          .new-chat-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            color: $mainColor;
            font-size: 18px;
            font-weight: $bold;
            line-height: 150%; /* 27px */

            .font-icon-ask {
              font-size: 20px;
            }
          }
        }

        .chat-history-close {
          padding: 4px;

          .icon.icon-close {
            display: inline-block;
            width:24px;
            height: 24px;
            background-image: url('../assets/img/icon-mobile-close.svg');
            background-repeat: no-repeat;
          }
        }
      }

      .chat-history-content {
        height: calc(100% - 72px - 72px);
        display: flex;
        flex-direction: column;
        justify-content: space-between;

        .content-wrapper {
          height: 100%;
          padding-top: 12px;
          .title {
            height: 40px;
            padding: 10px 24px;
            color: #888;
            font-size: 13px;
            line-height: 1.5;
            font-weight: 500;
            margin-bottom: 8px;
          }
          .contents {
            position: relative;
            top: 0;
            width: 100%;
            height: calc(100% - 48px);

            &.over {
              &::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 12px;
                background: linear-gradient(0, rgba(255, 255, 255, 0.00) 0%, #fff 100%);
              }
              &::after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 12px;
                background: linear-gradient(180deg, rgba(0, 0, 0, 0.00) 0%, rgba(0, 0, 0, 0.06) 100%);
              }
            }
          }
          .list-wrapper {
            width: 100%;
            height: 100%;
            overflow-y: auto;

            .section-body-loading {
              display: flex;
              justify-content: center;
            }
          }
          ul {
            padding-inline-start: 0;
            padding: 0 20px 0 12px;
            li {
              list-style: none;
              padding: 8px 12px;
              transition: all .3s;
              color: #444;
              font-size: 15px;
              font-weight: 600;
              line-height: 150%; /* 22.5px */
              margin-bottom: 4px;
              &:last-child {
                margin: 0
              }
            }
          }
        }

      }
      .chat-history-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px 16px;
        background-color: #fff;
        height: 72px;

        .user-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
          padding-left: 8px;

          span {
            display: inline-block;
            font-size: 13px;
            font-weight: 500;
            line-height: 120%; /* 15.6px */
            &.company {
              color: #2F2F2F;
              font-weight: $regular;
              line-height: 100%;
            }

            &.email {
              color: #0E90A5;
            }
          }
        }

        .be-btn {
          width: 38px;
          height: 38px;
          padding: 11px;
          border-color: #bbb;
        }
      }
    }
  }

  .logo {
    width: 100%;
    text-align: center;
    margin-top: 4px;
    .app-logo {
      font-size: 18px;
    }
  }
}


.slide-left-enter-active,
.slide-left-leave-active {
  .chat-history-wrapper {
    transition: all 0.5s;
  }
}
.slide-left-leave-active {
  .chat-history-wrapper {
    transition: all 0.5s;
  }
}
.slide-left-enter-from,
.slide-left-leave-to {
  .chat-history-wrapper {
    margin-left: -100vw;
  }
}
</style>
