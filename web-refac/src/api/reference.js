import httpClient from "@/libs/http-client.js";

export const createPost = (params) => {
  const url = `/reference/insert_post`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getReferenceList = (params = {}) => {
  const url = `/reference/get_post`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getReferenceDetail = (params) => {
  const url = `/reference/get_post_detail`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const updateReferenceData = (params) => {
  const url = `/reference/update_post`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const deleteReferenceData = (params) => {
  const url = `/reference/delete_post`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getTokenSize = (params) => {
  const url = `/reference/get_tokensize`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getCategories = () => {
  const url = `/reference/get_all_categories`

  return httpClient.get(url).then(res => {
    return res.data
  })
}

export const saveCategories = (params) => {
  const url = `/reference/update_category`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const deleteCategory = (params) => {
  const url = `/reference/delete_category`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const temporaryPost = (params) => {
  const url = `/reference/insert_post_temporary`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getTemporaryPost = () => {
  const url = `/reference/get_post_temporary_detail`

  return httpClient.get(url).then(res => {
    return res.data
  })
}

export const deleteFileData = (params) => {
  const url = `/reference/delete_file`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}
