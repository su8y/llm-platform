import { ref, markRaw } from 'vue'
import ModalContainer from '@/components/Modal/ModalContainer.vue'

const modalState = ref(false)
const modalComponent = ref(null)
const modalContent = ref(null)
let modalInstance = null

export function getModalInstance () {
  return modalInstance
}
export default {
  install: (app, options) => {
    const modal = {
      open (component, content = null) {
        return new Promise((resolve, reject) => {
          modalComponent.value = markRaw(component);
          modalContent.value = { content, resolve, reject }
          modalState.value = true
        })
      },
      close () {
        modalComponent.value = null
        modalState.value = false
        modalContent.value = null
      },
      isOpen () {
        if (modalState.value) {
          document.body.style.overflow = 'hidden'
        } else {
          document.body.style.overflow = 'auto'
        }
        return modalState.value
      },
      getComponent () {
        return modalComponent.value
      }
    };

    modalInstance = modal
    app.component('modalContainer', ModalContainer)
    app.provide('$modal', modal)
    app.provide('modalState', modalState);
    app.provide('modalComponent', modalComponent);
    app.provide('modalContent', modalContent);
  }
}
