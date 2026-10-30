import httpClient, { refreshAuthToken } from "@/libs/http-client.js"
import { getAuthToken } from "@/libs/auth-helper.js";

let aborter = new AbortController()
let baseUrl = 'http://localhost:5000'
const env = import.meta.env

if (env.VITE_APP_API_URL) {
  baseUrl = env.VITE_APP_API_URL
} else {
  baseUrl = window.location.origin + '/llm-platform-api'
}

export async function askQuestion(data, onStart, onDataCallback, onEnd, isAuthRetry = false) {
  aborter.abort()
  aborter = new AbortController()

  const authToken = getAuthToken()

  let headers = {
    Authorization: `Bearer ${authToken?.accessToken}`,
    'Content-Type': 'application/json'
  }


  fetch(`${baseUrl}/playground/chat`, {
    credentials: 'include',
    signal: aborter.signal,
    method: 'POST',
    headers,
    body: JSON.stringify(data)
  })
    .then(async (response) => {
      if (!response.ok) {
        // 401 이면 토큰 재발급 후 1회만 재시도. 재발급 실패는 http-client 가 로그인 화면으로 보낸다.
        if (response.status === 401 && !isAuthRetry) {
          await refreshAuthToken()
          return askQuestion(data, onStart, onDataCallback, onEnd, true)
        }
        if (response.status === 401) {
          onEnd()
          onDataCallback('세션이 만료되었습니다. 다시 로그인해주세요.')
        }
        throw response
      }

      return response
    })
    .then(async (response) => {
      if (!response) {
        return
      }
      onStart()
      const loopRunner = true
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      const messageId = response.headers.get('id')

      while (loopRunner) {
        const { done, value } = await reader.read()

        if (done) {
          onEnd(messageId)
          break
        }

        const decoded = decoder.decode(value, { stream: true })
        onDataCallback(decoded)
      }
    })
    .catch((e) => {
      if (aborter.signal.aborted) {
        console.log('생성 멈춤')
        onEnd(null, true)
      }

      onEnd()
      console.log(e)
    })
}

export function abortRendering() {
  try {
    aborter.abort()
  } catch (e) {
    console.log(e)
  }
}

export function getHistory(params) {
  const url = '/playground/get_conversation_history'

  return httpClient.get(url, params).then(res => {
    return res.data
  })
}

export const getReference = (params) => {
  const url = '/playground/get_retrieval_data'

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const newChat = () => {
  const url = '/playground/new_chat'

  return httpClient.post(url, {}).then(res => {
    return res.data
  })
}

export const updateRating = (params) => {
  const url = '/playground/update_rating'

  return httpClient.post(url, params).then(res => {
    return res.data.data
  })
}

export const updateComment = (params) => {
  const url = '/playground/update_comment'

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getChatTitle = () => {
  const url = '/playground/get_chat_title'

  return httpClient.get(url).then(res => {
    return res.data
  })
}

export const getChatTitleList = (params) => {
  const url = '/playground/get_conversation_history_title'

  return httpClient.get(url, params).then(res => {
    return res.data
  })
}



