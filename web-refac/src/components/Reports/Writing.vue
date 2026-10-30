<script setup>
import {inject, ref, onMounted, onBeforeUnmount, reactive, defineAsyncComponent, watch} from 'vue'
import { useI18n } from 'vue-i18n'

import { fileUploadBase64 } from '@/api/common.js'
import { WARNING_TYPE } from '@/libs/constants.js'

import UiInput from "@/components/Ui/UiInput.vue"
import UiButton from "@/components/Ui/UiButton.vue"
import Warning from "@/components/Modal/Warning.vue"
import Loading from "@/components/Modal/Loading.vue"

const CKEditor = defineAsyncComponent(() =>
    import('@/components/Editor/CKEditor.vue')
)

const { t, locale } = useI18n()
const modal = inject('$modal')
const emits = defineEmits(['check', 'create', 'save', 'delete'])
const props = defineProps({
  userData: Object,
  categoryData: Object,
  postData: Object,
  temporaryData: Object,
  uploadAble: Boolean,
  tokenSize: Number
})

const isReference = ref(true)
const editFocus = ref(false)
const fileNames = ref([])
const files = ref([])
const base64Files = ref([])
const postDataState = ref(props.postData)
const categoryDataState = ref(props.categoryData)
const categoryDropDown = reactive({
  is1depth: false,
  is2depth: false,
  is3depth: false
})

// watch(() => props.uploadAble, (newValue) => {
//   if (!newValue) alert(t('modal.postCapacity'))
// }, {immediate: true})

onMounted(() => {
  window.addEventListener('click', handleClick)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', handleClick)
})

const handleClick = async (e) => {
  e.stopPropagation()
  closeDropDown()
  if (!e.isTrusted || e.target === window) return

  const classList = e.target.classList

  if (!classList.contains('cancel') ||
      !classList.contains('save-temporary') ||
      !classList.contains('create') ||
      !classList.contains('be-dropdown') ||
      !classList.contains('be-input') ||
      !classList.contains('be-btn')
  ) {
    checkTokenSize()
  }

}

const radioSelect = (type) => {
  isReference.value = type === 'reference'
  postDataState.value.isOn = isReference.value
}

const createCancel = () => {
  modal.open(Warning)
}

let lastCheckTime = 0
const checkTokenSize = () => {
  const now = Date.now()
  if (now - lastCheckTime < 100) return

  lastCheckTime = now

  if (postDataState.value.title || postDataState.value.content) {
    emits('check', {title: postDataState.value.title, content: postDataState.value.content})
  }
}


const create = async () =>{
  checkTokenSize()
  postDataState.value.files = base64Files.value

  if (props.uploadAble) {
    const params = {
      title: postDataState.value.title || '-',
      author: postDataState.value.author || props.userData.value.user_id,
      content: postDataState.value.content || null,
      is_on: postDataState.value.isOn,
      lang: postDataState.value.lang,
      image_url: [],
      files: postDataState.value.files,
      post_category_id: null
    }

    if (categoryDataState.value.select3depthCategory) {
      params.post_category_id = categoryDataState.value.select3depthCategory.id
      params.category_depth_1_id = categoryDataState.value.select1depthCategory.id
      params.category_depth_2_id = categoryDataState.value.select2depthCategory.id
    } else if (categoryDataState.value.select2depthCategory) {
      params.post_category_id = categoryDataState.value.select2depthCategory.id
      params.category_depth_1_id = categoryDataState.value.select1depthCategory.id
    } else if (categoryDataState.value.select1depthCategory) {
      params.post_category_id = categoryDataState.value.select1depthCategory.id
    }

    if (props.temporaryData !== null) {
      params.id = props.temporaryData.id
    }

    const content = document.querySelector('.content .ck.ck-content')
    if (content) {
      const imgList = content.querySelectorAll('img')
      for (let i = 0, iLen = imgList.length; i < iLen; i++) {
        const imgElem = imgList[i]
        let image = imgElem.getAttribute('src')

        if (image.includes('data:image/') && image.includes('base64')) {
          try {
            const uploadResult = await fileUploadBase64({ image })

            if (uploadResult && uploadResult.error) {
              alert(uploadResult.error.message)
              modal.close()
              return
            } else {
              const uploadUrl = uploadResult.url
              postDataState.value.content = postDataState.value.content.replace(image, uploadUrl)
              params.content = postDataState.value.content
              image = uploadUrl

              if (image) {
                params.image_url.push(image)
              }
            }
          } catch (e) {
            console.log(e)
          }
        }

      }
    }

    emits('create', params)
  }
}

