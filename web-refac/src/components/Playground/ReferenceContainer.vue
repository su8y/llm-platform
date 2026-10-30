<script setup>
import { defineEmits, getCurrentInstance, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { getReference } from '@/api/playground'
import { getVersionList } from "@/api/prompt.js";
import { APP_DOMAIN } from "@/libs/constants.js";
import { formatDate, convertMarkdownToHtml } from "@/libs/parse.js";

const emits = defineEmits(['elementHighlight'])
const props = defineProps({
  isReference: {
    type: Boolean,
    default: false
  },
  messageId: String,
  question: String,
  messageRef: Element,
})

const app = getCurrentInstance()
const bus = app?.appContext.config.globalProperties.emitter
const { t } = useI18n()
const selectedIndex = ref()
const prompt = ref('')
const scroller = ref()
const isSearchLoading = ref(false)
const promptVersionList = ref({})
const promptVersion = ref(null)
const referenceList = ref(null)
const mcpTools = ref([])
const initialPrompt = {
  memo: '',
  prompt: ''
}

getPromptVersionList('prompt')

async function getPromptVersionList (kind) {
  const data = { kind }

  try {
    const res = await getVersionList(data)

    if (res.code === 200) {
      const versionList = res.data

      if (versionList.length > 0) {
        for (let i in versionList) {
          versionList[i]['version'] =
              (versionList[i].version ? '* ' : '- ') + formatDate(versionList[i].version, 'num')
        }

        promptVersionList.value[kind] = versionList
        const prompt = versionList[0]

        promptVersion.value = prompt.version

      } else {
        promptVersionList.value[kind] = versionList
        prompt.value[kind] = initialPrompt
      }

    }
  } catch (e) {
    console.error('Error: ', e)
  }
}

const convertHTML = (content) => {
  const dom = document.createElement('p')
  dom.innerHTML = content

  const headingTags = dom.querySelectorAll('h1, h2, h3, h4, h5, h6')
  if (headingTags.length > 0) {
    headingTags.forEach(tag => {
      tag.style.fontSize = '15px'
    });
  }

  if (dom.querySelectorAll('img').length !== 0) {
    const images = dom.querySelectorAll('img')
    for (let i = 0; i < images.length; i++) {
      images[i].width = 0
      images[i].height = 0
      images[i].style.objectFit = 'contain'
      images[i].style.width = '100%'
      images[i].style.height = 'auto'
    }
  }
  if (dom.querySelectorAll('figure').length !== 0) {
    const figures = dom.querySelectorAll('figure')
    for (let i = 0; i < figures.length; i++) {
      figures[i].style.maxWidth = '400px'
      figures[i].style.width = '100%'
    }
  }

  if (dom.querySelectorAll('footer').length !== 0) {
    const footers = dom.querySelectorAll('footer')
    for (let i = 0; i < footers.length; i++) {
      footers[i].innerHTML = ''
    }
  }
  for (let i = dom.childNodes.length - 1; i >= 0; i--) {
    let node = dom.childNodes[i];

    if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim().length > 0) {
      node.remove(); // 텍스트 노드 제거
    }
  }

  return dom.innerHTML.replace(/<style[\s\S]*?>[\s\S]*?<\/style>/gi, '')
}

const setReferenceItem = async () => {
  isSearchLoading.value = true

  const param = {
    id: props.messageId
  }

  try {
    const res = await getReference(param)

    if (res.code === 200) {
      referenceList.value = {
        question: res.data.question,
        reference: res.data.retrieval_data,
        answer: '...',
        created: new Date()
      }
      mcpTools.value = res.data.mcp_tools
      selectedIndex.value = null
      isSearchLoading.value = false
    } else {
      alert(res.message)
      console.log('Error: ', res)
      isSearchLoading.value = false
    }

  } catch (e) {
    isSearchLoading.value = false
    console.error('Error: ', e)
  }
}

watch(() => props.messageId, () => {
  setReferenceItem()
})

const dateRangeStr = (item) => {
  const year = item.getFullYear();
  const month = item.getMonth() + 1;
  const day = item.getDate();
  const hour = item.getHours().toString().padStart(2, '0');
  const minute = item.getMinutes().toString().padStart(2, '0');
  const second = item.getSeconds().toString().padStart(2, '0');

  return t('dateTime.format', {
    year,
    month,
    day,
    hour,
    minute,
    second
  });
}

const scrollToElement = () => {
  emits('elementHighlight', true, props.messageId)
  const nextElement = props.messageRef.nextElementSibling
  nextElement.scrollIntoView({
    block: 'start',  // 또는 'center', 'end', 'nearest'
    behavior: 'smooth'
  })
}

const hideReference = () => {
  bus.emit('onReferenceData', {isShow: false, element: null})
}

const markdownToHtml = (content) => {
  const decoder = new TextDecoder()

  console.log(decoder.decode(content))
}
</script>

