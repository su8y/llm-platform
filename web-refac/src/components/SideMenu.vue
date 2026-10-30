<script setup>
import { computed } from 'vue'
import { useRoute } from "vue-router"
import { useI18n } from 'vue-i18n'
import AppLogo from "@/components/AppLogo.vue";

import { USE_MCP_ID_LIST } from '@/libs/constants.js'

const { t } = useI18n()
const route = useRoute()
const supportEmail = import.meta.env.VITE_SUPPORT_EMAIL || ''
const appName = import.meta.env.VITE_APP_NAME || ''
const props = defineProps({
  userData: {
    type: Object,
    default: () => {}
  }
})

const getAuth = (key) => computed(() => userAuth.value && userAuth.value[key]);

const userAuth = computed(() => props.userData?.userAuth);
const changeRobot = computed(() => {
  const path = route.path.split('/')[2]
  let iconName = ''
  switch (path) {
    case 'chat':
      iconName = 'playground-becle'
      break
    case 'aimail':
      iconName = 'history-becle'
      break
    case 'reference':
      iconName = 'reference-becle'
      break
    case 'admin':
      iconName = 'admin-becle'
      break
  }

  return iconName
})

const useAccountManage = getAuth('authAccountManage');
const useReferenceCategoryManage = getAuth('authReferenceCategoryManage');
const usePromptManage = getAuth('authPromptManage');
const useReferenceManage = computed(() =>
    userAuth.value?.authReferenceView && userAuth.value?.authReferenceWrite
);
const useAiEmail = computed(() => {
  return userAuth.value?.authEmailView
})
const usePlayground = getAuth('authPlaygroundUse');

const isActive = (name) => {
  if (name === 'Reference' && route.name === 'ReferencePost') return true
  return route.name === name
}

const isDepth1Active = (pathName) => {
  const path = route.path.split('/')[2]

  return path === pathName
}
</script>

