import { SUPPORT_EMAIL } from '@/libs/constants.js'
import { getI18nInstance } from '@/libs/i18n.js'

/** 안내 문구의 연락처. VITE_SUPPORT_EMAIL 이 없으면 '관리자' 로 표시한다. */
export function supportContact () {
  if (SUPPORT_EMAIL) return SUPPORT_EMAIL
  const i18n = getI18nInstance()
  return i18n?.global?.t('common.supportFallback') || 'administrator'
}
