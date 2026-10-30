<script setup>
import { ref, reactive, watch, onBeforeMount, onMounted, onBeforeUnmount, computed } from 'vue'
import { useStore } from 'vuex'
import { useI18n } from 'vue-i18n'

import { dateFormatter, bytesToMB } from "@/libs/utils.js";
import { PENPAL_DETAIL_STATUS, BEUSABE_EMAIL } from "@/libs/constants.js";
import { convertCidToS3 } from '@/libs/imageConverter.js'

import PenpalReplied from "@/components/Panpal/PenpalReplied.vue";

const emits = defineEmits(['change', 'update', 'delete', 'deleteFile'])
const props = defineProps({
  inboxData: Object,
  answer: String,
  status: String,
  managerList: Array,
  managerAddressList: Array,
  isPass: Boolean
})

const { t } = useI18n()
const store = useStore()

const isEditing = ref(false)
const answerData = ref(null)
const answerStatus = ref('')
const isAttachmentOpen = ref(true)
const isEditCompany = ref(false)
const editedCompany = ref('')
const selectedManager = ref('')
const isManagerHover = ref(false)
const replaceData = ref('')
const dropdownStatus = reactive({
  isStatusList: false,
  isManagerList: false,
  isCcList: false
})

watch(() => props.inboxData, (newInboxData) => {

  replaceData.value = newInboxData?.thread
  if (newInboxData?.imageInfo) {
    replaceData.value = convertCidToS3(newInboxData?.imageInfo, replaceData.value)
  }

  editedCompany.value = newInboxData?.company
  isEditCompany.value = false

}, { immediate: true })

watch(() => props.isPass, (newIsPass) => {
  isEditing.value = newIsPass
}, { immediate: true, deep: true })

onBeforeMount(async () => {
  try {
    await store.dispatch('storeUserData')
  } catch (e) {
    console.error(`Error: ${e.message}`)
  }
})

onMounted(() => {
  window.addEventListener('click', closeDropdown)
  window.addEventListener('touchstart', closeDropdown)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', closeDropdown)
  window.removeEventListener('touchstart', closeDropdown)
})

const isTo = computed(() => {
  return props.inboxData?.toMail.includes(BEUSABE_EMAIL)
})

const emailStatus = computed(() => {
  const currentStatus = props.inboxData?.status === 'received' ? 'parsed' : props.inboxData?.status
  const list = {...PENPAL_DETAIL_STATUS}
  switch (currentStatus) {
    case 'parsed':
      delete list['sent']
      delete list['parsed']
      break
    case 'answering':
      delete list['spam']
      delete list['answering']
      delete list['close']
      break
    case 'sent':
      delete list['spam']
      delete list['answering']
      delete list['sent']
      delete list['close']
      break
    case 'close':
      delete list['spam']
      delete list['answering']
      delete list['sent']
      delete list['close']
      break
    case 'spam':
      delete list['spam']
      delete list['answering']
      delete list['sent']
      delete list['close']
      delete list['spam']
      break
  }

  return list
})

const managerList = computed(() => {
  return ['none', ...props.managerList]
})

const managerAddressList = computed(() => {
  return ['', ...props.managerAddressList]
})

const onEditing = (type = null) => {
  if (type === 'back') {
    isEditing.value = false
    return
  }
  emits('change', 'checkThread', {id: props.inboxData?.id})
}

const scrollTop = () => {
  window.scrollTo({top: 0, behavior: 'smooth'});
}

const toggleDropDown = (type) => {
  switch (type) {
    case 'status':
      dropdownStatus.isStatusList = !dropdownStatus.isStatusList
      dropdownStatus.isManagerList = false
      break
    case 'manager':
      dropdownStatus.isManagerList = !dropdownStatus.isManagerList
      dropdownStatus.isStatusList = false
      break
    case 'cc':
      dropdownStatus.isCcList = !dropdownStatus.isCcList
      dropdownStatus.isStatusList = false
      dropdownStatus.isManagerList = false
      break
  }
}

const selectDropDown = (item, type) => {
  if (type === 'status') {
    answerStatus.value = item
    setStatus()
  }
  if (type === 'manager') {
    selectedManager.value = item
    setManager()
  }

  toggleDropDown(type)
}

const closeDropdown = () => {
  dropdownStatus.isStatusList = false
  dropdownStatus.isManagerList = false
}

const createAnswer = () => {
  emits('change', 'create', props.inboxData?.id)
}

