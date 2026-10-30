<script setup>
/** 폴더 트리 노드(재귀). 클릭=이동, ▸=펼침(자식 지연 로드), 드롭=이동 대상 */
import { ref, computed } from 'vue'

const props = defineProps({
  node: { type: Object, required: true },          // { dirId, dirName }
  treeCache: { type: Object, required: true },      // { [dirId]: [{dirId, dirName}] }
  currentDirId: { type: Number, default: null },
  depth: { type: Number, default: 0 },
  expandedSet: { type: Object, required: true }     // Set
})
const emits = defineEmits(['navigate', 'expand', 'drop'])

const isDragOver = ref(false)
const children = computed(() => props.treeCache[props.node.dirId] || null)
const isExpanded = computed(() => props.expandedSet.has(props.node.dirId))
const isActive = computed(() => props.currentDirId === props.node.dirId)

const toggle = (e) => {
  e.stopPropagation()
  emits('expand', props.node.dirId)
}
const onDrop = (e) => {
  isDragOver.value = false
  const raw = e.dataTransfer.getData('application/x-drive-item')
  if (!raw) return
  emits('drop', { target: props.node.dirId, payload: JSON.parse(raw) })
}
</script>

<template>
  <li class="tree-node">
    <div
        class="tree-row"
        :class="{ active: isActive, 'drag-over': isDragOver }"
        :style="{ paddingLeft: `${8 + depth * 16}px` }"
        @click="emits('navigate', node)"
        @dragover.prevent="isDragOver = true"
        @dragleave="isDragOver = false"
        @drop.prevent="onDrop">
      <span class="caret" :class="{ open: isExpanded, leaf: children && children.length === 0 }" @click="toggle">
        <i class="font-icon-right-arrow" />
      </span>
      <i class="icon-folder" :class="{ open: isExpanded || isActive }" />
      <span class="name" :title="node.dirName">{{ node.dirName }}</span>
    </div>
    <ul v-if="isExpanded && children && children.length" class="tree-children">
      <FileTree
          v-for="child in children" :key="child.dirId"
          :node="child" :tree-cache="treeCache" :current-dir-id="currentDirId" :depth="depth + 1" :expanded-set="expandedSet"
          @navigate="emits('navigate', $event)" @expand="emits('expand', $event)" @drop="emits('drop', $event)" />
    </ul>
  </li>
</template>

<style lang="scss" scoped>
.tree-node { list-style: none; }
.tree-children { list-style: none; margin: 0; padding: 0; }
.tree-row {
  display: flex; align-items: center; gap: 6px; height: 32px; padding-right: 8px; border-radius: 6px; cursor: pointer; font-size: 13px; color: #444; user-select: none;
  &:hover { background: #f3f4f8; }
  &.active { background: rgba($mainColor, .10); color: $mainColor; font-weight: 600; }
  &.drag-over { outline: 2px dashed $mainColor; outline-offset: -2px; background: rgba($mainColor, .06); }
  .caret { width: 16px; height: 16px; display: inline-flex; align-items: center; justify-content: center; transition: transform .15s; font-size: 10px; color: #999;
    &.open { transform: rotate(90deg); }
    &.leaf { visibility: hidden; }
  }
  .name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}
.icon-folder {
  width: 16px; height: 13px; flex: none; border-radius: 2px 2px 3px 3px; background: #f5c451; position: relative;
  &::before { content: ''; position: absolute; left: 0; top: -3px; width: 7px; height: 4px; border-radius: 2px 2px 0 0; background: #f5c451; }
  &.open { background: #f2b32f; }
}
</style>
