import Cookies from 'js-cookie'
import { STORAGE_ITEM, AUTH_COOKIE } from '@/libs/constants'

// 토큰은 localStorage(origin 단위, 포트 포함)에 보관한다.
// 쿠키는 포트를 구분하지 않아 같은 호스트의 다른 로컬 앱과 섞이므로 쓰지 않는다.

function readStorage () {
  try {
    const raw = localStorage.getItem(STORAGE_ITEM.authToken)
    return raw ? JSON.parse(raw) : null
  } catch (e) {
    console.error('[auth-helper.readStorage]', e)
    return null
  }
}

function writeStorage (tokenData) {
  try {
    localStorage.setItem(STORAGE_ITEM.authToken, JSON.stringify(tokenData))
  } catch (e) {
    console.error('[auth-helper.writeStorage]', e)
  }
}

function removeStorage () {
  try {
    localStorage.removeItem(STORAGE_ITEM.authToken)
  } catch (e) {
    console.error('[auth-helper.removeStorage]', e)
  }
}

// 이전 버전이 남긴 쿠키 토큰을 1회 이관하고 쿠키는 지운다.
function migrateLegacyCookie () {
  const raw = Cookies.get(AUTH_COOKIE.name)
  if (!raw) {
    return null
  }

  Cookies.remove(AUTH_COOKIE.name, { path: AUTH_COOKIE.path })

  try {
    const tokenData = JSON.parse(raw)
    if (tokenData?.accessToken) {
      writeStorage(tokenData)
      return tokenData
    }
  } catch (e) {
    console.error('[auth-helper.migrateLegacyCookie]', e)
  }
  return null
}

export function setAuthToken (data = {}) {
  const tokenData = {
    accessToken: data.accessToken,
    refreshToken: data.refreshToken,
  }

  writeStorage(tokenData)
}

export function getAuthToken () {
  const tokenData = readStorage()
  if (tokenData?.accessToken) {
    return tokenData
  }
  return migrateLegacyCookie()
}

export function setAuthData (data) {
  setAuthToken(data)
}

export function removeAuthData () {
  removeStorage()
  Cookies.remove(AUTH_COOKIE.name, { path: AUTH_COOKIE.path })
}

export function setChatbotCookie (data) {
  const sessionKey = {
    chatbotKey: data.chatbotKey
  }

  Cookies.set('Chatbot-key', JSON.stringify(sessionKey), 0)
}

export function getChatbotCookie () {
  return Cookies.get('Chatbot-key') && JSON.parse(Cookies.get('Chatbot-key', true))
}
