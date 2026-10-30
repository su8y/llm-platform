<script setup>
import {ref, inject, computed, reactive, nextTick} from 'vue';
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from "vue-i18n";
import { useStore } from 'vuex';
import AppLogo from "@/components/AppLogo.vue";

import { register } from "@/api/user.js";
import { HTTP_CODES, SEND_MAIL_TYPE, ID_REG_EXP, PW_REG_EXP, EMAIL_REG_EXP, LANGUAGE_LIST } from '@/libs/constants.js'
import {changeLocale, getLocaleMessages} from '@/libs/i18n';

import SendMail from "@/components/Modal/SendMail.vue";
import Loading from "@/components/Modal/Loading.vue";

const modal = inject('$modal')
const modalContent = inject('modalContent')
const {query, path} = useRoute()
const router = useRouter()
const i18n = useI18n()
const store = useStore()
const { t, locale,setLocaleMessage } = i18n

const isRegAgree = ref(false)
const gapError = ref(false)
const isLoading = ref(false)
const isLanguageList = ref(false)
const inputs = reactive([
  { label: 'register.id', signIntype: 'userId', type: 'text', placeholder:'register.placeholder.userId', value: null, isFocused: false, hasError: false, isDisabled: false },
  { label: 'register.password', signIntype: 'password', type: 'password', placeholder: 'register.placeholder.password', value: null, isFocused: false, hasError: false, isDisabled: false },
  { label: 'register.passwordConfirm', signIntype: 'passwordCheck', type: 'password', placeholder: '', value: null, isFocused: false, hasError: false, isDisabled: false },
  { label: 'register.email', signIntype: 'email', type: 'email', placeholder: 'register.placeholder.email', value: modalContent.value ? modalContent.value.content?.emailAddress : null, isFocused: false, hasError: false, isDisabled: modalContent.value && !!modalContent.value.content },
  { label: 'register.companyName', signIntype: 'company', type: 'text', placeholder: 'register.placeholder.company', value: modalContent.value ? modalContent.value.content?.companyName : null, isFocused: false, hasError: false, isDisabled: modalContent.value &&  !!modalContent.value.content },
  { label: 'register.department', signIntype: 'department', type: 'text', placeholder: 'register.placeholder.department', value: null, isFocused: false, isDisabled: false },
  {signIntype: 'agree', value:isRegAgree}
])
const errorText = reactive({
  userId: 'register.error.regExp.userId',
  password: 'register.error.regExp.password',
  passwordCheck: 'register.error.regExp.passwordCheck',
  email: 'register.error.regExp.email',
  company: 'register.error.regExp.company',
})

const currentLocale = computed(() => {
  return modalContent.value && modalContent.value.content?.lang === locale.value
      ? modalContent.value.content?.lang
      : locale.value
})
const isMobile = computed(() => store.state.isMobile)

const handleFocus = (index) => {
  inputs[index].isFocused = true
  inputs[index].hasError = false
}

const validateInput = (input, passwordValue) => {
  const validationRules = {
    userId: (value) => ID_REG_EXP.test(value),
    password: (value) => PW_REG_EXP.test(value),
    passwordCheck: (value) => value === passwordValue,
    email: (value) => EMAIL_REG_EXP.test(value),
    agree: (value) => value === true
  }

  let errorMessages = {
    userId: 'register.error.required.userId',
    password: 'register.error.required.password',
    passwordCheck: 'register.error.required.passwordCheck',
    email: 'register.error.required.email',
    company: 'register.error.required.company',
    agree: 'register.error.required.agree'
  }

  if (!input.value) {
    if (input.signIntype !== 'department') {
      errorText[input.signIntype] = errorMessages[input.signIntype] || 'register.error.required.required'
      return false
    }
  } else if (validationRules[input.signIntype] && !validationRules[input.signIntype](input.value)) {
    return false
  }

  return true
}

