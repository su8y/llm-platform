<script setup>
import { ref, computed, onMounted, onBeforeUnmount, onBeforeMount } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useStore } from 'vuex'
import { useI18n } from "vue-i18n";

import SideMenu from "@/components/SideMenu.vue";
import Header from "@/components/Header.vue";

const route = useRoute();
const router = useRouter()
const store = useStore()
const i18n = useI18n()

const content = ref(null)
const isScroll = ref(false)
const userData = ref(null)

const routerName = computed(() => {
  const name = new Map()
      .set('Dashboard', 'Dashboard')
      .set('List', 'List')
      .set('History', 'History')
      .set('Board', 'Board')
      .set('ReferencePost', 'Board')
      .set('Writing', 'Board')
      .set('Playground', 'Playground')
      .set('MCP', 'MCP')
      .set('Prompt', 'Prompt')
      .set('MailPrompt', 'MailPrompt')
      .set('Members', 'Members')
      .set('Setting', 'Setting')
      .set('Plan', 'Plan')
      .set('FileDrive', 'File Drive')
      .set('FileDriveDetail', 'File Drive')
      .set('PenpalDashboard', 'Penpal Dashboard')
      .set('PenpalList', 'Inbox List')
      .set('PenpalDetail', 'Inbox List')
      .set('PenpalRag', 'Email RAG')
      .set('PenpalRagDetail', 'Email RAG')

  return name.get(route.name)
});
const isMobile = computed(() => store.state.isMobile)

const contentScroll = () => {
  if (content.value.scrollTop !== 0) {
    isScroll.value = true
  } else {
    isScroll.value = false
  }
}

onMounted(async () => {
  content.value.addEventListener('scroll', contentScroll)
})

onBeforeMount(async () => {
  try {
    // 사용자 데이터 불러오기
    userData.value = await store.dispatch('storeUserData');
  } catch (error) {
    console.error('사용자 데이터를 불러오는 중 오류가 발생했습니다:', error);
    router.push('/');
  }
});

onBeforeUnmount(() => {
  content.value.removeEventListener('scroll', contentScroll)
})
</script>

<template>
  <div class="report-wrapper">
    <template v-if="!isMobile">
      <SideMenu :user-data="userData" />
    </template>
    <div class="report-right">
      <template v-if="!isMobile">
        <Header :router-name="routerName" :is-scroll="isScroll" :user-data="userData" :i18n="i18n" />
      </template>
      <div class="report-content" ref="content">
        <slot />
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.report-wrapper {
  width: 100%;
  min-height: 100vh;
  background-color: $backgroundColor;

  .report-right {
    width: calc(100% - 212px);
    box-sizing: border-box;
    margin-left: 212px;
    min-height: 100%;
    overflow-x: hidden;
  }
}

.mobile {
  .report-wrapper {
    background-color: #ECECEC;
    min-height: 100dvh;
    .report-right {
      width: 100%;
      min-width: auto;
      margin-left: 0;
    }
  }
}
// @media all and (max-width: 768px) {
// }
</style>
