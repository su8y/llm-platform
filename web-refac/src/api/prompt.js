import httpClient from "@/libs/http-client.js"

export const getVersionList = (params) => {
  const url = '/prompt/get_version'

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getPrompt = (params) => {
  const url = '/prompt/get_prompt'

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const insertPrompt = (params) => {
  const url = '/prompt/insert_prompt'

  return httpClient.post(url, params)
}

export const updateGreeting = (params) => {
  const url = '/prompt/update_greetings'

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getGreeting = () => {
  const url = '/prompt/get_greetings'

  return httpClient.get(url).then(res => {
    return res.data
  })
}
