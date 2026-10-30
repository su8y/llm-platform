import "vue-toastification/dist/index.css";
import './styles/app.scss'

import { createApp } from 'vue'
import VCalendar from 'v-calendar';
import { CkeditorPlugin } from '@ckeditor/ckeditor5-vue'
import { createHead } from "@vueuse/head";

import 'v-calendar/style.css';
import Toast from "vue-toastification";
import mitt from 'mitt'
import App from './App.vue'
import router from './router'
import modalPlugin from './plugins/modal'
import { initI18n, initLocale } from '@/libs/i18n'

import Tooltip from "@/directives/tooltip/index.js";
import { clickOutside } from './directives/click-outside';
import store from '@/store'

import UiButton from "@/components/Ui/UiButton.vue";
import UiInput from "@/components/Ui/UiInput.vue";
import UiPagination from "@/components/Ui/UiPagination.vue";

async function appFunc () {
    const app = createApp(App)
    const head = createHead()
    const emitter = mitt()
    const locale = await initLocale()
    const i18n = initI18n(locale)
    app
        .component('UiButton', UiButton)
        .component('UiInput', UiInput)
        .component('UiPagination', UiPagination)

    app.use(router)
    app.use(modalPlugin)
    app.use(VCalendar, {})
    app.use(Tooltip)
    app.use(store)
    app.use(head)
    app.use(i18n)
    app.use(Toast, {
        position: 'bottom-center',
        timeout: 3000,
        closeOnClick: true,
        pauseOnHover: true,
        maxToasts: 3,
        transition: 'Vue-Toastification__fade',
        closeButton: false,
        hideProgressBar: true,
        icon: false
    })


// 글로벌 디렉티브 등록
    app.directive('click-outside', clickOutside);

    app.config.globalProperties.emitter = emitter
    app.mount('#app')
}

appFunc()
