<script setup>
import { ref, computed, watch, reactive, inject, defineAsyncComponent } from 'vue'

import { dateFormatter } from "@/libs/utils.js";
import { DRIVE_STATUS, WARNING_TYPE } from "@/libs/constants.js";
import { convertHtmlToMarkdown, convertMarkdownToHtml } from "@/libs/parse.js";

import UiButton from "@/components/Ui/UiButton.vue";
import Warning from "@/components/Modal/Warning.vue";

const CKEditor = defineAsyncComponent(() =>
    import('@/components/Editor/CKEditor.vue')
)
const modal = inject('$modal')

const emits = defineEmits(['delete', 'update', 'change'])
const props = defineProps({
  fileData: {
    type: Object,
    required: true
  },
  fileDetailData: {
    type: Object,
    required: true
  },
  currentPage: {
    type: Number,
    required: true
  },
  editing: {
    type: Boolean,
    default: true
  }
})

const isEditing = ref(false)
const page = ref(1)
const isDataEdit = ref(false)
const copyFileData = ref(convertMarkdownToHtml(props.fileDetailData?.content))
const isDisabled = ref(true)
const isPaginationInProgress = ref(false)
const editedFileData = reactive({
  page: [],
  content: []
})

const fileSizeToMb = computed(() => {
  return (value) => {
    return (value / (1024 * 1024)).toFixed(2)
  }
})

const pageLength = computed(() => {
  return props.fileDetailData?.allPage?.length
})

const convertHtml = computed(() => {
  let markdownContent = props.fileDetailData?.content

  markdownContent = markdownContent?.replace(
      /!\[([^\]]*)\]\(\/image\/placeholder\)/g,
      '$1'
  )

  return convertMarkdownToHtml(markdownContent)
})

watch(() => props.fileDetailData?.content, (value) => {
  const htmlContent = convertMarkdownToHtml(value)
  const editedIndex = editedFileData.page.lastIndexOf(page.value);

  if (editedIndex > -1) {
    copyFileData.value = editedFileData.content[editedIndex];
    return
  }
  copyFileData.value = htmlContent
})

watch(() => props.editing, (value) => {
  if (!value) {
    isEditing.value = false
    editedFileData.page = []
    editedFileData.content = []
  }
})

watch(() => copyFileData.value, async (newValue) => {
  // 페이지네이션 중이면 isDisabled 값을 변경하지 않음
  if (isPaginationInProgress.value) return;

  await onChangeData(true)

  if (isDataEdit.value) return
  const convertPropsData = convertMarkdownToHtml(props.fileDetailData?.content)
  const normalizedText1 = normalizeText(convertPropsData);
  const normalizedText2 = normalizeText(newValue);

  if (editedFileData.content.length > 0) {
    for (let i = 0; i < editedFileData.content.length; i++) {
      const convertPropsData = convertMarkdownToHtml(props.fileDetailData?.content)
      const normalizedText1 = normalizeText(convertPropsData);
      const normalizedText2 = normalizeText(editedFileData.content[i]);

      isDisabled.value = compareWithoutSpaces(normalizedText1, normalizedText2);
    }
    return
  }

  isDisabled.value = compareWithoutSpaces(normalizedText1, normalizedText2);
})


const deleteFile = async (id) => {
  emits('delete', {fileId: id})
}

const onEditing = async () => {
  if (isEditing.value) {
    modal.open(Warning, WARNING_TYPE.UPDATE_PDF_CANCEL).then(() => {
      modal.close()
      isEditing.value = !isEditing.value
      editedFileData.page = []
      editedFileData.content = []
    }).catch(() => {
      modal.close()
    })
  } else {
    isEditing.value = !isEditing.value
    editedFileData.page = []
    editedFileData.content = []
    copyFileData.value = await convertMarkdownToHtml(props.fileDetailData?.content)
  }

}

