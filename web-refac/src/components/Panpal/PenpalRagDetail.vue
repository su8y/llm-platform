<script setup>
import { computed, ref, watch } from 'vue'

import { dateFormatter, bytesToMB } from "@/libs/utils.js";
import { convertCidToS3 } from "@/libs/imageConverter.js";

const emits = defineEmits(['change'])
const props = defineProps({
  ragData: Object,
  answer: String,
  status: String
})

const replaceData = ref(null)
const isAttachmentOpen = ref(false)

const hoursFromReceived = computed(() => {
  const data = props.ragData

  const sentAt = dateFormatter(data.sentAt, 'time')
  const receivedAt = dateFormatter(data.receivedAt, 'time')
  const sentAtDate = new Date(sentAt)
  const receivedAtDate = new Date(receivedAt)

  const diff = sentAtDate.getTime() - receivedAtDate.getTime()
  const diffHours = Math.floor(diff / (1000 * 60 * 60))

  return diffHours
})

watch(() => props.ragData, (newInboxData) => {

  replaceData.value = newInboxData?.thread
  if (newInboxData?.imageInfo) {
    replaceData.value = convertCidToS3(newInboxData?.imageInfo, replaceData.value)
  }
}, { immediate: true })

const scrollTop = () => {
  window.scrollTo({top: 0, behavior: 'smooth'});
}
</script>

<template>
  <template v-if="props.ragData">
    <div class="reference-detail-wrapper">
      <div class="monitoring-detail-header">
        <div class="back-list">
          <RouterLink :to="{ name: 'PenpalRag' }">
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
            <span>{{ props.ragData?.messageId }}</span>
          </div>
        </div>
      </div>
      <div class="email-container">
        <div class="reference-detail-container">
          <div class="header">
            <div class="header-left flex x-between y-center">
              <h2 class="header-title">{{ props.ragData?.subject }}</h2>
            </div>
          </div>
          <div class="detail-wrapper">
            <div class="flex flex-column label-wrapper">
              <div class="flex y-center detail-info">
                <span class="detail-label">{{ $t('penpal.column.toMail') }}</span>
                <div class="label-value email">
                  <template v-for="(mail, i) in props.ragData?.toMail" :key="i">
                    <span>
                      {{ props.ragData?.toName[i] }}{{ `<${mail}>` }}<template v-if="i !== props.ragData?.toMail.length - 1">, </template>
                    </span>
                  </template>
                </div>
              </div>
              <div class="flex y-center detail-info">
                <span class="detail-label">{{ $t('penpal.detail.cc') }}</span>
                <div class="label-value email">
                  <template v-for="(mail, i) in props.ragData?.ccMail" :key="i">
                    <span>
                      {{ props.ragData?.ccName[i] }}{{ `<${mail}>` }}<template v-if="i !== props.ragData?.ccMail.length - 1">, </template>
                    </span>
                  </template>
                </div>
              </div>
              <template v-if="props.ragData?.bccMail.length"></template>
              <div class="flex y-center detail-info">
                <span class="detail-label">{{ $t('penpal.detail.hiddenCc') }}</span>
                <div class="label-value email">
                  <template v-for="(mail, i) in props.ragData?.bccMail" :key="i">
                    <span>
                      {{ props.ragData?.bccName[i] }}{{ `<${mail}>` }}<template v-if="i !== props.ragData?.bccMail.length - 1">, </template>
                    </span>
                  </template>
                </div>
              </div>
            </div>
            <div class="detail">
              <div class="detail-desc flex flex-column">
                <template v-if="props.ragData.attachments.length">
                  <div class="detail-attachment">
                    <div class="attachment-header">
                      <button class="toggle-btn" :class="{close: !isAttachmentOpen}" @click="isAttachmentOpen = !isAttachmentOpen">
                        <i class="font-icon-down-arrow" />
                      </button>
                      <span class="count">{{ $t('penpal.detail.attachments') }}
                        <span>{{ props.ragData?.attachments.length }}</span>{{ $t('penpal.detail.count') }}
                      </span>
                      <button class="save-btn" @click="emits('change', 'download', props.ragData?.attachments)">{{ $t('penpal.detail.allSave') }}</button>
                    </div>
                    <template v-if="isAttachmentOpen">
                      <div class="attachments">
                        <template v-for="(file, index) in props.ragData?.attachments" :key="index">
                          <div class="flex y-center x-between">
                            <div class="flex y-center">
                              <!--                          <i class="icon" :class="`icon&#45;&#45;${file.contentType?.split('/')[1]}`" />-->
                              <span class="file-name">{{ file.filename }} </span>
                              <span class="file-size">{{ bytesToMB(file.size) }}MB</span>
                            </div>
                            <button class="file-download" @click="emits('change', 'download', file)">
                              <i class="icon icon--download-black" />
                            </button>
                          </div>

                        </template>
                      </div>
                    </template>
                  </div>
                </template>
              </div>
              <div class="detail-content" v-html="replaceData"></div>
            </div>
          </div>
        </div>
        <div class="label-container">
          <div class="manager-container">
            <label>{{ $t('penpal.column.manager') }}</label>
            <span class="current-manager flex y-center">
              <template v-if="props.ragData?.manager">
                {{ props.ragData?.manager === 'none' ? $t('penpal.detail.noneManager') : props.ragData?.manager }}
              </template>
              <template v-else>
                {{ $t('penpal.detail.noneManager') }}
              </template>
            </span>
          </div>
          <div class="info-container top">
            <div class="date">
              <label>{{ $t('penpal.column.sentAt') }}</label>
              <div class="date-reply">
                <span>{{ dateFormatter(props.ragData?.sentAt, 'time') }}</span>
                <p class="hour">
                  {{ $t(`penpal.detail.replyIn`, {hour: hoursFromReceived}) }}
                </p>
              </div>
            </div>
            <div class="to-mail">
              <label>{{ $t('penpal.column.fromMail') }}</label>
              <span>{{ `${props.ragData?.fromName}<${props.ragData?.fromMail}>` }}</span>
            </div>
            <div class="keyword">
              <label>{{ $t('penpal.detail.keyword') }}</label>
              <span>{{ props.ragData?.keyword.split(' ').join(', ') }}</span>
            </div>
          </div>
          <!--   2025.10.16 현재 스펙에서 제외   -->
