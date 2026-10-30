import {createRouter, createWebHistory} from 'vue-router'

import {
  getI18nInstance,
  getLocaleCookie,
  getLocaleMessages,
  setLocaleCookie
} from "@/libs/i18n.js";
import {getAuthToken} from "@/libs/auth-helper.js";

import LoginView from "@/views/LoginView.vue"
import PlaygroundView from "@/views/Playground/PlaygroundView.vue";
import PromptView from "@/views/Playground/PromptView.vue";
import EmailPromptView from "@/views/Email/EmailPromptView.vue";
import DashboardView from "@/views/History/DashboardView.vue";
import MonitoringListView from "@/views/History/MonitoringListView.vue";
import MonitoringDetailView from "@/views/History/MonitoringDetailView.vue";
import ReferenceListView from "@/views/Reference/ReferenceListView.vue";
import ReferenceDetailView from "@/views/Reference/ReferenceDetailView.vue";
import CategoryView from "@/views/Reference/CategoryView.vue";
import WritingView from "@/views/WritingView.vue";
import MembersView from "@/views/Admin/MembersView.vue";
import MailReceiveView from '@/views/Admin/MailReceiveView.vue'
import PlanView from "@/views/Admin/PlanView.vue";
import FileDriveView from "@/views/FileDrive/FileDriveView.vue";
import FileDriveDetailView from "@/views/FileDrive/FileDriveDetailView.vue";
import PenpalDashboardView from '@/views/Penpal/PenpalDashboardView.vue'
import PenpalListView from "@/views/Penpal/PenpalListView.vue";
import PenpalRagView from "@/views/Penpal/PenpalRagView.vue";
import PenpalRagDetailView from "@/views/Penpal/PenpalRagDetailView.vue";
import PenpalDetailView from "@/views/Penpal/PenpalDetailView.vue";

import DefaultLayout from "@/Layouts/DefaultLayout.vue"
import Register from "@/components/Modal/Register.vue";
import {getModalInstance} from "@/plugins/modal.js";

import {useStore} from "vuex";

const routes = [
  {
    path: '/',
    redirect: '/signin'
  },
  {
    path: '/signin',
    name: 'LoginView',
    component: LoginView,
    meta: {
      requiresAuth: false,
      title: 'seo.signin.title',
      desc: 'seo.signin.desc'
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { requiresAuth: false }
  },
  {
    path: '/tool/chat/playground',
    name: 'Playground',
    component: PlaygroundView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.playground'
    }
  },
  {
    path: '/tool/chat/playground/mcp',
    name: 'MCP',
    component: PlaygroundView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.playground'
    }
  },
  {
    path: '/tool/chat/prompt',
    name: 'Prompt',
    component: PromptView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.prompt'
    }
  },
  {
    path: '/tool/chat/dashboard',
    name: 'Dashboard',
    component: DashboardView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.chat'
    }
  },
  {
    path: '/tool/chat/history',
    name: 'History',
    component: MonitoringListView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.history'
    }
  },
  {
    path: '/tool/chat/history/:id',
    name: 'MonitoringPost',
    component: MonitoringDetailView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.history'
    },
  },
  {
    path: '/tool/reference',
    name: 'Board',
    component: ReferenceListView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.reference'
    }
  },
  {
    path: '/tool/reference/setting',
    name: 'Setting',
    component: CategoryView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.setting'
    }
  },
  {
    path: '/tool/reference/post/:id',
    name: 'ReferencePost',
    component: ReferenceDetailView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.setting'
    },
  },
  {
    path: '/tool/reference/drive',
    name: 'FileDrive',
    component: FileDriveView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.drive'
    }
  },
  {
    path: '/tool/reference/drive/detail/:fileId',
    name: 'FileDriveDetail',
    component: FileDriveDetailView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.drive'
    }
  },
  {
    path: '/tool/reference/rag',
    name: 'PenpalRag',
    component: PenpalRagView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.rag'
    }
  },
  {
    path: '/tool/reference/rag/detail/:id',
    name: 'PenpalRagDetail',
    component: PenpalRagDetailView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true
    }
  },
  {
    path: '/tool/writing',
    name: 'Writing',
    component: WritingView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.reference'
    }
  },
  {
    path: '/tool/admin/members',
    name: 'Members',
    component: MembersView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.members'
    }
  },
  {
    path: '/tool/admin/mail-receive',
    name: 'MailReceive',
    component: MailReceiveView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.mailReceive'
    }
  },
  {
    path: '/tool/admin/plan',
    name: 'Plan',
    component: PlanView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.plan'
    }
  },
  {
    path: '/tool/aimail/dashboard',
    name: 'PenpalDashboard',
    component: PenpalDashboardView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.aimail'
    }
  },
  {
    path: '/tool/aimail/mailPrompt',
    name: 'MailPrompt',
    component: EmailPromptView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.prompt'
    }
  },
  {
    path: '/tool/aimail/inbox/list',
    name: 'PenpalList',
    component: PenpalListView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.aimailList'
    }
  },
  {
    path: '/tool/aimail/inbox/:id',
    name: 'PenpalDetail',
    component: PenpalDetailView,
    meta: {
      layout: DefaultLayout,
      requiresAuth: true,
      title:'seo.aimailList'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/tool/chat/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to) {
    return to.name === 'LoginView' ? { top: 0, left: 0 } : false
  }
})
import store from '@/store'
// login 하지 않은 상태로 내부 페이지 진입 시 로그인 페이지로 redirect
router.beforeEach(async (to, from, next) => {
  try {
    const authToken = getAuthToken()
    const i18n = getI18nInstance()
    const isAuthenticated = !!authToken?.accessToken
    let user = store.state.userData || null

    const modal = getModalInstance()
    const POPUP_QUERY_KEYS = ['certification', 'invitation', 'changePassword', 'register', 'isModal']
    const isModalOpen = Object.keys(to.query).some(key =>
      POPUP_QUERY_KEYS.includes(key)
    )

    if (!isModalOpen && modal?.close) {
      modal.close()
    }

    let langParam = to.params.lang
    const { locale, setLocaleMessage } = i18n.global

    if (langParam) {
      if (locale.value !== langParam) {
        const messages = getLocaleMessages(langParam)
        setLocaleCookie(langParam)
        setLocaleMessage(langParam, messages)
        locale.value = langParam
        document.documentElement.setAttribute('lang', locale.value)
      }
    }

    const color = to.meta.bodyColor ?? ''
    document.body.style.backgroundColor = color

    if (!to.meta.requiresAuth){
      return next()
    }

    if (!isAuthenticated && to.meta.requiresAuth) {
      if (from.name) alert(i18n.global.t('modal.sessionExpired'))
      return next({ path: '/signin', replace: true })
    }
    next()
  } catch (e) {
    console.error(`Error: ${e}`)
    next('/')
  }
})

export default router
