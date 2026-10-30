<script setup>
import { reactive, watch } from 'vue'
import { dateFormatter } from "@/libs/utils.js"

const props = defineProps({
  settings: { type: Object, required: true },
  notice: { type: Object, default: () => ({ type: '', text: '' }) }
})
const emits = defineEmits(['test', 'save', 'delete', 'runNow'])

const imap = reactive({ isActive: true, pollIntervalSec: 60, imapHost: '', imapPort: 993, imapUseSsl: true, imapUsername: '', imapPassword: '', imapFolder: 'INBOX' })
const ses = reactive({ isActive: true, pollIntervalSec: 60, sesRegion: 'ap-northeast-2', sesBucket: '', sesPrefix: '', sesAccessKey: '', sesSecretKey: '' })
const smtp = reactive({ isActive: true, smtpHost: '', smtpPort: 587, smtpUseSsl: false, smtpUseTls: true, smtpUsername: '', smtpPassword: '', fromAddress: '', fromName: '' })

watch(() => props.settings, (next) => {
  const i = next?.imap
  if (i) Object.assign(imap, { isActive: !!i.is_active, pollIntervalSec: i.poll_interval_sec, imapHost: i.imap_host || '', imapPort: i.imap_port || 993, imapUseSsl: !!i.imap_use_ssl, imapUsername: i.imap_username || '', imapPassword: '', imapFolder: i.imap_folder || 'INBOX' })
  const s = next?.ses
  if (s) Object.assign(ses, { isActive: !!s.is_active, pollIntervalSec: s.poll_interval_sec, sesRegion: s.ses_region || '', sesBucket: s.ses_bucket || '', sesPrefix: s.ses_prefix || '', sesAccessKey: s.ses_access_key || '', sesSecretKey: '' })
  const m = next?.smtp
  if (m) Object.assign(smtp, { isActive: !!m.is_active, smtpHost: m.smtp_host || '', smtpPort: m.smtp_port || 587, smtpUseSsl: !!m.smtp_use_ssl, smtpUseTls: !!m.smtp_use_tls, smtpUsername: m.smtp_username || '', smtpPassword: '', fromAddress: m.from_address || '', fromName: m.from_name || '' })
}, { deep: true, immediate: true })

const imapParams = () => ({ sourceType: 'imap', ...imap, imapPort: Number(imap.imapPort), pollIntervalSec: Number(imap.pollIntervalSec) })
const sesParams = () => ({ sourceType: 'ses', ...ses, pollIntervalSec: Number(ses.pollIntervalSec) })
const smtpParams = () => ({ sourceType: 'smtp', ...smtp, smtpPort: Number(smtp.smtpPort) })
const onSslToggle = () => { if (smtp.smtpUseSsl) smtp.smtpUseTls = false; smtp.smtpPort = smtp.smtpUseSsl ? 465 : 587 }
const fmt = (v) => v ? dateFormatter(v, 'time') : '-'
</script>

