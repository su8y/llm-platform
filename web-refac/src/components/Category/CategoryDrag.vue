<script setup>
import { ref, onMounted, nextTick, watch, inject, computed } from 'vue'
import draggable from 'vuedraggable'

import { deleteCategory } from "@/api/reference.js";
import { HTTP_CODES, WARNING_TYPE } from '@/libs/constants.js'

import Warning from "@/components/Modal/Warning.vue";

const modal = inject('$modal')
const props = defineProps({
  title: String,
  list: {
    type: Array,
    default: () => []
  },
  depth: Number,
  parent: {
    type: Object,
    default: () => {}
  },
  error: Boolean
})

const emits = defineEmits(['select', 'error', 'delete'])

const selectedItem = ref(null)
const listGroup = ref(null)
const listIndex = ref(null)
const newCategory = ref(null)

onMounted(async () => {
  await nextTick();
});

watch(
    () => props.parent,
    async (newValue) => {
      if (!newValue) {
        console.warn('props.parent is null or undefined');
        return;
      }
      selectedItem.value = null
    }
)

watch(
    () => props.list,
    async (newValue) => {
      if (!newValue || newValue.length === 0) {
        console.warn('list is null, undefined, or empty');
        newCategory.value = null
        return
      }
      newCategory.value = null
    },
    { deep: true }
)

const onSelect = (item) => {
  if (selectedItem.value && selectedItem.value.name === item.name) {
    selectedItem.value = null;
    emits('select', null, props.depth, 'unSelect');
  } else {
    selectedItem.value = { ...item, depth: props.depth };
    selectedItem.value.isShow = true;
    emits('select', item, props.depth, 'select');
  }
};

const onEdit = (item, state) => {
  const list = props.list

  if (item.name !== item.nameEdit && !state) {
    const isSameCategory = list.some((category) => {
      return category.name === item.nameEdit
    })

    if (isSameCategory && !state || item.nameEdit && item.nameEdit.trim().length === 0) {
      modal.open(Warning, WARNING_TYPE.EDIT_CATEGORY)
      return
    }
  }

  for (let i = 0, iLen = list.length; i < iLen; i++) {
    const listItem = list[i]
    listItem.isEdit = false
    if (listItem.nameEdit) {
      listItem.name = listItem.nameEdit
    }
  }

  item.isEdit = state
  if (item.isEdit) {
    item.nameEdit = item.name
  } else {
    item.name = item.nameEdit
  }

  emits('error', props.depth, false)
}

const onAdd = () => {
  if (!newCategory.value || newCategory.value.trim().length === 0) {
    modal.open(Warning, WARNING_TYPE.EMPTY_DUPLICATED_CATEGORY)

    return
  } else {
    const isSameCategory = props.list.some((item) => {
      return item.name === newCategory.value.trim()
    })
    if (isSameCategory) {
      modal.open(Warning, WARNING_TYPE.EMPTY_DUPLICATED_CATEGORY)
      return
    }
  }

  let currentMaxSeq = -1
  if (props.list.length > 0) {
    const lastItem = props.list[props.list.length - 1]
    if (lastItem && lastItem.order >= 0) {
      currentMaxSeq = lastItem.order
    }
  }

  const item = {
    name: newCategory.value,
    isEdit: false,
    order: currentMaxSeq + 1,
    depth: props.depth,
    children: []
  }

  props.list.push(item)
  onSelect(item, 'add')
  newCategory.value = null
}

const onRemove = async (element) => {
  if ('children' in element && element.children.length > 0) {
    return modal.open(Warning, WARNING_TYPE.CHILD_CATEGORY_EXISTENCE)
  }

  if (!Object.hasOwn(element, 'id')) {
    props.list.splice(props.list.indexOf(element), 1)
    return
  }

  const params = {
    id: element.id
  }

  try {
    await modal.open(Warning, WARNING_TYPE.CATEGORY_DELETE).then(async () => {
      modal.close()

      const res = await deleteCategory(params)

      if (res.code === HTTP_CODES.SUCCESS) {
        location.reload()
      } else if (res.code === HTTP_CODES.USE_CATEGORY) {
        modal.open(Warning, WARNING_TYPE.CATEGORY_USE_REFERENCE)
      } else {
        alert(res.message)
        console.log('Error: ', res)
      }
    }).catch(() => {
      modal.close()
    })
  } catch (e) {
    console.log(e.response.status)
    console.error('Error: ', e)

  }
}

const canAddCategory = computed(() => {
  if (!selectedItem.value) {
    if (props.depth === 1) {
      return false
    } else if (props.depth === 2 && props.parent.depth === 1) {
      return false
    } else return !(props.depth === 3 && props.parent.depth === 2);
  } else {
    return false
  }
})

const toggleEdit = (item) => {
  item.isEdit = false
  item.nameEdit = item.name
}

</script>

