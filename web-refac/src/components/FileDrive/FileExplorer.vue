<script setup>
/** 파일 저장소 탐색기: 폴더 트리 + 현재 폴더 내용(폴더/파일) + 드래그앤드롭 업로드/이동 */
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

import { dateFormatter } from '@/libs/utils.js'
import { DRIVE_STATUS, PAGE_OPTIONS } from '@/libs/constants.js'
import { downloadFileUrl } from '@/api/drive.js'
import FileTree from '@/components/FileDrive/FileTree.vue'

const props = defineProps({
  rootId: { type: Number, default: null },
  currentDirId: { type: Number, default: null },
  path: { type: Array, default: () => [] },             // [{dirId, dirName}] root → current
  directories: { type: Array, default: () => [] },
  files: { type: Array, default: () => [] },
  treeCache: { type: Object, default: () => ({}) },
  expandedSet: { type: Object, required: true },
  page: { type: Object, required: true },
  fileStatusMap: { type: Map, default: () => new Map() },
  creditAvailable: { type: Number, default: 0 },
  isUploadDisabled: { type: Boolean, default: false },
  searchName: { type: String, default: '' }
})
const emits = defineEmits(['navigate', 'expand', 'upload', 'move', 'rename', 'delete', 'retry', 'makeDir', 'search', 'changePage', 'changePageOption'])

const router = useRouter()
const { t } = useI18n()

const viewMode = ref(localStorage.getItem('drive.viewMode') || 'grid')
const selected = reactive(new Set())
const isDropActive = ref(false)
const dragDepth = ref(0)
const dragOverDir = ref(null)
const editing = reactive({ type: null, id: null, name: '' })   // type: 'newDir' | 'renameDir' | 'renameFile'
const keyword = ref(props.searchName)
const fileInput = ref(null)
const pageOptionOpen = ref(false)

const setView = (mode) => { viewMode.value = mode; try { localStorage.setItem('drive.viewMode', mode) } catch (e) { /* 저장소 차단 환경 */ } }
const fileSizeMb = (v) => `${(v / (1024 * 1024)).toFixed(2)}MB`
const statusOf = (file) => props.fileStatusMap.get(file.fileId)?.status ?? file.status
const statusKey = (file) => DRIVE_STATUS[statusOf(file)]
const percentOf = (file) => {
  const s = props.fileStatusMap.get(file.fileId)
  if (!s || !s.totalPage) return null
  const p = Math.floor((s.completePage / s.totalPage) * 100)
  return p >= 100 ? 99 : p
}
const isBusy = (file) => [0, 1, 3, 5].includes(statusOf(file))
const selectedCount = computed(() => selected.size)
const rootNode = computed(() => props.rootId ? { dirId: props.rootId, dirName: t('drive.root') } : null)

// ---- 선택
const keyOf = (kind, id) => `${kind}:${id}`
const isSelected = (kind, id) => selected.has(keyOf(kind, id))
const toggleSelect = (kind, id, e) => {
  const k = keyOf(kind, id)
  if (!(e?.metaKey || e?.ctrlKey || e?.target?.type === 'checkbox')) selected.clear()
  selected.has(k) ? selected.delete(k) : selected.add(k)
}
const clearSelection = () => selected.clear()
const selectedItems = () => [...selected].map(k => { const [kind, id] = k.split(':'); return { kind, id: Number(id) } })

// ---- 폴더 이동/열기
const openDir = (dir) => { clearSelection(); emits('navigate', dir) }
const openFile = (file) => { if (!isBusy(file)) router.push({ name: 'FileDriveDetail', params: { fileId: file.fileId } }) }

// ---- 드래그: 항목 이동
const onItemDragStart = (kind, item, e) => {
  const k = keyOf(kind, kind === 'dir' ? item.dirId : item.fileId)
  if (!selected.has(k)) { selected.clear(); selected.add(k) }
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('application/x-drive-item', JSON.stringify({ items: selectedItems() }))
}
const onDirDragOver = (dir, e) => {
  if (e.dataTransfer.types.includes('application/x-drive-item')) { e.dataTransfer.dropEffect = 'move'; dragOverDir.value = dir.dirId }
}
const onDirDrop = (dir, e) => {
  dragOverDir.value = null
  const raw = e.dataTransfer.getData('application/x-drive-item')
  if (!raw) return
  emits('move', { target: dir.dirId, payload: JSON.parse(raw) })
  clearSelection()
}
const onTreeDrop = ({ target, payload }) => { emits('move', { target, payload }); clearSelection() }
const onBreadcrumbDrop = (dir, e) => onDirDrop(dir, e)