<template>
  <div class="reference-container" :class="{ 'isReference': !props.isReference }">
    <h1 class="container-header">
      <span class="be-font size-16 bold text-grey-md">
        {{ t('reference.reference') }}
        <span class="icon-wrap" @click="scrollToElement">
          <i class="font-icon-target" />
        </span>
      </span>
      <UiButton :type="'icon'" :class="{ 'isReference': !props.isReference }" @click="hideReference">
        {{ t('common.close') }}
        <i class="font-icon-close" />
      </UiButton>
    </h1>
    <div class="container-body flex flex-column x-between">
      <template v-if="referenceList">
        <div>
          <div class="prompt-versions">
            <h3 class="prompt-header">
              Prompt
            </h3>
            <span class="version">
              Version {{ promptVersion }}
            </span>
            <template v-if="mcpTools.length">
              <span class="version">
                MCP Tools: {{ mcpTools.join(', ') }}
              </span>
            </template>
          </div>
          <template v-if="referenceList || isSearchLoading">
            <div class="reference-list flex flex-column" ref="scroller">
              <template v-if="isSearchLoading">
                <div class="reference-list-loading">
                  <i class="icon icon--loading-animated" />
                </div>
              </template>
              <template v-else>
                <div class="flex flex-column be-font text-grey-lg size-13 line-height-150"
                    :class="['reference-item', 'selected']"
                    v-bind:key="item + index"
                >
                  <div class="reference-item-header flex y-start x-between">
                    <p>Q. {{ referenceList.question }}</p>
                  </div>
                  <div class="reference-item-body">
                    <div class="reference-body-field">
                      <p>Date: {{ dateRangeStr(referenceList.created) }}</p>
                    </div>
                    <div class="reference-body-field">
                      <p>Reference: </p>
                      <template v-for="(refer, index) in referenceList.reference" :key="refer">
                        <div class="reference-item-list">
                          <p class="reference-subject be-font">{{ index + 1 }}. {{ refer.title }}</p>
                          <template v-if="!isNaN(Number(refer.url))">
                            <p class="reference-url be-font size-13">
                                - {{ t('reference.source') }}:
                                <a :href="refer.data_type === 'parser' ? `${APP_DOMAIN}/tool/reference/drive/detail/${refer.url}` : `${APP_DOMAIN}/tool/reference/post/${refer.url}`" target="_blank">
                                  {{ refer.data_type === 'parser' ? `${APP_DOMAIN}/tool/reference/drive/detail/${refer.url}` : `${APP_DOMAIN}/tool/reference/post/${refer.url}` }}
                                </a>
                            </p>
                          </template>
                          <template v-if="refer.data_type === 'parser'">
                            <p
                                class="text-content"
                                v-html="convertMarkdownToHtml(refer.content)"
                            ></p>
                          </template>
                          <template v-else>
                            <p
                                class="text-content"
                              v-html="convertHTML(refer.content)"
                            ></p>
                          </template>
                        </div>
                      </template>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </template>
        </div>
      </template>
      <div class="reference-list-loading" v-else>
        <i class="icon icon--loading-animated" />
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.reference-container {
  width: 34%;
  background-color: $grey-100;
  overflow-y: auto;

  &.isReference {
    margin-right: -34%;
  }
}

.empty-container {
  height: 100%;
  gap: 15px;
}

.container-header {
  border-top-left-radius: 5px;

  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 32px;
  border-bottom: 1px solid $grey-50;

  > span {
    color: $grey-600;
    font-size: 18px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 8px;

    .icon-wrap {
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: $radius-4;
      border: 1px solid #CCC;
      background: $whiteColor;
      padding: 4px;
      box-sizing: border-box;
      font-size: 16px;
      color: #ec0047;
      cursor: pointer;
    }
  }
}

.container-body {
  height: calc(100% - 60px);
  padding: 20px 32px;
}

.prompt-versions {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-bottom: 21px;
  border-bottom: 1px dashed $line-lg;
}

.reference-list {
  gap: 10px;
  overflow-y: auto;
  margin-top: 21px;

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

  &-loading {
    display: flex;
    justify-content: center;
    width: 100%;
    padding-bottom: 20px;
  }
}

.reference-body-field {
  display: flex;
  gap: 5px;
}

.reference-item {
  width: 100%;
  border-radius: 8px;
  p {
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    word-break: break-all;
  }

  &.selected {
    p {
      overflow: visible;
      white-space: pre-line;
    }

    .reference-item-body {
      .reference-body-field {
        &:not(:first-child) {
          display: block;
        }
        padding: 10px 0;
        &:not(:first-child) {
          border-top: 1px solid #dbdbdb;
        }
      }
      .long-text-title {
        display: block;
      }
      .text-content {
        padding-left: 10px;

        figure.image.image_resized img {
          margin: 10px 0;
        }
      }
    }
  }
}

.reference-item-header {
  gap: 5px;
}
.reference-item-list {
  padding: 10px 0;
  &:not(:last-child) {
    border-bottom: 1px dashed #9e9e9e;
  }

  .text-content {
    figure.image {
      margin: 10px 0 ;
    }
  }
}

.reference-url {
  padding-left: 10px;
  padding-bottom: 10px;
  a {
    color: $primary-lg;
  }
}

.item-fold-button {
  width: 100%;
  padding: 5px 0;
  cursor: pointer;
  .icon-open {
    rotate: 90deg;

    &.open {
      rotate: -90deg;
    }
  }
}

.search {
  padding: 10px 17px;
  position: relative;

  &-button {
    position: absolute;
    top: 50%;
    right: 8%;
    padding: 3px;
    transform: translate(0, -43%);
  }
}

</style>