<template>
  <div class="category">
    <h1 class="category-title">{{ title }}</h1>
    <div class="category-input-wrapper">
      <UiInput v-model="newCategory" :type="'text'" :placeholder="$t('referenceCategory.inputCategoryName')" :maxLength="20"
               :disabled="canAddCategory"/>
      <UiButton :type="'primary square'" @click="onAdd" :disabled="props.depth === 3 && !props.parent">
        +
      </UiButton>
    </div>
    <div class="list" :class="{'error': error}">
      <template v-if="list.length !== 0">
        <draggable tag="ul" :list="list" itemKey="id" class="list-group" handle=".handle" ref="listGroup">
          <template #item="{ element, index }">
            <template v-if="element">
              <li class="list-group-item handle"
                  :class="{select: selectedItem && selectedItem.name === element.name && selectedItem.order === element.order, isHover: listIndex === index && !element.isEdit}"
                  @click.prevent="onSelect(element)"
                  @mouseenter="listIndex = index"
                  @mouseleave="listIndex = null"
              >
                <div class="list-left">
                  <span class="icon-container">
                    <i class="font-icon-category-list"></i>
                  </span>
                  <template v-if="!element.isEdit">
                    <span class="text">
                      {{ element.name ? element.name : '-' }}
                    </span>
                  </template>
                  <template v-if="element.isEdit">
                    <input class="category-input" type="text" :placeholder="$t('referenceCategory.inputCategoryName')" v-model="element.nameEdit"   @keyup.enter="onEdit(element, false)"/>
                  </template>
                </div>
                <div class="icon-wrap">
                  <template v-if="listIndex === index && !element.isEdit">
                    <span class="icon-container">
                      <i class="font-icon-write" @click.stop="onEdit(element, true)"></i>
                    </span>
                    <span  class="icon-container">
                      <i class="font-icon-delete" @click="onRemove(element)"></i>
                    </span>
                  </template>
                  <template v-if="element.isEdit" >
                    <span class="icon-container">
                      <i class="icon icon--check" @click.stop="onEdit(element, false)"></i>
                    </span>
                    <span class="icon-container">
                      <i class="font-icon-close" @click.stop="toggleEdit(element)"></i>
                    </span>
                  </template>
                </div>
              </li>
            </template>
          </template>
        </draggable>
      </template>
      <template v-else>
        <div class="list-empty">
          <i class="icon icon--empty" />
          <span>{{ $t('referenceCategory.noData', { depth: title }) }}</span>
        </div>
      </template>
    </div>
  </div>
</template>

<style lang="scss" scoped>

.category {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 11px;
  min-width: 172px;
  width: 100%;

  .category-title {
    padding: 12px;
    color: #262626;
    font-size: 16px;
    font-weight: 700;
  }

  .category-input-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;

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

  .list {
    height: calc(100dvh - 230px);
    background-color: $whiteColor;
    box-shadow: 0px 1px 3px 0px rgba(0, 0, 0, 0.16);

    &.error {
      border-color: #de1b1b;
    }
    .handle {
      cursor: move;
      float: right;
      padding-top: 8px;
      padding-bottom: 8px;
    }
    .list-group {
      height: 100%;
      min-height: 20px;
      display: -ms-flexbox;
      display: -webkit-box;
      display: flex;
      -ms-flex-direction: column;
      -webkit-box-orient: vertical;
      -webkit-box-direction: normal;
      flex-direction: column;
      padding-left: 0;
      margin-bottom: 0;

      .list-group-item {
        position: relative;
        padding: 19px 6px 19px 20px;
        margin-bottom: 0px;
        background-color: #fff;
        border-bottom: 1px solid $line-sm;
        transition: background .3s;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;

        .list-left {
          width: 100%;
          display: flex;
          align-items: center;
          gap: 15px;

          .category-input {
            width: 100%;
          }

          .icon-container {
            width: 10px;
            height: 14px;

            .font-icon-category-list {
              color: $grey-500;
              font-size: 14px;
            }
          }
        }

        &.select {
          border-radius:5px;
          outline: 3px solid #EC0047;
          z-index: 9999;
        }

        .category-input {
          width: 70%;
          border-radius: 5px;
          border: 1px solid $line-md;
          background-color: $whiteColor;
          padding: 12px;

          &:focus {
            border: 1px solid #289eef;
            outline: none;
          }
        }

        .icon-wrap {
          display: flex;
          align-items: center;
          gap: 4px;

          .icon-container {
            width: 28px;
            height: 28px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 6px;
            box-sizing: border-box;
            transition: all .3s;
            cursor: pointer;

            .font-icon-close,
            .font-icon-delete,
            .font-icon-write{
              color: #888;
              font-size: 16px;
            }

            &:hover {
              border-radius: $radius-4;
              background: #f4f4f4;
            }

            &:active {
              background: #E6E6E6;
            }
          }
        }

        .text {
          line-height: 28px;
        }

        &.isHover {
          background: $grey-50;
        }
      }
    }
  }

  .list-empty {
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 14px;
    color: #767676;
    font-size: 13px;
    font-weight: 500;
  }

  &.disabled {

  }
}
</style>