const sendMail = async (event) => {
  emits('change', 'send', event)
}

const updateCompany = async () => {
  const params = {
    id: props.inboxData?.id,
    company: editedCompany.value
  }
  emits('change', 'editCompany', params)
}

const fileDownload = async (attachment) => {
  if (!Array.isArray(attachment)) {
    emits('change', 'fileDownload', attachment)
  } else {
    for (let i = 0; i < attachment.length; i++) {
      const file = attachment[i]
      emits('change', 'fileDownload', file)
    }
  }
}

const setManager = () => {
  const params = {
    id: props.inboxData?.id,
    managerId: selectedManager.value
  }

  emits('change', 'setManager', params)
}

const setStatus = () => {
  const params = {
    id: props.inboxData?.id,
    status: answerStatus.value
  }

  emits('change', 'setStatus', params)
}
</script>

<template>
  <template v-if="!isEditing">
    <div class="reference-detail-wrapper">
      <div class="monitoring-detail-header">
        <div class="back-list">
          <RouterLink :to="{ name: 'PenpalList' }">
            <UiButton :type="'only-icon outline'">
              <i class="font-icon-left-arrow" />
            </UiButton>
          </RouterLink>
          <span>
          {{ $t('common.back') }}
         </span>
        </div>
        <div class="edit-btn-wrap">
          <div class="mail-info-id">
            <span v-html="$t('penpal.detail.mailInfoId')"></span>
            <span>{{ props.inboxData?.id }}</span>
          </div>
          <UiButton :type="'icon primary'" @click="onEditing">
            <i class="font-icon-save"></i>
            {{ $t('penpal.detail.reply') }}
          </UiButton>
        </div>
      </div>
      <div class="email-container">
        <div class="reference-detail-container">
          <div class="header">
            <div class="header-left flex x-between y-center">
              <h2 class="header-title">{{ props.inboxData?.subject }}</h2>
            </div>
          </div>
          <div class="detail-wrapper">
            <div class="flex label-wrapper">
              <div class="flex y-center">
                <span class="detail-label">{{ $t('penpal.column.fromMail') }}</span>
                <span class="label-value email">{{ props.inboxData?.fromName }}&lt;{{ props.inboxData?.fromMail }}&gt;</span>
              </div>
              <div class="flex y-center">
                <span class="detail-label company">{{ $t('penpal.column.company') }}</span>
                <template v-if="isEditCompany">
                  <UiInput
                      :type="'text'"
                      v-model="editedCompany"
                  />
                  <div class="btn-wrapper">
                    <button class="icon-container">
                      <i class="icon icon--check" @click="updateCompany"></i>
                    </button>
                    <button class="icon-container">
                      <i class="font-icon-close" @click.stop="isEditCompany = false, editedCompany = props.inboxData?.company"></i>
                    </button>
                  </div>
                </template>
                <template v-else>
                  <span class="label-value company" @click="isEditCompany = true">{{ props.inboxData?.company }}</span>
                </template>
              </div>
            </div>
            <div class="detail">
              <template v-if="props.inboxData?.attachments.length">
                <div class="detail-attachment">
                  <div class="attachment-header">
                    <button class="toggle-btn" :class="{close: !isAttachmentOpen}" @click="isAttachmentOpen = !isAttachmentOpen">
                      <i class="font-icon-down-arrow" />
                    </button>
                    <span class="count">{{ $t('penpal.detail.attachments') }}
                      <span>{{ props.inboxData?.attachments.length }}</span>{{ $t('penpal.detail.count') }}
                    </span>
                    <button class="save-btn" @click="fileDownload(props.inboxData?.attachments)">{{ $t('penpal.detail.allSave') }}</button>
                  </div>
                  <template v-if="isAttachmentOpen">
                    <div class="attachments">
                      <template v-for="(file, index) in props.inboxData?.attachments" :key="index">
                        <div class="flex y-center x-between">
                          <div class="flex y-center">
