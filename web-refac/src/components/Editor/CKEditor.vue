<script setup>
import { ref, computed, watch, defineProps, defineEmits } from 'vue'
import { useI18n } from 'vue-i18n'
import { Ckeditor } from '@ckeditor/ckeditor5-vue'
import coreTranslations from 'ckeditor5/translations/ko.js';
import coreTranslationsJa from 'ckeditor5/translations/ja.js';

import '@ckeditor/ckeditor5-language/build/translations/ko.js'
import '@ckeditor/ckeditor5-language/build/translations/ja.js'

defineExpose({ Ckeditor })

import 'ckeditor5/ckeditor5.css'

// CKEditor 빌드를 사용 (개별 플러그인 import 대신)
import {
  ClassicEditor,
  Essentials,
  Bold,
  Italic,
  Font,
  Paragraph,
  Heading,
  List,
  Alignment,
  HorizontalLine,
  Link,
  BlockQuote,
  Image,
  ImageCaption,
  ImageStyle,
  ImageToolbar,
  ImageUpload,
  ImageResizeEditing,
  ImageResizeHandles,
  ImageResizeButtons,
  Table,
  TableToolbar,
  MediaEmbed,
  GeneralHtmlSupport,
  Indent,
  IndentBlock,
  SourceEditing,
  Markdown,
  PasteFromMarkdownExperimental
} from 'ckeditor5'

import Base64UploadAdapter from './Base64UploaderPlugin'

const { t, locale } = useI18n()

const emit = defineEmits(['update:modelValue', 'blurEditor', 'isEditorChange'])
const props = defineProps({
  value: {
    default: '',
    required: false
  },
  readonly: {
    default: false
  },
  tagName: {
    type: String,
    required: false,
    default: 'div'
  },
  disabled: {
    type: Boolean,
    required: false
  },
  uploadUrl: {
    type: String,
    required: false
  },
  config: {
    type: Object,
    required: false,
    default () {
    }
  },
  isOpen: {
    default: false,
    type: Boolean,
    required: false
  },
  modelValue: {
    type: String
  },
  isFileEditor: {
    type: Boolean,
  }
})

const editor = ref(ClassicEditor)
const editorRef = ref(null)