// ---- 드래그: 데스크톱 파일 업로드
const hasFiles = (e) => [...(e.dataTransfer?.types || [])].includes('Files')
const onZoneDragEnter = (e) => { if (!hasFiles(e)) return; dragDepth.value++; isDropActive.value = true }
const onZoneDragLeave = (e) => { if (!hasFiles(e)) return; dragDepth.value--; if (dragDepth.value <= 0) { dragDepth.value = 0; isDropActive.value = false } }
const onZoneDrop = (e) => {
  dragDepth.value = 0; isDropActive.value = false
  if (!hasFiles(e)) return
  submitFiles(e.dataTransfer.files)
}
const submitFiles = (fileList) => {
  if (props.isUploadDisabled) return
  const maxSize = 50 * 1024 * 1024
  const formData = new FormData()
  const rejected = []
  for (const file of fileList) {
    const isPdf = file.type === 'application/pdf' || /\.pdf$/i.test(file.name)
    if (!isPdf || file.size > maxSize) { rejected.push(file.name); continue }
    formData.append('files', file)
  }
  formData.append('currentDirId', props.currentDirId)
  emits('upload', { formData, rejected, count: fileList.length - rejected.length })
}
const onFileInput = (e) => { submitFiles(e.target.files); e.target.value = '' }

// ---- 새 폴더 / 이름 변경 (인라인 편집)
const startNewDir = () => { editing.type = 'newDir'; editing.id = null; editing.name = '' }
const startRename = (kind, item) => { editing.type = kind === 'dir' ? 'renameDir' : 'renameFile'; editing.id = kind === 'dir' ? item.dirId : item.fileId; editing.name = kind === 'dir' ? item.dirName : item.fileName }
const cancelEdit = () => { editing.type = null; editing.id = null; editing.name = '' }
const commitEdit = () => {
  const name = editing.name.trim()
  if (!name) return cancelEdit()
  if (editing.type === 'newDir') emits('makeDir', name)
  else if (editing.type === 'renameDir') emits('rename', { dirId: editing.id, newName: name })
  else if (editing.type === 'renameFile') emits('rename', { fileId: editing.id, newName: name })
  cancelEdit()
}

// ---- 삭제
const removeOne = (kind, item) => {
  const name = kind === 'dir' ? item.dirName : item.fileName
  if (!window.confirm(t('drive.confirmDeleteOne', { name }))) return
  emits('delete', [{ kind, id: kind === 'dir' ? item.dirId : item.fileId }])
}
const removeSelected = () => {
  if (!selected.size || !window.confirm(t('drive.confirmDelete'))) return
  emits('delete', selectedItems()); clearSelection()
}

const onSearch = () => emits('search', keyword.value.trim())
</script>