<!--                            <i class="icon" :class="`icon&#45;&#45;${file.contentType.split('/')[1]}`" />-->
                            <span class="file-name">{{ file.filename }} </span>
                            <span class="file-size">{{ bytesToMB(file.size) }}MB</span>
                          </div>
                          <button class="file-download" @click="fileDownload(file)">
                            <i class="icon icon--download-black" />
                          </button>
                        </div>
                      </template>
                    </div>
                  </template>
                </div>
              </template>
              <div class="detail-content" v-html="replaceData"></div>
            </div>
          </div>
        </div>
        <div class="label-container">
          <div class="status-container">
            <div class="be-dropdown status flex y-center" :class="props.inboxData?.status === 'received' ? 'parsed' : props.inboxData?.status" ref="dropdown" @click.stop.prevent="toggleDropDown('status')">
              <span class="current-status flex y-center">
                {{ $t(`penpal.statusList.${PENPAL_DETAIL_STATUS[props.inboxData?.status === 'received' ? 'parsed' : props.inboxData?.status]}`) }}
              </span>
              <span class="be-icon size-20 icon-grey-md icon-dropdown" :class="{'is-show': dropdownStatus.isStatusList}">
                <i class="font-icon-right-arrow"></i>
              </span>
              <Transition name="slide">
                <template v-if="dropdownStatus.isStatusList">
                  <ul class="list" :class="{'is-show': dropdownStatus.isStatusList}">
                    <template v-for="type in emailStatus" :key="type">
                      <li @click.stop="selectDropDown(type, 'status')">
                        <span class="status" :class="`status-${type}`">
                          {{ $t(`penpal.statusList.${type}`) }}
                        </span>
                      </li>
                    </template>
                  </ul>
                </template>
              </Transition>
            </div>
          </div>
          <div class="manager-container">
            <label>{{ $t('penpal.column.manager') }}</label>
            <div class="be-dropdown manager flex y-center"
                 ref="dropdown"
                 @mouseover="isManagerHover = true"
                 @mouseleave="isManagerHover = false"
                 @click.stop.prevent="toggleDropDown('manager')">
              <span class="current-manager flex y-center">
                <template v-if="props.inboxData?.manager">
                  {{ props.inboxData?.manager === 'none' ? $t('penpal.detail.noneManager') : props.inboxData?.manager }}
                </template>
                <template v-else>
                  {{ $t('penpal.detail.noneManager') }}
                </template>
              </span>
              <span class="be-icon size-20 icon-grey-md icon-dropdown" :class="{'is-show': dropdownStatus.isManagerList}">
                <i class="font-icon-right-arrow"></i>
              </span>
              <Transition name="slide">
                <template v-if="dropdownStatus.isManagerList">
                  <ul class="list" :class="{'is-show': dropdownStatus.isManagerList}">
                    <template v-for="(manager, i) in managerList" :key="manager">
                      <li @click.stop="selectDropDown(manager, 'manager')">
                        <span class="manager">
                          {{ manager === 'none' ? t('penpal.detail.noneManager') : manager }}
                          <span>{{ managerAddressList[i] }}</span>
                        </span>
                      </li>
                    </template>
                  </ul>
                </template>
              </Transition>
            </div>
          </div>
          <div class="info-container top">
            <div class="date">
              <label>{{ $t('penpal.detail.receivedDate') }}</label>
              <span>{{ dateFormatter(props.inboxData?.receivedAt, 'time') }}</span>
            </div>
            <div class="type">
              <label>{{ $t('penpal.detail.receivedType') }}</label>
              <span class="type-tag" :class="{'to': isTo}">{{ isTo ? $t('penpal.search.to') : $t('penpal.detail.cc') }}</span>
            </div>
            <div class="to-mail">
              <label>{{ $t('penpal.search.to') }}</label>
              <template v-for="(mail, i) in props.inboxData?.toMail" :key="i">
                <span>
                  {{ props.inboxData?.toName[i] }}{{ `<${mail}>` }}<template v-if="i !== props.inboxData?.toMail.length - 1">, </template>
                </span>
              </template>
            </div>
            <template v-if="props.inboxData?.ccMail.length">
              <div class="cc-info">
                <div @click.stop.prevent="toggleDropDown('cc')">
                  <label>{{ $t('penpal.detail.ccInfo') }}</label>
                  <span class="be-icon size-20 icon-grey-md icon-dropdown" :class="{'is-show': dropdownStatus.isCcList}">
                    <i class="font-icon-right-arrow"></i>
                  </span>
                </div>
                <template v-if="dropdownStatus.isCcList">
                  <template v-for="(mail, i) in props.inboxData?.ccMail" :key="i">
                    <span>
                      {{ props.inboxData?.ccName[i] }}{{ `<${mail}>` }}<template v-if="i !== props.inboxData?.ccMail.length - 1">, </template>
                    </span>
                  </template>
                </template>
              </div>
            </template>
          </div>
          <div class="info-container bottom">
            <div class="keyword">
              <label>{{ $t('penpal.detail.keyword') }}</label>
              <span>{{ props.inboxData?.keyword.split(' ').join(', ') }}</span>
            </div>