<template>
  <div class="mail-receive-wrapper flex flex-column">
    <h3 class="title be-font text-grey-md bold size-18">{{ $t('mailReceive.title') }}</h3>
    <p class="desc">{{ $t('mailReceive.desc') }}</p>
    <p v-if="notice.text" class="notice" :class="notice.type">{{ notice.text }}</p>

    <div class="cards">
      <!-- IMAP -->
      <section class="card">
        <header class="card-head">
          <h4>{{ $t('mailReceive.imap') }}</h4>
          <label class="check"><input type="checkbox" v-model="imap.isActive" /> {{ $t('mailReceive.active') }}</label>
        </header>
        <div class="grid">
          <label>{{ $t('mailReceive.host') }}<input v-model.trim="imap.imapHost" placeholder="imap.example.com" /></label>
          <label>{{ $t('mailReceive.port') }}<input v-model.number="imap.imapPort" type="number" /></label>
          <label class="check"><input type="checkbox" v-model="imap.imapUseSsl" /> {{ $t('mailReceive.ssl') }}</label>
          <label>{{ $t('mailReceive.username') }}<input v-model.trim="imap.imapUsername" autocomplete="off" /></label>
          <label>{{ $t('mailReceive.password') }}<input v-model="imap.imapPassword" type="password" autocomplete="new-password" :placeholder="settings.imap?.hasImapPassword ? '••••••••' : ''" /><small>{{ $t('mailReceive.passwordKeep') }}</small></label>
          <label>{{ $t('mailReceive.folder') }}<input v-model.trim="imap.imapFolder" /></label>
          <label>{{ $t('mailReceive.interval') }}<input v-model.number="imap.pollIntervalSec" type="number" min="15" /></label>
        </div>
        <div class="status" v-if="settings.imap">
          <span>{{ $t('mailReceive.lastPolled') }}: {{ fmt(settings.imap.last_polled_at) }}</span>
          <span>{{ $t('mailReceive.lastSuccess') }}: {{ fmt(settings.imap.last_success_at) }}</span>
          <span>{{ $t('mailReceive.received') }}: {{ settings.imap.received_count }}</span>
          <span v-if="settings.imap.last_error" class="error">{{ $t('mailReceive.lastError') }}: {{ settings.imap.last_error }}</span>
        </div>
        <p v-else class="status muted">{{ $t('mailReceive.notConfigured') }}</p>
        <div class="actions">
          <UiButton :type="'outline sm'" @click="emits('test', imapParams())">{{ $t('mailReceive.test') }}</UiButton>
          <UiButton :type="'primary sm'" @click="emits('save', imapParams())">{{ $t('mailReceive.save') }}</UiButton>
          <UiButton v-if="settings.imap" :type="'outline sm'" @click="emits('delete', 'imap')">{{ $t('mailReceive.delete') }}</UiButton>
        </div>
      </section>

      <!-- SES -->
      <section class="card">
        <header class="card-head">
          <h4>{{ $t('mailReceive.ses') }}</h4>
          <label class="check"><input type="checkbox" v-model="ses.isActive" /> {{ $t('mailReceive.active') }}</label>
        </header>
        <div class="grid">
          <label>{{ $t('mailReceive.region') }}<input v-model.trim="ses.sesRegion" placeholder="ap-northeast-2" /></label>
          <label>{{ $t('mailReceive.bucket') }}<input v-model.trim="ses.sesBucket" /></label>
          <label>{{ $t('mailReceive.prefix') }}<input v-model.trim="ses.sesPrefix" placeholder="inbound/" /></label>
          <label>{{ $t('mailReceive.accessKey') }}<input v-model.trim="ses.sesAccessKey" autocomplete="off" /></label>
          <label>{{ $t('mailReceive.secretKey') }}<input v-model="ses.sesSecretKey" type="password" autocomplete="new-password" :placeholder="settings.ses?.hasSesSecretKey ? '••••••••' : ''" /><small>{{ $t('mailReceive.secretKeep') }}</small></label>
          <label>{{ $t('mailReceive.interval') }}<input v-model.number="ses.pollIntervalSec" type="number" min="15" /></label>
        </div>
        <div class="status" v-if="settings.ses">
          <span>{{ $t('mailReceive.lastPolled') }}: {{ fmt(settings.ses.last_polled_at) }}</span>
          <span>{{ $t('mailReceive.lastSuccess') }}: {{ fmt(settings.ses.last_success_at) }}</span>
          <span>{{ $t('mailReceive.received') }}: {{ settings.ses.received_count }}</span>
          <span v-if="settings.ses.last_error" class="error">{{ $t('mailReceive.lastError') }}: {{ settings.ses.last_error }}</span>
        </div>
        <p v-else class="status muted">{{ $t('mailReceive.notConfigured') }}</p>
        <div class="actions">
          <UiButton :type="'outline sm'" @click="emits('test', sesParams())">{{ $t('mailReceive.test') }}</UiButton>
          <UiButton :type="'primary sm'" @click="emits('save', sesParams())">{{ $t('mailReceive.save') }}</UiButton>
          <UiButton v-if="settings.ses" :type="'outline sm'" @click="emits('delete', 'ses')">{{ $t('mailReceive.delete') }}</UiButton>
        </div>
      </section>

      <!-- SMTP 발신 -->
      <section class="card">
        <header class="card-head">
          <h4>{{ $t('mailReceive.smtp') }}</h4>
          <label class="check"><input type="checkbox" v-model="smtp.isActive" /> {{ $t('mailReceive.active') }}</label>
        </header>
        <p class="desc">{{ $t('mailReceive.smtpDesc') }}</p>
        <div class="grid">
          <label>{{ $t('mailReceive.host') }}<input v-model.trim="smtp.smtpHost" placeholder="smtp.example.com" /></label>
          <label>{{ $t('mailReceive.port') }}<input v-model.number="smtp.smtpPort" type="number" /></label>
          <label class="check"><input type="checkbox" v-model="smtp.smtpUseSsl" @change="onSslToggle" /> {{ $t('mailReceive.implicitSsl') }}</label>
          <label class="check"><input type="checkbox" v-model="smtp.smtpUseTls" :disabled="smtp.smtpUseSsl" /> {{ $t('mailReceive.starttls') }}</label>
          <label>{{ $t('mailReceive.username') }}<input v-model.trim="smtp.smtpUsername" autocomplete="off" /></label>
          <label>{{ $t('mailReceive.password') }}<input v-model="smtp.smtpPassword" type="password" autocomplete="new-password" :placeholder="settings.smtp?.hasSmtpPassword ? '••••••••' : ''" /><small>{{ $t('mailReceive.passwordKeep') }}</small></label>
          <label>{{ $t('mailReceive.fromAddress') }}<input v-model.trim="smtp.fromAddress" placeholder="cs@example.com" /></label>
          <label>{{ $t('mailReceive.fromName') }}<input v-model.trim="smtp.fromName" /></label>
        </div>
        <div class="status" v-if="settings.smtp">
          <span>{{ $t('mailReceive.lastTest') }}: {{ fmt(settings.smtp.last_test_at) }}</span>
          <span v-if="settings.smtp.last_error" class="error">{{ $t('mailReceive.lastError') }}: {{ settings.smtp.last_error }}</span>
        </div>
        <p v-else class="status muted">{{ $t('mailReceive.notConfigured') }}</p>
        <div class="actions">
          <UiButton :type="'outline sm'" @click="emits('test', smtpParams())">{{ $t('mailReceive.test') }}</UiButton>
          <UiButton :type="'primary sm'" @click="emits('save', smtpParams())">{{ $t('mailReceive.save') }}</UiButton>
          <UiButton v-if="settings.smtp" :type="'outline sm'" @click="emits('delete', 'smtp')">{{ $t('mailReceive.delete') }}</UiButton>
        </div>
      </section>
    </div>

    <div class="actions run-now">
      <UiButton :type="'primary sm'" :disabled="!settings.imap && !settings.ses" @click="emits('runNow')">{{ $t('mailReceive.runNow') }}</UiButton>
    </div>
  </div>
