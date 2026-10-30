<script setup>
const appName = import.meta.env.VITE_APP_NAME || ''

import {computed, ref} from "vue";
import {useI18n} from "vue-i18n";
import {useStore} from "vuex";

const props =  defineProps({
  isConnected: {
    type: Boolean,
    default: true
  }
})

const { t } = useI18n()

const store = useStore()
const isMobile = computed(() => store.state.isMobile)

const fullScreenMode = ref(false)
const emits = defineEmits(['expand','close'])

const handleExpand = () => {
  fullScreenMode.value = !fullScreenMode.value
  emits('expand', fullScreenMode.value)
}
</script>

<template>
  <div class="chat-header">
    <div class="right-content">
      <div class="assistant-profile">
        <i class="icon icon--ai-assistant"></i>
        <div :class="['status', { disabled: !props.isConnected }]"></div>
      </div>
      <div class="assistant-detail">
        <div class="assistant-name">{{ appName || "AI Chat" }}<i class="icon icon--badge-beta"></i></div>
        <div class="introduce">{{ t('chatBot.subHeader') }}</div>
      </div>
    </div>
    <div class="button-container" >
      <button @click="handleExpand" v-if="!isMobile">
        <i class="icon" :class="fullScreenMode ? 'icon--arrow-reduce' : 'icon--arrow-expand'"></i>
      </button>
      <button @click="emits('close')">
        <i class="icon icon--close-size24"></i>
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.chat-header {
  position: relative;
  display: flex;
  align-items: flex-start;
  width: 100%;

  .right-content {
    display: flex;
    align-items: center;
    gap: 16px;
    margin: 4px 0 0 4px;
  }
}

.assistant-profile {
  position: relative;
  width: 42px;
  height: 42px;
  .icon--ai-assistant {
    border-radius: 50em;
    box-shadow: 0px 0px 0px 0.358px rgba(0, 0, 0, 0.06) inset;
  }
  .status {
    position: absolute;
    right: 1px;
    bottom: 2px;
    width: 10px;
    height: 10px;
    border-radius: 100%;
    border: 2px solid #FFF;
    background-color: #58C900;
    box-sizing: border-box;
    box-shadow: 0px 1px 2px 0px #00000040;
    &.disabled {
      background-color: #e92020;
    }
  }
}

.assistant-detail {
  display: flex;
  flex-direction: column;
  gap: 6px;
  .assistant-name {
    display: flex;
    align-items: center;
    gap: 4px;
    position: relative;
    color: #111;
    font-size: 13px;
    font-weight: 600;
  }
  .introduce {
    color: #7D7D7D;
    font-size: 12px;
    font-weight: 500;
    line-height: 1;
  }
}

.button-container {
  display: flex;
  gap: 16px;
  margin-left: auto;
  .icon {
    display: block;
  }
}
</style>
