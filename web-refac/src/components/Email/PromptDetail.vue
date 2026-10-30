<script setup>
import { ref, watch, defineEmits, onMounted, onBeforeUnmount, watchEffect } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  kind: String,
  size: String,
  prompt: Object,
  latestPrompt: Object,
  list: Object,
  isLoading: Boolean,
  isDropdown: Boolean,
  isGreetingEdit: Boolean
})
const emits = defineEmits(['search', 'save', 'select'])
const inputData = defineModel('inputData')
const greetingData = defineModel('greetingData')
const isEditMode = ref(false)
const scroller = ref(null)
const selectedVersion = ref()
const dropdownOpen = ref(false)
const isGreeting = ref(false)
const newGreeting = ref(greetingData.value)

onMounted(() => {
  window.addEventListener('click', closeDropdown)
  window.removeEventListener('touchstart', closeDropdown)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', closeDropdown)
  window.removeEventListener('touchstart', closeDropdown)
})

watch(
    () => props.list,
    (newList, prevList) => {
      if (newList !== prevList && newList.length > 0) {
        selectedVersion.value = newList[0]
      }
    }
)
watch(
    () => props.isDropdown,
    () => {
      if (dropdownOpen.value) {
        dropdownOpen.value = false
      }
    }
)

watch(() => greetingData.value, (value) => {
  newGreeting.value = value
})

const toggleDropDown = () => {
  dropdownOpen.value = !dropdownOpen.value
}

const handleSelectVersion = (selected) => {
  selectedVersion.value = selected
  dropdownOpen.value = false
  emits('select', props.kind, selectedVersion.value.prompt_id)
}

const handleChangeEditMode = () => {
  if (isEditMode.value) {
    resetInputData()
  }
  isEditMode.value = !isEditMode.value
}

const resetInputData = () => {
  inputData.value.prompt = props.latestPrompt.prompt
  inputData.value.memo = props.latestPrompt.memo
}

const handleClickSave = () => {
  const confirmed = confirm(t('prompt.isSaved'))
  if (!confirmed) {
    return
  }
  saveNewPrompt()
  handleChangeEditMode()
}

const saveNewPrompt = () => {
  emits('save', props.kind)
}

const copy = () => {
  navigator.clipboard.writeText(props.prompt.prompt).then(() => alert(t('common.copy')))
}

const getSize = () => {
  return props.size
}

const closeDropdown = () => {
  dropdownOpen.value = false
}

const onSaveGreetings = async () => {
  isGreeting.value = false
  emits('greetingSave', {greetings: newGreeting.value || greetingData.value})
}
</script>