<!--          <div class="info-container bottom">-->
<!--            <i class="icon icon&#45;&#45;dot" />-->
<!--            <div class="whether-sent">-->
<!--              <label>{{ $t('penpal.detail.whetherSent') }}</label>-->
<!--              <span>{{ $t('penpal.detail.success') }}</span>-->
<!--            </div>-->
<!--            <i class="icon icon&#45;&#45;dot" />-->
<!--            <div class="whether-send-back">-->
<!--              <label>{{ $t('penpal.detail.whetherSendBack') }}</label>-->
<!--            </div>-->
<!--          </div>-->
        </div>
      </div>
    </div>
    <div class="top-btn-wrapper flex flex-column xy-center gap-8">
      <i class="icon icon--arrow-circle" @click="scrollTop" />
      <span>{{ $t('penpal.detail.top') }}</span>
    </div>
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
          justify-content: center;
          align-items: flex-start;

          .detail-info {
            width: 100%;
            padding: 18px 16px;
            border-bottom: 1px solid $line-sm;

            .detail-label {
              min-width: 100px;
              max-width: 116px;
              color: #777;
              font-size: 13px;
              font-weight: 600;
            }


            .label-value {
              color: #2F2F2F;
              font-size: 15px;
              font-weight: 500;
              line-height: 120%;
              word-break: break-word;
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
            overflow: auto;

            :deep(pre) {
              white-space: pre-wrap;
              word-break: break-word;
            }

            :deep(.cc-mail) {
              width: 100% !important;
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
      height: fit-content;
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

      .manager-container {
        border-bottom: 1px solid #888;
        padding-bottom: 12px;

        label {
          margin-left: 4px;
        }

        .current-manager {
          padding: 12px;
        }
      }

      .info-container {
        padding: 12px 0;
        display: flex;
        flex-direction: column;
        gap: 24px;

        &.bottom {
          border-bottom: none;
          gap: 16px;
        }

        div {
          display: flex;
          flex-direction: column;
          gap: 12px;

          &.keyword, &.whether-sent, &.whether-send-back {
            gap: 8px;
          }

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

          &.date-reply {
            gap: 0;
            font-size: 13px;
            font-weight: 600;
            line-height: 150%;

            .hour {
              font-size: 13px;
              font-weight: 600;
              line-height: 150%;
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