const editorData = computed(() => props.modelValue)
const editorConfig = computed(() => {
  const config = {
    plugins: [
      Essentials,
      Bold,
      Italic,
      Font,
      Paragraph,
      Heading,
      List,
      Alignment,
      HorizontalLine,
      Link,
      BlockQuote,
      Image,
      ImageCaption,
      ImageStyle,
      ImageToolbar,
      ImageUpload,
      ImageResizeEditing,
      ImageResizeHandles,
      ImageResizeButtons,
      Table,
      TableToolbar,
      MediaEmbed,
      Base64UploadAdapter,
      GeneralHtmlSupport,
      Indent,
      IndentBlock,
      SourceEditing,
      // Markdown,
      // PasteFromMarkdownExperimental
    ],
    htmlSupport: {
      allow: [
        {
          name: /.*/, // 모든 태그 허용
          attributes: true, // 모든 속성 허용
          classes: true, // 모든 클래스 허용
          styles: true // 모든 스타일 허용
        }
      ],
      disallow: [
        {
          name: 'figure'  // figure 태그 명시적 차단
        }

      ], // img 태그 제한 제거
      allowEmpty: ['i', 'span', 'hr', 'div', 'p'] // 빈 태그 보존
    },
    allowedContent: true,
    placeholder: t('common.content'),
    language: {
      ui: locale.value
    },
    translations: [
      coreTranslations,
      coreTranslationsJa
    ],
    fontSize: {
      options: [
        10,
        12,
        13,
        'default',
        16,
        20,
        32
      ]
    },
    fontColor: {
      colors: [
        {
          color: '#1e1e1e',
          label: 'black'
        }, {
          color: '#696969',
          label: 'Dark Grey'
        }, {
          color: '#929292',
          label: 'Grey'
        }, {
          color: '#d6d6d6',
          label: 'Light Grey'
        }, {
          color: '#fff',
          label: 'White',
          hasBorder: true
        }, {
          color: '#ec0047',
          label: 'Red'
        }, {
          color: '#fbbd1c',
          label: 'Yellow'
        }, {
          color: '#9fd325',
          label: 'Green'
        }, {
          color: '#57c1ff',
          label: 'blue'
        }, {
          color: '#8871ff',
          label: 'Violet'
        }, {
          color: '#c20842',
          label: 'Deep Red'
        }, {
          color: '#f37200',
          label: 'Deep Orange'
        }, {
          color: '#549300',
          label: 'Deep Green'
        }, {
          color: '#0087CA',
          label: 'Deep Blue'
        }, {
          color: '#6554c0',
          label: 'Deep Violet'
        }
      ]
    },
    fontBackgroundColor: {
      colors: [
        {
          color: '#f4edf9',
          label: 'Pale Violet'
        }, {
          color: '#e4f7ff',
          label: 'Pale Blue'
        }, {
          color: '#ffe5cb',
          label: 'Pale Orange'
        }, {
          color: '#fcf3da',
          label: 'Pale Yellow'
        }, {
          color: '#fff',
          label: 'White',
          hasBorder: true
        }, {
          color: '#f1dbff',
          label: 'Light Violet'
        }, {
          color: '#c6ebff',
          label: 'Light Blue'
        }, {
          color: '#ffc68e',
          label: 'Light Orange'
        }, {
          color: '#ffe8a9',
          label: 'Light Yellow'
        }, {
          color: '#e6e6e6',
          label: 'Light Grey'
        }
      ]
    },
    heading: {
      options: [
        { model: 'heading1', view: 'h1', title: 'Heading 1', class: 'ck-heading_heading1' },
        { model: 'heading2', view: 'h2', title: 'Heading 2', class: 'ck-heading_heading2' },
        { model: 'heading3', view: 'h3', title: 'Heading 3', class: 'ck-heading_heading3' },
        { model: 'heading4', view: 'h4', title: 'Heading 4', class: 'ck-heading_heading4' },
        { model: 'heading5', view: 'h5', title: 'Heading 5', class: 'ck-heading_heading5' },
        { model: 'heading6', view: 'h6', title: 'Heading 6', class: 'ck-heading_heading6' },
        { model: 'paragraph', title: 'Paragraph', class: 'ck-heading_paragraph' }
      ]
    },
    lineHeight: {
      options: [
        0.5,
        1,
        'default',
        1.65,
        2,
        2.5,
        3
      ]
    },
    table: {
      contentToolbar: ['tableColumn', 'tableRow', 'mergeTableCells'],
      defaultHeadings: { rows: 1, columns: 0 }
    },
    image: {
      resizeOptions: [
        {
          name: 'resizeImage:original',
          value: null,
          icon: 'original'
        },
        {
          name: 'resizeImage:custom',
          value: 'custom',
          icon: 'custom'
        },
        {
          name: 'resizeImage:50',
          value: '50',
          icon: 'medium'
        },
        {
          name: 'resizeImage:75',
          value: '75',
          icon: 'large'
        }
      ],
      toolbar: [
        'imageStyle:inline',
        {
          name: 'imageStyle:icons',
          items: [
            'imageStyle:alignLeft',
            'imageStyle:alignRight'
          ],
          defaultItem: 'imageStyle:alignLeft'
        },
        {
          name: 'imageStyle:blockIcons',
          items: [
            'imageStyle:alignBlockLeft',
            'imageStyle:block',
            'imageStyle:alignBlockRight'
          ],
          defaultItem: 'imageStyle:alignBlockLeft'
        },
        '|',
        'toggleImageCaption',
        'imageTextAlternative',
        'ckboxImageEdit',
        'resizeImage:50',
        'resizeImage:75',
        'resizeImage:original',
      ],
      styles: [
        'alignCenter',
        'alignLeft',
        'alignRight'
      ]
    },
    // 플러그인을 문자열로 지정 (ClassicEditor에 포함된 것들 사용)
    extraPlugins: [Base64UploadAdapter],
    toolbar: {
      items: [
        'heading',
        'fontSize',
        '|',
        'bold',
        'italic',
        'underline',
        'fontColor',
        'fontBackgroundColor',
        '|',
        'alignment',
        'outdent',
        'indent',
        'lineHeight',
        '|',
        'numberedList',
        'bulletedList',
        '|',
        'horizontalLine',
        'link',
        'blockQuote',
        'imageUpload',
        'insertTable',
        'mediaEmbed',
        '|',
        'sourceEditing'
      ]
    },
    mediaEmbed: {
      elementName: 'oembed',
      migrateToPreferredTagOnChange: true,
      previewsInData: true
    }
  }

  if (props.isFileEditor) {
    config.toolbar.items = [
      'heading',
      'fontSize',
      '|',
      'bold',
      'italic',
      '|',
      'numberedList',
      'bulletedList',
      '|',
      'horizontalLine',
      'link',
      'blockQuote',
      'imageUpload',
      'insertTable'
    ];
  }

  return config
})

