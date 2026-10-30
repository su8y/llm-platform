import httpClient from "@/libs/http-client.js";

export const getMonitoringList = (params) => {
  const url = `/monitoring/get_chat_history`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const updateMonitoringData = (params) => {
  const url = `/monitoring/update_chat_history`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getMonitoringDetail = (params) => {
  const url = `/monitoring/get_chat_history_detail_head`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getMonitoringDetailChat = (params) => {
  const url = `/monitoring/get_chat_history_detail_tail`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getRating = (params) => {
  const url = '/monitoring/get_chat_rating'

  return httpClient.post(url, params).then(res => {
    return res.data.data
  })
}

export const getResponseCount = (params) => {
  const url = '/monitoring/get_chat_count'

  return httpClient.post(url, params).then(res => {
    return res.data.data
  })
}

export const getAskRanking = (params) => {
  const url = '/monitoring/get_top'

  return httpClient.post(url, params).then(res => {
    return res.data.data
  })
}

