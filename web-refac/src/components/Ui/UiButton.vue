<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
</script>

<template>
  <button class="be-btn" :class="props.type" :disabled="props.disabled">
    <slot></slot>
  </button>
</template>
