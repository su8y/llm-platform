import { useI18n } from 'vue-i18n'
import {useRouter} from "vue-router";
import {getAuthToken} from "@/libs/auth-helper.js";
import {useStore} from "vuex";
import {computed} from "vue";

export function useUserRouter() {
    const { locale } = useI18n()
    const router = useRouter()
    const store = useStore()
    const isMobile = computed(() => store.state.isMobile)

    return function () {
        const isLogin = !!getAuthToken()
        if (isLogin) {
          return router.push({
            path: '/signin',
          })
        } else {
          if(isMobile.value) {
            return router.push({
              path: '/register',
            })
          } else {
            return router.push({
                path: '/signin',
                query: {
                    register: 'True',
                    lang: locale.value
                }
            })
          }
        }
    }
}
