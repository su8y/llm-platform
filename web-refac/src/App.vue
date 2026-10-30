<script setup>
import {inject, onMounted, onUnmounted, computed, watch, nextTick} from 'vue'
import {RouterView, useRoute, useRouter} from 'vue-router'
import { useStore } from 'vuex'

import ModalContainer from "@/components/Modal/ModalContainer.vue";
import { useHeadI18n } from "@/composables/useHeadI18n.js";

const modal = inject('$modal')
const store = useStore()
const route = useRoute()
const router = useRouter()

useHeadI18n()
const isMobile = computed(() => store.state.isMobile)

watch(() => route.path, (newPath, oldPath) => {
  const newPage = newPath.split('/')
  const oldPage = oldPath.split('/')
  if (newPage[2] !== oldPage[2] || newPage[3] !== oldPage[3]) {
    // 라우트가 변경될 때 스토어 초기화
    store.commit('setPagination', { newPage: 1, newLimit: 10 })
    store.commit('setInboxSearchData', {
      subject: null,
      from: null,
      status: null,
      manager: null,
      startDate: null,
      endDate: null
    })
    store.commit('setMonitoringSearchData', {
      id: null,
      status: null,
      manager: null,
      startDate: null,
      endDate: null
    })
    store.commit('setReferenceSearchData', {
      isOn: null,
      startDate: null,
      endDate: null,
      title: null,
      author: null,
      category: null
    })
    store.commit('setFileSearchData', {
      name: null,
      startDate: null,
      endDate: null
    })
    store.commit('setRagSearchData', {
      to: null,
      subject: null,
      manager: null,
      startDate: null,
      endDate: null,
    })
  }
}, { immediate: false })

watch(() => isMobile.value, (value) => {
  if (value) app.classList.add('mobile')
  else app.classList.remove('mobile')
})

const handleResize = () => {
  nextTick(() => {
    if (route.meta.isIntro) {
      const isMobile = window.innerWidth <= 768
      store.commit('setIsMobile', isMobile)
    } else {
      store.dispatch('checkIsMobile')
    }
  })
}


onMounted( () => {
  handleResize()
  window.addEventListener('resize', handleResize)
  const app = document.getElementById('app')
  if (store.state.isMobile) app.classList.add('mobile')

})

watch(
    () => route.meta.isIntro,
    () => {
      handleResize()
    },
    { immediate: true }
)

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})


</script>


<template>
  <component :is="$route.meta.layout || 'div'">
    <RouterView :key="$route.fullPath" />
  </component>
  <ModalContainer :visible="modal.isOpen()">
    <component :is="modal.getComponent()"></component>
  </ModalContainer>
</template>

<style>
#app:not(.mobile) {
  min-width: 1280px;
  overflow-x: auto;
  scrollbar-gutter: stable;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE/Edge */
}

#app:not(.mobile)::-webkit-scrollbar {
  width: 0px; /* Chrome, Safari, Opera */
  height: 0px;
}

</style>
