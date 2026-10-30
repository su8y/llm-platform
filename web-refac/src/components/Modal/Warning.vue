<script setup>
import { supportContact } from '@/libs/support.js'
import { inject, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { WARNING_TYPE } from '@/libs/constants.js'

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
  desc2: '',
  leftBtn: '',
  rightBtn: '',
})

const {
  AUTHORITY,
  SECESSION,
  REFERENCE_DELETE,
  CERTIFICATION_EMAIL,
  EXPIRATION_INVITATION,
  CATEGORY_DELETE,
  CATEGORY_USE_REFERENCE,
  DUPLICATED_EMAIL,
  INVALID_EMAIL,
  DUPLICATED_RE_INVITE,
  EMPTY_DUPLICATED_CATEGORY,
  EDIT_CATEGORY,
  CHILD_CATEGORY_EXISTENCE,
  FILE_UPLOAD_ERROR,
  PARSER_CREDIT_ERROR,
  CATEGORY_SAVE,
  PLAN_CANCEL,
  DELETE,
  UPDATE_PDF_FILE,
  UPDATE_PDF_CANCEL,
  DELETE_PDF_FILE,
  REQUIRED_COMMENT,
  SEND_CONFIRM,
  PASSWORD_LINK_EXPIRED,
  ATTACHMENT_ERROR,
  SEND_MAIL_ERROR,
  HAS_THREAD,
  EMAIL_COUNT_ERROR,
  FAILED_SEND_MAIL
} = WARNING_TYPE