</template>

<style scoped lang="scss">
.mail-receive-wrapper { padding: 24px; gap: 12px; }
.desc { color: #777; font-size: 14px; }
.notice { padding: 10px 12px; border-radius: 6px; font-size: 14px; white-space: pre-wrap; }
.notice.ok { background: #e8f7ee; color: #1d7a46; }
.notice.error { background: #fdecec; color: #b42318; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 16px; }
.card { border: 1px solid #e3e3e3; border-radius: 8px; padding: 16px; display: flex; flex-direction: column; gap: 12px; background: #fff; }
.card-head { display: flex; align-items: center; justify-content: space-between; h4 { font-size: 16px; font-weight: 600; } }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 14px; }
.grid label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: #444; }
.grid label.check, .card-head label.check { flex-direction: row; align-items: center; gap: 6px; }
.grid input[type="text"], .grid input:not([type]), .grid input[type="number"], .grid input[type="password"] { border: 1px solid #d5d5d5; border-radius: 4px; padding: 6px 8px; font-size: 14px; }
.grid small { color: #999; font-size: 11px; }
.status { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 12px; color: #555; }
.status .error { color: #b42318; width: 100%; word-break: break-all; }
.status.muted { color: #999; }
.actions { display: flex; gap: 8px; }
.run-now { justify-content: flex-end; }
</style>