const updateFile = async () => {
  const params = {
    fileId: props.fileData.fileId,
    currentPage: editedFileData.page,
  }

  if (editedFileData.page.length !== editedFileData.content.length) {
    editedFileData.content.shift()
  }

  let convertContent = []
  for (let i = 0; i < editedFileData.content.length; i++) {
    convertContent.push(await convertHtmlToMarkdown(editedFileData.content[i]))
  }

  params.content = convertContent

  emits('update', params)
}

const updatePagination = (type) => {
  isPaginationInProgress.value = true;

  // 현재 페이지의 데이터를 저장
  if (isDataEdit.value) {
    editedFileData.page.push(page.value);
    editedFileData.content.push(copyFileData.value);
  }

  // 페이지 변경
  isDataEdit.value = false;
  type === 'left' ? page.value-- : page.value++;

  const editedIndex = editedFileData.page.indexOf(page.value);
  if (editedIndex > -1) {
    copyFileData.value = editedFileData.content[editedIndex];

  } else {
    copyFileData.value = props.fileDetailData?.content;
  }

  // 페이지네이션 작업이 완료된 후 플래그 해제 (약간의 지연 추가)
  setTimeout(() => {
    isPaginationInProgress.value = false;
  }, 1000);

  emits('change', page.value)
}

const normalizeText = (html) => {
  // 이미지 태그의 존재 여부를 확인하기 위한 임시 저장소
  const div = document.createElement('div');
  div.innerHTML = html;

  // 이미지 태그 개수와 정보 수집
  const images = div.querySelectorAll('img');
  const imageData = Array.from(images).map(img => ({
    src: img.src,
    alt: img.alt || ''
  }));

  // 이미지 정보를 포함한 해시값 생성 (단순화를 위해 JSON 문자열로 변환)
  const imageHash = JSON.stringify(imageData);

  // 텍스트 콘텐츠 추출
  let textContent = div.textContent.replace(/\s+/g, ' ').trim();

  // 이미지 해시값을 텍스트 콘텐츠에 추가하여 반환
  return textContent + '|' + imageHash;
}

const compareWithoutSpaces = (text1, text2) => {
  // '|' 문자로 분리하여 텍스트와 이미지 해시값 분리
  const [textContent1, imageHash1 = ''] = text1.split('|');
  const [textContent2, imageHash2 = ''] = text2.split('|');

  // 텍스트와 이미지 해시값 모두 비교
  const noSpaces1 = textContent1.replace(/\s/g, '');
  const noSpaces2 = textContent2.replace(/\s/g, '');

  return noSpaces1 === noSpaces2 && imageHash1 === imageHash2;
}

const onChangeData = async (value) => {
  isDataEdit.value = value
  const convertPropsData = convertMarkdownToHtml(props.fileDetailData?.content)

  const normalizedText1 = normalizeText(convertPropsData);
  const normalizedText2 = normalizeText(copyFileData.value);
  const noSpacesComparison = compareWithoutSpaces(normalizedText1, normalizedText2);

  // 이미 편집된 페이지인지 확인
  const pageIndex = editedFileData.page.indexOf(page.value);

  if (isDataEdit.value) {
    // 페이지가 이미 존재하는 경우 콘텐츠만 업데이트
    if (pageIndex !== -1) {
      // 기존 콘텐츠 업데이트
      editedFileData.content[pageIndex] = copyFileData.value;
    } else {
      // 새로운 페이지와 콘텐츠 추가
      editedFileData.page.push(page.value);
      editedFileData.content.push(copyFileData.value);
    }
  }

  if (noSpacesComparison) {
    // 변경 내용이 없는 경우 해당 페이지 제거
    const pageIndexToRemove = editedFileData.page.indexOf(page.value);
    if (pageIndexToRemove !== -1) {
      editedFileData.page.splice(pageIndexToRemove, 1);
      editedFileData.content.splice(pageIndexToRemove, 1);
    }
  }

  isDataEdit.value = false;
}


