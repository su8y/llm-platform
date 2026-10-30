<script setup>
import { supportContact } from '@/libs/support.js'
import { defineProps, ref, onMounted, computed, inject, onBeforeMount, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

import { thousand, setPlanAlertCookie, getPlanAlertCookie } from "@/libs/utils.js";
import { removeAuthData } from '@/libs/auth-helper'
import { LANGUAGE_LIST } from '@/libs/constants'
import { changeLocale } from "@/libs/i18n.js";

import MemberStatus from "@/components/Modal/MemberStatus.vue";

const modal = inject('$modal')
const store = useStore()
const router = useRouter()

const props = defineProps({
  routerName: {
    type: String,
    default: 'Playground'
  },
  isScroll: {
    type: Boolean,
    default: false
  },
  userData: {
    type: Object,
    default: () => {}
  },
  i18n: {
    type: Object,
    default: () => {}
  }
})

const { t, locale } = props.i18n

const isProfile = ref(false)
const creditData = ref({})
const isPlanWarning = ref(false)
const isLanguageList = ref(false)

const title = computed(() => {
  const camelCaseTitle = props.routerName
      .split(' ')
      .map((word, index) => {
        if (index === 0) {
          return word.toLowerCase()
        } else {
          return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
        }
      })
      .join('')

  return t(`common.sideMenu.${camelCaseTitle}`)
})


onBeforeMount(async () => {
  await store.dispatch('storeCreditData')

  creditData.value = await store.state.creditData.data
  const isAlertCookie = getPlanAlertCookie()
  const noneCredit = creditData.value.useAbleCredit === 0 || !creditData.value.useAbleCredit

  if (noneCredit && isAlertCookie) {
    isPlanWarning.value = noneCredit
    store.commit('setPlanAlert', isPlanWarning.value)
  }
})

onMounted(() => {
  window.addEventListener('click', (e) => {
    const classList = e.target.classList
    if (isProfile.value) {
      if (!classList.contains('profile')) {
        isProfile.value = false
        isLanguageList.value = false
      } else {
        isLanguageList.value = false
      }
    }
  })
  window.addEventListener('touchstart', (e) => {
    const classList = e.target.classList
    if (isProfile.value) {
      if (!classList.contains('profile')) {
        isProfile.value = false
        isLanguageList.value = false
      } else {
        isLanguageList.value = false
      }
    }
  })
})

watch(() => store.state.isPlanAlert, (value) => {
  if (value) {
    isPlanWarning.value = value
    setPlanAlertCookie(value)
  }
})

watch(() =>  store.state.creditData, (value) => {
  creditData.value = value.data
})

const subTitle = computed(() => {
  const headersDesc = new Map([
    ['Playground', t('headers.playground')],
    ['MCP', t('headers.playground')],
    ['Dashboard', t('headers.dashboard')],
    ['Board', t('headers.referenceList')],
    ['History', t('headers.historyList')],
    ['Prompt', t('headers.prompt')],
    ['Members', t('headers.members')],
    ['Setting', t('headers.referenceCategory')],
    ['Plan', t('headers.plan')],
    ['Penpal', t('headers.penpal')],
    ['Inbox List', t('headers.inbox')],
    ['File Drive', t('headers.fileDrive')],
    ['Email RAG', t('headers.emailRag')],
    ['Penpal Dashboard', t('headers.penpalDashboard')],
  ])

  return headersDesc.get(props.routerName)
})

const iconStyle = computed(() => {
  const headersDesc = new Map([
    ['Playground', 'icon--playground-black'],
    ['MCP', 'icon--playground-black'],
    ['Dashboard', 'icon--dashboard-black'],
    ['Board', 'icon--board-black'],
    ['List', 'icon--list-black'],
    ['Prompt', 'icon--prompt-black'],
    ['Members', 'icon--members-black'],
    ['Setting', 'icon--setting-black'],
    ['Plan', 'icon--plan-black'],
    ['Penpal', 'icon--penpal-black'],
    ['Email RAG', 'icon--rag-black'],
    ['Inbox List', 'icon--list-black'],
    ['History', 'icon--history-black'],
    ['File Drive', 'icon--file-drive-black'],
    ['Penpal Dashboard', 'icon--dashboard-black'],
  ])

  const routerName = props.routerName

  return headersDesc.get(routerName)
})

const battery = computed(() => {
  const ratio = (creditData.value.useAbleCredit / creditData.value.totalCredit) * 100

  return ratio >= 70 ? 'full' : ratio >= 30 ? 'half' : 'handful';
})

const currentLocale = computed(() => {
  return locale.value
})


const profileOpen = () => {
  isProfile.value = !isProfile.value
}

const signOut = () => {
  store.commit('clearAllUserData')
  removeAuthData()
  router.push('/signin')
}

const closeAlert = () => {
  isPlanWarning.value = false
  setPlanAlertCookie(false)
  store.commit('setPlanAlert', isPlanWarning.value)
}

const onLocaleChange = (lang) => {
  changeLocale(props.i18n, lang)
  isLanguageList.value = false
  location.reload()
}

</script>

<template>
  <div class="header flex y-center x-between" :class="{isScroll: props.isScroll}">
    <div class="header-left">
      <h1 class="title flex y-center">
        <i :class="iconStyle" />
        {{ title }}
      </h1>
      <div class="line"></div>
      <span class="sub-title">
        {{ subTitle }}
      </span>
    </div>
    <div class="profile-wrapper">
      <div class="plan-wrapper">
        <span class="plan">
          {{ t('plan.remainingQuestion') }} :
          <span class="strong">{{ thousand(creditData.useAbleCredit) }}</span>/{{ thousand(creditData.totalCredit) }}{{ t('plan.questionCount') }}
        </span>
        <i class="icon" :class="`icon--battery-${battery}`" />
      </div>
      <template v-if="isPlanWarning">
        <div class="plan-warning-wrapper">
          <div class="text">
            <span class="title">{{ t('plan.nonRemainQuestion.title') }}</span>
            <div class="line horizontal"></div>
            <span class="desc" v-html="t('plan.nonRemainQuestion.desc')"></span>
            <span class="contact">{{ t('plan.nonRemainQuestion.contact', {email: supportContact()}) }}</span>
          </div>
          <i class="font-icon-close" @click="closeAlert"></i>
        </div>
      </template>
      <div class="line xs"></div>
      <span v-memo="[props.userData?.userAuth.authName]" class="user-authority" @click="modal.open(MemberStatus, 'authority')">
        <span class="icon-wrap">
          <i class="icon" :class="`icon--${props.userData && props.userData.userAuth.authName.toLowerCase()}`" />
        </span>
        {{ props.userData && props.userData.userAuth.authName }}
      </span>
      <span class="be-icon hover-size-24 icon-grey-md profile-btn" @click.stop="profileOpen">
        <i class="font-icon-profile"></i>
      </span>
      <template v-if="isProfile">
        <div class="profile flex flex-column gap-8">
          <i class="icon icon--arrow-up" />
          <div class="user-id">
            <p>{{ props.userData && props.userData.userId }}</p>
          </div>
          <div class="btn-wrapper">
            <div @click="signOut">{{ t('common.logout') }}</div>
          </div>
          <div class="language-wrap flex x-between y-center gap-8">
            <span class="language-title">Language</span>
            <div class="be-dropdown flex y-center language" ref="dropdown" @click.stop.prevent="isLanguageList = !isLanguageList">
                <span class="current-language">
                  <i class="icon icon--lang" :class="currentLocale"></i>
                  {{ currentLocale.toUpperCase() }}
                </span>
              <span class="be-icon size-20 icon-grey-md icon-dropdown">
                  <i class="font-icon-right-arrow"></i>
                </span>
              <Transition name="slide">
                <template v-if="isLanguageList">
                  <ul class="list" :class="{'is-show': isLanguageList}">
                    <template v-for="item in LANGUAGE_LIST" :key="item.code">
                      <li @click.stop="onLocaleChange(item.code)">
                        <i class="icon icon--lang" :class="item.code"></i>
                        {{ item.code.toUpperCase() }}
                      </li>
                    </template>
                  </ul>
                </template>
              </Transition>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.header {
  padding: 16px;
  background-color: $whiteColor;
  box-shadow: 0px 10px 20px 0px rgba(0, 0, 0, 0.06);

  &.isScroll {
    width: 100%;
    align-items: center;
    background-color: $whiteColor;
  }

  &-left {
    display: flex;
    gap: 20px;
    align-items: center;

    .title {
      color: $grey-600;
      font-size: 22px;
      font-weight: 700;
      margin-left: 4px;
      gap: 8px;

      .font-icon-plan {
        font-size: 16px;
      }
    }

    .line {
      width: 1px;
      height: 12px;
      background: $grey-100;
    }

    .sub-title {
      color: $grey-600;
      font-size: 13px;
      font-weight: 400;
      line-height: 120%; /* 15.6px */
    }
  }


  .profile-wrapper {
    position: relative;
    top: 0;
    right: 0;
    z-index: 9;
    display: flex;
    align-items: center;
    gap: 12px;

    .plan-wrapper {
      display: flex;
      align-items: center;
      gap: 12px;

      .plan {
        color: #444;
        font-size: 12px;
        font-weight: 500;

        .strong {
          font-weight: $semiBold;
        }
      }

      .icon {
        width: 35px;
        height: 30px;
        background-size: 30px;
      }

      .font-icon-refresh {
        cursor: pointer;

      }
    }

    .plan-warning-wrapper {
      width: 238px;
      position: absolute;
      top: 40px;
      right: 35px;
      background-color: $whiteColor;
      border-radius: 8px;
      box-shadow: $shadow-popup-mdx2;
      padding: 18px 20px;

      &::before {
        content: '';
        background-color: #fff;
        position: absolute;
        top: -4px;
        left: 50%;
        z-index: 2;
        width: 10px;
        height: 10px;
        -webkit-box-shadow: -1px 1px 0 0 rgba(0, 0, 0, 0.16);
        box-shadow: -1px 1px 0 0 rgba(0, 0, 0, 0.16);
        transform: rotate(135deg);
      }

      .text {
        display: flex;
        flex-direction: column;
        gap: 8px;

        .title {
          color: $mainColor;
          font-size: 15px;
          font-weight: $semiBold;
          line-height: 150%; /* 22.5px */
        }

        .desc {
          color: #444;
          font-size: 13px;
          font-weight: $regular;
          line-height: 150%; /* 19.5px */
        }

        .contact {
          color: #444;
          font-size: 13px;
          font-weight: 500;
          line-height: 150%; /* 19.5px */
        }
      }

      .font-icon-close {
        position: absolute;
        top: 10px;
        right: 10px;
        cursor: pointer;
      }
    }

    .user-authority {
      display: flex;
      align-items: center;
      gap: 4px;
      color: #444;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;

      .icon-wrap {
        display: inline-block;
        width: 16px;
        height: 16px;
      }
    }

    .profile-btn {
      width: 34px;
      height: 34px;
      cursor: pointer;
      transition: all .3s;
      padding: 2px;

      &:hover {
        border-radius: 100%;
        background-color: $hover-deepgrey-bg;
      }
    }

    .profile {
      width: 220px;
      position: absolute;
      top: 35px;
      right: 0px;
      background-color: $whiteColor;
      padding: 10px;
      border-radius: 8px;
      box-shadow: 0 8px 15px 0 rgba(0, 0, 0, 0.16), 0 0 0 1px rgba(0, 0, 0, 0.16);
      z-index: 9999999999;

      .icon--arrow-up {
        position: absolute;
        top: -7.9px;
        right: 7px;
      }

      .user-id {
        color: #57AB00;
        font-size: 14px;
        font-weight: 600;
        line-height: 100%;
        padding: 8px 10px 17px 10px;
        border-bottom: 1px solid #d7d7d7;
      }

      .btn-wrapper {
        width: 100%;
        padding: 8px 12px;
        transition: background-color .3s;
        cursor: pointer;
        border-radius: 4px;

        &:hover {
          background-color: #ebebeb;
        }
      }

      .language-wrap {
        margin-top: 8px;

        .language-title {
          padding-left: 10px;
        }

        .be-dropdown {
          padding-right: 2px;
          width: 100px;
          cursor: pointer;
        }

      }

    }
  }
}
</style>
