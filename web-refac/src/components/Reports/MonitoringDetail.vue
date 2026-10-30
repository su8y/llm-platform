<script setup>
import { ref, reactive, getCurrentInstance, onMounted, onBeforeUnmount, defineAsyncComponent } from 'vue'
import { useI18n } from 'vue-i18n'

import { STATUS } from "@/libs/constants.js";
import { dateFormatter } from "@/libs/utils.js";
import { convertMarkdownToHtml } from "@/libs/parse.js";

import UiSwitch from "@/components/Ui/UiSwitch.vue";
import ReferenceContainer from "@/components/Playground/ReferenceContainer.vue";

const BarChart = defineAsyncComponent(() =>
    import('@/components/Chart/BarChart.vue')
)

const emits = defineEmits(['change', 'update'])
const props = defineProps({
  postData: Object,
  chatData: Array,
  page: Object
})

const app = getCurrentInstance()
const bus = app?.appContext.config.globalProperties.emitter
const { t } = useI18n()

const isEditing = ref(false)
const isDisabled = ref(false)
const statusType = ref('all')
const manager = ref(props.postData.managerId || null)
const ratingValues = ref([1, 2, 3, 4, 5])
const hoverIndex = ref(null)
const isReference = ref(false)
const messageId = ref(null)
const messageContainer = ref(null)
const dropdownStatus = reactive({
  isStatusListStatus: false,
  isManagerList: false
})

onMounted(() => {
  window.addEventListener('click', closeDropdown)
  window.addEventListener('touchstart', closeDropdown)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', closeDropdown)
  window.removeEventListener('touchstart', closeDropdown)
})

const onEditing = () => {
  isEditing.value = !isEditing.value
  isDisabled.value = !isDisabled.value
}

const toggleStatusList = (type) => {
  if (type === 'status') {
    dropdownStatus.isStatusListStatus = !dropdownStatus.isStatusListStatus
    dropdownStatus.isManagerList = false
  } else {
    dropdownStatus.isStatusListStatus = false
    dropdownStatus.isManagerList = !dropdownStatus.isManagerList
  }
}

const selectStatus = (item, type) => {
  type === 'status' ? statusType.value = item : manager.value = item
  toggleStatusList(type)
}

const updateMonitoring = () => {
  const params = {
    sessionKey: props.postData.sessionKey,
    manager_id: manager.value === t('historyDetail.noManager') ? '' : manager.value,
    issue_status: statusType.value === 'all' ? '' : statusType.value
  }

  emits('update', params)
}

const onChangePage = (page) => {
  emits('change', 'current', page)
  isReference.value = false
}

const onReference = (id) => {
  isReference.value = !isReference.value
  messageId.value = id
  messageContainer.value.style.maxHeight = `${messageContainer.value.clientHeight}px`
}

const closeDropdown = () => {
  dropdownStatus.isStatusListStatus = false
  dropdownStatus.isManagerList = false
}

const convertHtml = (content) => {
  const html = convertMarkdownToHtml(content)
  const dom = document.createElement('div')
  dom.innerHTML = html
  const aTags = dom.querySelectorAll('a')

  if (aTags.length) {
    for (let i = 0; i < aTags.length; i++) {
      if (!aTags[i].href.includes('mailto')) {
        aTags[i].setAttribute('target', '_blank')
      }
      aTags[i].style.color = '#0074FF'
    }
  }

  return dom.innerHTML
}

bus.on('onReferenceData', (params) => {
  isReference.value = params.isShow
})
</script>

