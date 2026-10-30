import { createI18n } from 'vue-i18n'
import Cookies from 'js-cookie'
import i18nMessages from '../data/i18n-message.json'
import { LOCALE_COOKIE } from "@/libs/constants.js";
import {getUserIP} from "@/api/common.js";

let i18n

export function getI18nInstance() {
  return i18n
}

function traverseItem (data, container, locale, fallbackLocale) {
  for (const key of Object.keys(data)) {
    const value = data[key]

    if (typeof value !== 'object') {
      continue
    }

    if (typeof value[locale] === 'string') {
      container[key] = value[locale]
      continue
    } else if (value[locale] === undefined && typeof value[fallbackLocale] === 'string') {
      container[key] = value[fallbackLocale]
      continue
    }

    if (!container[key]) {
      container[key] = {}
    }
    traverseItem(value, container[key], locale, fallbackLocale)
  }
}

export function getLocaleMessages (locale, fallbackLocale) {
  const messages = {}
  traverseItem(i18nMessages.messages, messages, locale, fallbackLocale)
  return messages
}

export function initI18n (locale, fallbackLocale = 'en') {
  const messages = {
    [locale]: getLocaleMessages(locale, fallbackLocale)
  }

  i18n = createI18n({
    legacy: false,
    globalInjection: true,
    locale,
    messages,
    warnHtmlInMessage: 'off',
    escapeParameter: true,
  })
  return i18n
}

export async function changeLocale (i18n, locale) {
  if (i18n.locale.value === locale) {
    return
  }
  setLocaleCookie(locale)
}

export function getI18n () {
  if (!i18n) {
    // i18n이 초기화되지 않은 경우 기본 인스턴스 생성
    const defaultLocale = 'ko'
    return initI18n(defaultLocale)
  }
  return i18n
}
export function setLocaleCookie (value = 'en') {
  Cookies.set(LOCALE_COOKIE.name, value, {
    expires: LOCALE_COOKIE.expires,
    path: LOCALE_COOKIE.path,
    domain: LOCALE_COOKIE.domain
  })
}

export function getLocaleCookie () {
  return Cookies.get(LOCALE_COOKIE.name, {
    path: LOCALE_COOKIE.path,
    domain: LOCALE_COOKIE.domain
  })
}

export async function initLocale () {
  let locale = getLocaleCookie()
  if (!locale) {
    try {
      const res = await getUserIP()
      const country = res.data.geo_info.country_code

      switch (country) {
        case 'KR':
          locale = 'ko'
          break
        case 'JP':
          locale = 'ja'
          break
        default:
          locale = 'en'
      }
      setLocaleCookie(locale)
    } catch (e) {
      console.error(e)
      locale = 'en'
    }
  }
  document.documentElement.setAttribute('lang', locale)

  return locale
}