watch(
    () => props.modelValue,
    (newVal) => {
      if (editorRef.value && newVal !== editorRef.value.getData()) {
        editorRef.value.setData(newVal)
      }
    }
)

const onEditorReady = (ed) => {
  editorRef.value = ed

  if (props.readonly) {
    // 고유 ID로 읽기 전용 모드 활성화
    ed.enableReadOnlyMode('ui-readonly-mode');
  } else {
    // 필요한 경우 읽기 전용 모드 비활성화
    ed.disableReadOnlyMode('ui-readonly-mode');
  }


  ed.model.document.on( 'change', async () => {
    const changes = ed.model.document.differ.getChanges();

    for (const change of changes) {
      if (change.name === 'imageBlock' && change.type === 'remove') {

        if (change.attributes) {
          for (const attr of change.attributes) {
            if (attr[0] && attr[0] === 'uploadStatus') {
              if (attr[1] && attr[1] === 'uploading') {
                console.log('remove : ', change)
              }
            }
          }
        }
      }
    }
  } )

  editorRef.value = ed

  let initialContent = '';

  // 초기값 세팅
  if (props.modelValue) {
    ed.setData(props.modelValue)
    initialContent = ed.getData();
  }

  // 내부에서 실제로 내용이 바뀔 때만 부모에 emit
  ed.model.document.on('change:data', () => {
    const html = ed.getData()
    emit('update:modelValue', html)
  })

  let contentChanged = false;

  ed.model.document.on('change:data', () => {
    const currentContent = ed.getData();
    // 초기 콘텐츠와 현재 콘텐츠 비교
    contentChanged = (initialContent !== currentContent);
  });

  ed.editing.view.document.on('blur', () => {
    setTimeout(() => {
      // 특정 에디터 인스턴스의 DOM 요소 참조
      const editorElement = ed.ui.view.element;

      // 현재 활성화된 요소가 해당 에디터 내부에 있는지 확인
      if (editorElement && editorElement.contains(document.activeElement)) {
        // 에디터 내부의 어떤 요소를 클릭한 경우 - emit 하지 않음
        return;
      }

      // 실제로 내용이 변경된 경우에만 이벤트 emit
      if (contentChanged) {
        emit('blurEditor');
        emit('isEditorChange', true);
        // 변경된 내용을 새로운 초기 상태로 업데이트
        initialContent = ed.getData();
        contentChanged = false;
      }
    }, 50);
  });
}

const offEditor = (e) => {
  if (!e.isTrusted || e.target === window) return

  if (editorData.value) {
    emit('blurEditor')
  }
}

const onEnter = (e) => {
  if (!e.isTrusted || e.target === window) return

  if (e.key === 'Enter' || e.key === 'Backspace') {
    emit('blurEditor')
  }
}

watch(() => props.isOpen, (value) => {
  if (value && editorRef.value) {
    editorRef.value.editing.view.focus()
  }
})
</script>

<template>
  <div
      class="ui-editor"
      :class="{ readonly }"
      @keyup="onEnter"
  >
    <span class="default-text">
