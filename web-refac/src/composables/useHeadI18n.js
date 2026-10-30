
import { useI18n } from 'vue-i18n'
import {useHead} from "@vueuse/head";
import {useRoute} from "vue-router";
import {computed} from "vue";

export function useHeadI18n () {
    const { t } = useI18n()
    const route = useRoute()

  const pageTitle = computed(() => {
    return route?.meta?.title ? t(route.meta.title) : ''
  })

  const pageDesc = computed(() => {
    return route?.meta?.desc ? t(route.meta.desc) : ''
  })

    const fullTitle = computed(() => {
      const title = pageTitle.value || ''
      const appName = import.meta.env.VITE_APP_NAME || ''
      return appName && title ? `${appName} | ${title}` : (appName || title)
    })

    const baseMeta = computed(() => {
        const meta = [
            { name: 'title', content: fullTitle.value },
            { name: 'description', content: pageDesc.value },
            { property: 'og:title', content: fullTitle.value },
            { property: 'og:description', content: pageDesc.value }
        ]

        return meta
    })
    useHead({
        title: fullTitle,
        meta: baseMeta
    })
}
