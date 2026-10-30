import { format } from 'date-fns'
import Cookies from 'js-cookie'
import { ALERT_COOKIE } from "@/libs/constants.js";

export function isArray (value) {
  return Array.isArray(value)
}

export function isPlainObject (value) {
  return Object.prototype.toString.call(value) === '[object Object]'
}

export function isInteger (value) {
  return typeof value === 'number' && isFinite(value) && Math.floor(value) === value
}

export function upperFirst (value) {
  value = String(value)

  if (!value.length) {
    return value
  }
  return value.charAt(0).toUpperCase() + value.slice(1)
}

export function getPercentage (value, total, digits) {
  if (isNaN(value) || isNaN(total) || total === 0) {
    return 0
  }

  let result = value / total * 100

  if (digits !== undefined) {
    result = Number(result.toFixed(digits))
  }
  return result
}

export function thousand (value) {
  value = Number(value)
  return value.toLocaleString('en-US')
}

function getBrowserInfo () {
  const uaContains = (str) => window.navigator.userAgent.indexOf(str) !== -1
  let name = null
  let platform = null

  if (uaContains('Windows')) {
    platform = 'window'

    if (uaContains('MSIE') || uaContains('Trident/')) {
      name = 'ie'
    }
  }

  if (uaContains('Firefox')) {
    name = 'firefox'
  }

  if (uaContains('Chrome')) {
    name = 'chrome'
  }

  if (uaContains('Safari') && !uaContains('Chrome')) {
    name = 'safari'
  }

  if (uaContains('Edge')) {
    name = 'edge'
  }

  return {
    name,
    platform
  }
}

export function dateFormatter (date, type = null) {
  if (!date || isNaN(new Date(date).getTime())) {
    return '-';
  }

  if (type === 'time') {
    return format(date, 'yyyy-MM-dd HH:mm:ss')
  }

  return format(date, 'yyyy-MM-dd')
}

export const browserInfo = getBrowserInfo()

export function setPlanAlertCookie (value) {
  Cookies.set(ALERT_COOKIE.name, value, {
    expires: ALERT_COOKIE.expires,
    path: ALERT_COOKIE.path,
  })
}

export function getPlanAlertCookie () {
  return Cookies.get(ALERT_COOKIE.name) && JSON.parse(Cookies.get(ALERT_COOKIE.name, true))
}

export function removePlanAlertCookie () {
  return Cookies.remove(ALERT_COOKIE.name)
}

export const bytesToMB = (bytes) => {
  return (bytes / 1024 / 1024).toFixed(2)
}