<!--      {{ $t('post.opinionPlz') }}-->
    </span>
    <ckeditor
        disable-two-way-data-binding
        :value="editorData"
        :editor="editor"
        :config="editorConfig"
        :tag-name="tagName"
        :disabled="disabled"
        @ready="onEditorReady"
        @blur="offEditor"
    />
  </div>
</template>

<style lang="scss">
.ui-editor {
  min-height: 40px;
  height: 100%;
  & > .default-text {
    display: block;
    position: absolute;
    left: 20px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 14px;
    color: #bbb;
  }
  &.readonly {
    :deep(.ck-editor) {
      margin: -10px;
    }
    .ck-sticky-panel {
      display: none;
    }
    .ck-rounded-corners {
      border: none;
    }
  }
}

.ck.ck-editor {
  height: calc(100% - 40px);
  .ck-editor__main {
    height: 100%;
    .ck-content {
      height: 100%;

      .mailtrack-img {
        display: none !important;
      }

      .gmail_quote {
        div {
          font-style: normal !important;
        }

        span {
          margin: 0 !important;
          display: inline-block !important;
        }
      }
    }
  }
}

.ck-content .table, .ck-content .image {
  margin: 0;
}

:deep(.ck.ck-editor__top) {
  display: none;
  border: none;
  border-radius: 0;
  .ck-sticky-panel {
    border: none;
    .ck-sticky-panel__content {
      border: none;
      .ck-toolbar {
        border: none;
      }
    }
  }
}

.ck-source-editing-area {
  height: 100%;

  textarea {
    overflow: auto;
  }
}

:deep(.ck.ck-editor__main) {
  min-height: 135px;
  height: 100%;
  margin-bottom: 70px;
  font-size: 16px;
  line-height: 1.63;
  color: #444;
  // overflow-y: auto;

  &>.ck-editor__editable:not(.ck-focused) {
    outline: none;
    min-height: 130px;
    padding: 25px 25px 0;
    border: none !important;
    & .ck-blurred {
    }
    .table {
      table {
        border: 1px solid #d9d5d4;
        width: auto;
      }
    }
  }
  &>.ck-editor__editable:not(.ck-editor__nested-editable).ck-focused {
    min-height: 130px;
    padding: 25px 25px 0;
    border: none !important;
    box-shadow: none;
    .table {
      table {
        border: 1px solid #d9d5d4;
        width: auto;
      }
    }
  }
  &>.ck.ck-editor__editable_inline>:first-child {
    margin-top: 0;
  }
}
.comment-active {
  :deep(.ck.ck-editor__main){
    height: 100%;
    display: block;
  }
  :deep(.ck.ck-editor__top) {
    display: block;
  }
}

// heading css
:deep(.ck.ck-toolbar>.ck-toolbar__items > .ck-heading-dropdown) {
  width: 110px;
}

:deep(.ck-insert-table-dropdown__grid) {
  width: 340px;
}
// underline icon css
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > .ck-button:nth-child(5)) {
  background: url('@/assets/img/ckeditor/icon-ckeditor-underline.svg') no-repeat center !important;
}
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > .ck-button:nth-child(5):hover) {
  background: var(--ck-color-button-on-hover-background) url('@/assets/img/ckeditor/icon-ckeditor-underline.svg') no-repeat center !important;
}
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > .ck-button:nth-child(5).ck-on) {
  background: var(--ck-color-button-default-hover-background) url('@/assets/img/ckeditor/icon-ckeditor-underline.svg') no-repeat center !important;
}
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > .ck-button:nth-child(5).ck-on:hover) {
  background: var(--ck-color-button-on-hover-background) url('@/assets/img/ckeditor/icon-ckeditor-underline.svg') no-repeat center !important;
}
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > .ck-button:nth-child(5) > svg) {
  display: none !important;
}

// bulletedList position
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > div:nth-child(12) .ck-dropdown__panel.ck-dropdown__panel-visible .ck.ck-toolbar .ck-toolbar__items) {
  padding-left: 64px !important;
}
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > div:nth-child(12) .ck-dropdown__panel.ck-dropdown__panel-visible .ck.ck-toolbar .ck-toolbar__items button) {
  position: relative !important;
  &:nth-child(3) {
    position: absolute !important;
    left: 12px !important;
    float: left !important;
  }
}

