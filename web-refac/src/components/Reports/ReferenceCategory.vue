<script setup>
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import UiButton from "@/components/Ui/UiButton.vue";
import CategoryDrag from "@/components/Category/CategoryDrag.vue";

const { t } = useI18n()
const emits = defineEmits(['save'])
const props = defineProps({
  list: Object
})

const depthList = ref(props.list)
const depthError = reactive({
  depth1: false,
  depth2: false,
  depth3: false
})
const selectedItem = reactive({
  depth1: {},
  depth2: {}
})

const onSelect = (item, depth, type) => {
  if (type === 'select') {
    if (depth === 1) {
      selectedItem.depth1 = item
      depthList.value.depth2List = item.children
      depthList.value.depth3List = []
      depthList.value.depth3List = []
    } else if (depth === 2) {
      selectedItem.depth2 = item
      depthList.value.depth3List = item.children
    }
  } else {
    if (depth === 2) {
      depthList.value.depth3List = []
    } else if (depth === 1) {
      depthList.value.depth2List = []
    }
  }
}
const onSave = async () => {
  depthError.depth1 = false
  depthError.depth2 = false
  depthError.depth3 = false

  if (!depthError.depth1 && !depthError.depth2 && !depthError.depth3) {
    emits('save', {categories: depthList.value.depth1List})
  } else {
    alert(t('referenceCategory.inputCategoryName'))
    return false
  }
}

const onError = (depth, state) => {
  switch (depth) {
    case 1:
      depthError.depth1 = state
      break
    case 2:
      depthError.depth2 = state
      break
    case 3:
      depthError.depth3 = state
      break
  }
}
</script>

<template>
  <div class="category-wrapper">
    <UiButton :type="'primary'" @click="onSave">
      <i class="font-icon-save" />
      {{ $t('common.save2') }}
    </UiButton>
    <div class="list-name">
      <CategoryDrag :title="$t('referenceCategory.depth.depth1')" :depth="1" :list="props.list.depth1List" @select="onSelect" @error="onError" :error="depthError.depth1" />
      <CategoryDrag :title="$t('referenceCategory.depth.depth2')" :depth="2" :parent="selectedItem.depth1" :list="props.list.depth2List" @select="onSelect" @error="onError" :error="depthError.depth2"></CategoryDrag>
      <CategoryDrag :title="$t('referenceCategory.depth.depth3')" :depth="3" :parent="selectedItem.depth2" :list="props.list.depth3List" @select="onSelect" @error="onError" :error="depthError.depth3"></CategoryDrag>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.category-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  padding: 32px;
}
.list-name {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 20px;
  box-sizing: border-box;
}

</style>
