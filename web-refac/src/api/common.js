import httpClient from "@/libs/http-client.js";

export const fileUploadBase64 = (param) => {
  const url = '/reference/image_upload_base64'

  return httpClient.post(url, param).then((res) => {
    return res.data
  })
}

export const getUserIP = () => {
  const url = '/geo/get_geo_info'
  return httpClient.get(url).then(res => {
    return res.data
  })
}
