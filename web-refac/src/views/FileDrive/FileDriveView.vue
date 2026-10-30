<script setup>
import { ref, reactive, onBeforeMount, onBeforeUnmount, inject } from 'vue'
import { useStore } from 'vuex'
import { useI18n } from 'vue-i18n'

import { loadFiles, uploadFiles, onRetryAnalytics, getFileStatus, deleteFile, makeDirectory, moveToDirectory, renameItem } from '@/api/drive.js'
import { HTTP_CODES, WARNING_TYPE } from '@/libs/constants.js'

import FileExplorer from '@/components/FileDrive/FileExplorer.vue'
import Loading from '@/components/Modal/Loading.vue'
import Warning from '@/components/Modal/Warning.vue'

const modal = inject('$modal')
const store = useStore()
const { t } = useI18n()

const rootId = ref(null)
const currentDirId = ref(null)
const path = ref([])                       // [{dirId, dirName}] root → current
const directories = ref([])
const files = ref([])
const treeCache = reactive({})             // dirId → children
const expandedSet = reactive(new Set())
const fileStatusMap = ref(new Map())
const creditAvailable = ref(0)
const userData = ref(null)
const searchName = ref('')
const page = reactive({ totalLength: 0, limit: 10, currentPage: 1, selectedOption: store.state.limitPage ? parseInt(store.state.limitPage) : 20 })
let pollTimer = null

onBeforeMount(async () => {
  userData.value = await store.dispatch('storeUserData')
  await load()
})
onBeforeUnmount(() => stopPolling())

const fail = (res, e) => {
  console.error('[FileDriveView]', e || res)
  alert(e?.response?.data?.message || res?.message || String(e))
}

const fetchPage = async (dirId, { page: pageNo = 1, perPage = page.selectedOption, name = '' } = {}) => {
  const res = await loadFiles({ params: { currentDirId: dirId, page: pageNo, perPage, name: name || undefined } })
  if (res.code !== HTTP_CODES.SUCCESS) throw new Error(res.message)
  return res.data
}

const load = async () => {
  try {
    const data = await fetchPage(currentDirId.value, { page: page.currentPage, name: searchName.value })
    if (!rootId.value) rootId.value = data.currentDirId
    currentDirId.value = data.currentDirId
    if (!path.value.length) path.value = [{ dirId: data.currentDirId, dirName: t('drive.root') }]
    directories.value = data.directories || []
    files.value = data.files?.file || []
    treeCache[data.currentDirId] = directories.value
    expandedSet.add(data.currentDirId)
    page.totalLength = data.files?.count || 0
    page.limit = page.selectedOption
    creditAvailable.value = data.parserCreditAvailable ?? 0
    managePolling()
  } catch (e) {
    fail(null, e)
  }
}

// ---- 탐색
const navigate = async (dir) => {
  const idx = path.value.findIndex(p => p.dirId === dir.dirId)
  if (idx >= 0) path.value = path.value.slice(0, idx + 1)
  else {
    // 트리에서 바로 클릭한 경우 경로를 캐시로 복원, 없으면 현재 경로 뒤에 붙인다
    const chain = findChain(rootId.value, dir.dirId, [])
    path.value = chain ? [{ dirId: rootId.value, dirName: t('drive.root') }, ...chain] : [...path.value, dir]
  }
  currentDirId.value = dir.dirId
  page.currentPage = 1
  searchName.value = ''
  await load()
}
const findChain = (fromId, targetId, acc) => {
  for (const child of treeCache[fromId] || []) {
    if (child.dirId === targetId) return [...acc, child]
    const deeper = findChain(child.dirId, targetId, [...acc, child])
    if (deeper) return deeper
  }
  return null
}
const expand = async (dirId) => {
  if (expandedSet.has(dirId)) { expandedSet.delete(dirId); return }
  if (!treeCache[dirId]) {
    try { const data = await fetchPage(dirId, { perPage: 1 }); treeCache[dirId] = data.directories || [] } catch (e) { fail(null, e); return }
  }
  expandedSet.add(dirId)
}
const refreshTree = (dirId) => { delete treeCache[dirId] }

