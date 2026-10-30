import httpClient from "@/libs/http-client.js";

export const getCurrentPlan = (params) => {
  const url = `/plan/get_current_plan`

  return httpClient.get(url, params).then(res => {
    return res.data
  })
}

export const getPlanList = (params) => {
  const url = `/plan/get_plan_history`;

  return httpClient.post(url, params).then(res => {
    return res.data
  })
}

export const getCurrentCredit = (params) => {
  const url = `/plan/get_current_credit`

  return httpClient.get(url, params).then(res => {
    return res.data
  })
}
