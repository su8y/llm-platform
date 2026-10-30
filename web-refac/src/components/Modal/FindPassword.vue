<script setup>
import { ref, reactive, inject, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from "vue-i18n";
import { useStore } from 'vuex'

import { changePassword, findPassword } from "@/api/user.js";

import {HTTP_CODES, ID_REG_EXP, PW_REG_EXP, SEND_MAIL_TYPE, SUCCESS_TYPE} from "@/libs/constants.js";
import SendMail from "@/components/Modal/SendMail.vue";
import Success from "@/components/Modal/Success.vue";

const store = useStore()
const router = useRouter()
const { t, locale } = useI18n()
const modal = inject('$modal')
const type = inject('modalContent')

const modalContent = ref(type.value.content)
const gapError = ref(false)
const inputs = reactive({
  userId: { label: t('register.id'), signIntype: 'userId', type: 'text', placeholder: t('findPassword.placeholder.userId'), value: null, isFocused: false, hasError: false },
  newPassword: { label: t('findPassword.label'), signIntype: 'password', type: 'password', placeholder: t('register.placeholder.password'), value: null, isFocused: false, hasError: false },
})
const errorText = reactive({
  userId: t('findPassword.error.required.userId'),
  password: t('findPassword.error.required.password'),
})

const isReset = computed(() => {
  return modalContent.value?.type === 'reset'
})

const isDisabled = computed(() => {
  return !inputs.userId.value && !inputs.newPassword.value
})

const isMobile = computed(() => store.state.isMobile)

const handleFocus = (type) => {
  if (type === 'id') {
    inputs.userId.isFocused = true
    inputs.userId.hasError = false
  } else {
    inputs.newPassword.isFocused = true
    inputs.newPassword.hasError = false
  }
}

const validateInput = (input) => {
  const validationRules = {
    userId: (value) => ID_REG_EXP.test(value),
    password: (value) => PW_REG_EXP.test(value)
  }

  let errorMessage = {
    userId: t('findPassword.error.regExp.userId'),
    password: t('register.error.regExp.password')
  }

  if (!input.value) {
    errorText[input.signIntype] = errorMessage[input.signIntype] || t('findPassword.error.required.required')
    return false
  } else if (validationRules[input.signIntype] && !validationRules[input.signIntype](input.value)) {
    errorText[input.signIntype] = errorMessage[input.signIntype] || t('register.error.regExp.required')
    return false
  }

  return true
}

const onFindPassword = async () => {
  let allValid = true

  inputs.userId.hasError = !validateInput(inputs.userId)
  if (inputs.userId.hasError) {
    allValid = false
  }

  if (allValid) {
    const params = {
      userId: inputs.userId.value,
      lang: locale.value
    }
    try {
      await findPassword(params).then(res => {
        if (res.code === HTTP_CODES.SUCCESS) {
          modal.open(SendMail, {type: SEND_MAIL_TYPE.SEND_RESET_PASSWORD, content: res.data.emailAddress})
        } else {
          if (res.code === HTTP_CODES.NOT_REGISTERED_ID) {
            inputs.userId.hasError = true
            errorText.userId = t('register.error.notRegistered.id')
          }
          console.log(`ERROR: ${res.code} ${res.message}`)
        }
      })
    } catch (e) {
      console.error(e)
    }
  }
}

const resetPassword = async () => {
  let allValid = true
  inputs.newPassword.hasError = !validateInput(inputs.newPassword)

  if (inputs.newPassword.hasError) {
    allValid = false
  }

  if (allValid) {
    const params = {
      userId: modalContent.value.userId,
      userPassword: inputs.newPassword.value,
      acceptance: modalContent.value.findKey
    }

    try {
      const res = await changePassword(params)
      if (res.code === HTTP_CODES.SUCCESS) {
        modal.open(Success, SUCCESS_TYPE.CHANGE_PASSWORD).then(() => {
          router.push({ name: 'LoginView' })
        })
      } else {
        console.log(`ERROR: ${res.code} ${res.message}`)
      }
    } catch (e) {
      console.error(`Error: ${e}`)
    }
  }
}

const handleSave = async () => {
  if (isReset.value) {
    await resetPassword()
  } else {
    await onFindPassword()
  }
}


</script>

<template>
  <div class="find-password-container" :class="{isMobile}">
    <div class="find-password-wrap flex flex-column xy-center">
      <div class="logo-wrap">
        <span class="be-icon icon-grey-xs size-50">
          <i class="font-icon-reset-pw" />
        </span>
        <h3 class="sign-in be-font size-20 semi-bold">
          {{ $t('findPassword.title') }}
        </h3>
      </div>
      <div class="input-wrap">
        <div class="input-container flex x-center flex-column">
          <template v-if="!isReset">
            <UiInput
                :input-style="(inputs.userId.hasError && gapError) ? 'error' : null"
                :type="inputs.userId.type"
                :placeholder="inputs.userId.placeholder"
                v-model="inputs.userId.value"
                @focus="handleFocus('id')"
                @updateValue="inputs.userId.value = $event"
                @enter="onFindPassword">
              <template #label>
                {{ inputs.userId.label }}
              </template>
              <template #error v-if="inputs.userId.hasError || gapError">
                <span class="error-text">
                  {{ errorText[inputs.userId.signIntype] }}
                </span>
              </template>
            </UiInput>
          </template>
          <template v-else>
            <UiInput
                :input-style="(inputs.newPassword.hasError && gapError) ? 'error' : null"
                :type="inputs.newPassword.type"
                :placeholder="inputs.newPassword.placeholder"
                v-model="inputs.newPassword.value"
                @focus="handleFocus('pw')"
                @updateValue="inputs.newPassword.value = $event"
                @enter="resetPassword">
              <template #label>
                {{ inputs.newPassword.label }}
              </template>
              <template #error v-if="inputs.newPassword.hasError || gapError">
                <span class="error-text">
                  {{ errorText[inputs.newPassword.signIntype] }}
                </span>
              </template>
            </UiInput>
          </template>
        </div>
      </div>
    </div>
    <div class="btn-wrap flex xy-center" :class="{isReset}">
      <UiButton :type="'outline'" @click="modal.close()">
        {{ $t('common.cancel') }}
      </UiButton>
      <UiButton :type="'icon primary'" :disabled="isDisabled" @click="handleSave">
        {{ isReset ? $t('common.confirm') : $t('common.next') }}
      </UiButton>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.find-password-container {
  min-width: 400px;
  padding: 30px 30px 5px 30px;

  &.isMobile {
    min-width: initial;
  }
  .find-password-wrap {
    width: 100%;
    height: 100%;

    .logo-wrap {
      text-align: center;
      .sign-in {
        margin-top: 10px;
      }
    }

    .input-wrap {
      width: 309px;
      padding-top: 30px;

      .input-container {
        width: 100%;
        position: relative;
        gap: 5px;
      }
    }
  }

  .btn-wrap {
    margin-top: 58px;
    gap: 10px;

    &.isReset {
      margin-top: 74px;
    }
  }
}
</style>