const saveTemporary = async () => {
  checkTokenSize()
  modal.open(Loading)
  postDataState.value.files = base64Files.value

  if (props.uploadAble) {
    const params = {
      title: postDataState.value.title || null,
      author: postDataState.value.author || props.userData.user_id,
      content: postDataState.value.content || null,
      is_on: postDataState.value.isOn,
      lang: postDataState.value.lang,
      image_url: [],
      files: postDataState.value.files,
      post_category_id: null
    }

    if (props.temporaryData !== null) {
      params.id = props.temporaryData.id
    }

    if (categoryDataState.value.select3depthCategory) {
      params.post_category_id = categoryDataState.value.select3depthCategory.id
      params.category_depth_1_id = categoryDataState.value.select1depthCategory.id
      params.category_depth_2_id = categoryDataState.value.select2depthCategory.id
    } else if (categoryDataState.value.select2depthCategory) {
      params.post_category_id = categoryDataState.value.select2depthCategory.id
      params.category_depth_1_id = categoryDataState.value.select1depthCategory.id
    } else if (categoryDataState.value.select1depthCategory) {
      params.post_category_id = categoryDataState.value.select1depthCategory.id
    }

    const content = document.querySelector('.content .ck.ck-content')
    if (content) {
      const imgList = content.querySelectorAll('img')
      for (let i = 0, iLen = imgList.length; i < iLen; i++) {
        const imgElem = imgList[i]
        let image = imgElem.getAttribute('src')

        if (image.includes('data:image/') && image.includes('base64')) {
          try {
            const uploadResult = await fileUploadBase64({ image })

            if (uploadResult && uploadResult.error) {
              alert(uploadResult.error.message)
              modal.close()
              return
            } else {
              const uploadUrl = uploadResult.url
              postDataState.value.content = postDataState.value.content.replace(image, uploadUrl)
              params.content = postDataState.value.content
              image = uploadUrl

              if (image) {
                params.image_url.push(image)
              }
            }
          } catch (e) {
            alert(e)
            console.log('Error: ', e)
          }
        }

      }
    }

    emits('save', params)
  } else {
    modal.close()
  }
}

const onFileChange = (e) => {
  files.value = e.target.files
  base64Files.value = []
  const maxSize = 50 * 1024 * 1024

  if (files.value.length > 0) {
    files.value.forEach((file) => {
      const fileSize = file.size
      const reader = new FileReader()

      if (fileSize > maxSize || fileNames.value.length === 1) {
        return modal.open(Warning, WARNING_TYPE.FILE_UPLOAD_ERROR)
      }

      reader.onload = () => {
        const base64String = reader.result.split(',')[1]

        base64Files.value.push({
          fileName: file.name,
          fileType: file.type,
          fileData: base64String
        })
      }
      reader.readAsDataURL(file)
      fileNames.value.push(file)
    })
  }
}

const deleteFile = async (index) => {
  const file = fileNames.value[index]
  if (Object.hasOwn(file, 'id')) {
    emits('delete', {id: file.id, index: index})
  } else {
    for (let i=0; i < base64Files.value.length; i++) {
      if (base64Files.value[i].fileName === file.name) base64Files.value.splice(i, 1)
    }
    fileNames.value.splice(index, 1)
  }
}

const onTokenCheck = (e) => {
  if (e.key === 'Enter' || e.key === 'Backspace') {
    checkTokenSize()
  }
}