// HorizontalLine
:deep(.ck-editor__editable .ck-horizontal-line) {
  border-bottom: 1px solid #d6d6d6;
  margin: 20px 0;
}

// quote icon css
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > button:nth-child(19)) {
  background: url('@/assets/img/ckeditor/icon-ckeditor-quote.svg') no-repeat center !important;
}
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > button:nth-child(19):hover) {
  background: var(--ck-color-button-default-hover-background) url('@/assets/img/ckeditor/icon-ckeditor-quote.svg') no-repeat center !important;
}
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > button:nth-child(19) > svg) {
  display: none !important;
}

// image icon css
:deep(.ck-file-dialog-button > button) {
  background: url('@/assets/img/ckeditor/icon-ckeditor-image.svg') no-repeat center !important;
}
:deep(.ck-file-dialog-button > button:hover) {
  background: var(--ck-color-button-default-hover-background) url('@/assets/img/ckeditor/icon-ckeditor-image.svg') no-repeat center !important;
}
:deep(.ck-file-dialog-button > button > svg) {
  display: none !important;
}

// table icon css
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > .ck-dropdown:nth-child(21) > button) {
  background: url('@/assets/img/ckeditor/icon-ckeditor-table.svg') no-repeat center left 2px  !important;
  padding-left: 23px;
}
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > .ck-dropdown:nth-child(21) > button:hover) {
  background: var(--ck-color-button-default-hover-background) url('@/assets/img/ckeditor/icon-ckeditor-table.svg') no-repeat center left 2px  !important;
}
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > .ck-dropdown:nth-child(21) > button > svg:nth-child(1)) {
  display: none !important;
}

// video icon css
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > .ck-dropdown:nth-child(22) > button) {
  background: url('@/assets/img/ckeditor/icon-ckeditor-video.svg') no-repeat center left 2px  !important;
  padding-left: 25px;
}
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > .ck-dropdown:nth-child(22) > button:hover) {
  background: var(--ck-color-button-default-hover-background) url('@/assets/img/ckeditor/icon-ckeditor-video.svg') no-repeat center left 2px  !important;
}
:deep(.ck.ck-toolbar_grouping>.ck-toolbar__items > .ck-dropdown:nth-child(22) > button > svg:nth-child(1)) {
  display: none !important;
}

@media all and (max-width: 768px) {
  :deep(.ck-insert-table-dropdown__grid) {
    width: 140px;
  }
  :deep(.ck-insert-table-dropdown-grid-box) {
    width: 10px;
    height: 10px;
    min-width: 10px;
    min-height: 10px;
  }
  :deep(.ck-toolbar__grouped-dropdown>.ck-dropdown__panel>.ck-toolbar>.ck-toolbar__items>button:nth-last-child(4)) {
    background: url('@/assets/img/ckeditor/icon-ckeditor-quote.svg') no-repeat center !important;
  }
  :deep(.ck-toolbar__grouped-dropdown>.ck-dropdown__panel>.ck-toolbar>.ck-toolbar__items>button:nth-last-child(4):hover) {
    background: var(--ck-color-button-default-hover-background) url('@/assets/img/ckeditor/icon-ckeditor-quote.svg') no-repeat center !important;
  }
  :deep(.ck-toolbar__grouped-dropdown>.ck-dropdown__panel>.ck-toolbar>.ck-toolbar__items>button:nth-last-child(4) > svg) {
    display: none !important;
  }

  :deep(.ck-toolbar__grouped-dropdown .ck-dropdown__panel .ck-toolbar .ck-toolbar__items>div:nth-last-child(2) > button) {
    background: url('@/assets/img/ckeditor/icon-ckeditor-table.svg') no-repeat center left 2px  !important;
    padding-left: 23px;
  }
  :deep(.ck-toolbar__grouped-dropdown .ck-dropdown__panel .ck-toolbar .ck-toolbar__items>div:nth-last-child(2) > button:hover) {
    background: var(--ck-color-button-default-hover-background) url('@/assets/img/ckeditor/icon-ckeditor-table.svg') no-repeat center left 2px  !important;
  }
  :deep(.ck-toolbar__grouped-dropdown .ck-dropdown__panel .ck-toolbar .ck-toolbar__items>div:nth-last-child(2) > button > svg:nth-child(1)) {
    display: none !important;
  }

  :deep(.ck-toolbar__grouped-dropdown .ck-dropdown__panel .ck-toolbar .ck-toolbar__items>div:last-child > button) {
    background: url('@/assets/img/ckeditor/icon-ckeditor-video.svg') no-repeat center left 2px  !important;
    padding-left: 25px;
  }
  :deep(.ck-toolbar__grouped-dropdown .ck-dropdown__panel .ck-toolbar .ck-toolbar__items>div:last-child > button:hover) {
    background: var(--ck-color-button-default-hover-background) url('@/assets/img/ckeditor/icon-ckeditor-video.svg') no-repeat center left 2px  !important;
  }
  :deep(.ck-toolbar__grouped-dropdown .ck-dropdown__panel .ck-toolbar .ck-toolbar__items>div:last-child > button > svg:nth-child(1)) {
    display: none !important;
  }
}

