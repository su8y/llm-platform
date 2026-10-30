<script setup>
import { defineProps, ref, inject, computed } from 'vue'
import { useStore } from 'vuex'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  }
})

const modal = inject('$modal')
const modalState = inject('modalState');
const modalComponent = inject('modalComponent');
const modalContent = inject('modalContent');

const store = useStore()

const isDropdown = ref(false)

const isMobile = computed(() => store.state.isMobile)

const closeDropdown = (e) => {
  const className = e.target.classList
  if (!className.contains('list')) {
    isDropdown.value = !isDropdown.value
  }
}

const closeModal = () => {
  modalState.value = false;
  modalComponent.value = null;
  modalContent.value = null;
};

</script>

<template>
  <div class="modal-wrapper" v-if="props.visible" @click.stop.self="modal.close()">
    <div class="modal-container" :class="{isMobile}" @click="closeDropdown">
      <component :is="modal.getComponent()" v-bind="modalContent" v-bind:is-dropdown="isDropdown"  @close="closeModal" />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.modal-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 1;
  visibility: visible;
  transition: opacity 0.3s ease;
  z-index: 9999999999;

  .modal-container {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background-color: $grey-0;
    padding: 20px;
    border-radius: 1em;
    box-shadow: $shadow-popup-lg;
    transition: transform 0.3s ease, opacity 0.3s ease;

    &.isMobile {
      width: calc(100% - 30px);
    }
  }
}
</style>