const selectDropDown = (item, depth) => {
  switch (depth) {
    case '1depth':
      categoryDataState.value.select1depthCategory = item
      categoryDataState.value.depth2List = item.children || null
      categoryDataState.value.depth3List = categoryDataState.value.depth2List.children || null
      categoryDropDown.is1depth = false
      categoryDataState.value.select2depthCategory = null
      categoryDataState.value.select3depthCategory = null
      break
    case '2depth':
      categoryDataState.value.select2depthCategory = item
      categoryDataState.value.depth3List = item.children || null
      categoryDropDown.is2depth = false
      categoryDataState.value.select3depthCategory = null
      break
    case '3depth':
      categoryDataState.value.select3depthCategory = item
      categoryDropDown.is3depth = false
      break
  }
}

const toggleDropDown = (depth) => {
  switch (depth) {
    case '1depth':
      categoryDropDown.is1depth = !categoryDropDown.is1depth
      categoryDropDown.is2depth = false
      categoryDropDown.is3depth = false
      break
    case '2depth':
      categoryDropDown.is1depth = false
      categoryDropDown.is2depth = !categoryDropDown.is2depth
      categoryDropDown.is3depth = false
      break
    case '3depth':
      categoryDropDown.is1depth = false
      categoryDropDown.is2depth = false
      categoryDropDown.is3depth = !categoryDropDown.is3depth
      break
  }
}

const closeDropDown = () => {
  categoryDropDown.is1depth = false
  categoryDropDown.is2depth = false
  categoryDropDown.is3depth = false
}
</script>

