<script setup>
import { ref, inject, computed, defineAsyncComponent, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { fileUploadBase64 } from "@/api/common.js";
import { dateFormatter } from "@/libs/utils.js";
import { WARNING_TYPE } from "@/libs/constants.js";

import UiButton from "@/components/Ui/UiButton.vue";
import UiInput from "@/components/Ui/UiInput.vue";
import Warning from "@/components/Modal/Warning.vue";
import {convertHtmlToMarkdown, convertMarkdownToHtml} from "@/libs/parse.js";

const CKEditor = defineAsyncComponent(() =>
    import('@/components/Editor/CKEditor.vue')
)

const emits = defineEmits(['change', 'update', 'delete', 'deleteFile'])
const props = defineProps({
  postData: Object,
  categoryData: Object,
  editData: Object,
  fileData: Object,
  isReference: Boolean
})

const { locale } = useI18n()
const modal = inject('$modal')
const route = useRoute()

const isEditing = ref(false)
const isDisabled = ref(false)
const editFocus = ref(false)
const isLoading = ref(false)
const categoriesData = ref(props.categoryData)
const fileDataState = ref(props.fileData)
const editDataState = ref(props.editData)

const editDataContent = computed(() => {
  return convertMarkdownToHtml(editDataState.value.content)
})

const isMarkdown = computed(() => {
  return props.postData.is_markdown
})

onMounted(() => {
  window.addEventListener('click', closeDropdown)
  window.addEventListener('touchstart', closeDropdown)
})

onBeforeUnmount(() => {
  window.removeEventListener('click', closeDropdown)
  window.removeEventListener('touchstart', closeDropdown)
})

const convertHTML = (content) => {
  const dom = document.createElement('p')
  dom.innerHTML = content
  if (dom.querySelectorAll('img').length !== 0) {
    const images = dom.querySelectorAll('img')
    for (let i = 0; i < images.length; i++) {
      images[i].width = '0'
      images[i].height = '0'
      images[i].style.objectFit = 'contain'
      images[i].style.width = 'fit-content'
      images[i].style.height = 'auto'
    }
  }
  if (dom.querySelectorAll('figure').length !== 0) {
    const figures = dom.querySelectorAll('figure')
    for (let i = 0; i < figures.length; i++) {
      figures[i].style.maxWidth = '900px'
      figures[i].style.width = '100%'
    }
  }
  return dom.innerHTML
}

const radioSelect = (type) => {
  emits('change', 'reference', type === 'reference')
  editDataState.value.isOn = type === 'reference'
}

const onEditing = () => {
  isEditing.value = !isEditing.value
  isDisabled.value = !isDisabled.value
}

const setCategoryParams = (params) => {
  const categories = {
    3: {
      post_category_id: categoriesData.value.select3depthCategory?.id,
      category_depth_1_id: categoriesData.value.select1depthCategory?.id,
      category_depth_2_id: categoriesData.value.select2depthCategory?.id
    },
    2: {
      post_category_id: categoriesData.value.select2depthCategory?.id,
      category_depth_1_id: categoriesData.value.select1depthCategory?.id
    },
    1: {
      post_category_id: categoriesData.value.select1depthCategory.id
    }
  }

  const depth = categoriesData.value.select3depthCategory ? 3 : categoriesData.value.select2depthCategory ? 2 : 1
  return { ...params, ...categories[depth] }
}

const updateReference = async () => {
  isLoading.value = true
  let params = {
    ...editDataState.value,
    id: props.postData.id,
    lang: locale.value,
    image_url: [],
    files: fileDataState.value.base64Files,
    post_category_id: null
  }

  if (categoriesData.value.select1depthCategory) params = setCategoryParams(params)

  const content = document.querySelector('.content .ck.ck-content')
  if (content) {
    if (isMarkdown.value) {
      params.content = await convertHtmlToMarkdown(content.innerHTML)
    } else {
      const imgList = content.querySelectorAll('img')
      for (let i = 0, iLen = imgList.length; i < iLen; i++) {
        const imgElem = imgList[i]
        let image = imgElem.getAttribute('src')

        if (image.includes('data:image/') && image.includes('base64')) {
          const uploadResult = await fileUploadBase64({ image })
          const uploadUrl = uploadResult.url

          editDataState.value.content = editDataState.value.content.replace(image, uploadUrl)
          params.content = props.editData.content
          image = uploadUrl
        }

        if (image) {
          params.image_url.push(image)
        }
      }
    }
  }

  emits('update', params)
}

const deleteReference = async (id) => {
  emits('delete', {id: id})
}

const selectDropDown = (item, depth) => {
  switch (depth) {
    case '1depth':
      categoriesData.value.select1depthCategory = item
      categoriesData.value.categoryDepth2List = item.children || null
      categoriesData.value.categoryDepth3List = categoriesData.value.categoryDepth2List.children || null
      categoriesData.value.is1depthCategory = false
      categoriesData.value.select2depthCategory = null
      categoriesData.value.select3depthCategory = null
      break
    case '2depth':
      categoriesData.value.select2depthCategory = item
      categoriesData.value.categoryDepth3List = item.children || null
      categoriesData.value.is2depthCategory = false
      categoriesData.value.select3depthCategory = null
      break
    case '3depth':
      categoriesData.value.select3depthCategory = item
      categoriesData.value.is3depthCategory = false
      break
  }
}

const dropdownMap = new Map([
  ['1depth', 'is1depthCategory'],
  ['2depth', 'is2depthCategory'],
  ['3depth', 'is3depthCategory'],
])

const resetOtherDropdowns = (current) => {
  const keys = ['1depth', '2depth', '3depth']

  for (let i=0; i < keys.length; i++) {
    if (keys[i] !== current) categoriesData.value[dropdownMap.get(keys[i])] = false
  }
}

const toggleDropDown = (depth) => {
  if (!dropdownMap.has(depth)) return

  const current = dropdownMap.get(depth)
  categoriesData.value[current] = !categoriesData.value[current]

  resetOtherDropdowns(depth)
}

const closeDropdown = () => {
  categoriesData.value.is1depthCategory = false
  categoriesData.value.is2depthCategory = false
  categoriesData.value.is3depthCategory = false
}

const onFileChange = (e) => {
  fileDataState.value.files = e.target.files
  fileDataState.value.base64Files = []
  const maxSize = 50 * 1024 * 1024

  if (fileDataState.value.files.length > 0) {
    fileDataState.value.files.forEach((file) => {
      const fileSize = file.size
      const reader = new FileReader()

      if (fileSize > maxSize || fileDataState.value.fileNames.length === 1) {
        return modal.open(Warning, WARNING_TYPE.FILE_UPLOAD_ERROR)
      }

      reader.onload = () => {
        const base64String = reader.result.split(',')[1]

        fileDataState.value.base64Files.push({
          fileName: file.name,
          fileType: file.type,
          fileData: base64String
        })
      }
      reader.readAsDataURL(file)
      fileDataState.value.fileNames.push(file)
    })
  }
}

const deleteFile = async (index) => {
  const file = fileDataState.value.fileNames[index]
  if (Object.hasOwn(file, 'id')) {
    emits('deleteFile', {id: file.id, index: index})
  } else {
    for (let i=0; i < fileDataState.value.base64Files.length; i++) {
      if (fileDataState.value.base64Files[i].fileName === file.name) fileDataState.value.base64Files.splice(i, 1)
    }
    fileDataState.value.fileNames.splice(index, 1)
  }
}

</script>

<template>
  <template v-if="props.postData">
    <div class="reference-detail-wrapper">
      <div class="monitoring-detail-header">
        <div class="back-list">
          <RouterLink :to="{ name: 'Board', query: {page: route.query.page, limit: route.query.limit,} }">
            <UiButton :type="'only-icon outline'">
              <i class="font-icon-left-arrow" />
            </UiButton>
          </RouterLink>
          <span>
          {{ $t('common.back') }}
         </span>
        </div>
        <div class="edit-btn-wrap">
          <UiButton :type="'icon outline'" @click="deleteReference(props.postData.id)">
            {{ $t('common.delete2') }}
            <i class="font-icon-delete"></i>
          </UiButton>
          <template v-if="!isEditing">
            <UiButton :type="'icon outline primary'" @click="onEditing">
              {{ $t('common.edit2') }}
              <i class="font-icon-write"></i>
            </UiButton>
          </template>
          <template v-else>
            <UiButton :type="'icon primary'" @click="updateReference">
              {{ $t('common.save2') }}
              <i class="font-icon-save"></i>
            </UiButton>
          </template>
        </div>
      </div>
     <div class="reference-detail-container">
        <div class="header">
          <div class="header-left flex y-center">
            <h2 class="header-title">{{ $t('common.detail') }}</h2>
          </div>
        </div>
        <div class="detail-wrapper">
          <div class="detail flex">
            <div class="detail-group flex title">
              <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('referenceDetail.title') }}</p>
              <div class="right flex flex-column x-center title">
                <template v-if="!isEditing">
                  <p>{{ props.postData.title }}</p>
                </template>
                <template v-else>
                  <UiInput :type="'text'" :value="editDataState.title" @updateValue="editDataState.title = $event"/>
                </template>
              </div>
            </div>
            <div class="detail-group flex category">
              <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('referenceList.column.category') }}</p>
              <template v-if="!isEditing">
                <div class="right flex flex-column x-center" :class="{disabled: isDisabled}">
                  <p>
                    {{ props.postData.category['1'] }} > {{ props.postData.category['2'] || '-' }} > {{ props.postData.category['3'] || '-' }}
                  </p>
                </div>
              </template>
              <template v-else>
                <div class="category-dropdown-wrapper">
                  <div class="be-dropdown flex y-center" ref="dropdown" @click.stop.prevent="toggleDropDown('1depth')">
                  <span class="current-type">
                    {{ categoriesData.select1depthCategory && categoriesData.select1depthCategory.name || $t('referenceCategory.depth.depth1') }}
                  </span>
                    <span class="be-icon size-20 icon-grey-md icon-dropdown">
                      <i class="font-icon-right-arrow"></i>
                    </span>
                    <Transition name="slide">
                      <template v-if="categoriesData.is1depthCategory">
                        <ul class="list" :class="{'is-show': categoriesData.is1depthCategory}">
                          <template v-for="item in categoriesData.categoryDepth1List" :key="item.depth">
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
                      {{ categoriesData.select2depthCategory && categoriesData.select2depthCategory.name || $t('referenceCategory.depth.depth2') }}
                    </span>
                    <span class="be-icon size-20 icon-grey-md icon-dropdown">
                      <i class="font-icon-right-arrow"></i>
                    </span>
                    <Transition name="slide">
                      <template v-if="categoriesData.is2depthCategory">
                        <ul class="list" :class="{'is-show': categoriesData.is2depthCategory}">
                          <template v-for="item in categoriesData.categoryDepth2List" :key="item.depth">
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
                      {{ categoriesData.select3depthCategory && categoriesData.select3depthCategory.name || $t('referenceCategory.depth.depth3') }}
                    </span>
                    <span class="be-icon size-20 icon-grey-md icon-dropdown">
                        <i class="font-icon-right-arrow"></i>
                      </span>
                    <Transition name="slide">
                      <template v-if="categoriesData.is3depthCategory">
                        <ul class="list" :class="{'is-show': categoriesData.is3depthCategory}">
                          <template v-for="item in categoriesData.categoryDepth3List" :key="item.depth">
                            <li @click.stop="selectDropDown(item, '3depth')">
                              {{ item.name }}
                            </li>
                          </template>
                        </ul>
                      </template>
                    </Transition>
                  </div>
                </div>
              </template>
            </div>
            <div class="detail-group flex">
              <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('referenceList.column.createdDate') }}</p>
              <div class="right flex flex-column x-center" :class="{disabled: isDisabled}">
                <p>{{ dateFormatter(props.postData.reg_date, 'time') }}</p>
              </div>
            </div>

            <div class="detail-group flex">
              <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('referenceList.column.isReference') }}</p>
              <div class="right flex x-center radio-wrap">
                <div class="flex y-center" :class="{selected: isReference, disabled: !isEditing }" @click="radioSelect('reference')">
                  <span class="check-selected"></span>
                  <label for="reference">{{ $t('common.onReference') }}</label>
                </div>
                <div class="flex y-center" :class="{selected: !isReference, disabled: !isEditing }" @click="radioSelect('notReference')">
                  <span class="check-selected"></span>
                  <label for="notReference">{{ $t('common.offReference') }}</label>
                </div>
              </div>
            </div>
            <div class="detail-group flex">
              <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('referenceList.column.author') }}</p>
              <div class="right flex flex-column x-center" :class="{disabled: isDisabled}">
                <p>{{ props.postData.author }}</p>
              </div>
            </div>
            <div class="detail-group flex">
              <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('referenceList.column.citationCount') }}</p>
              <div class="right flex flex-column x-center" :class="{disabled: isDisabled}">
                <p>{{ props.postData.use_count }}</p>
              </div>
            </div>
          </div>
          <template v-if="isEditing">
            <div class="flex flex-column gap-16 file-wrapper">
              <div class="flex y-center gap-20 file-upload">
                <span class="title">{{ $t('writing.fileUpload') }}</span>
                <label for="file_upload" class="file-upload-btn disabled">{{ $t('writing.fileRegister') }}</label>
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
              <template v-if="fileDataState.fileNames && fileDataState.fileNames.length !== 0">
                <template v-for="(file, index) in fileDataState.fileNames" :key="file.name">
                  <div class="flex y-center x-between gap-20 file-list">
                    <p>{{ file.name }}</p>
                    <span class="icon-wrap" @click="deleteFile(index)">
                      <i class="font-icon-close" />
                    </span>
                  </div>
                </template>
              </template>
            </div>
          </template>
          <div class="detail-desc flex">
            <p class="detail-desc-title be-font text-grey-sm size-13 bold">{{ $t('referenceDetail.content') }}</p>
            <template v-if="!isEditing">
              <div class="detail">
                <template v-for="file in fileDataState.fileNames" :key="file.name">
                  <p class="files">{{ file.name }}</p>
                </template>
                <p v-html="!isMarkdown ? convertHTML(props.postData.content) : convertMarkdownToHtml(props.postData.content)"></p>
              </div>
            </template>
            <template v-else>
              <div class="writing-desc" @click.stop="editFocus = true">
                <template v-if="isMarkdown">
                  <CKEditor
                      v-model="editDataContent"
                      :placeholder="$t('common.content')"
                      :value="editDataContent"
                      :limit="60000"
                      :class="'write-tiptap'"
                      class="board-write-block content"
                      :type="'post'"
                      :active="editFocus"/>
                </template>
                <template v-else>
                  <CKEditor
                      v-model="editDataState.content"
                      :placeholder="$t('common.content')"
                      :value="editDataState.content"
                      :limit="60000"
                      :class="'write-tiptap'"
                      class="board-write-block content"
                      :type="'post'"
                      :active="editFocus"/>
                </template>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </template>