// ---- 업로드
const upload = async ({ formData, rejected, count }) => {
  if (rejected.length) alert(`${t('drive.uploadHint')}\n${rejected.join('\n')}`)
  if (!count) return
  modal.open(Loading)
  try {
    const res = await uploadFiles(formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    if (res.code === HTTP_CODES.SUCCESS) await load()
    else modal.open(Warning, WARNING_TYPE.PARSER_CREDIT_ERROR)
  } catch (e) {
    console.error('[FileDriveView.upload]', e)
    modal.open(Warning, WARNING_TYPE.PARSER_CREDIT_ERROR)
  } finally {
    modal.close()
  }
}

// ---- 폴더/이름/이동/삭제
const makeDir = async (name) => {
  try {
    const res = await makeDirectory({ dirName: name, currentDirId: currentDirId.value })
    if (res.code !== HTTP_CODES.SUCCESS) return fail(res)
    refreshTree(currentDirId.value); await load()
  } catch (e) { fail(null, e) }
}
const rename = async (params) => {
  try {
    const res = await renameItem(params)
    if (res.code !== HTTP_CODES.SUCCESS) return fail(res)
    refreshTree(currentDirId.value); await load()
  } catch (e) { fail(null, e) }
}
const move = async ({ target, payload }) => {
  const items = (payload?.items || []).filter(i => !(i.kind === 'dir' && i.id === target))
  if (!items.length || target === currentDirId.value) return
  modal.open(Loading)
  try {
    for (const item of items) {
      const res = await moveToDirectory(item.kind === 'dir' ? { dirId: item.id, toDirId: target } : { fileId: item.id, toDirId: target })
      if (res.code !== HTTP_CODES.SUCCESS) { fail(res); break }
    }
    refreshTree(currentDirId.value); refreshTree(target); await load()
  } catch (e) {
    fail(null, e)
  } finally {
    modal.close()
  }
}
const remove = async (items) => {
  modal.open(Loading)
  try {
    for (const item of items) {
      const res = await deleteFile(item.kind === 'dir' ? { dirId: item.id } : { fileId: item.id })
      if (res.code !== HTTP_CODES.SUCCESS) { fail(res); break }
    }
    refreshTree(currentDirId.value); await load()
  } catch (e) {
    fail(null, e)
  } finally {
    modal.close()
  }
}
const retry = async (fileId) => {
  modal.open(Loading)
  try {
    const res = await onRetryAnalytics({ fileId })
    if (res.code !== HTTP_CODES.SUCCESS) fail(res)
    await load()
  } catch (e) { fail(null, e) } finally { modal.close() }
}

// ---- 검색/페이지
const search = async (name) => { searchName.value = name; page.currentPage = 1; await load() }
const changePage = async (n) => { page.currentPage = n; await load() }
const changePageOption = async (n) => { page.selectedOption = n; page.currentPage = 1; store.commit('setPagination', { newPage: 1, newLimit: n }); await load() }

// ---- 분석 상태 폴링 (대기/분석 중 파일이 있을 때만 5초 간격)
const managePolling = () => {
  const active = files.value.filter(f => [1, 3].includes(fileStatusMap.value.get(f.fileId)?.status ?? f.status))
  if (!active.length) return stopPolling()
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    const targets = files.value.filter(f => [1, 3].includes(fileStatusMap.value.get(f.fileId)?.status ?? f.status))
    if (!targets.length) return stopPolling()
    for (const f of targets) {
      try {
        const res = await getFileStatus({ params: { fileId: f.fileId, status: fileStatusMap.value.get(f.fileId)?.status ?? f.status } })
        if (res.code === HTTP_CODES.SUCCESS) {
          fileStatusMap.value = new Map(fileStatusMap.value).set(res.data.fileId, res.data)
          if (res.data.status === 4) f.status = 4
        }
      } catch (e) { console.error('[FileDriveView.poll]', e) }
    }
  }, 5000)
}
const stopPolling = () => { if (pollTimer) { clearInterval(pollTimer); pollTimer = null } }
</script>

<template>
  <FileExplorer
      :root-id="rootId" :current-dir-id="currentDirId" :path="path"
      :directories="directories" :files="files" :tree-cache="treeCache" :expanded-set="expandedSet"
      :page="page" :file-status-map="fileStatusMap" :credit-available="creditAvailable"
      :is-upload-disabled="creditAvailable === 0 || userData?.isExpiredPlan === true" :search-name="searchName"
      @navigate="navigate" @expand="expand" @upload="upload" @move="move" @rename="rename" @delete="remove"
      @retry="retry" @makeDir="makeDir" @search="search" @changePage="changePage" @changePageOption="changePageOption" />
</template>