<template>
  <template v-if="props.userData">
    <div class="writing-wrapper">
      <div class="writing-header">
        <i class="icon icon--pencil" />
        <div class="btn-wrap" :class="locale">
          <UiButton class="cancel" :type="'outline only-text'" @click="createCancel">
            {{ t('common.cancel2') }}
          </UiButton>
          <UiButton class="save-temporary" :type="'outline only-text'" @click="saveTemporary">
            {{ t('common.saveTemporary') }}
          </UiButton>
          <UiButton class="create" :type="'icon primary'" @click="create">
            <i class="font-icon-save" />
            {{ t('common.save2') }}
          </UiButton>
        </div>
      </div>
      <div class="writing-wrap">
        <div class="writing-options">
          <div class="option-top">
            <div class="option title">
              <div class="right" @keydown="onTokenCheck">
                <UiInput
                    :wrap-style="'inline'"
                    :type="'text'"
                    :placeholder="t('common.title')"
                    v-model="postDataState.title">
                  <template #label>
                    <span class="option-title">
                      {{ t('referenceDetail.title') }}
                    </span>
                  </template>
                </UiInput>
              </div>
            </div>
          </div>
          <div class="option-bottom">
            <div class="option author">
              <div class="right">
                <UiInput
                    :wrap-style="'inline'"
                    :type="'text'"
                    v-model="postDataState.author">
                  <template #label>
                    <span class="option-title">
                      {{ t('referenceList.column.author') }}
                    </span>
                  </template>
                </UiInput>
              </div>
            </div>

            <div class="option radio">
              <p class="option-title">{{ t('referenceList.column.isReference') }}</p>
              <div class="right radio-wrap">
                <div :class="{selected: isReference || postDataState.isOn }" @click="radioSelect('reference')">
                  <span class="check-selected"></span>
                  <label for="reference">{{ t('common.onReference') }}</label>
                </div>
                <div :class="{selected: !isReference || !postDataState.isOn}" @click="radioSelect('notReference')">
                  <span class="check-selected"></span>
                  <label for="notReference">{{ t('common.offReference') }}</label>
                </div>
              </div>
            </div>
          </div>
          <div class="option category">
            <span class="option-title">
              {{ t('referenceList.column.category') }}
            </span>
            <div class="category-dropdown-wrapper">
              <div class="be-dropdown flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('1depth')">
                <span class="current-type">
                  {{ categoryDataState.select1depthCategory && categoryDataState.select1depthCategory.name || t('referenceCategory.depth.depth1') }}
                </span>
                <span class="be-icon size-20 icon-grey-md icon-dropdown">
                  <i class="font-icon-right-arrow"></i>
                </span>
                <Transition name="slide">
                  <template v-if="categoryDropDown.is1depth">
                    <ul class="list" :class="{'is-show': categoryDropDown.is1depth}">
                      <template v-for="item in categoryDataState.depth1List" :key="item.depth">
                        <li @click.stop="selectDropDown(item, '1depth')">
                          {{ item.name }}
                        </li>
                      </template>
                    </ul>
                  </template>
                </Transition>
              </div>
              <div class="be-dropdown flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('2depth')">
                <span class="current-type">
                  {{ categoryDataState.select2depthCategory && categoryDataState.select2depthCategory.name || t('referenceCategory.depth.depth2') }}
                </span>
                <span class="be-icon size-20 icon-grey-md icon-dropdown">
                  <i class="font-icon-right-arrow"></i>
                </span>
                <Transition name="slide">
                  <template v-if="categoryDropDown.is2depth">
                    <ul class="list" :class="{'is-show': categoryDropDown.is2depth}">
                      <template v-for="item in categoryDataState.depth2List" :key="item.depth">
                        <li @click.stop="selectDropDown(item, '2depth')">
                          {{ item.name }}
                        </li>
                      </template>
                    </ul>
                  </template>
                </Transition>
              </div>
              <div class="be-dropdown flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('3depth')">
                <span class="current-type">
                  {{ categoryDataState.select3depthCategory && categoryDataState.select3depthCategory.name || t('referenceCategory.depth.depth3') }}
                </span>
                <span class="be-icon size-20 icon-grey-md icon-dropdown">
                  <i class="font-icon-right-arrow"></i>
                </span>
                <Transition name="slide">
                  <template v-if="categoryDropDown.is3depth">
                    <ul class="list" :class="{'is-show': categoryDropDown.is3depth}">
                      <template v-for="item in categoryDataState.depth3List" :key="item.depth">
                        <li @click.stop="selectDropDown(item, '3depth')">
                          {{ item.name }}
                        </li>
                      </template>
                    </ul>
                  </template>
                </Transition>
              </div>
            </div>
          </div>
          <div class="option flex flex-column gap-16 file-wrapper">
            <div class="flex y-center gap-20 file-upload">
              <span class="option-title">{{ t('writing.fileUpload') }}</span>
              <label for="file_upload" class="file-upload-btn disabled">
                {{ t('writing.fileRegister') }}
              </label>
              <input
                  id="file_upload"
                  ref="fileUpload"
                  :type="'file'"
                  :hidden="true"
                  disabled
                  accept=".csv, .xlsx, .pdf, .jpg, .png, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel, application/pdf, image/jpeg, image/png"
                  @change="onFileChange"
              />
            </div>
            <template v-if="fileNames.length !== 0">
              <template v-for="(file, index) in fileNames" :key="file.name">
                <div class="flex y-center x-between gap-20 file-list">
                  <p>{{ file.name }}</p>
                  <span class="icon-wrap" @click="deleteFile(index)">
                    <i class="font-icon-close" />
                  </span>
                </div>
              </template>
            </template>
          </div>
        </div>
        <div class="writing-desc" @click.stop="editFocus = true">
          <div class="token-size">
            <span>
              {{ t('writing.usedToken') }}
              <span :style="{color: tokenSize < 8150 ? '#262626' : '#ec0047'}">{{ tokenSize }}</span> / 8150
            </span>
          </div>
          <CKEditor
              v-model="postDataState.content"
              class="board-write-block content"
              :class="'write-tiptap'"
              :placeholder="t('common.content')"
              :limit="60000"
              :type="'post'"
              :active="editFocus"
              @blurEditor="checkTokenSize()"
            />
        </div>
      </div>
    </div>
  </template>
</template>