<!--            <i class="icon icon&#45;&#45;dot" />-->
<!--            <div class="comment">-->
<!--              <label>{{ $t('penpal.detail.comment') }}</label>-->
<!--              <span>{{ props.inboxData?.comment || '-' }}</span>-->
<!--            </div>-->
          </div>
        </div>
      </div>
    </div>
    <div class="top-btn-wrapper flex flex-column xy-center gap-8">
      <i class="icon icon--arrow-circle" @click="scrollTop" />
      <span>{{ $t('penpal.detail.top') }}</span>
    </div>
  </template>
  <template v-else>
    <PenpalReplied
        :data="props.inboxData"
        :answer-data="answerData"
        :answer-status="props.status"
        @edit="onEditing('back')"
        @create="createAnswer"
        @send="sendMail"
        @download="fileDownload"
    />
  </template>
</template>

<style lang="scss" scoped>
.template {
  visibility: hidden;
}

.reference-detail-wrapper {
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;

  .monitoring-detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .back-list {
      display: flex;
      gap: 12px;
      align-items: center;
      span {
        color: $grey-400;
        font-size: 16px;
        font-weight: 700;
      }
    }

    .edit-btn-wrap {
      position: relative;
      display: flex;
      align-items: center;

      .mail-info-id {
        color: #A3A3A3;
        font-size: 12px;
        font-weight: 500;
        margin-right: 20px;
      }


      :deep(.be-btn) {
        max-width: initial;
      }
    }
  }

  .email-container {
    display: flex;
    gap: 23px;

    .reference-detail-container {
      border-radius: $radius-16;
      background: $whiteColor;
      box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.16);
      padding: 28px 32px;
      min-width: 699px;
      width: 100%;

      .header {
        border-bottom: 1px solid $line-sm;
        position: relative;
        padding-bottom: 28px;

        .header-left {

          .header-title {
            color: $grey-600;
            font-size: 16px;
            font-weight: 700;
          }
        }

        .btn-wrap {
          position: absolute;
          right: -10px;
          top: 0;
          gap: 10px;
        }
      }

      .detail-wrapper {
        width: 100%;
        height: 100%;

        .label-wrapper {
          align-items: center;
          justify-content: space-between;
          padding: 18px 16px;
          border-bottom: 1px solid $line-sm;
          height: 72px;

          div {
            &:deep(.be-input-wrapper) {
              min-width: 115px;
              margin-left: 16px;

              .be-input {
                padding-right: 10px;
              }

              .delete-text {
                display: none;
              }
            }

            .btn-wrapper {
              margin-left: 8px;
              display: flex;
              align-items: center;
              gap: 4px;

              .icon-container {
                width: 28px;
                height: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
              }
            }

            .detail-label {
              min-width: 100px;
              max-width: 116px;
              color: #777;
              font-size: 13px;
              font-weight: 600;

              &.company {
                min-width: 80px;
                text-align: right;
              }
            }


            .label-value {
              color: #2F2F2F;
              font-size: 15px;
              font-weight: 500;

              &.email {
                max-width: 360px;
              }

              &.company {
                min-width: 140px;
                transition: all .3s;
                padding: 4px 8px;
                cursor: pointer;
                margin-left: 16px;

                &:hover {
                  border-radius: 5px;
                  background-color: #EBEBEB;
                  padding: 4px 8px;
                }
              }
            }
          }


        }
        .detail {
          padding: 20px;

          .detail-attachment {
            border: 1px solid #E0E0E0;
            border-radius: 5px;
            padding: 10px 22px 15px 13px;
            max-width: 540px;
            margin-bottom: 20px;

            .attachment-header {
              display: flex;
              align-items: center;
              gap: 15px;

              .toggle-btn {
                &.close {
                  transform: rotate(180deg);
                }
              }

              .count {
                color: #2f2f2f;
                font-size: 13px;
                font-weight: 400;

                > span {
                  font-weight: 600;
                }
              }

              .save-btn {
                margin-left: 13px;
                color: #777;
                font-size: 12px;
                font-weight: 400;
                position: relative;

                &::before {
                  content: '';
                  position: absolute;
                  top: 50%;
                  left: -13px;
                  transform: translateY(-50%);
                  width: 1px;
                  height: 8px;
                  background: #D9D9D9;
                }
              }
            }

            .attachments {
              margin-top: 15px;
              height: 100%;

              .file-name {
                margin-left: 14px;
                color: #2F2F2F;
                font-size: 13px;
                font-weight: 400;
              }

              .file-size {
                color: #909090;
                font-size: 12px;
                font-weight: 400;
                margin-left: 6px;
              }
            }
          }

          .detail-content {
            word-break: break-word;

            :deep(pre) {
              white-space: pre-wrap;
              word-break: break-word;
            }

            :deep(td) {
              text-align: initial;
            }
          }
        }
      }
    }

    .label-container {
      width: 100%;
      border-radius: $radius-16;
      background: $whiteColor;
      box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.16);
      padding: 28px;
      min-width: 274px;
      max-width: 274px;

      label {
        color: #777;
        font-size: 13px;
        font-weight: 600;
        line-height: 150%;
      }

      .icon-dropdown.is-show {
        transform: rotate(270deg) translateY(0%) translateX(40%);
      }

      .status-container {
        .be-dropdown {
          cursor: pointer;

          $penpalStatus: (
            parsed: (#D4EABD, #68BB0C, #006200),
            answering: (#BADFFF, #0096FF, #1760EC),
            sent: (#FFFCED, #B6A029, #72620F),
            spam: (#EBEBEB, #BBB, #666),
            close: (#FFFCED, #B6A029, #72620F)
          );

          @each $name, $colors in $penpalStatus {
            &.status.#{$name} {
              background-color: nth($colors, 1);
              border-color: nth($colors, 2);

              .current-status {
                color: nth($colors, 3);
                font-size: 13px;
                font-weight: 600;
                line-height: 150%;
              }

            }
          }

          &.manager {
            .current-manager {
              padding: 4px 12px;
            }
          }

          .list {
            top: 42px;
            max-height: 150px;
            overflow-y: scroll;
          }
        }
      }

      .manager-container {
        margin-top: 8px;
        border-bottom: 1px solid #888;
        padding: 12px 0;

        label {
          margin-left: 4px;
        }

        .be-dropdown {
          border: none;
          transition: all .3s;
          cursor: pointer;

          .current-manager {
            color: #2F2F2F;
            font-size: 13px;
            font-weight: 600;
            line-height: 150%;
            padding: 12px;
          }

          .be-icon {
            display: none;
          }

          &:hover {
            background-color: #F5F5F5;
            .be-icon {
              display: block;
            }
          }

          .list {
            top: 42px;
            max-height: 150px;
            overflow-y: scroll;

            .manager {
              display: flex;
              flex-direction: column;
              color: #2F2F2F;
              font-size: 13px;
              font-weight: 600;
              line-height: 150%;

              > span {
                color: #888;
                font-size: 12px;
                font-weight: 400;
                line-height: 150%;
              }
            }
          }
        }
      }

      .info-container {
        padding: 12px 0;
        border-bottom: 1px solid #888;
        display: flex;
        flex-direction: column;
        gap: 24px;

        &.bottom {
          border-bottom: none;
          gap: 16px;
          margin-top: 12px;
        }

        div {
          display: flex;
          flex-direction: column;
          gap: 12px;

          span {
            color: #2F2F2F;
            font-size: 13px;
            font-weight: 600;
            line-height: 150%;

            &.type-tag {
              width: fit-content;
              color: #fff;
              font-size: 12px;
              font-weight: 600;
              line-height: 100%;
              padding: 4px;
              background-color: #707EC5;
              border-radius: 3px;

              &.to {
                background-color: #57AB00;
              }
            }
          }

          &.cc-info {
            > div {
              width: fit-content;
              cursor: pointer;
              flex-direction: row;
              align-items: center;
              gap: 4px;

              label {
                cursor: pointer;
              }

              .icon-dropdown {
                width: 13px;
                height: 13px;
                transform: rotate(90deg);

                &.is-show {
                  transform: rotate(270deg) translateY(-30%);
                }
              }
            }
          }
        }
      }
    }
  }
}

.top-btn-wrapper {
  width: 100%;
  margin-bottom: 20px;

  .icon {
    cursor: pointer;
  }

  span {
    color: #666;
    text-align: center;
    font-size: 12px;
    font-weight: 500;
  }
}

</style>