const createAccount = async () => {
  isLoading.value = true
  let allValid = true
  const passwordValue = inputs.find(i => i.signIntype === 'password')?.value

  inputs.forEach((input) => {
    input.hasError = !validateInput(input, passwordValue)
    if (input.hasError) {
      isLoading.value = false
      allValid = false
    }
  })

  if (allValid) {
    const params = inputs.reduce((acc, input) => {
      switch (input.signIntype) {
        case 'userId':
          acc.user_id = input.value
          break
        case 'password':
          acc.user_password = input.value
          break
        case 'email':
          acc.email_address = input.value
          break
        case 'company':
          acc.company_name = input.value
          break
        case 'department':
          acc.department = input.value
          break
        default:
          break
      }
      return acc
    }, {})

    if (query) {
      params.invitationKey = query.invitationKey
    }
    params.lang = currentLocale.value

    try {
      const res = await register(params)

      const error = res.code
      switch (error) {
        case HTTP_CODES.DUPLICATED.ID:
          isLoading.value = false
          inputs[0].hasError = true
          errorText.userId = 'register.error.duplicated.userId'
          break
        case HTTP_CODES.DUPLICATED.EMAIL:
          isLoading.value = false
          inputs[3].hasError = true
          errorText.email = 'register.error.duplicated.email'
          break
        case HTTP_CODES.DUPLICATED.COMPANY:
          isLoading.value = false
          inputs[4].hasError = true
          errorText.company = 'register.error.duplicated.company'
          break
        case HTTP_CODES.BAD_REQUEST:
        case HTTP_CODES.SERVER:
          isLoading.value = false
          alert(res.message)
          inputs[0].hasError = true
          inputs[3].hasError = true
          inputs[4].hasError = true
          break
        default:
          isLoading.value = false
          modal.open(SendMail, SEND_MAIL_TYPE.SEND_REGISTER)
          router.push({ name: 'LoginView' })
      }

    } catch (e) {
      isLoading.value = false
      console.error('Error: ', e)
    }
  }
}

const onLocaleChange = (lang) => {
  const messages = getLocaleMessages(lang,'en')
  changeLocale(i18n, lang)
  setLocaleMessage(lang, messages)
  locale.value = lang;
  isLanguageList.value = false
  router.replace({
    path: path,
    query: {
      ...query,
      isModal: true,
      lang: lang
    }
  })
  document.documentElement.setAttribute('lang', lang)
}

const exitRegister = () => {
  if (query.register || query.isModal || query.lange ) {
    router.replace(path)
  } else {
    isMobile.value ? router.push('/') : modal.close()
  }
}

const policyText = computed(() => {
  return t('register.agree').replaceAll('%%locale%%', locale.value)
})
</script>

<template>
  <template v-if="isLoading">
    <div class="section-body-loading">
      <i class="icon icon--loading-animated"/>
    </div>
  </template>
  <template v-else>

    <div class="sign-in-wrap flex y-between" @click="isLanguageList = false">
      <template v-if="isMobile">
          <span class="sign-in-header icon-wrap">
            <AppLogo />
            <template v-if="isMobile">
              <i class="font-icon-close" @click="router.push('/')"/>
            </template>
          </span>
      </template>
      <div class="logo-wrap flex flex-column">
        <template v-if="!isMobile">
            <span class="icon-wrap">
              <AppLogo />
            </span>
        </template>
        <h3 class="sign-in be-font semi-bold size-40" :class="{isMobile}">
          {{ t('register.title') }}
        </h3>
        <span class="sign-in-desc" :class="{isMobile}" v-html="t('register.desc')"></span>
        <template v-if="!isMobile">
          <div class="line horizontal"></div>
        </template>
        <template v-if="!isMobile">
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
        </template>
      </div>
      <div class="input-wrap flex x-center flex-column">
        <div class="form-group flex x-center flex-column">
          <div class="input-container"  v-for="(input, index) in inputs.filter(i => i.signIntype !== 'agree')" :key="input.label">
            <UiInput
                :class="isMobile ? 'font-16' : ''"
                :value="input.value"
                :index="index"
                :input-style="input.hasError && input.signIntype !== 'department' && 'error'"
                :type="input.type"
                :placeholder="t(input.placeholder)"
                :disabled="input.isDisabled"
                @focus="handleFocus(index)"
                @updateValue="input.value = $event">
              <template #label>
                {{ t(input.label) }}<span v-if="input.signIntype !== 'department'">*</span>
              </template>
              <template #error v-if="input.hasError || gapError">
                  <span class="error-text">
                    {{ t(errorText[input.signIntype]) }}
                  </span>
              </template>
            </UiInput>
          </div>
        </div>
        <div class="chek-group">
          <div class="default-chk-box agree-chk">
            <input
                type="checkbox"
                id="agreePersonal"
                v-model="isRegAgree" />
            <label for="agreePersonal"><span class="label" v-html="policyText"></span></label>
          </div>
          <span class="error-agree-text" v-if="errorText.agree && !isRegAgree">{{ t(errorText.agree) }}</span>
        </div>
        <div class="btn-wrap flex">
          <template v-if="!isMobile">
            <UiButton :type="'outline'" @click="exitRegister">
                <span>
                  {{ t('common.cancel2') }}
                </span>
            </UiButton>
            <UiButton :type="'icon primary'" @click="createAccount">
              <i class="font-icon-save"/>
              {{ t('common.save2') }}
            </UiButton>
          </template>
          <template v-else>
            <div class="footer-wrapper">
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
            <UiButton :type="'primary widthFull'" @click="createAccount">
              {{ t('register.title') }}
            </UiButton>
          </template>
        </div>
      </div>
    </div>
  </template>