<template>
  <div class="explorer">
    <!-- 왼쪽: 폴더 트리 -->
    <aside class="tree-pane">
      <div class="pane-title">{{ $t('drive.folders') }}</div>
      <ul v-if="rootNode" class="tree">
        <FileTree
            :node="rootNode" :tree-cache="treeCache" :current-dir-id="currentDirId" :expanded-set="expandedSet"
            @navigate="openDir" @expand="emits('expand', $event)" @drop="onTreeDrop" />
      </ul>
      <div class="credit" v-if="creditAvailable >= 0">{{ $t('drive.creditLeft', { n: creditAvailable }) }}</div>
    </aside>

    <!-- 오른쪽: 내용 -->
    <section class="content-pane">
      <header class="toolbar">
        <nav class="breadcrumb">
          <template v-for="(dir, i) in path" :key="dir.dirId">
            <span v-if="i > 0" class="sep">/</span>
            <button
                class="crumb" :class="{ current: i === path.length - 1, 'drag-over': dragOverDir === dir.dirId }"
                @click="i < path.length - 1 && openDir(dir)"
                @dragover.prevent="onDirDragOver(dir, $event)" @dragleave="dragOverDir = null" @drop.prevent="onBreadcrumbDrop(dir, $event)">
              {{ i === 0 ? $t('drive.root') : dir.dirName }}
            </button>
          </template>
        </nav>
        <div class="tools">
          <div class="search">
            <input v-model="keyword" :placeholder="$t('drive.searchPlaceholder')" @keyup.enter="onSearch" />
            <button class="icon-btn" @click="onSearch"><i class="font-icon-search" /></button>
          </div>
          <div class="view-toggle">
            <button :class="{ on: viewMode === 'grid' }" :title="$t('drive.viewGrid')" @click="setView('grid')">▦</button>
            <button :class="{ on: viewMode === 'list' }" :title="$t('drive.viewList')" @click="setView('list')">☰</button>
          </div>
          <UiButton :type="'outline sm'" @click="startNewDir">{{ $t('drive.newFolder') }}</UiButton>
          <UiButton :type="'primary sm'" :disabled="isUploadDisabled" @click="fileInput.click()">{{ $t('drive.upload') }}</UiButton>
          <input ref="fileInput" type="file" hidden multiple accept=".pdf,application/pdf" :disabled="isUploadDisabled" @change="onFileInput" />
        </div>
      </header>

      <div v-if="selectedCount" class="selection-bar">
        <span>{{ $t('drive.selected', { n: selectedCount }) }}</span>
        <UiButton :type="'outline sm'" @click="removeSelected">{{ $t('drive.delete') }}</UiButton>
        <button class="link" @click="clearSelection">{{ $t('common.cancel') }}</button>
      </div>

      <div
          class="dropzone" :class="{ active: isDropActive, [viewMode]: true }"
          @dragenter.prevent="onZoneDragEnter" @dragover.prevent @dragleave="onZoneDragLeave" @drop.prevent="onZoneDrop"
          @click.self="clearSelection">
        <div v-if="isDropActive" class="drop-overlay"><span>{{ $t('drive.dropHint') }}</span></div>

        <!-- 새 폴더 인라인 입력 -->
        <div v-if="editing.type === 'newDir'" class="item dir editing">
          <i class="icon-folder big" />
          <input v-model="editing.name" :placeholder="$t('drive.folderName')" autofocus @keyup.enter="commitEdit" @keyup.esc="cancelEdit" @blur="commitEdit" />
        </div>

        <!-- 폴더 -->
        <div
            v-for="dir in directories" :key="`d${dir.dirId}`"
            class="item dir" :class="{ selected: isSelected('dir', dir.dirId), 'drag-over': dragOverDir === dir.dirId }"
            draggable="true"
            @click.stop="toggleSelect('dir', dir.dirId, $event)" @dblclick.stop="openDir(dir)"
            @dragstart="onItemDragStart('dir', dir, $event)"
            @dragover.prevent="onDirDragOver(dir, $event)" @dragleave="dragOverDir = null" @drop.prevent.stop="onDirDrop(dir, $event)">
          <input type="checkbox" class="check" :checked="isSelected('dir', dir.dirId)" @click.stop="toggleSelect('dir', dir.dirId, $event)" />
          <i class="icon-folder big" />
          <template v-if="editing.type === 'renameDir' && editing.id === dir.dirId">
            <input v-model="editing.name" autofocus @click.stop @keyup.enter="commitEdit" @keyup.esc="cancelEdit" @blur="commitEdit" />
          </template>
          <template v-else>
            <span class="name" :title="dir.dirName" @click.stop="openDir(dir)">{{ dir.dirName }}</span>
          </template>
          <span class="meta" v-if="viewMode === 'list'">{{ $t('drive.folders') }}</span>
          <div class="actions" @click.stop>
            <button :title="$t('drive.rename')" @click="startRename('dir', dir)"><i class="font-icon-writing" /></button>
            <button :title="$t('drive.delete')" @click="removeOne('dir', dir)">✕</button>
          </div>
        </div>

        <!-- 파일 -->
        <div
            v-for="file in files" :key="`f${file.fileId}`"
            class="item file" :class="{ selected: isSelected('file', file.fileId), busy: isBusy(file) }"
            draggable="true"
            @click.stop="toggleSelect('file', file.fileId, $event)" @dblclick.stop="openFile(file)"
            @dragstart="onItemDragStart('file', file, $event)">
          <input type="checkbox" class="check" :checked="isSelected('file', file.fileId)" @click.stop="toggleSelect('file', file.fileId, $event)" />
          <i class="icon-file"><span>PDF</span></i>
          <template v-if="editing.type === 'renameFile' && editing.id === file.fileId">
            <input v-model="editing.name" autofocus @click.stop @keyup.enter="commitEdit" @keyup.esc="cancelEdit" @blur="commitEdit" />
          </template>
          <template v-else>
            <span class="name" :title="file.fileName" @click.stop="openFile(file)">{{ file.fileName }}</span>
          </template>
          <span class="meta size">{{ fileSizeMb(file.fileSize) }}</span>
          <span class="meta date" v-if="viewMode === 'list'">{{ dateFormatter(file.regDate, 'time') }}</span>
          <span class="status" :class="statusKey(file)">
            {{ $t(`drive.status.${statusKey(file)}`) }}<template v-if="percentOf(file) !== null && statusOf(file) === 3"> ({{ percentOf(file) }}%)</template>
            <button v-if="statusOf(file) === 5" class="retry" :title="$t('drive.retry')" @click.stop="emits('retry', file.fileId)"><i class="font-icon-refresh" /></button>
          </span>
          <div class="actions" @click.stop>
            <a :href="downloadFileUrl(file.fileId)" target="_blank" rel="noopener" :title="$t('drive.download')">⤓</a>
            <button :title="$t('drive.rename')" @click="startRename('file', file)"><i class="font-icon-writing" /></button>
            <button :title="$t('drive.delete')" @click="removeOne('file', file)">✕</button>
          </div>
        </div>

        <div v-if="!directories.length && !files.length && editing.type !== 'newDir'" class="empty">
          <p>{{ $t('drive.emptyFolder') }}</p>
          <p class="hint">{{ $t('drive.dropHint') }}</p>
        </div>
      </div>

      <footer class="pager" v-if="page.totalLength > 0">
        <div class="page-option" @click.stop="pageOptionOpen = !pageOptionOpen">
          <span>{{ $t('common.pageCount', { count: page.selectedOption }) }}</span>
          <ul v-if="pageOptionOpen" class="list">
            <li v-for="n in PAGE_OPTIONS" :key="n" @click.stop="emits('changePageOption', n); pageOptionOpen = false">{{ $t('common.pageCount', { count: n }) }}</li>
          </ul>
        </div>
        <UiPagination :total="page.totalLength" :limit="page.limit" :currentPage="page.currentPage" @changePage="emits('changePage', $event)" />
      </footer>
    </section>
  </div>