const modalConfig = {
  [AUTHORITY]: {
    title: 'modal.warning.authority.title',
    desc: 'modal.warning.authority.desc',
    leftBtn: 'common.cancel',
    rightBtn: 'common.change'
  },
  [SECESSION]: {
    title: 'modal.warning.secession.title',
    desc: 'modal.warning.secession.desc',
    leftBtn: 'common.cancel',
    rightBtn: 'members.column.withdrawal'
  },
  [REFERENCE_DELETE]: {
    title: 'modal.warning.referenceDelete.title',
    desc: 'modal.warning.referenceDelete.desc',
    leftBtn: 'common.cancel',
    rightBtn: 'common.delete'
  },
  [CERTIFICATION_EMAIL]: {
    title: 'modal.warning.certificationEmail.title',
    desc: 'modal.warning.certificationEmail.desc',
    leftBtn: 'common.close'
  },
  [EXPIRATION_INVITATION]: {
    title: 'modal.warning.expirationInvitation.title',
    desc: 'modal.warning.expirationInvitation.desc',
    leftBtn: 'common.close'
  },
  [CATEGORY_DELETE]: {
    title: 'modal.warning.deleteCategory.title',
    leftBtn: 'common.cancel',
    rightBtn: 'common.delete'
  },
  [CATEGORY_USE_REFERENCE]: {
    title: 'modal.warning.childCategoryExistence.title',
    desc: 'modal.warning.childCategoryExistence.desc',
    leftBtn: 'common.close'
  },
  [DUPLICATED_EMAIL]: {
    title: 'modal.warning.duplicatedEmail.title',
    desc: 'modal.warning.duplicatedEmail.desc',
    leftBtn: 'common.close'
  },
  [INVALID_EMAIL]: {
    title: 'modal.warning.invalidEmail.title',
    desc: 'modal.warning.invalidEmail.desc',
    leftBtn: 'common.close'
  },
  [DUPLICATED_RE_INVITE]: {
    title: 'modal.warning.duplicatedReInvite.title',
    desc: 'modal.warning.duplicatedReInvite.desc',
    leftBtn: 'common.close'
  },
  [EMPTY_DUPLICATED_CATEGORY]: {
    title: 'modal.warning.emptyDuplicatedCategory.title',
    desc: 'modal.warning.emptyDuplicatedCategory.desc',
    leftBtn: 'common.close'
  },
  [EDIT_CATEGORY]: {
    title: 'modal.warning.editCategory.title',
    desc: 'modal.warning.editCategory.desc',
    leftBtn: 'common.close'
  },
  [CHILD_CATEGORY_EXISTENCE]: {
    title: 'modal.warning.childCategoryExistence.title',
    desc: 'modal.warning.childCategoryExistence.desc',
    leftBtn: 'common.close'
  },
  [FILE_UPLOAD_ERROR]: {
    title: 'modal.warning.fileUploadError.title',
    desc: 'modal.warning.fileUploadError.desc',
    leftBtn: 'common.close'
  },
  [PARSER_CREDIT_ERROR]: {
    title: 'modal.warning.parserCreditError.title',
    desc: 'modal.warning.parserCreditError.desc',
    descParams: { email: supportContact()},
    leftBtn: 'common.close'
  },
  [CATEGORY_SAVE]: {
    title: 'modal.save',
    leftBtn: 'common.cancel',
    rightBtn: 'common.save'
  },
  [PLAN_CANCEL]: {
    title: 'modal.warning.planCancel.title',
    desc: 'modal.warning.planCancel.desc',
    descParams: { email: supportContact() },
    leftBtn: 'common.close'
  },
  [DELETE]: {
    title: 'modal.warning.delete.title',
    desc: 'modal.warning.delete.desc',
    leftBtn: 'common.cancel',
    rightBtn: 'common.delete'
  },
  [UPDATE_PDF_FILE]: {
    title: 'modal.warning.updatePdfFile.title',
    desc: 'modal.warning.updatePdfFile.desc1',
    descParams: {pages: type.value.content?.pages?.join(', ')},
    desc2: 'modal.warning.updatePdfFile.desc2',
    leftBtn: 'common.cancel',
    rightBtn: 'common.save'
  },
  [UPDATE_PDF_CANCEL]: {
    title: 'modal.warning.updatePdfCancel.title',
    desc: 'modal.warning.updatePdfCancel.desc',
    leftBtn: 'common.cancel',
    rightBtn: 'common.confirm'
  },
  [DELETE_PDF_FILE]: {
    title: 'modal.warning.deletePdfFile.title',
    desc: 'modal.warning.deletePdfFile.desc',
    leftBtn: 'common.cancel',
    rightBtn: 'common.delete'
  },
  [SEND_CONFIRM]: {
    title: 'penpal.detail.sendConfirm',
    desc: 'penpal.detail.toMail',
    descParams: {email: type.value.content?.email},
    leftBtn: 'common.cancel',
    rightBtn: 'common.confirm'
  },
  [REQUIRED_COMMENT]: {
    title: 'penpal.detail.requiredComment',
    leftBtn: 'common.confirm'
  },
  [PASSWORD_LINK_EXPIRED]: {
    title: 'modal.warning.passwordExpired.title',
    desc: 'modal.warning.passwordExpired.desc',
    leftBtn: 'common.close'
  },
  [ATTACHMENT_ERROR]: {
    title: 'modal.warning.attachmentError.title',
    desc: 'modal.warning.attachmentError.desc',
    leftBtn: 'common.close'
  },
  [SEND_MAIL_ERROR]: {
    title: 'modal.warning.sendMailError.title',
    desc: 'modal.warning.sendMailError.desc',
    descParams: {type: Array.isArray(type.value.content?.required) ? type.value.content?.required.join('/') : type.value.content?.required},
    leftBtn: 'common.edit2'
  },
  [HAS_THREAD]: {
    title: 'modal.warning.checkBeforeEmail.title',
    desc: 'modal.warning.checkBeforeEmail.desc',
    leftBtn: 'common.cancel',
    rightBtn: 'common.confirm'
  },
  [EMAIL_COUNT_ERROR]: {
    title: 'modal.warning.emailCountError.title',
    leftBtn: 'common.confirm'
  },
  [FAILED_SEND_MAIL]: {
    title: 'modal.warning.failedSendMail.title',
    desc: 'modal.warning.failedSendMail.desc',
    descParams: {email: supportContact()},
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
  const config = modalConfig[type.value.content?.type ? type.value.content.type : type.value.content] || modalConfig.default

  state.title = t(config.title)

  if (config.desc) {
    state.desc = config.descParams
      ? t(config.desc, config.descParams)
      : t(config.desc)
  }

  if (config.desc2) {
    state.desc2 = t(config.desc2)
  }

  state.leftBtn = t(config.leftBtn)

  if (config.rightBtn) state.rightBtn = t(config.rightBtn)
}

setModalState(type)

const btnAction = (direction) => {
  const isRight = direction === 'right'
  switch (type.value.content?.type ? type.value.content.type : type.value.content) {
    case AUTHORITY:
    case SECESSION:
    case REFERENCE_DELETE:
    case CATEGORY_DELETE:
    case CATEGORY_SAVE:
    case PLAN_CANCEL:
    case DELETE:
    case UPDATE_PDF_FILE:
    case UPDATE_PDF_CANCEL:
    case DELETE_PDF_FILE:
    case SEND_CONFIRM:
    case HAS_THREAD:
      isRight
        ? handleConfirm()
        : handleCancel()
      break
    case CERTIFICATION_EMAIL:
    case EXPIRATION_INVITATION:
      if (!isRight) {
        router.push('/')
        modalClose()
      }
      break
    case PASSWORD_LINK_EXPIRED:
      if (!isRight) {
        router.push('/signin')
        modalClose()
      }
      break
    case SEND_MAIL_ERROR:
    case FAILED_SEND_MAIL:
      if (!isRight) {
        handleCancel()
        modalClose()
      }
      break
    case ATTACHMENT_ERROR:
      if (!isRight) {
        modalClose()
      }
      break
    default:
      if (isRight) {
        router.push({ name: 'Board' })
        modalClose()
      } else{
        modalClose()
      }
  }
}

const handleConfirm = () => {
  if (props.resolve) props.resolve(true); // Confirm 처리
}

const handleCancel = () => {
  if (props.reject) props.reject(false); // 취소 시 reject 호출
};
const modalClose = () => {
  modal.close()
}

</script>

<template>
  <div class="send-mail-container">
    <template v-if="type.content?.type">
      <template v-if="type.content.type === 'sendMailError'">
        <button class="close-btn" @click="modalClose">
          <i class="font-icon-close" />
        </button>
      </template>
    </template>
    <template v-else>
      <template v-if="type.content === 'sendMailError'">
        <button class="close-btn" @click="modalClose">
          <i class="font-icon-close" />
        </button>
      </template>
    </template>
    <div class="send-mail-wrap">
      <div class="title-wrap">
        <i class="font-icon-error"></i>
        <h3 class="title" v-html="state.title"></h3>
      </div>
      <div class="desc" :class="{'isDesc2': state.desc2}">
        <p class="text1" v-html="state.desc"></p>
      </div>
      <template v-if="state.desc2">
        <div class="desc2">
          <p class="text2" v-html="state.desc2"></p>
        </div>
      </template>
    </div>
    <div class="btn-wrap">
      <UiButton :type="state.leftBtn === '닫기' && state.rightBtn ? 'primary' : 'outline'" @click="btnAction('left')">
        {{ state.leftBtn }}
      </UiButton>
      <UiButton v-if="state.rightBtn && state.leftBtn" :type="state.leftBtn === '닫기' && state.rightBtn? 'outline' : 'primary'" @click="btnAction('right')">
        {{ state.rightBtn }}
      </UiButton>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.send-mail-container {
  min-width: 400px;
  padding: 30px 30px 5px;
  position: relative;

  .close-btn {
    position: absolute;
    top: 0px;
    right: 0px;
    width: 20px;
    height: 20px;
    background: transparent;
    border: none;
    outline: none;
    font-size: 16px;
  }

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

      &.isDesc2 {
        margin-bottom: 15px;
      }
    }

    .desc2 {
      padding-bottom: 20px;
      padding-top: 0;
    }
  }

  .btn-wrap {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
  }
}
</style>