<style lang="scss">
.writing-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  width: calc(100dvw - 212px);
  height: 100%;

  .writing-header {
    display: flex;
    justify-content: space-between;
    padding: 0 12px;

    .icon--pencil {
      margin-left: 16px;
    }

    .btn-wrap {
      display: flex;
      align-items: center;
      gap: 15px;
      margin-right: 7px;

      &.en {
        .be-btn {
          max-width: initial;
        }
      }
    }
  }


  .writing-wrap {
    padding: 32px;
    height: 100%;
    background-color: $whiteColor;
    border-radius: 20px;
    box-shadow: $shadow-panel-sm;
    box-sizing: border-box;

    .writing-options {
      display: flex;
      flex-direction: column;
      gap: 32px;
      .option:not(.radio) {
        width: 100%;

        .option-title {
          display: flex;
          align-items: center;
          color: $grey-300;
          font-size: 13px;
          font-weight: 600;
          line-height: 120%; /* 15.6px */
        }

        .right {
          min-width: 440px;
          width: 100%;
          font-size: 14px;
          color: $textColor;
          box-sizing: border-box;

          .be-input-wrapper {
            .delete-text {
              top: 50%;
              transform: translateY(-50%);
            }
          }

          input {
            width: 100%;
          }

          &.radio-wrap {
            display: flex;
            align-items: center;
            width: auto;
            gap: 12px;

            div {
              display: flex;
              align-items: center;
              gap: 6px;
              color: #666;
              font-size: 15px;
              font-weight: $regular;
              line-height: 13px; /* 86.667% */
            }
          }
        }
      }


      .option-bottom {
        display: flex;
        align-items: center;
        gap: 32px;
        .option {

          &-title {
            color: $grey-300;
            font-size: 13px;
            font-weight: 600;
            line-height: 120%; /* 15.6px */
          }

          &.author {
            margin-right: 32px;
            width: fit-content;
          }

          &.radio {
            display: flex;
            align-items: center;
            gap: 24px;
            .radio-wrap {
              display: flex;
              align-items: center;
              gap: 20px;
              div {
                display: flex;
                align-items: center;
                gap: 8px;

                .check-selected {
                  position: relative;
                  display: inline-block;
                  width: 14px;
                  height: 14px;
                  border: 2px solid #d4d4d4;
                  border-radius: 50%;
                }

                &.selected {
                  .check-selected {
                    border-color: #ec0047;
                    &:before {
                      content: '';
                      position: absolute;
                      width: 8px;
                      height: 8px;
                      background-color: #ec0047;
                      border-radius: 50%;
                      top: 50%;
                      left: 50%;
                      transform: translate(-50%, -50%);
                    }
                  }
                }
              }
            }
          }
          &:last-child {
            position: relative;
            &::before {
              position: absolute;
              top: 50%;
              left: -32px;
              transform: translateY(-50%);
              content: '';
              width: 1px;
              height: 14px;
              background: #D7D7D7;
            }
          }
        }
      }

      .option {
        width: 100%;
        &.category {
          width: 100%;
          display: flex;
          align-items: center;
          gap: 24px;

          .category-dropdown-wrapper {
            width: 100%;
            display: flex;
            align-items: center;
            gap: 12px;
          }
        }
      }
    }

    .file-wrapper {
      .file-list {
        width: 50%;

        .icon-wrap {
          display: inline-block;
          width: 16px;
          height: 16px;
          cursor: pointer;
        }
      }

      .file-upload-btn {
        color: $whiteColor;
        background-color: $mainColor;
        border-radius: 5px;
        padding: 11px;
        text-align: center;
        font-size: $font-14;
        font-weight: $bold;
        min-width: 73px;
        max-width: 118px;
        height: 38px;
        transition: all .3s;
        line-height: 1;
        cursor: pointer;

        &.disabled {
          background-color: $grey-100;
          pointer-events: none;
        }
      }
    }

    .writing-desc {
      margin-top: 57px;
      width: 100%;
      height: calc(100dvh - 500px);
      position: relative;

      .token-size {
        position: absolute;
        right: 0;
        top: -30px;
      }
    }
  }
}
</style>
