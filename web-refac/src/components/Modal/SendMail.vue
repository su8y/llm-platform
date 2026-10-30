<script setup>
import { supportContact } from '@/libs/support.js'
import { ref, computed, inject } from "vue";
import { useI18n } from 'vue-i18n'

import { SEND_MAIL_TYPE } from '@/libs/constants.js'

const props = defineProps({
  resolve: Function, // Promise resolve
  reject: Function,  // Promise reject
})

const { t } = useI18n()

const {
  SEND_INVITE,
  SEND_REGISTER,
  SEND_RESET_PASSWORD,
  SEND_AI_EMAIL
} = SEND_MAIL_TYPE

const modal = inject('$modal')
const type = inject('modalContent')

const isInvite = ref(type.value.content === SEND_INVITE)
const modalContent = ref(type.value.content?.type ? type.value.content.type : type.value.content)
const isAiEmail = ref(modalContent.value === SEND_AI_EMAIL)

const title = computed(() => {
  switch (modalContent.value) {
    case SEND_REGISTER:
      return t('modal.sendMail.register.title')
    case SEND_INVITE:
      return t('modal.sendMail.invite.title')
    case SEND_RESET_PASSWORD:
      return t('modal.sendMail.resetPassword.title')
    case SEND_AI_EMAIL:
      return t('modal.checkReply')
    default:
      return null
  }
})

const desc = computed(() => {
  switch (modalContent.value) {
    case SEND_REGISTER:
      return t('modal.sendMail.register.desc', { email: supportContact()})
    case SEND_INVITE:
      return t('modal.sendMail.invite.desc')
    case SEND_RESET_PASSWORD:
      return t('modal.sendMail.resetPassword.desc')
    default:
      return null
  }
})

const handleConfirm = () => {
  if (props.resolve) props.resolve(true); // Confirm 처리
}

const handleCancel = () => {
  modal.close()
}
</script>

<template>
  <div  class="send-mail-container">
    <div class="send-mail-wrap flex flex-column xy-center">
      <div class="title-wrap">
        <i class="icon icon--send-mail"></i>
          <h3 class="title be-font size-20 semi-bold text-grey-lg" v-html="title"></h3>
      </div>
      <template v-if="type.content?.type">
        <p class="email-masking" v-html="type.content.content"></p>
      </template>
      <template v-if="!isAiEmail">
        <div class="desc flex flex-column xy-center" :class="{'invite-text': isInvite, 'password': type.content?.type }">
          <p class="text1 be-font" v-html="desc">
          </p>
        </div>
      </template>
    </div>
    <div class="btn-wrap flex x-center">
      <template v-if="isInvite">
        <UiButton class="cancel-btn" :type="'primary'" @click="handleConfirm">{{ t('common.confirm') }}</UiButton>
      </template>
      <template v-else-if="isAiEmail">
        <UiButton class="cancel-btn" :type="'primary'" @click="handleConfirm">{{ t('common.confirm') }}</UiButton>
        <UiButton class="cancel-btn" :type="'outline'" @click="handleCancel">{{ t('common.cancel') }}</UiButton>
      </template>
      <template v-else>
        <UiButton class="cancel-btn" :type="'primary'" @click="modal.close()">{{ t('common.confirm') }}</UiButton>
      </template>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.send-mail-container {
  padding: 20px 20px 5px;
  min-width: 400px;
  .send-mail-wrap {
    width: 100%;
    height: 100%;
    margin-bottom: 20px;

    .title-wrap {
      text-align: center;
      .title {
        margin-top: 10px;
      }
    }

    .email-masking {
      padding-top: 12px;
      font-size: 14px;
      font-weight: 400;
      line-height: 150%; /* 1.5rem */
    }

    .desc {
      padding-top: 30px;
      text-align: center;
      margin-bottom: 20px;

      &.invite-text, &.password {
        padding-top: 12px;
      }

      p {
        line-height: 150%;
      }
    }
  }

  .btn-wrap {
    gap: 10px;
  }
}
</style>

