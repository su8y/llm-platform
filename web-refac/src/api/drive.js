import httpClient from "@/libs/http-client.js";

export const loadFiles = (params) => {
  const url = `/drive/get_page`

  return httpClient.get(url, params).then(res => {
    return res.data
  })
}

export const uploadFiles = (params, config) => {
  const url = `/drive/upload_file`

  return httpClient.post(url, params, config).then(res => {
    return res.data
  })
}

export const deleteFile = (params) => {
  const url = `/drive/delete`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getFileData = (params) => {
  const url = `/drive/get_file_info`

  return httpClient.get(url, params).then(res => {
    return res.data
  })
}

export const onSearch = (params) => {
  const url = `/drive/search`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const onRetryAnalytics = (params) => {
  const url = `/drive/retry`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getFileDetailData = (params) => {
  const url = `/drive/file_view`

  return httpClient.get(url, params).then(res => {
    return res.data
  })
}

export const updateFileDetail = (params) => {
  const url = `/drive/update_file_content`

  return httpClient.put(url, params).then(res => {
    return res.data
  })
}


export const getFileStatus = (params) => {
  const url = `/drive/get_status`

  return httpClient.get(url, params).then(res => {
    return res.data
  })
}

// ---- 폴더 트리 / 드래그앤드롭 이동
export const makeDirectory = (params) => {
  const url = `/drive/make_directory`

  return httpClient.post(url, params).then(res => res.data)
}

export const moveToDirectory = (params) => {
  const url = `/drive/move_to_directory`

  return httpClient.put(url, params).then(res => res.data)
}

export const renameItem = (params) => {
  const url = `/drive/rename`

  return httpClient.put(url, params).then(res => res.data)
}

export const downloadFileUrl = (fileId) => {
  return `${import.meta.env.VITE_APP_API_URL || window.location.origin + '/llm-platform-api'}/drive/download?fileId=${fileId}`
}
