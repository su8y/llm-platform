<script setup>
import { ref, onBeforeMount, inject } from "vue"
import { useI18n } from "vue-i18n"

import { getMailSettings, testMailSetting, upsertMailSetting, deleteMailSetting, runMailReceiveNow, getSmtpSetting, testSmtpSetting, upsertSmtpSetting, deleteSmtpSetting } from '@/api/penpal.js'
import { HTTP_CODES } from "@/libs/constants.js"

import AdminMailReceive from "@/components/Admin/AdminMailReceive.vue"
import Loading from "@/components/Modal/Loading.vue"

const modal = inject('$modal')
const { t } = useI18n()

const settings = ref({ imap: null, ses: null, smtp: null })
const notice = ref({ type: '', text: '' })

const setNotice = (type, text) => {
  notice.value = { type, text }
}

const load = async () => {
  try {
    const [res, smtpRes] = await Promise.all([getMailSettings(), getSmtpSetting()])
    if (res.code === HTTP_CODES.SUCCESS && smtpRes.code === HTTP_CODES.SUCCESS) {
      const next = { imap: null, ses: null, smtp: smtpRes.data || null }
      for (const row of res.data || []) next[row.source_type] = row
      settings.value = next
    } else {
      setNotice('error', res.message || smtpRes.message)
    }
  } catch (e) {
    console.error('[MailReceiveView.load]', e)
    setNotice('error', e.response?.data?.message || String(e))
  }
}

onBeforeMount(load)

const onTest = async (params) => {
  modal.open(Loading)
  try {
    const res = params.sourceType === 'smtp' ? await testSmtpSetting(params) : await testMailSetting(params)
    if (res.code === HTTP_CODES.SUCCESS) {
      setNotice('ok', `${t('mailReceive.testOk')} (${JSON.stringify(res.data)})`)
    } else {
      setNotice('error', `${t('mailReceive.testFail')}: ${res.message}`)
    }
  } catch (e) {
    console.error('[MailReceiveView.onTest]', e)
    setNotice('error', `${t('mailReceive.testFail')}: ${e.response?.data?.message || e}`)
  } finally {
    modal.close()
  }
}

const onSave = async (params) => {
  modal.open(Loading)
  try {
    const res = params.sourceType === 'smtp' ? await upsertSmtpSetting(params) : await upsertMailSetting(params)
    if (res.code === HTTP_CODES.SUCCESS) {
      setNotice('ok', t('mailReceive.saved'))
      await load()
    } else {
      setNotice('error', res.message)
    }
  } catch (e) {
    console.error('[MailReceiveView.onSave]', e)
    setNotice('error', e.response?.data?.message || String(e))
  } finally {
    modal.close()
  }
}

const onDelete = async (sourceType) => {
  if (!window.confirm(t('mailReceive.confirmDelete'))) return
  modal.open(Loading)
  try {
    const res = sourceType === 'smtp' ? await deleteSmtpSetting() : await deleteMailSetting({ sourceType })
    if (res.code === HTTP_CODES.SUCCESS) {
      setNotice('ok', t('mailReceive.deleted'))
      await load()
    } else {
      setNotice('error', res.message)
    }
  } catch (e) {
    console.error('[MailReceiveView.onDelete]', e)
    setNotice('error', e.response?.data?.message || String(e))
  } finally {
    modal.close()
  }
}

const onRunNow = async () => {
  modal.open(Loading)
  try {
    const res = await runMailReceiveNow()
    if (res.code === HTTP_CODES.SUCCESS) {
      setNotice('ok', t('mailReceive.fetched', { n: res.data?.received ?? 0 }))
      await load()
    } else {
      setNotice('error', res.message)
    }
  } catch (e) {
    console.error('[MailReceiveView.onRunNow]', e)
    setNotice('error', e.response?.data?.message || String(e))
  } finally {
    modal.close()
  }
}
</script>

<template>
  <AdminMailReceive
      :settings="settings"
      :notice="notice"
      @test="onTest"
      @save="onSave"
      @delete="onDelete"
      @runNow="onRunNow"
  />
</template>
