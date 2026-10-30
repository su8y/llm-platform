import httpClient from "../libs/http-client";

export const register = (params) => {
  const url = `/user/register`;

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const login = (params) => {
  const url = `/user/login`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getUserInfo = () => {
  const url = `/user/get_info`

  return httpClient.get(url).then(res => {
    return res.data
  })
}

export const findPassword = (params) => {
  const url = `/user/find_password`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getInviteInfo = (params) => {
  const url = `/user/get_register_info`

  return httpClient.get(url, params).then(res => {
    return res.data
  })
}

export const validationPassword = (params) => {
  const url = `/user/check_validation_find_password`

  return httpClient.get(url, params).then(res => {
    return res.data
  })
}

export const changePassword = (params) => {
  const url = `/user/change_password`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}
