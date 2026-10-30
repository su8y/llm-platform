import httpClient from "@/libs/http-client.js";

export const inviteMember = (params) => {
  const url = `/admin/invite_member`;

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getMembersList = (params) => {
  const url = `/admin/get_members`;

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getAuthNameList = () => {
  const url = `/admin/get_auth_name`;

  return httpClient.get(url).then(res => {
    return res.data
  })
}

export const changeUserAuth = (params) => {
  const url = `/admin/change_auth`;

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const deleteUser = (params) => {
  const url = `/admin/delete_user`;

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const reInviteMember = (params) => {
  const url = `/admin/reinvite_member`;

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}