// content css
:deep(.ck.ck-editor__editable) {
  h1 {
    font-size: 30px;
    line-height: 39px;
    font-weight: 500;

  }
  h2 {
    font-size: 26px;
    line-height: 37px;
    font-weight: bold;
  }
  h3 {
    font-size: 24px;
    line-height: 32px;
    font-weight: bold;
  }
  h4 {
    font-size: 20px;
    line-height: 26px;
    font-weight: bold;
  }
  h5 {
    font-size: 16px;
    line-height: 26px;
    font-weight: bold;
  }
  h6 {
    font-size: 14px;
    line-height: 19px;
    font-weight: bold;
  }
  & > .ck-placeholder::before {
    font-size: 16px;
    color: #bbbbbb;
  }
  p {
    color: #1e1e1e;
  }
  i {
    font-style: italic;
    font-synthesis:initial;
  }
  ul {
    list-style-type:square;
    li {
      margin-left: 20px;
      &::marker {
        color: #1e1e1e;
      }
      ul {
        list-style-type: disc;
        li {
          ul {
            list-style-type: circle;
            li {
              ul {
                list-style-type:square;
              }
            }
          }
        }
      }
    }
  }
  ol {
    list-style-type:decimal;
    li {
      margin-left: 20px;
      &::marker {
        color: #1e1e1e;
      }
    }
  }
  blockquote {
    border-left: 1px solid #b6b6b6;
    color: #030303;
    padding-left: 20px;
    font-size: 14px;
    p {
      color: #929292;
      font-synthesis:initial;
    }
  }
  a {
    font-weight: bold;
    color: #0087CA;
    text-decoration: underline;
  }
  .table {
    min-width: 20%;
    table {
      border: 1px solid #d9d5d4;
      width: auto;
      tr {
        th {
          background: #fff8ef;
          border: 1px solid #d9d5d4;
          span {
          }
        }
        td {
          border: 1px solid #d9d5d4;
          span {
          }
        }
      }
    }
  }
  .image {
    & figcaption {
      min-height: 20px;
      caption-side: bottom;
      word-break: break-word;
      color: var(--ck-color-image-caption-text);
      background-color: var(--ck-color-image-caption-background);
      padding: 0.6em;
      font-size: .75em;
      outline-offset: -1px;
    }
    &.image-style-align-left {
      float: left;
    }
    &.image-style-align-center {
      margin-left: auto;
      margin-right: auto;
    }
    &.image-style-align-right {
      float: right;
      // margin-left:0;
    }

    .ck-editor__editable.ck-editor__nested-editable {
      min-height: 20px;
    }
  }
}