</template>

<style lang="scss" scoped>
.sign-in-wrap {
  width: 680px;
  gap: 60px;
  padding: 20px 20px 0;

  .logo-wrap {
    width: 100%;
    gap: 22px;

    .sign-in {
      color: #555;
      margin-top: 27px;
    }

    .sign-in-desc {
      color: $grey-500;
      font-size: 15px;
      font-weight: 600;
      line-height: 150%; /* 22.5px */
    }

    .language-wrap {
      width: 40%;
      display: flex;
      flex-direction: column;
      gap: 8px;

      .language-title {
        color: $grey-500;
        font-size: 13px;
        font-weight: 400;
        line-height: 14px; /* 107.692% */
      }
    }
  }

  .input-wrap {
    gap: 20px;

    .form-group {
      gap: 32px;
      padding-top: 13px;
    }

    .input-container {
      width: 318px;
    }

    .chek-group {
      display: flex;
      flex-direction: column;
      gap: 7px;
      .default-chk-box {
        &:deep {
          a {
            text-decoration: underline;
          }
        }
      }
      .error-agree-text {
        display: block;
        margin-left: 23px;
        color: red;
        font-size: 12px;
      }
    }
  }
}

.btn-wrap {
  margin-top: 20px;
  justify-content: center;
  gap: 4px;
}

.mobile {
  .sign-in-wrap {
    width: 100%;
    align-items: center;
    flex-direction: column;
    background-color: #fff;
    gap: 34px;
    padding: 12px 13px;

    .sign-in-header {
      width: 100%;
      padding: 0 13px;
      position: fixed;
      top: 0;
      z-index: 999;
      height: 56px;
      background-color: #fff;

      &::before {
        content: '';
        position: absolute;
        top: 100%;
        left: 0;
        width: 100%;
        height: 12px;
        background: linear-gradient(0, rgba(255, 255, 255, 0.00) 0%, rgba(0, 0, 0, 0.06) 100%);
        z-index: 100;
      }

      &.icon-wrap {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 19px;

        .app-logo {
          font-size: 20px;
          margin-left: 3px;
        }

        .font-icon-close {
          color: #666;
          font-size: 30px;
        }
      }
    }

    .logo-wrap {
      gap: 14px;
      margin-top: 75px;

      .sign-in.isMobile, .sign-in-desc.isMobile {
        margin: 0 auto;
        text-align: center;
      }

      .sign-in.isMobile {
        color: #1E1E1E;
        font-size: 30px;
        font-weight: 600;
      }

      .sign-in-desc.isMobile {
        color: #444;
        font-size: 13px;
        font-weight: 400;
        line-height: 150%; /* 19.5px */
      }
    }

    .input-wrap {
      gap: 28px;
      padding: 0 9px;
      width :100%;
      .input-container {
        width: 100%;
      }
    }

    .btn-wrap {
      flex-direction: column;
      gap: 34px;
      justify-content: center;
      margin-top: 8px;

      .language-wrap {
        width: 172px;
        max-height: 100px;
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 8px;

        .language-title {
          color: $grey-500;
          font-size: 13px;
          font-weight: 400;
          line-height: 14px; /* 107.692% */
        }

        .list {
          max-height: 100px;

          li {
            padding: 8px 9px;
          }
        }
      }
    }

    .footer-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;


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
      }
    }
  }
}
// @media all and (max-width: 768px) {
// }

</style>