const handlePagination = () => {
  const allPage = props.fileDetailData.allPage
  if (!allPage.includes(page.value)) {
    page.value = 1
  }
  emits('change', page.value)
}
</script>

<template>
  <template v-if="props.fileData">
    <div class="reference-detail-wrapper">
      <div class="monitoring-detail-header">
        <div class="back-list">
          <RouterLink :to="{ name: 'FileDrive' }">
            <UiButton :type="'only-icon outline'">
              <i class="font-icon-left-arrow" />
            </UiButton>
          </RouterLink>
          <span>
          {{ $t('common.back') }}
         </span>
        </div>
        <div class="edit-btn-wrap">
          <template v-if="isEditing">
            <UiButton :type="'outline'" @click="onEditing">
              {{ $t('common.cancel2') }}
            </UiButton>
            <UiButton :type="'icon primary'" :disabled="isDisabled" @click="updateFile">
              {{ $t('common.save2') }}
              <i class="font-icon-save"></i>
            </UiButton>
          </template>
          <template v-else>
            <UiButton :type="'icon outline'" @click="deleteFile(props.fileData.fileId)">
              {{ $t('common.delete2') }}
              <i class="font-icon-delete"></i>
            </UiButton>
            <UiButton :type="'icon outline primary'" @click="onEditing">
              {{ $t('common.edit2') }}
              <i class="font-icon-write"></i>
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
              <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('drive.column.fileName') }}</p>
              <div class="right flex flex-column x-center title">
                <p>{{ props.fileData.fileName }}</p>
              </div>
            </div>
            <div class="detail-group flex">
              <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('drive.column.regDate') }}</p>
              <div class="right flex flex-column x-center">
                <p>{{ dateFormatter(props.fileData.regDate, 'time') }}</p>
              </div>
            </div>

            <div class="detail-group flex">
              <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('drive.column.fileSize') }}</p>
              <div class="right flex flex-column x-center">
                <p>{{ `${fileSizeToMb(props.fileData.fileSize)}MB` }}</p>
              </div>
            </div>
            <div class="detail-group flex">
              <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('drive.column.fileType') }}</p>
              <div class="right flex flex-column x-center">
                <p>{{ props.fileData.fileType }}</p>
              </div>
            </div>
            <div class="detail-group flex">
              <p class="left be-font text-grey-sm size-13 bold flex y-center">{{ $t('drive.column.status') }}</p>
              <div class="right flex flex-column x-center">
                <p>{{ $t(`drive.status.${DRIVE_STATUS[props.fileData.status]}`) }}</p>
              </div>
            </div>
            <div class="detail-desc flex flex-column">
              <template v-if="!isEditing">
                <div class="pdf-pagination-container flex x-center">
                  <div class="pagination-wrapper flex y-center">
                    <div class="pagination-content flex y-center gap-8">
                      <input type="number" class="current-page" v-model="page" @change="handlePagination" />
                      <span> / </span>
                      <span class="total-page">{{ props.fileDetailData?.unitCount || 0 }}</span>
                    </div>
                    <div class="pdf-pagination-btn-wrapper flex gap-4">
                      <UiButton :type="'only-icon outline'" :disabled="page === 1 || !pageLength" @click="updatePagination('left')">
                        <i class="font-icon-fill-left-arrow" />
                      </UiButton>
                      <UiButton :type="'only-icon outline'" :disabled="page === props.fileDetailData?.unitCount || !pageLength" @click="updatePagination('right')">
                        <i class="font-icon-fill-right-arrow" />
                      </UiButton>
                    </div>
                  </div>
                </div>
                <div class="detail">
                  <div class="detail-content" v-html="convertHtml"></div>
                </div>
              </template>
              <template v-else>
                <div class="writing-desc">
                  <div class="pdf-pagination-container flex x-center">
                    <div class="pagination-wrapper flex y-center">
                      <div class="pagination-content flex y-center gap-8">
                        <input type="number" class="current-page" v-model="page" @change="handlePagination" />
                        <span> / </span>
                        <span class="total-page">{{ props.fileDetailData?.unitCount || 0 }}</span>
                      </div>
                      <div class="pdf-pagination-btn-wrapper flex gap-4">
                        <UiButton :type="'only-icon outline'" :disabled="page === 1 || !pageLength" @click="updatePagination('left')">
                          <i class="font-icon-fill-left-arrow" />
                        </UiButton>
                        <UiButton :type="'only-icon outline'" :disabled="page === props.fileDetailData?.unitCount || !pageLength" @click="updatePagination('right')">
                          <i class="font-icon-fill-right-arrow" />
                        </UiButton>
                      </div>
                    </div>
                  </div>
                  <CKEditor
                      v-model="copyFileData"
                      class="board-write-block content"
                      :placeholder="$t('common.content')"
                      :limit="60000"
                      :class="['write-tiptap', 'file-editor']"
                      :type="'post'"
                      :is-file-editor="true"
                      @isEditorChange="onChangeData"
                  />
                </div>
              </template>
            </div>
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
        }
      }

      .detail-desc {
        width: 100%;
        position: relative;

        .pdf-pagination-container {
          padding: 15px 0;
          width: 190px;
          position: absolute;
          top: 16px;
          left: 50%;
          transform: translateX(278px);
          background: #fff;
          border-radius: 3px;
          border: 1px solid hsl(220, 6%, 81%);
          z-index: 1;

          .pagination-wrapper {
            .pagination-content {
              min-width: 102px;

              .current-page {
                max-width: 50px;
                text-align: center;
                padding: 6px 0;
                border: 1px solid #BBB;
                border-radius: 5px;
                box-sizing: border-box;

                /* Chrome, Safari, Edge, Opera */
                &::-webkit-outer-spin-button,
                &::-webkit-inner-spin-button {
                  -webkit-appearance: none;
                  margin: 0;
                }

                /* Firefox  */
                &[type='number'] {
                  -moz-appearance: textfield;
                }
              }
            }
          }
        }

        .detail-desc-title {
          width: 122px;
          padding: 16px 15px;
        }


        .detail {
          background-color: $grey-100;
          white-space: normal;
          word-break: keep-all;
          flex: 1;
          width: 100%;
          min-height: 200px;
          max-height: 800px;
          padding: 16px 0;
          border: none;
          resize: none;
          overflow: auto;

          .detail-content {
            padding: 12px;
            border-radius: 6px;
            background-color: $whiteColor;
            margin: 0 auto;
            max-width: 540px;
            min-height: 764px;
            box-shadow: 0px 2px 4px -2px rgba(0, 0, 0, 0.2);
            word-break: break-word;

            :deep(blockquote) {
              overflow: hidden;
              padding-right: 1.5em;
              padding-left: 1.5em;
              margin-left: 0;
              margin-right: 0;
              font-style: italic;
              border-left: solid 5px hsl(0, 0%, 80%);
            }

            :deep(img) {
              max-width: 100%;
              height: auto;
            }
          }

          &:focus {
            outline: none;
          }

          .files {
            margin-bottom: 12px;
          }
        }

        .writing-desc {
          width: 100%;
          height: 800px;
          position: relative;

          .file-editor {
            :deep(.ck.ck-editor__top) {
              position: absolute;
              width: 190px;
              left: 50%;
              transform: translateX(278px);
              top: 80px;

              .ck-sticky-panel .ck-sticky-panel__content {
                border-bottom-width: initial;
              }
            }
          }

          :deep(.ck.ck-editor__main) {
            background-color: $grey-100;
            padding: 16px 0;
          }

          :deep(.ck.ck-content) {
            box-sizing: border-box;
            border-radius: 6px;
            padding: 12px;
            background-color: $whiteColor;
            margin: 0 auto;
            max-width: 540px;
            height: 100%;
            box-shadow: 0px 2px 4px -2px rgba(0, 0, 0, 0.2);
          }
        }
      }
    }
  }
}

</style>

