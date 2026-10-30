<script setup>
import { ref, defineEmits } from 'vue'

import { newChat } from '@/api/playground'

const emit = defineEmits(['newSessionSetting'])
const isTooltipVisible = ref(false)

const showTooltip = () => {
  isTooltipVisible.value = true
}

const hideTooltip = () => {
  isTooltipVisible.value = false
}

const handleClickNewChatButton = async () => {
  try {
    await newChat().then(res => {
      emit('newSessionSetting', res.sessionKey)
    })

  } catch (e) {
    console.error(e)
  }
}
</script>

<template>
  <div class="chat-header">
    <div class="chat-header-wrapper flex y-center x-between">
      <div class="chat-profile-wrapper flex y-center gap-8">
        <div class="chat-profile">
          <i class="icon icon--ai-assistant"></i>
          <i class="icon icon--chat-on"></i>
        </div>
        <span class="be-icon icon-blue size-20">
          <i class="icon-playground"></i>
        </span>
        <p class="be-font size-16 text-blue bold">Playground</p>
      </div>
      <div class="flex gap-8 btn-wrap">
        <button
            class="new-chat-button"
            @mouseover="showTooltip"
            @mouseout="hideTooltip"
            @click="handleClickNewChatButton"
        >
          <span class="be-icon hover-size-34 hover">
            <i class="font-icon-refresh"></i>
          </span>
        </button>
        <span class="be-icon hover-size-34 hover" @click="$modal.close()">
          <i class="font-icon-close" />
        </span>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.chat-header-wrapper {
  .chat-profile-wrapper {
    span {
      width: 20px;
      height: 20px;
    }
    .chat-profile {
      position: relative;

      .icon--chat-on {
        position: absolute;
        right: -9%;
        bottom: -1%;
      }
    }
  }

  .btn-wrap {
    position: absolute;
    top: 2%;
    right: 2%;
  }
}

</style>