</template>

<style lang="scss" scoped>
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
      gap: 8px;
      align-items: center;
    }
  }

  .reference-detail-container {
    border-radius: $radius-16;
    background: $whiteColor;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.16);
    padding: 28px 32px;
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

      .detail {
        flex-wrap: wrap;

        &:deep(img) {
          flex-grow: 1;
          flex-shrink: 1;
          max-width: 100%;
        }

        .detail-group {
          flex: 1 1 calc(50% - 10px);
          border-bottom: 1px solid $line-sm;

          &.category {
            flex: 0 0 100%;

            .category-dropdown-wrapper {
              width: 50%;
              display: flex;
              align-items: center;
              gap: 12px;
            }
          }

          &.title {
            flex: 0 0 100%;

            .right {
              &:deep(.be-input-wrapper) {
                .delete-text {
                  top: 53%;
                  transform: translateY(-50%);
                }
              }
            }
          }

          .left {
            min-width: 122px;
            padding: 10px 15px;
          }

          .right {
            &.disabled {
              p {
                color: $grey-100;
              }
            }

            p {
              padding: 10px 0;
            }


            &.disabled {
              color: $grey-100;
            }

            &.radio-wrap {
              gap: 12px;
              padding: 10px 0;

              div {
                gap: 8px;

                .check-selected {
                  position: relative;
                  display: inline-block;
                  width: 14px;
                  height: 14px;
                  border: 2px solid $grey-300;
                  border-radius: 50%;
                }

                &.disabled {
                  pointer-events: none;
                  color: #aaa;
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
        }
      }

      .detail-author {
        display: flex;
        border-bottom: 1px solid $line-sm;

        .left {
          width: 122px;
          padding: 10px 15px;
        }

        .right {

          &.disabled {
            p {
              color: $grey-100;
            }
          }

          p {
            padding: 10px 0;
          }

          &.disabled {
            color: $grey-100;
          }
        }
      }

      .file-wrapper {
        .file-upload {
          margin-top: 10px;
          gap: 35px;

          .title {
            color: #8c8c8c;
            font-size: 13px;
            font-weight: $bold;
            padding: 10px 15px;
          }
        }
        .file-list {
          margin-left: 100px;
          padding: 10px 15px;
          width: 30%;

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

      .detail-desc {
        .detail-desc-title {
          width: 122px;
          padding: 16px 15px;
        }

        .detail {
          white-space: normal;
          word-break: keep-all;
          flex: 1;
          width: 100%;
          min-height: 200px;
          max-height: 800px;
          padding: 16px 0;
          border: none;
          resize: none;
          overflow-y: scroll;

          &:focus {
            outline: none;
          }

          .files {
            margin-bottom: 12px;
          }
        }

        .writing-desc {
          margin-top: 16px;
          width: 100%;
          height: 800px;
        }
      }
    }
  }
}

</style>

