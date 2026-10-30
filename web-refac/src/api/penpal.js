import httpClient from "@/libs/http-client.js"

export const getInboxList = (params) => {
  const url = `/email/inbox_list`;

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}
export const getInboxData = (params) => {
  const url = `/email/get_inbox`;

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getVersionList = () => {
  const url = '/email/get_prompt_version'

  return httpClient.get(url).then(res => {
    return res.data
  })
}

export const getPrompt = (params) => {
  const url = '/email/get_prompt'

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const insertPrompt = (params) => {
  const url = '/email/insert_prompt'

  return httpClient.post(url, params)
}

export const fileDownloadForInbox = (params) => {
  const url = `/email/indox_file_download/${params.s3Key}`

  return httpClient.get(url, {
    responseType: 'blob'
  })
}

export const createEmailAnswer = (params) => {
  const url = `/email/create_answer`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const sendAiEmail = (params, config) => {
  const url = `/email/send_email`

  return httpClient.post(url, params, config).then(res => {
    return res.data
  })
}

export const getEmailRag = (params) => {
  const url = `/emailrag/emailrag_list`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}


export const getEmailRagDetail = (params) => {
  const url = `/emailrag/get_emailrag_detail`

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const fileUploadBase64 = (param) => {
  const url = '/email/upload_base64_image'

  return httpClient.post(url, param).then((res) => {
    return res.data
  })
}

export const getManagers = () => {
  const url = `/email/get_manager_list`

  return httpClient.get(url).then((res) => {
    return res.data
  })
}

export const setManager = (params) => {
  const url = `/email/set_manager`

  return httpClient.post(url, params).then((res) => {
    return res.data
  })
}

export const setMailStatus = (params) => {
  const url = `/email/change_status`

  return httpClient.post(url, params).then((res) => {
    return res.data
  })
}

export const getSendInfo = (params) => {
  const url = `/email/get_send_info`

  return httpClient.post(url, params).then((res) => {
    return res.data
  })
}

export const getInitAnswer = (params) => {
  const url = `/email/init_answer`

  return httpClient.post(url, params).then((res) => {
    return res.data
  })
}

export const saveTemporaryMail = (params) => {
  const url = `/email/save_send_info`

  return httpClient.post(url, params).then((res) => {
    return res.data
  })
}

export const saveAttachment = (params) => {
  const url = `/email/save_send_info_upload_attach`

  return httpClient.post(url, params).then((res) => {
    return res.data
  })
}

export const editCompany = (params) => {
  const url = `/email/update_company`

  return httpClient.post(url, params).then((res) => {
    return res.data
  })
}


export const checkThread = (params) => {
  const url = `/email/check_has_thread`

  return httpClient.post(url, params).then((res) => {
    return res.data
  })
}

export const getHistory = (params) => {
  const url = `/email/get_inbox_history`

  return httpClient.post(url, params).then((res) => {
    return res.data
  })
}

export const getDashboardManager = (params) => {
  const url = `/email/get_dashboard_manager_count`

  return httpClient.post(url, params).then((res) => {
    return res.data
  })
}

export const getDashboardChart = (params) => {
  const url = `/email/get_dashboard_chart`

  return httpClient.post(url, params).then((res) => {
    return res.data
  })
}


export const getDashboardLine = (params) => {
  const url = `/email/get_dashboard_line`

  return httpClient.post(url, params).then((res) => {
    return res.data
  })
}

// ---- 메일 수신 설정 (master 전용)
export const getMailSettings = () => {
  const url = '/email/setting/list'

  return httpClient.get(url).then(res => res.data)
}

export const testMailSetting = (params) => {
  const url = '/email/setting/test'

  return httpClient.post(url, params).then(res => res.data)
}

export const upsertMailSetting = (params) => {
  const url = '/email/setting/upsert'

  return httpClient.post(url, params).then(res => res.data)
}

export const deleteMailSetting = (params) => {
  const url = '/email/setting/delete'

  return httpClient.post(url, params).then(res => res.data)
}

export const runMailReceiveNow = () => {
  const url = '/email/setting/run_now'

  return httpClient.post(url, {}).then(res => res.data)
}

// ---- SMTP 발신 설정 (master 전용)
export const getSmtpSetting = () => {
  const url = '/email/setting/smtp/get'

  return httpClient.get(url).then(res => res.data)
}

export const testSmtpSetting = (params) => {
  const url = '/email/setting/smtp/test'

  return httpClient.post(url, params).then(res => res.data)
}

export const upsertSmtpSetting = (params) => {
  const url = '/email/setting/smtp/upsert'

  return httpClient.post(url, params).then(res => res.data)
}

export const deleteSmtpSetting = () => {
  const url = '/email/setting/smtp/delete'

  return httpClient.post(url, {}).then(res => res.data)
}
