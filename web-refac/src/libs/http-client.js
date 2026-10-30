import axios from 'axios';
import { getAuthToken, setAuthToken, removeAuthData } from '@/libs/auth-helper.js'
import { HTTP_CODES } from '@/libs/constants'
import { isArray, isPlainObject } from '@/libs/utils'

let baseUrl = 'http://localhost:5000'
const env = import.meta.env

if (env.VITE_APP_API_URL) {
  baseUrl = env.VITE_APP_API_URL
} else {
  baseUrl = window.location.origin + '/llm-platform-api'
}

const REFRESH_TOKEN_URL = '/user/refresh_token'
const SIGN_IN_PATH = '/signin'

const httpClient = axios.create({
  baseURL: baseUrl,
})

function isApiUrl (url) {
  if (url.charAt(0) === '/') {
    return true
  }
  return url.indexOf(baseUrl) === 0
}

function normalizeRequest (data) {
  if (isPlainObject(data)) {
    for (const key of Object.keys(data)) {
      if (typeof data[key] === 'string') {
        data[key] = data[key].trim()
      } else {
        normalizeRequest(data[key])
      }
    }
  } else if (isArray(data)) {
    for (let i = 0; i < data.length; i++) {
      if (typeof data[i] === 'string') {
        data[i] = data[i].trim()
      } else {
        normalizeRequest(data[i])
      }
    }
  }
}

// 토큰 재발급은 동시에 하나만 진행하고, 같은 시점의 401 요청들은 그 결과를 공유한다.
let refreshPromise = null

export function refreshAuthToken () {
  if (refreshPromise) {
    return refreshPromise
  }

  const authToken = getAuthToken()
  if (!authToken?.refreshToken) {
    return Promise.reject(new Error('No refresh token'))
  }

  refreshPromise = httpClient
    .post(REFRESH_TOKEN_URL, { refresh_token: authToken.refreshToken }, { skipAuthRefresh: true })
    .then((res) => {
      // 서버는 refresh 실패를 HTTP 200 + body.code 401 로 내려준다
      const tokenData = res.data?.data
      if (res.data?.code !== HTTP_CODES.SUCCESS || !tokenData?.accessToken) {
        throw new Error(`Refresh token rejected: ${res.data?.code}`)
      }
      setAuthToken(tokenData)
      return tokenData
    })
    .catch((e) => {
      // 재발급 실패 = 세션 종료. 저장 토큰을 지우고 로그인 화면으로 보낸다.
      console.error('[http-client.refreshAuthToken]', e)
      redirectToSignIn()
      throw e
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

function redirectToSignIn () {
  removeAuthData()
  if (window.location.pathname !== SIGN_IN_PATH) {
    window.location.replace(SIGN_IN_PATH)
  }
}

httpClient.interceptors.request.use(async (config) => {
  if (isApiUrl(config.url)) {

    normalizeRequest(config.data)

    if (config.method === 'get') {
      if (!config.params) {
        config.params = {}
      }
      config.params.t = new Date().getTime()
    }

    const authToken = getAuthToken()

    if (authToken && !config.skipAuthRefresh) {
      config.headers = Object.assign(config.headers, {
        Authorization: `Bearer ${authToken.accessToken}`
      })
    }
  }

  return config
}, (error) => {
  return Promise.reject(error)
})

// 401 이면 refresh token 으로 재발급 후 원 요청을 1회 재시도한다. 재발급 실패 시에만 로그아웃.
httpClient.interceptors.response.use((response) => {
  return response
}, async (error) => {
  const config = error.config
  const status = error.response?.status

  const canRetry = status === 401
    && config
    && !config.skipAuthRefresh
    && !config.isAuthRetry
    && isApiUrl(config.url)
    && !!getAuthToken()?.refreshToken

  if (!canRetry) {
    return Promise.reject(error)
  }

  config.isAuthRetry = true

  try {
    const tokenData = await refreshAuthToken()
    config.headers = Object.assign(config.headers || {}, {
      Authorization: `Bearer ${tokenData.accessToken}`
    })
    return httpClient(config)
  } catch (e) {
    return Promise.reject(error)
  }
})

export default httpClient
