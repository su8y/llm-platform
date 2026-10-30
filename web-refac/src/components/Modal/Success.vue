<script setup>
import { inject, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { SUCCESS_TYPE } from '@/libs/constants.js'

const props = defineProps({
  resolve: Function, // Promise resolve
  reject: Function,  // Promise reject
})

const router = useRouter()
const modal = inject('$modal')
const type = inject('modalContent')
const { t } = useI18n()

const state = reactive({
  title: '',
  desc: '',
  leftBtn: '',
  rightBtn: '',
  className: '',
  isCloseIcon: false
})

const {
  AUTHENTICATION_EMAIL,
  TEMPORARY_SAVE,
  SEND_MAIL,
  CHANGE_PASSWORD
} = SUCCESS_TYPE

const modalConfig = {
  [AUTHENTICATION_EMAIL]: {
    title: 'modal.success.authenticationEmail.title',
    leftBtn: 'common.close'
  },
  [TEMPORARY_SAVE]: {
    title: 'modal.success.temporarySave.title',
    desc: 'modal.success.temporarySave.desc',
    leftBtn: 'common.close',
  },  [SEND_MAIL]: {
    title: 'penpal.detail.sendSuccess',
    leftBtn: 'common.close'
  },
  [CHANGE_PASSWORD]: {
    title: 'modal.success.resetPassword.title',
    desc: 'modal.success.resetPassword.desc',
    leftBtn: 'common.close'
  },
  default: {
    title: 'modal.warning.cancel.title',
    desc: 'modal.warning.cancel.desc',
    leftBtn: 'common.close',
    rightBtn: 'common.cancel'
  }
}

const setModalState = (type) => {
  const config = modalConfig[type.value.content] || modalConfig.default

  state.className = config.className || ''

  state.isCloseIcon = config.isCloseIcon || false

  state.title = t(config.title)

  if (config.desc) state.desc = t(config.desc)

  if (config.leftBtn) state.leftBtn = t(config.leftBtn)

  if (config.rightBtn) state.rightBtn = t(config.rightBtn)
}

setModalState(type)

const btnAction = (direction) => {
  const isRight = direction === 'right'
  switch (type.value.content) {
    case SEND_MAIL:
      router.push({ name: 'PenpalList' })
      break
    case AUTHENTICATION_EMAIL:
      modalClose()
      break
    case TEMPORARY_SAVE:
    case CHANGE_PASSWORD:
      handleConfirm()
      break
    default:
      if (isRight) {
        modalClose()
      } else {
        modalClose()
      }
  }
}

const modalClose = () => {
  if (type.value.content === AUTHENTICATION_EMAIL) {
    router.replace('/')
  }
  modal.close()
}

const handleConfirm = () => {
  if (props.resolve) props.resolve(true); // Confirm 처리
}
</script>


<template>
  <div :class="`send-mail-container ${state.className}`">
    <button type="button" class="icon icon--close-size16 color-444"  v-if="state.isCloseIcon" @click="modalClose"></button>
    <div class="send-mail-wrap">
      <div class="title-wrap">
        <i class="icon icon--success"></i>
        <h3 class="title" v-html="state.title"></h3>
      </div>
      <div class="desc">
        <p class="text1" v-html="state.desc"></p>
      </div>
    </div>
    <div class="btn-wrap">
      <UiButton v-if="state.leftBtn" :type="'outline'" @click="btnAction('left')">
        {{ state.leftBtn }}
      </UiButton>
      <UiButton v-if="state.rightBtn" :type="'primary'" @click="btnAction('right')">
        {{ state.rightBtn }}
      </UiButton>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.send-mail-container {
  min-width: 400px;
  padding: 30px 30px 5px;
  .send-mail-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    width: 100%;
    height: 100%;
    margin-bottom: 20px;

    .title-wrap {
      text-align: center;
      font-size: $font-50;

      .font-icon-error {
        color: $common-red;
      }

      .title {
        margin-top: 10px;
        font-size: 24px;
        font-weight: 500;
        color: #444;
      }
    }

    .desc {
      display: flex;
      justify-content: center;
      align-items: center;
      flex-direction: column;
      padding-top: 30px;
      text-align: center;
      margin-bottom: 20px;

      p {
        white-space: normal;
        word-break: keep-all;
        font-size: 14px;
        font-weight: 500;
        color: #444;

        &.text2 {
          width: 230px;
        }
      }
    }
  }

  .btn-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
  }

  .icon--close-size16{
    position: absolute;
    top:14px;
    right: 14px;
  }
}

/* 768px 모바일 */
@media all and (max-width: 768px) {
  .send-mail-container {  }
}
</style>

