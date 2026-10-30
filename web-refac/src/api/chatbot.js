import httpClient from "@/libs/http-client.js";

let aborter = new AbortController()
let baseUrl = 'http://localhost:5000'
const env = import.meta.env

if (env.VITE_APP_API_URL) {
  baseUrl = env.VITE_APP_API_URL
} else {
  baseUrl = window.location.origin + '/llm-platform-api'
}

export async function chatbotAskQuestion(data, onStart, onDataCallback, onEnd) {
  aborter.abort()
  aborter = new AbortController()

  let headers = {
    'Content-Type': 'application/json'
  }


  fetch(`${baseUrl}/chatbot/chat`, {
    credentials: 'include',
    signal: aborter.signal,
    method: 'POST',
    headers,
    body: JSON.stringify(data)
  })
    .then((response) => {
      if (!response.ok) {
        if (response.status === 401) {
          onEnd()
          onDataCallback('세션이 연장되었습니다. 다시 질문해주세요.')
        }
        throw response
      }

      return response
    })
    .then(async (response) => {
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

export const getChatbotKey = () => {
  const url = '/chatbot/get_chatbot_key'

  return httpClient.get(url).then(res => {
    return res.data
  })
}

export const getChatbotConversationHistory = (params) => {
  const url = '/chatbot/get_conversation_history'

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const chatbotKeyCheck = (params) => {
  const url = '/chatbot/check_chatbot_key'

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}
