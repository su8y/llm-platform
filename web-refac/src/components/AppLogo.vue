<script setup>
const appName = import.meta.env.VITE_APP_NAME || ''
</script>

<template>
  <span v-if="appName" class="app-logo">{{ appName }}</span>
</template>

<style scoped lang="scss">
.app-logo {
  display: inline-block;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.02em;
  white-space: nowrap;
}
</style>