:deep(.ck .ck-editor__editable:not(.ck-editor__nested-editable).ck-focused) {
  border: none;
  overflow-y: auto;
}
.writing-active {
  & > .default-text {
    display: none;
  }
  &:deep(.ck.ck-editor__top) {
    display: block;
  }
  &:deep(.ck.ck-editor__mai)n{
    display: block;
    padding: 0;
  }
  &:deep(.ck.ck-editor__editable_inline) {
    padding: 0 25px;
  }
  &:deep(.ck.ck-editor__editable_inline>:first-child) {
    margin-top: 0;
  }
}

.board-write-block {
  height: 100%;
  & > .default-text {
    display: none;
  }
  &:deep(.ck.ck-editor__top) {
    display: block;
  }
  &:deep(.ck.ck-editor) {
    display: block;
    height: 100%;
    padding: 0;
    font-size: 16px;
    color: #222;
    line-height: 1.63;
  }
  :deep(.ck.ck-editor__mai)n{
    min-height: 500px;
    margin-bottom: 0;
    display: block;
    font-size: 16px;
    line-height: 1.63;
    color: #444;

    &>.ck-editor__editable {
      outline: none;
      min-height: 0px;
      height: 490px;
      max-height: 490px;
      border: none !important;
      padding: 25px 25px 0;
      box-sizing: border-box;
      & p:first-child {
        margin-top: 0;
      }
      & p:last-child {
        margin-bottom: 0;
      }
    }
    &>.ck-editor__editable:not(.ck-editor__nested-editable).ck-focused {
      min-height: auto;
      height: 490px;
      max-height: 490px;
    }
  }
  &:deep(.ck.ck-editor__editable_inline>:first-child) {
    margin-top: 0;
  }
}

@media all and (max-width: 768px) {
  .ui-editor {
    padding-top: 0;
  }
  :deep(.ck.ck-editor__mai)n{
    max-height: 190px;
    &>.ck-editor__editable:not(.ck-editor__nested-editable).ck-focused {
      min-height: 131px;
      max-height: 170px;
    }
    &>.ck-editor__editable:not(.ck-focused) {
      min-height: 131px;
      max-height: 170px;
    }
  }
  .board-write-block {
    height: 100%;
    :deep(.ck.ck-editor__top) {
    }
    :deep(.ck.ck-editor__mai) {
      height: 100%;
      min-height: 260px;
      &>.ck-editor__editable:not(.ck-editor__nested-editable).ck-focused {
        height: 260px;
        max-height: 260px;
      }
      .ck-editor__editable:not(.ck-focused) {
        height: 260px;
      }
    }
  }
  // heading css
  :deep(.ck.ck-toolbar>.ck-toolbar__items > .ck-heading-dropdown) {
    width: 110px;
    & > .ck-dropdown__panel_se.ck-dropdown__panel-visible {
      margin-top: 10px;
      ul {
        li {
          padding: 0;
          line-height: 0;
          button {
            margin: 0;
            padding: 0 0 0 5px;
          }
        }
      }
    }
    & .ck-dropdown__panel_se.ck-dropdown__panel-visible {
      z-index: 3000;
      top: 17px;
    }
  }
  :deep(.ck.ck-sticky-panel .ck-sticky-panel__content_sticky) {
    z-index: 3000;
    top: 17px;
  }

  :deep(.ck.ck-editor__mai) {
    &>.ck-editor__editable:not(.ck-focused) {
      .table {
        overflow: auto;
        table {
          min-width: 775px;
          width: auto;

        }
      }
    }
    &>.ck-editor__editable:not(.ck-editor__nested-editable).ck-focused {
      .table {
        overflow: auto;
        table {
          min-width: 775px;
          width: auto;
        }
      }
    }
  }
  :deep(.ck.ck-editor__editable) {
    .table {
      overflow: auto;
      table {
        border: 1px solid #d9d5d4;
        min-width: 770px;
        width: auto;
        tr {
          th {
            background: #fff8ef;
            border: 1px solid #d9d5d4;
            height: auto !important;
          }
          td {
            border: 1px solid #d9d5d4;
            height: auto !important;
          }
        }
      }
    }
  }
}
</style>