<template>
  <div class="monitoring-detail-wrapper">
    <div class="monitoring-detail-header">
      <div class="back-list">
        <RouterLink :to="{name: 'History' }">
          <UiButton :type="'only-icon outline'">
            <i class="font-icon-left-arrow" />
          </UiButton>
        </RouterLink>
        <span>
        {{ $t('common.back') }}
        </span>
      </div>
      <div class="edit-btn-wrap">
        <template v-if="!isEditing">
          <UiButton :type="'icon outline primary'" @click="onEditing">
            {{ $t('common.edit2') }}
            <i class="font-icon-write"></i>
          </UiButton>
        </template>
        <template v-else>
          <UiButton :type="'icon primary'" @click="updateMonitoring">
            <i class="font-icon-save"></i>
            {{ $t('common.save2') }}
          </UiButton>
        </template>
      </div>
    </div>
    <div class="monitoring-detail-container">
      <div class="header">
        <div class="header-left flex y-center">
          <h2 class="left">{{ $t('common.detail') }}</h2>
        </div>
      </div>
      <div class="line horizontal"></div>
      <div class="detail-wrapper">
        <div class="detail">
          <div class="detail-group">
            <p class="left be-font text-grey-sm size-13 bold">{{ $t('historyDetail.sessionKey') }}</p>
            <div class="right session-key be-font size-15 flex flex-column x-center" :class="{disabled: isDisabled}">
              <p>{{ props.postData.sessionKey || '-' }}</p>
            </div>
          </div>
          <div class="line horizontal"></div>
          <div class="detail-container">
            <div>
              <div class="detail-group">
                <p class="left be-font text-grey-sm size-13 bold">{{ $t('historyList.column.manager') }}</p>
                <div class="right be-font size-15 flex flex-column x-center">
                  <template v-if="!isEditing">
                    <p>
                      <span>
                        {{ props.postData.managerId || $t('historyDetail.noManager') }}
                      </span>
                    </p>
                  </template>
                  <template v-else>
                    <div class="be-dropdown flex y-center status monitoring-detail" ref="dropdown" @click.stop.prevent="toggleStatusList('manager')">
                      <span class="current-status">
                        {{  manager || $t('historyDetail.noManager') }}
                      </span>
                      <span class="be-icon size-20 icon-grey-md icon-dropdown">
                        <i class="font-icon-right-arrow"></i>
                      </span>
                      <Transition name="slide">
                        <template v-if="dropdownStatus.isManagerList">
                          <ul class="list" :class="{'is-show': dropdownStatus.isManagerList}">
                            <template v-for="item in props.postData.idList" :key="item">
                              <li @click.stop="selectStatus(item, 'manager')">
                                <span class="status">
                                  {{ item }}
                                </span>
                              </li>
                            </template>
                          </ul>
                        </template>
                      </Transition>
                    </div>
                  </template>
                </div>
              </div>
              <div class="line horizontal"></div>

              <div class="detail-group">
                <p class="left be-font text-grey-sm size-13 bold">{{ $t('historyList.column.chatDate') }}</p>
                <div class="right be-font size-15 flex flex-column x-center" :class="{disabled: isDisabled}">
                  <p>{{ dateFormatter(props.postData.regDate, 'time') }}</p>
                </div>
              </div>
              <div class="line horizontal"></div>
            </div>
            <div>
              <div class="detail-group">
                <p class="left be-font text-grey-sm size-13 bold">{{ $t('historyList.column.status') }}</p>
                <div class="right be-font size-15 flex flex-column x-center">
                  <template v-if="!isEditing">
                    <p>
                      <span :class="`status-${props.postData.issueStatus}`">
                        {{ $t(`common.statusList.${STATUS[props.postData.issueStatus]}`) }}
                      </span>
                    </p>
                  </template>
                  <template v-else>
                    <div class="be-dropdown flex y-center status monitoring-detail" ref="dropdown" @click.stop.prevent="toggleStatusList('status')">
                      <span class="current-status" :class="`status-${statusType}`">
                        {{ $t(`common.statusList.${STATUS[statusType]}`) }}
                      </span>
                      <span class="be-icon size-20 icon-grey-md icon-dropdown">
                        <i class="font-icon-right-arrow"></i>
                      </span>
                      <Transition name="slide">
                        <template v-if="dropdownStatus.isStatusListStatus">
                          <ul class="list" :class="{'is-show': dropdownStatus.isStatusListStatus}">
                            <template v-for="type in STATUS" :key="type">
                              <li @click.stop="selectStatus(type, 'status')">
                                <span class="status" :class="`status-${type}`">
                                  {{ $t(`common.statusList.${STATUS[type]}`) }}
                                </span>
                              </li>
                            </template>
                          </ul>
                        </template>
                      </Transition>
                    </div>
                  </template>
                </div>
              </div>
              <div class="line horizontal"></div>
              <div class="detail-group">
                <p class="left be-font text-grey-sm size-13 bold">{{ $t('historyDetail.id') }}</p>
                <div class="right be-font size-15 flex flex-column x-center" :class="{disabled: isDisabled}">
                  <p>{{ props.postData.askerId }}</p>
                </div>
              </div>
              <div class="line horizontal"></div>
            </div>
          </div>
          <div class="detail-group">
            <p class="left be-font text-grey-sm size-13 bold">{{ $t('historyDetail.rating') }}</p>
            <div class="right rating-graph-wrapper" :class="{disabled: isDisabled}">
              <BarChart :x="props.postData.ratingGraph?.X" :data="props.postData.ratingGraph?.data" />
              <div class="average-rating-wrapper">
                <span class="average-rating-title">{{ $t('historyDetail.averageRating') }}</span>
                <div class="average-rating-container">
                  <span class="average-rating">
                    {{ props.postData.rating || 0 }}
                  </span>
                  <span class="average-total">/5</span>
                </div>
              </div>
            </div>
          </div>
          <div class="line horizontal"></div>
          <div class="detail-group playground">
            <div class="playground-top">
              <div class="playground-toolbar">
                <span class="toolbar-text">
                  {{ $t('historyDetail.reference') }}
                </span>
                <div class="line xs"></div>
                <div class="toolbar-toggle">
                  <span class="toolbar-text">{{ $t('historyDetail.seeAll') }}</span>
                  <UiSwitch :default="false"
                            :off-color="'#d7d7d7'"
                            :on-color="'#64b950'"
                            :off-label="''"
                            :on-label="''"
                            :size="'xsmall'"
                            :width="30"
                            :on-value="true"
                            :off-value="false"
                            @change="emits('change', 'all', $event)"/>
                </div>
              </div>
              <UiPagination
                  :total="props.page.totalLength"
                  :limit="props.page.limit"
                  :currentPage="props.page.currentPage"
                  @changePage="onChangePage" />
            </div>
            <div class="right be-font size-15 question" :class="{disabled: isDisabled}" ref="messageContainer">
              <div class="message-container" :class="{isReference}">
                <template v-for="(item, index) in props.chatData" :key="item.regDate">
                  <div class="messages">
                    <template v-if="item.role === 'ai'">
                      <div class="ai be-font size-14 flex">
                        <span class="icon-wrap">
                          <i class="icon icon--ai-assistant" />
                        </span>
                        <div class="message-wrap">
                          <div class="message-top">
                            <div class="rating-wrapper">
                              <span>
                                {{ dateFormatter(item.regDate, 'time') }}
                              </span>
                              <template v-if="item.rating">
                                <div class="rating-container flex y-center">
                                  <span v-for="(value) in ratingValues" :key="value">
                                    <i v-if="value <= item.rating" class="icon icon--star-fill" />
                                    <i v-else class="icon icon--star-transparent" />
                                  </span>
                                </div>
                              </template>
                            </div>
                            <template v-if="item.memo">
                              <div class="comment-wrapper">
                                <span class="comment">
                                  {{ $t('playground.comment') }} : {{ item.memo }}
                                </span>
                              </div>
                            </template>
                          </div>
                          <div class="message" @mouseenter="hoverIndex = index" @mouseleave="hoverIndex = null">
                            <svg class="chat-arrow" :class="{'highlight': isHighlight && highlightIndexes&& highlightIndexes.includes(messageIndex)}" width="37" height="25" viewBox="0 0 37 25" fill="none" xmlns="http://www.w3.org/2000/svg">
                              <path id="Vector 215" d="M0 0H36.5C31 9.63422 17 31.7929 17 21.677C17 3.01069 4.5 1.20428 0 0Z" fill="white"/>
                            </svg>
                            <template v-if="index === hoverIndex">
                              <div class="reference-tooltip" @click="onReference(item.id)">
                                <div class="tooltip-wrap">
                                  <i class="font-icon-reference-data" />
                                  {{ $t('playground.reference') }}
                                </div>
                              </div>
                            </template>
                            <span v-html="convertHtml(item.message)"></span>
                          </div>
                        </div>
                      </div>
                    </template>
                    <template v-else>
                      <div class="human be-font size-14 flex">
                        <span class="user-profile be-font size-22 text-white bold">
                          {{ (props.postData.askerId || '').charAt(0).toUpperCase() }}
                        </span>
                        <span class="message-wrap">
                          <span>
                            {{ dateFormatter(item.regDate, 'time') }}
                          </span>
                          <span class="message">
                            <svg class="chat-arrow" :class="{'highlight': isHighlight && highlightIndexes&& highlightIndexes.includes(messageIndex)}" width="37" height="25" viewBox="0 0 37 25" fill="none" xmlns="http://www.w3.org/2000/svg">
                              <path id="Vector 215" d="M0 0H36.5C31 9.63422 17 31.7929 17 21.677C17 3.01069 4.5 1.20428 0 0Z" fill="white"/>
                            </svg>
                            {{ item.message }}
                          </span>
                        </span>
                      </div>
                    </template>
                  </div>
                </template>
              </div>
              <ReferenceContainer
                  v-show="isReference"
                  :is-reference="isReference"
                  :message-id="messageId"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.monitoring-detail-wrapper {
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

    }
  }

  .monitoring-detail-container {
    border-radius: $radius-16;
    background: $whiteColor;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.16);
    padding: 28px 32px;

    .header {
      padding-bottom: 28px;
      position: relative;

      .header-left {
        .left {
          color: $grey-600;
          font-size: 16px;
          font-weight: 700;
        }
      }

      .btn-wrap {
        position: absolute;
        right: -10px;
        top: 0;
      }
    }

    .detail-wrapper {
      .detail {
        height: 100%;
        border-radius: 5px;

        .detail-container {
          display: flex;

          div {
            flex: 1;
          }
        }

        .detail-group {
          width: 100%;
          display: flex;
          gap: 42px;

          p {
            padding: 6px 10px;
          }

          .left {
            flex: 0 0 130px;
            padding: 16px 15px;
            line-height: 13px;

            &.rating {
              padding-top: 20px;
              align-items: flex-start;
            }
          }

          &.playground {
            margin-top: 53px;
            flex-direction: column;
            gap: 30px;

            .playground-top {
              margin-left: 16px;
              display: flex;
              align-items: center;
              gap: 30px;
              .playground-toolbar {
                display: flex;
                align-items: center;
                gap: 12px;

                .toolbar-text {
                  color: #767676;
                  font-size: 13px;
                  font-weight: 600;
                }

                .toolbar-toggle {
                  display: flex;
                  align-items: center;
                  gap: 10px;
                }
              }
            }
            .right {
              width: 100%;
              display: flex;
              border-radius: $radius-12;
              background: $grey-50;
              box-shadow: 0 1px 4px 0 rgba(0, 0, 0, 0.12) inset;
              overflow-x: hidden;

              .message-container {
                width: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                transition: all .3s;
                padding: 40px 0;
                overflow-y: auto;

                .messages {
                  width: 70%;
                }

                &.isReference {
                  width: 66%;
                  .message {
                    padding-left: 20px;
                    padding-right: 20px;
                  }
                }
              }
            }
          }

          .right {
            flex: 1;
            line-height: 13px; /* 86.667% */

            &.rating-graph-wrapper {
              padding: 24px 0;
              display: flex;
              align-items: center;
              gap: 88px;

              .bar_chart {
                max-width: 321px;
                width: 100%;
                height: 150px;
              }

              .average-rating-wrapper {
                margin-top: 50px;
                display: flex;
                flex-direction: column;
                gap: 15px;
                color: #767676;

                .average-rating-title {
                  font-size: 13px;
                  font-weight: 600;
                  line-height: 100%; /* 13px */
                }

                .average-rating-container {
                  display: flex;
                  align-items: flex-end;
                  gap: 5px;

                  .average-rating {
                    font-size: 32px;
                    font-weight: 700;
                    line-height: 100%; /* 32px */
                  }

                  .average-total {
                    font-size: 16px;
                    font-weight: 400;
                    line-height: 100%; /* 16px */
                    margin-bottom: 4px;
                  }
                }
              }

            }

            &.session-key {
              p {
                color: #ec0047;
                font-size: 16px;
                font-weight: 700;
              }
            }


            p {
              padding: 10px 0;
            }

            &.reference, &.question {
              p {
                line-height: 1.3;
              }
            }

            &.question {
              .ai, .human {
                padding: 10px 0;
                gap: 10px;
                line-height: 13px; /* 86.667% */
                .icon-wrap {
                  gap: 12px;
                }
              }

              .human {
                flex-direction: row-reverse;
                justify-content: flex-start;
                gap: 26px;

                .user-profile {
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  width: 36px;
                  height: 36px;
                  padding: 5px 9px;
                  background: $deepyellow-500;
                  border-radius: $radius-4;
                }

                .message-wrap {
                  max-width: 500px;
                  display: flex;
                  flex-direction: column;
                  align-items: flex-end;
                  gap: 12px;
                  position: relative;

                  .chat-arrow {
                    position: absolute;
                    top: 0;
                    right: -15px;
                    transform: scale(-1, 1);
                    z-index: 2;
                  }
                }

                .message {
                  position: relative;
                  padding: 24px 20px;
                  background: #fff;
                  border-radius: 16px 0 16px 16px;
                  box-shadow: 0 1px 3px #00000029;
                  line-height: 150%;
                }
              }

              .ai {
                display: flex;
                gap: 26px;

                .message-wrap {
                  max-width: 500px;
                  display: flex;
                  flex-direction: column;
                  gap: 10px;
                  position: relative;

                  .chat-arrow {
                    position: absolute;
                    top: 0;
                    left: -15px;
                    z-index: 2;
                  }

                  .message-top {
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    .rating-wrapper {
                      display: flex;
                      align-items: center;
                      gap: 12px;

                      .rating-container {
                        display: flex;
                        gap: 3px;
                      }
                    }

                    .comment-wrapper {
                      margin-bottom: 10px;
                      .comment {
                        color: $deepblue-500;
                        font-size: 13px;
                        font-weight: 400;
                        line-height: 150%; /* 19.5px */
                      }
                    }
                  }
                  .message {
                    width: fit-content;
                    position: relative;
                    background: #ffffff;
                    border-radius: 0 16px 16px 16px;
                    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.16);
                    padding: 20px 24px;
                    white-space: break-spaces;
                    line-height: 150%;

                    .reference-tooltip {
                      position: absolute;
                      z-index: 99;
                      top: 15px;
                      right: 15px;

                      .tooltip-wrap {
                        display: flex;
                        height: 34px;
                        min-width: 80px;
                        padding: 9px 13px 9px 11px;
                        align-items: center;
                        gap: 6px;
                        border-radius: 4px;
                        background: #EC0047;
                        color: $whiteColor;
                        cursor: pointer;

                        .font-icon-reference-data {
                          font-size: 16px;
                        }
                      }
                    }

                    li {
                      white-space: normal;
                      line-height: 2;
                    }
                  }
                }

              }

            }

            .rating {

              .circle-container {
                .circle {
                  width: 20px;
                  height: 20px;
                  border-radius: 50%;
                  border: 2px solid $line-xl;
                  cursor: pointer;

                  &.filled {
                    background-color: $statusYellow;
                  }
                }

                .line {
                  width: 20px;
                  height: 2px;
                  background-color: $line-xl;
                  transition: background-color 0.3s;
                }
              }

              &.disabled {
                .circle {
                  border-color: $grey-100;
                  cursor: not-allowed;
                  pointer-events: none;
                }

                .line {
                  background-color: $grey-100;
                }
              }
            }

            .monitoring-detail {
              width: 50%;
            }
          }

          &:first-child {
            .left {
              border-top-left-radius: 5px;
            }
          }

          &:last-child {
           .left {
              border-bottom-left-radius: 5px;
            }
          }
        }
      }
    }
  }
}
</style>