<template>
  <div :class="['prompt-wrapper', { edit: isEditMode }, getSize()]">
    <div class="prompt-viewer">
      <div class="prompt-viewer-controlbar">
        <div class="version">
          <p class="version-label">Version</p>
          <div class="version-select-wrap">
            <template v-if="isEditMode">
              <p class="version-edit">{{ $t('prompt.desc') }}</p>
            </template>
            <template v-else>
              <div class="be-dropdown flex y-center" ref="dropdown" @click.stop="toggleDropDown">
                <span class="current-type">
                  {{ selectedVersion ? selectedVersion.version : 'Select an option' }}
                </span>
                <span class="be-icon size-20 icon-grey-md icon-dropdown">
                  <i class="font-icon-right-arrow"></i>
                </span>
                <Transition name="slide">
                  <ul class="list" v-show="dropdownOpen">
                    <template v-for="option in list" :key="option.prompt_id">
                      <li @click.stop="handleSelectVersion(option)">
                        {{ option.version }}
                      </li>
                    </template>
                  </ul>
                </Transition>
              </div>
            </template>
            <div class="prompt-viewer-header">
              <template v-if="isEditMode">
                <UiButton :type="'icon primary'" @click="handleClickSave">
                  {{ $t('common.save2') }}
                  <i class="font-icon-save"></i>
                </UiButton>
              </template>
              <template v-else>
                <UiButton :type="'icon outline primary'" @click="handleChangeEditMode">
                  {{ $t('common.edit2') }}
                  <i class="font-icon-write" />
                </UiButton>
              </template>
            </div>
          </div>
        </div>
      </div>
      <div class="prompt-viewer-body" ref="scroller">
        <div class="section">
          <div class="section-header">
            <p class="section-header-title">{{ $t('playground.comment') }}</p>
          </div>
          <div class="section-body">
            <template v-if="isEditMode">
              <div class="section-body-textarea short">
                <UiInput
                    :inputStyle="'monitoring'"
                    :type="'text'"
                    :value="inputData.comment"
                    @updateValue="inputData.comment = $event"
                    />
              </div>
            </template>
            <template v-else-if="!isLoading">
              <UiInput :type="'text'"
                       :value="props.prompt?.comment"
                       :disabled="!isEditMode" />
            </template>
          </div>
        </div>
        <div class="section">
          <div class="section-header">
            <p class="section-header-title">Prompt</p>
            <button class="section-header-copyBtn flex xy-center" @click="copy">
              <i class="icon icon--copy" />
            </button>
          </div>
          <div class="section-body">
            <template v-if="isEditMode">
              <div :class="['section-body-textarea long', getSize()]">
                <textarea cols="30" rows="10" v-model="inputData.prompt"></textarea>
              </div>
            </template>
            <template v-else-if="!isLoading">
              <textarea cols="30" rows="10" :value="prompt?.prompt" disabled>
              </textarea>
            </template>
            <template v-else>
              <div class="section-body-loading flex x-center">
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.prompt-wrapper {
  color: #333;
  box-sizing: border-box;
  &.full {
    height: 100%;
  }
  &.short {
    height: 29%;
  }
  &.long {
    height: 70%;
  }

  .prompt-viewer {
    width: 100%;
    height: 100%;
    padding: 40px 135px;
    border-radius: 20px;
    display: flex;
    flex-direction: column;
    gap: 32px;

    &-controlbar {
      .version {
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 4px;

        &-label {
          color: $grey-300;
          font-size: 13px;
          font-weight: 600;
          line-height: 120%; /* 15.6px */
        }

        &-select-wrap {
          display: flex;
          align-items: center;
          gap: 16px;

          .be-dropdown {
            max-width: 250px;
          }
        }

        &-select {
          flex: 1;
          padding: 2px 10px;
          border: 1px solid $primary-xxl;
          border-radius: 10px;
          outline: none;
          -webkit-appearance: none;
          -moz-appearance: none;
          appearance: none;
          &-option {
            background: red;

            &-tooltip {
              position: absolute;
              font-weight: 700;
            }
          }
        }

        .select {
          position: relative;
          display: inline-block;
          width: 100%;
          &-input {
            padding: 6px 8px;
            border: 1px solid $primary-xxl;
            border-radius: 10px;
            background: #fff;
            cursor: pointer;

            &.grayscale {
              background: #e6e6e6;
            }
          }
          &-background {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1;
          }

          &-options {
            position: absolute;
            top: 105%;
            left: 0;
            right: 0;
            max-height: 300px;
            border: 1px solid $primary-xxl;
            border-radius: 5px;
            background: #fff;
            overflow-y: auto;
            z-index: 1;

            // 스크롤 바 커스텀 - WebKit 기반 브라우저 (Chrome, Edge, Opera, Safari, ios)
            &::-webkit-scrollbar {
              width: 8px;
            }

            &::-webkit-scrollbar-thumb {
              height: 30%;
              background: #e6e6e6;
              border-radius: 10px;
            }

            &::-webkit-scrollbar-track {
              background: none;
            }

            &-item {
              position: relative;
              padding: 8px 10px;
              cursor: pointer;

              &:not(:last-child) {
                border-bottom: 1px solid #f3f3f3;
              }
              &:first-child {
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
              }
              &:last-child {
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
              }
              &:hover {
                background: #f8eaf0;
              }
            }
          }

          .index {
            font-weight: 500;
            color: #e5476e;
            padding-right: 3px;
          }
        }
      }
    }

    &-body {
      display: flex;
      flex-direction: column;
      gap: 32px;
      overflow-y: auto;

      &::-webkit-scrollbar {
        width: 8px;
      }

      &::-webkit-scrollbar-thumb {
        height: 30%;
        background: #e6e6e6;
        border-radius: 10px;
      }

      &::-webkit-scrollbar-track {
        background: none;
      }

      .section {

        &-header {
          display: flex;
          gap: 8px;
          align-items: center;
          padding-bottom: 4px;

          &-title {
            color: $grey-400;
            font-size: $font-13;
          }

          &.flex {
            gap: 8px;
          }
          &-copyBtn {
            padding: 2px;
            border-radius: 5px;
            transition: all .3s;

            &:hover {
              background: $hover-deepgrey-bg;
            }
          }
        }
        &-body {
          white-space: pre-line;
          word-break: break-word;

          &-textarea {
            :deep(.be-input-wrapper) {
              .delete-text {
                top: 50%;
                transform: translateY(-40%);
              }
            }
          }

          input {
            width: 100%;
          }

          textarea {
            width: 100%;
            height: 516px;
            border-radius: 5px;
            border: 1px solid #BBB;
            background: #FFF;
            box-sizing: border-box;
            padding: 12px;
            resize: none;
            font-size: $font-14;
            line-height: 150%;

            &:disabled {
              color: $grey-300;
            }

            &:focus {
              border: 1px solid #289eef;
              outline: none;
            }
          }

          &-loading {
            width: 100%;
            padding-bottom: 20px;
          }
        }
      }
    }
  }

  .section.greetings {

    .section-header-title {
      color: $grey-400;
      font-size: $font-13;
    }
    .greetings-input-wrap {
      display: flex;
      align-items: center;
      gap: 8px;

      &:deep(.be-input-wrapper) {
        .delete-text {
          top: 50%;
          transform: translateY(-50%);
        }
      }

      .be-btn {
        margin-top: 4px;
      }
    }
  }


  .dim {
    display: none;
  }
  &.edit {
    .prompt-viewer {
      position: relative;
      z-index: 2;
    }
    .dim {
      display: block;
      position: fixed;
      width: 100%;
      height: calc(100% - 76px);
      bottom: 0;
      left: 0;
      background: #00000099;
      z-index: 1;
    }
  }
}
</style>
