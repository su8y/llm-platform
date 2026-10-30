<script setup>
import { ref, inject, onBeforeUnmount, onMounted, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useStore } from 'vuex';

import { changeLocale } from '@/libs/i18n';
import { LANGUAGE_LIST } from '@/libs/constants';

import SignInModal from "@/components/Modal/Register.vue";
import FindPassword from "@/components/Modal/FindPassword.vue";
import ChatFloatingButton from "@/components/ChatFloatingButton.vue";
import AppLogo from "@/components/AppLogo.vue";

const router = useRouter()
const i18n = useI18n()
const store = useStore()
const modal = inject('$modal')
const { t, locale } = i18n
const emits = defineEmits(['login', 'logout', 'getChatbotKey'])
const props = defineProps({
  error: Object,
  userData: Object,
})

const isFocus = ref(false)
const isLanguageList = ref(false)
const inputError = ref(props.error)
const inputs = reactive({
  id: null,
  password: null
})

onMounted(async () => {
  window.addEventListener('click', () => isLanguageList.value = false)
  window.addEventListener('touchstart', (e) => {
    if (e.target.parentElement.classList.contains('login-right')) {
      isLanguageList.value = false
    }
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('click', () => isLanguageList.value = false)
  window.removeEventListener('touchstart', () => isLanguageList.value = false)
})

const currentLocale = computed(() => {
  return locale.value
})
const isMobile = computed(() => store.state.isMobile)

const handleFocus = (type) => {
  switch (type) {
    case 'id':
      isFocus.value = true
      inputError.value.id = false
      break
    case 'password':
      isFocus.value = true
      inputError.value.password = false
      break
  }
}

const signIn = async () => {
  if (!inputs.id) {
    inputError.value.id = true
    inputError.value.text = t('register.error.required.userId')
    return
  }
  if (!inputs.password) {
    inputError.value.password = true
    inputError.value.text = t('register.error.required.password')
    return
  }

  emits('login', {user_id: inputs.id, user_password: inputs.password})
}

const openModal = (type) => {
  const modalType = type === 'signup' ? SignInModal : FindPassword
  modal.open(modalType)
};

const signOut = () => {
  emits('logout')
}

const getChatbotSessionKey = async () => {
  emits('getChatbotKey')
}

const onLocaleChange = (lang) => {
  changeLocale(i18n, lang)
  isLanguageList.value = false
  location.reload()
}

const goRegister = () => {
  isMobile.value ? router.push('/register') : openModal('signup')
}
</script>

<template>
  <div class="login-wrap">
    <div class="login-container">
      <div class="login-left">
        <div class="text-wrapper">
          <div class="main-text">
            <span class="knit-logo">
              <AppLogo />
            </span>
            <span class="knit-desc">
                Where Knowledge<br> Connects
              </span>
          </div>
          <div class="sub-text" v-html="t('common.introduction')">
          </div>
        </div>
        <ChatFloatingButton @handleChatBot="getChatbotSessionKey"/>
      </div>
      <div class="login-right-wrapper">
        <template v-if="!props.userData">
          <div class="login-right">
            <div class="login-top">
              <UiInput class="login-id" :class="isMobile ? 'font-16': ''"
                     :input-style="inputError.id && 'error'"
                     :type="'text'"
                     :placeholder="$t('register.placeholder.userId')"
                     @focus="handleFocus('id')"
                     @updateValue="inputs.id = $event" >
                <template #label>
                  {{ $t('register.id') }}
                </template>
                <template #error v-if="inputError.id">
                  <span class="error-text">
                    {{ inputError.text }}
                  </span>
                </template>
              </UiInput>
              <UiInput class="login-password" :class="isMobile ? 'font-16': ''"
                      :input-style="inputError.password && 'error'"
                      :type="'password'"
                      :placeholder="t('register.placeholder.userPassword')"
                      @focus="handleFocus('password')"
                      @updateValue="inputs.password = $event"
                      @enter="signIn" >
                <template #label>
                  {{ $t('register.password') }}
                </template>
                <template #error v-if="inputError.password">
                  <span class="error-text">
                    {{ inputError.text }}
                  </span>
                </template>
              </UiInput>
              <UiButton class="login-btn font-16" :type="'widthFull primary'" @click="signIn">{{ $t('common.login') }}</UiButton>
              <div class="auth-wrap">
                <p class="sign-in" @click="goRegister">{{ $t('common.adminRegister') }}</p>
                <p class="find-pw" @click="openModal('findPw')">{{ $t('common.findPassword') }}</p>
              </div>
            </div>
            <template v-if="isMobile">
              <div class="line"></div>
            </template>
            <div class="login-bottom">
              <div class="language-wrap">
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
          </div>
        </template>
        <template v-else>
          <div class="login-right login">
            <div class="login-top">
              <div class="login-logo-wrap">
                <span class="knit-logo">
                  <AppLogo />
                </span>
              </div>
              <div class="login-user-wrapper">
                <span class="login-user" v-html="$t('common.greetings', {name: props.userData.userId})">
                </span>
                <span class="login-text" v-html="$t('common.assistantMessage')">
                </span>
              </div>
              <RouterLink :to="{ name: props.userData.userId === 'jeju_internal' ? 'jejuPlayground' : 'Playground' }">
                <UiButton class="start-btn" :class="isMobile ? 'font-16' : ''" :type="'widthFull primary'">
                  {{ $t('common.start') }}
                </UiButton>
              </RouterLink>
              <div class="auth-wrap">
                <p class="find-pw" :class="isMobile ? 'font-16' : ''" @click="signOut">{{ $t('common.logout') }}</p>
              </div>
            </div>
            <div class="login-bottom">
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>

</template>

<style lang="scss" scoped>
.login-wrap {
  width: 100%;
  height: 100vh;
  background-color: $grey-900;
  display: flex;
  align-items: center;
  padding: 12px;
  background-image: url('@/assets/img/login-bg.png');
  background-repeat: no-repeat;
  background-size: 1362px;
  overflow-x: auto;

  &.isDisplay {
    padding: 0;

    .login-container {
      .login-right-wrapper {
        margin: 12px 12px 12px 0;
      }
    }
  }

  .login-container {
    display: grid;
    grid-template-columns: auto 376px;
    width: 100%;
    height: 100%;

    .login-left {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      justify-content: center;

      .text-wrapper {
        margin-left: 51px;
        margin-bottom: 30px;

        .main-text {
          display: flex;
          flex-direction: column;
          position: relative;
        }

        .knit-logo {
          display: block;
          margin-bottom: 20px;
          .app-logo {
            color: $whiteColor;
            font-size: 48px;
          }
        }

        .knit-desc {
          color: $whiteColor;
          font-size: 116px;
          font-weight: 800;
          line-height: 100%;
        }

        .sub-text {
          margin-top: 46px;
          max-width: 424px;
          color: $whiteColor;
          font-size: 24px;
          font-weight: 600;
          line-height: 130%; /* 31.2px */
        }
      }

      .chatbot-btn-wrapper {
        position: relative;
        .chat-btn {
          position: absolute;
          left: 513px;
          bottom: -10px;
          width: 172px;
          height: 172px;
          border-radius: 233px;
          background-color: $mainColor;
          overflow: hidden;
          cursor: pointer;
          animation: bounce .9s infinite linear;

          &:hover {
            animation-play-state: paused;
          }

          .chat-btn-text {
            position: absolute;
            top: 35px;
            left: 25px;
            color: #FFF;
            font-size: 22px;
            font-weight: 700;
          }

        }

        /* ----------------------------------------------
  * Generated by Animista on 2024-11-12 17:4:45
  * Licensed under FreeBSD License.
  * See http://animista.net/license for more info.
  * w: http://animista.net, t: @cssanimista
  * ---------------------------------------------- */

        /**
         * ----------------------------------------
         * animation heartbeat
         * ----------------------------------------
         */
        @-webkit-keyframes bounce {
          from {
            -webkit-transform: scale(1);
            transform: scale(1);
            -webkit-transform-origin: center center;
            transform-origin: center center;
            -webkit-animation-timing-function: ease-out;
            animation-timing-function: ease-out;
          }
          10% {
            -webkit-transform: scale(0.91);
            transform: scale(0.91);
            -webkit-animation-timing-function: ease-in;
            animation-timing-function: ease-in;
          }
          17% {
            -webkit-transform: scale(0.98);
            transform: scale(0.98);
            -webkit-animation-timing-function: ease-out;
            animation-timing-function: ease-out;
          }
          33% {
            -webkit-transform: scale(0.87);
            transform: scale(0.87);
            -webkit-animation-timing-function: ease-in;
            animation-timing-function: ease-in;
          }
          45% {
            -webkit-transform: scale(1);
            transform: scale(1);
            -webkit-animation-timing-function: ease-out;
            animation-timing-function: ease-out;
          }
        }
        @keyframes bounce {
          from {
            -webkit-transform: scale(1);
            transform: scale(1);
            -webkit-transform-origin: center center;
            transform-origin: center center;
            -webkit-animation-timing-function: ease-out;
            animation-timing-function: ease-out;
          }
          10% {
            -webkit-transform: scale(0.91);
            transform: scale(0.91);
            -webkit-animation-timing-function: ease-in;
            animation-timing-function: ease-in;
          }
          17% {
            -webkit-transform: scale(0.98);
            transform: scale(0.98);
            -webkit-animation-timing-function: ease-out;
            animation-timing-function: ease-out;
          }
          33% {
            -webkit-transform: scale(0.87);
            transform: scale(0.87);
            -webkit-animation-timing-function: ease-in;
            animation-timing-function: ease-in;
          }
          45% {
            -webkit-transform: scale(1);
            transform: scale(1);
            -webkit-animation-timing-function: ease-out;
            animation-timing-function: ease-out;
          }
        }

      }
    }

    .login-right {
      height: 100%;
      padding: 28px;
      background-color: $whiteColor;
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;

      .login-top {
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 27px;
        position: relative;

        .knit-logo {
          position: absolute;
          top: -130%;
        }

        .login-btn {
          height: 44px;
          margin-top: 17px;
        }

        .auth-wrap {
          display: flex;
          justify-content: center;
          gap: 15px;
          font-size: $font-14;
          font-weight: $semiBold;
          color: $grey-500;

          .sign-in {
            cursor: pointer;
            &:after {
              content: '';
              display: inline-block;
              width: 1px;
              height: 10px;
              background-color: $line-lg;
              margin-left: 15px;
            }
          }

          .find-pw {
            cursor: pointer;
          }
        }
      }

      .line {
        width: 100%;
        height: 1px;
        margin: 10px 0;
      }
      .login-bottom {
        display: flex;
        flex-direction: column;
        gap: 15px;
        align-items: center;
        text-align: center;


        .language-wrap {
          width: 53%;
          display: flex;
          align-items: center;
          gap: 8px;

          .language-title {
            color: $grey-500;
            font-size: 13px;
            font-weight: 400;
            line-height: 14px; /* 107.692% */
          }
        }

        .company {
          color: $grey-500;
          font-size: 12px;
          font-weight: 400;
          line-height: 120%; /* 14.4px */
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .copyright {
          color: $grey-500;
          text-align: center;
          font-size: 12px;
          font-weight: 400;
        }
      }


      &.login {
        gap: 14px;

        .login-logo-wrap {
          position: relative;

          .knit-logo {
            display: block;
            text-align: center;
            margin-bottom: 24px;
            .app-logo {
              font-size: 28px;
              color: $mainColor;
            }
          }
        }

        .login-user-wrapper {
          display: flex;
          flex-direction: column;
          gap: 12px;

          .login-user {
            color: $grey-600;
            font-size: 22px;
            font-weight: 600;
            line-height: 120%; /* 26.4px */
          }

          .login-text {
            color: $grey-500;
            font-size: 15px;
            font-weight: 600;
            line-height: 150%; /* 22.5px */

            .llm-platform {
              color: #EC0047;
            }
          }
        }

        .start-btn {
          margin-top: 12px;
          display: inline-flex;
          padding: 14px 20px;
          justify-content: center;
          align-items: center;
          border-radius: 5px;
          height: fit-content;
        }

      }
    }
  }
}


@media all and (max-width: 1440px) {
  .login-wrap {
    background-size: 1108px;
    .login-container {
      .login-left {
        .text-wrapper {
          width: 741px;
          .knit-desc {
            font-size: 100px;
          }
        }
      }
    }
  }
}

.mobile {
  .login-wrap {
    padding: 0;
    height: 100dvh;
    .login-container {
      display: flex;
      .login-left {
        .text-wrapper {
          display: none;
        }
        .chatbot-btn-wrapper {
          display: none;
        }
      }
      .login-right-wrapper {
        width: 100%;
        .login-right {
          padding: 20px 24px;
          overflow-y: auto;
          border-radius: 0;
          width: 100%;
          justify-content: center;
          gap: 25px;

          &.login {
            gap: 68px;
            .login-top {
              margin-top: 130px;
              gap: 13px;
              .start-btn {
                margin-top: 8px;
                padding: 14px;
              }
              .auth-wrap {
                margin-top: 5px;
                font-size: 16px;
              }
            }
          }
          .login-top {
            margin-top: 100px;
            height: fit-content;
            justify-content: center;
            gap: 28px;

            .auth-wrap {
              margin-top: -2px;
            }

            .login-btn {
              margin-top: 12px;
            }
          }

          .line {
            margin-top: 8px;
            margin-bottom: 0;
          }

          .login-bottom {
            margin-top: -3px;
            gap: 12px;
            .language-wrap {
              width: 172px;
            }
            .company {
              margin-top: 8px;
            }
          }
        }
      }
    }
  }
}

@media (orientation: landscape) {
  .mobile {
    .login-wrap .login-container .login-right-wrapper {
      .login-right {
        flex-direction: row;
        align-items: center;
        .login-top {
          flex: 1 -0 50%;
          gap: 10px;
        }
        .line {
          display: none;
        }
      }
    }
  }
}
// @media all and (max-width: 768px) {
// }

</style>
