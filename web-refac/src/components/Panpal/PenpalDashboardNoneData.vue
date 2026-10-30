<script setup>
const props = defineProps({
  type: {
    type: String,
    default: null
  }
})
</script>

<template>
  <div class="dashboard-none-data-container flex flex-column gap-8">
    <i class="icon icon--dashboard-none-data" />
    <span class="text" :class="props.type" v-html="$t(`penpal.dashboard.workStatus.${props.type}`)"></span>
  </div>
</template>

<style lang="scss" scoped>
.dashboard-none-data-container {
  width: 240px;
  height: 135px;
  padding: 20px;
  border-radius: 7.778px;
  background-color: $whiteColor;
  box-shadow: 0 8px 14px 0 rgba(0, 0, 0, 0.16);
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;

  .text {
    text-align: center;
    font-size: 13px;
    font-weight: 600;
    line-height: 120%; /* 15.6px */

    &.noneReceived {
      color: #444;
    }

    &.nonePending {
      color: #609E2E;
    }

    &.noneInProgress {
      color: #0085FF;
    }
  }
}
</style>
