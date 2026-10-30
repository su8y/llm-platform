<script setup>
import {ref, reactive, onBeforeMount, onMounted, inject} from "vue";
import { useStore } from "vuex";
import {useRoute, useRouter} from 'vue-router';
import { useI18n } from 'vue-i18n';

import {getInviteInfo, login} from "@/api/user.js";
import {changeLocale, getLocaleMessages} from "@/libs/i18n.js";
import { HTTP_CODES, SUCCESS_TYPE, WARNING_TYPE } from "@/libs/constants.js";
import { removeAuthData, setAuthToken} from "@/libs/auth-helper.js";
import { setPlanAlertCookie } from "@/libs/utils.js";

import Login from '@/components/Login.vue'
import Success from "@/components/Modal/Success.vue";
import SignInModal from "@/components/Modal/Register.vue";
import Warning from "@/components/Modal/Warning.vue";
import FindPassword from "@/components/Modal/FindPassword.vue";
import {useChatbotSessionKey} from "@/composables/useChatbotSessionKey.js";


const router = useRouter()
const route = useRoute()
const store = useStore()
const i18n = useI18n()
const modal = inject('$modal')
const query = route.query
const { t, setLocaleMessage, locale } = i18n
const { getChatbotSessionKey } = useChatbotSessionKey()

const userData = ref(null)
const error = reactive({
  text: null,
  id: false,
  password: false
})

onBeforeMount(async () => {
  if (!route.query.certification) {
    userData.value = await store.dispatch('storeUserData')
  }
})

onMounted(async () => {
  // register certify
  const queryEntries = Object.entries(query);
  const [firstKey, firstValue] = queryEntries[0] || [];
  const [secondKey, secondValue] = queryEntries[1] || [];

  switch (firstKey) {
    case 'certification':
      if (firstValue === 'True') {
        if (localStorage.getItem('isReloaded') !== 'true') {
          localStorage.setItem('isReloaded', 'true'); // Reload 여부를 'true'로 설정
          await changeLocale(i18n, secondValue);
          i18n.locale.value = secondValue;
          location.reload();
        } else {
          // Reload 이후 실행되는 코드
          modal.open(Success, SUCCESS_TYPE.AUTHENTICATION_EMAIL);
          localStorage.removeItem('isReloaded')
        }
      }
      break
    case 'invitation':
      if (firstValue === 'True') { // 초대 기간 유효
        const params = {
          params: {
            invitationKey: query.invitationKey
          }
        }
        try {
          const res = await getInviteInfo(params)

          if (res.code === HTTP_CODES.SUCCESS) {
            modal.open(SignInModal, res.data)
            await changeLocale(i18n, res.data.lang)
          } else {
            alert(res.message)
            console.log('Error: ', res)
          }
        } catch (e) {
          alert(e)
          console.error('Error: ', e)
        }
      } else if (firstValue === 'Expired') {  // 초대 기간 만료
        modal.open(Warning, WARNING_TYPE.EXPIRATION_INVITATION)
      }
      break
    case 'changePassword':
      if (firstValue === 'true') {
        modal.open(FindPassword, {type: 'reset', findKey: secondValue, userId: query.userId})
      } else {
        modal.open(Warning, WARNING_TYPE.PASSWORD_LINK_EXPIRED)
      }
      break
    case 'register':
      if (firstValue === 'True') {
        if(locale.value !== secondValue){
          const messages = getLocaleMessages(secondValue,'en')
          await changeLocale(i18n, secondValue)
          setLocaleMessage(secondValue, messages)
          document.documentElement.setAttribute('lang', secondValue)
          locale.value = secondValue;
        }
        modal.open(SignInModal)
      } else {
        await router.push('/')
      }
      break
    case 'findPassword':
      if (firstValue === 'True') {
        modal.open(FindPassword)
      }
      break
  }
})

const signIn = async (params) => {
  try {
    const res = await login(params)

    switch (res.code) {
      case HTTP_CODES.SUCCESS:
        setAuthToken(res.data)
        setPlanAlertCookie(true)
        userData.value = await store.dispatch('storeUserData')
        router.push({ name: 'LoginView' })
        break
      case HTTP_CODES.NOT_REGISTERED_ID:
        error.id = true
        error.text = t('register.error.notRegistered.id')
        break
      case HTTP_CODES.NOT_REGISTERED_PASSWORD:
        error.password = true
        error.text = t('register.error.notRegistered.password')
        break
      case HTTP_CODES.NOT_CERTIFIED_EMAIL:
        modal.open(Warning, WARNING_TYPE.CERTIFICATION_EMAIL)
        break
    }
  } catch (e) {
    console.error(e)
    alert(e.response.data.msg)
  }
}

const signOut = () => {
  store.commit('clearAllUserData')
  removeAuthData()
  location.reload()
}
</script>

<template>
  <Login
      :user-data="userData"
      :error="error"
      @login="signIn"
      @logout="signOut"
      @getChatbotKey="getChatbotSessionKey(true)"
  />
</template>

<style scoped>
</style>