<template>
  <div class="knit-side">
    <div class="side-container">
      <div class="side-wrapper">
        <RouterLink v-if="appName" :to="'/tool'" class="knit-logo">
          <AppLogo />
        </RouterLink>
        <div class="side-items">
          <div class="side-item playground" :class="{ historyActive: isDepth1Active('chat') }">
            <span class="depth1">
              <i class="icon--chat" :class="{'icon--chat-active': isDepth1Active('chat')}" />
              <span>{{ $t('common.sideMenu.chat') }}</span>
            </span>
            <div class="depth2">
              <RouterLink :to="{ name: 'Dashboard' }" :class="{ isActive: isActive('Dashboard') }">
                <i class="icon--dashboard" />
                <span>{{ $t('common.sideMenu.dashboard') }}</span>
              </RouterLink>
              <template v-if="usePlayground">
                <RouterLink :to="{ name: 'Playground' }" :class="{ isActive: isActive('Playground') }">
                  <i class="icon--playground" />
                  <span>{{ $t('common.sideMenu.playground') }}</span>
                </RouterLink>
                <template v-if="USE_MCP_ID_LIST.includes(props.userData.userId)">
                  <RouterLink :to="{ name: 'MCP' }" :class="{ isActive: isActive('MCP') }">
                    <i class="icon--playground" />
                    <span>{{ $t('common.sideMenu.mcp') }}</span>
                  </RouterLink>
                </template>
              </template>
              <template v-if="usePromptManage">
                <RouterLink :to="{ name: 'Prompt' }" :class="{ isActive: isActive('Prompt') }">
                  <i class="icon--prompt" />
                  <span>{{ $t('common.sideMenu.prompt') }}</span>
                </RouterLink>
              </template>
              <RouterLink :to="{ name: 'History' }" :class="{ isActive: isActive('History') || isActive('MonitoringPost') }">
                <i class="icon--history" />
                <span>{{ $t('common.sideMenu.history') }}</span>
              </RouterLink>
            </div>
          </div>
          <div class="line horizontal"></div>
          <template v-if="useAiEmail">
            <div class="line horizontal"></div>
            <div class="side-item reference" :class="{ historyActive: isDepth1Active('aimail') }">
              <span class="depth1 penpal">
                <i class="icon icon--penpal" :class="{'icon--penpal-active': isDepth1Active('aimail')}" />
                <span>{{ $t('common.sideMenu.penpal') }}</span>
              </span>
              <div class="depth2">
                <RouterLink :to="{ name: 'PenpalDashboard' }" :class="{ isActive: isActive('PenpalDashboard') }">
                  <i class="icon--dashboard" />
                  <span>{{ $t('common.sideMenu.dashboard') }}</span>
                </RouterLink>
                <RouterLink :to="{ name: 'PenpalList' }" :class="{ isActive: isActive('PenpalList') || isActive('PenpalDetail') }">
                  <i class="icon--list" />
                  <span>{{ $t('common.sideMenu.inboxList') }}</span>
                </RouterLink>
                <template v-if="usePromptManage">
                  <RouterLink :to="{ name: 'MailPrompt' }" :class="{ isActive: isActive('MailPrompt') }">
                    <i class="icon--prompt" />
                    <span>{{ $t('common.sideMenu.mailprompt') }}</span>
                  </RouterLink>
                </template>
              </div>
            </div>
          </template>
          <template v-if="useReferenceManage && useReferenceCategoryManage">
            <div class="line horizontal"></div>
            <div class="side-item reference" :class="{ historyActive: isDepth1Active('reference') }">
            <span class="depth1">
              <i class="icon--references" :class="{'icon--references-active': isDepth1Active('reference')}" />
              <span>{{ $t('common.sideMenu.references') }}</span>
            </span>
              <div class="depth2">
                <RouterLink :to="{ name: 'Board' }" :class="{ isActive: isActive('Board') || isActive('Reference') }">
                  <i class="icon--board" />
                  <span>{{ $t('common.sideMenu.board') }}</span>
                </RouterLink>
                <template v-if="usePlayground">
                  <RouterLink :to="{ name: 'FileDrive' }" :class="{ isActive: isActive('FileDrive') || isActive('FileDriveDetail') }">
                    <i class="icon--file-drive" />
                    <span>{{ $t('common.sideMenu.fileDrive') }}</span>
                  </RouterLink>
                </template>
                <template v-if="useAiEmail">
                  <RouterLink :to="{ name: 'PenpalRag' }" :class="{ isActive: isActive('PenpalRag') || isActive('PenpalRagDetail') }">
                    <i class="icon--rag" />
                    <span>{{ $t('common.sideMenu.emailRag') }}</span>
                  </RouterLink>
                </template>
                <RouterLink :to="{ name: 'Setting' }" :class="{ isActive: isActive('Setting') }">
                  <i class="icon--setting" />
                  <span>{{ $t('common.sideMenu.setting') }}</span>
                </RouterLink>
              </div>
            </div>
          </template>
          <template v-if="useAccountManage">
            <div class="line horizontal"></div>
            <div class="side-item reference" :class="{ historyActive: isDepth1Active('admin') }">
              <span class="depth1">
                <i class="icon--admin" :class="{'icon--admin-active': isDepth1Active('admin')}" />
                <span>{{ $t('common.sideMenu.admin') }}</span>
              </span>
              <div class="depth2">
                <RouterLink :to="{ name: 'Members' }" :class="{ isActive: isActive('Members') }">
                  <i class="icon--members" />
                  <span>{{ $t('common.sideMenu.members') }}</span>
                </RouterLink>
                <RouterLink v-if="useAiEmail" :to="{ name: 'MailReceive' }" :class="{ isActive: isActive('MailReceive') }">
                  <i class="icon--members" />
                  <span>{{ $t('common.sideMenu.mailReceive') }}</span>
                </RouterLink>
                <RouterLink :to="{ name: 'Plan' }" :class="{ isActive: isActive('Plan') }">
                  <i class="icon--plan" />
                  <span>{{ $t('common.sideMenu.plan') }}</span>
                </RouterLink>
              </div>
            </div>
          </template>
        </div>
      </div>
      <div class="side-footer">
<!--        <i class="icon" :class="`icon&#45;&#45;${changeRobot}`"/>-->
        <div class="footer-text" v-if="supportEmail">
          <span>{{ t('common.contact') }}: {{ supportEmail }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>

</style>