</template>

<style lang="scss" scoped>
$folder: #f5c451;
.explorer { display: grid; grid-template-columns: 240px 1fr; gap: 16px; padding: 20px 28px; min-height: calc(100vh - 120px); }
.tree-pane { border: 1px solid #e6e7ec; border-radius: 10px; background: #fff; padding: 12px 8px; display: flex; flex-direction: column; min-width: 0;
  .pane-title { font-size: 12px; font-weight: 700; color: #888; padding: 0 8px 8px; letter-spacing: .02em; }
  .tree { list-style: none; margin: 0; padding: 0; flex: 1; overflow: auto; }
  .credit { font-size: 12px; color: #888; padding: 10px 8px 0; border-top: 1px solid #f0f0f0; }
}
.content-pane { display: flex; flex-direction: column; gap: 10px; min-width: 0; }
.toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.breadcrumb { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; min-width: 0;
  .crumb { background: none; border: 1px dashed transparent; border-radius: 6px; padding: 4px 8px; font-size: 14px; color: #666; cursor: pointer;
    &:hover { background: #f3f4f8; } &.current { color: #222; font-weight: 700; cursor: default; } &.drag-over { border-color: $mainColor; background: rgba($mainColor, .08); } }
  .sep { color: #bbb; }
}
.tools { display: flex; align-items: center; gap: 8px;
  .search { display: flex; align-items: center; border: 1px solid #d9dbe3; border-radius: 6px; overflow: hidden; background: #fff;
    input { border: 0; padding: 7px 10px; font-size: 13px; width: 200px; outline: none; }
    .icon-btn { border: 0; background: #f6f7fa; padding: 0 10px; height: 32px; cursor: pointer; } }
  .view-toggle { display: flex; border: 1px solid #d9dbe3; border-radius: 6px; overflow: hidden;
    button { border: 0; background: #fff; width: 32px; height: 32px; cursor: pointer; color: #999; &.on { background: rgba($mainColor, .12); color: $mainColor; } } }
}
.selection-bar { display: flex; align-items: center; gap: 12px; padding: 8px 12px; background: rgba($mainColor, .08); border-radius: 8px; font-size: 13px; color: $mainColor;
  .link { background: none; border: 0; color: #777; cursor: pointer; text-decoration: underline; } }
.dropzone { position: relative; flex: 1; border: 2px dashed #e3e5ec; border-radius: 12px; background: #fafbfd; padding: 16px; min-height: 360px; display: grid; align-content: start; gap: 10px;
  &.grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
  &.list { grid-template-columns: 1fr; gap: 4px; }
  &.active { border-color: $mainColor; background: rgba($mainColor, .05); }
  .drop-overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,.75); border-radius: 12px; z-index: 5; pointer-events: none;
    span { font-size: 15px; font-weight: 600; color: $mainColor; } }
}
.item { position: relative; display: flex; align-items: center; gap: 8px; padding: 10px; border: 1px solid #e9eaef; border-radius: 10px; background: #fff; cursor: pointer; user-select: none; min-width: 0;
  &:hover { border-color: #cfd3e0; box-shadow: 0 2px 8px rgba(0,0,0,.05); .actions { opacity: 1; } }
  &.selected { border-color: $mainColor; background: rgba($mainColor, .06); }
  &.drag-over { outline: 2px dashed $mainColor; outline-offset: -2px; }
  &.busy .name { color: #999; }
  .check { position: absolute; top: 8px; left: 8px; margin: 0; opacity: 0; } &:hover .check, &.selected .check { opacity: 1; }
  .name { flex: 1; min-width: 0; font-size: 13px; color: #222; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  input { flex: 1; min-width: 0; border: 1px solid $mainColor; border-radius: 4px; padding: 4px 6px; font-size: 13px; }
  .meta { font-size: 12px; color: #999; white-space: nowrap; }
  .status { font-size: 11px; font-weight: 600; white-space: nowrap; display: inline-flex; align-items: center; gap: 4px;
    &.failed, &.pending { color: #777; } &.analyzing { color: #57AB00; } &.finished { color: #B240FF; } &.unparsed { color: $mainColor; } &.success { color: #57AB00; }
    .retry { border: 0; background: none; cursor: pointer; color: inherit; .font-icon-refresh { transform: scaleY(-1) rotate(270deg); } } }
  .actions { display: flex; gap: 2px; opacity: 0; transition: opacity .15s;
    button, a { border: 0; background: #f3f4f8; border-radius: 4px; width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #666; text-decoration: none; font-size: 12px; &:hover { background: #e4e6ee; color: #222; } } }
}
.grid .item { flex-direction: column; align-items: stretch; text-align: center; padding: 18px 10px 12px; gap: 6px;
  .name { white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; line-height: 1.3; }
  .icon-folder.big, .icon-file { margin: 0 auto; }
  .actions { position: absolute; top: 6px; right: 6px; } }
.list .item { padding: 6px 10px; .check { position: static; opacity: 1; } .icon-folder.big { width: 20px; height: 16px; &::before { width: 9px; height: 5px; } } .icon-file { width: 18px; height: 22px; span { font-size: 6px; } } }
.icon-folder { width: 16px; height: 13px; flex: none; border-radius: 2px 2px 3px 3px; background: $folder; position: relative;
  &::before { content: ''; position: absolute; left: 0; top: -3px; width: 7px; height: 4px; border-radius: 2px 2px 0 0; background: $folder; }
  &.big { width: 52px; height: 40px; border-radius: 4px 4px 6px 6px; &::before { width: 22px; height: 9px; top: -7px; border-radius: 4px 4px 0 0; } } }
.icon-file { width: 40px; height: 50px; flex: none; border: 2px solid #d64b4b; border-radius: 4px; position: relative; display: flex; align-items: flex-end; justify-content: center; background: #fff;
  span { font-size: 9px; font-weight: 800; color: #d64b4b; margin-bottom: 4px; } }
.empty { grid-column: 1 / -1; text-align: center; color: #999; padding: 60px 0; font-size: 14px; .hint { font-size: 12px; margin-top: 6px; color: #bbb; } }
.pager { display: flex; align-items: center; justify-content: center; gap: 16px; padding: 6px 0;
  .page-option { position: relative; font-size: 13px; color: #666; cursor: pointer; padding: 6px 10px; border: 1px solid #e3e5ec; border-radius: 6px; background: #fff;
    .list { position: absolute; bottom: 110%; left: 0; list-style: none; margin: 0; padding: 4px 0; background: #fff; border: 1px solid #e3e5ec; border-radius: 6px; min-width: 100%; box-shadow: 0 4px 14px rgba(0,0,0,.08); z-index: 4;
      li { padding: 6px 10px; white-space: nowrap; &:hover { background: #f3f4f8; } } } } }
@media (max-width: 900px) { .explorer { grid-template-columns: 1fr; } .tree-pane { max-height: 220px; } }
</style>
