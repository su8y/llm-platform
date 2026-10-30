<script setup>
import { ref, watch, onMounted, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { getGreeting, getPrompt, getVersionList, insertPrompt, updateGreeting } from '@/api/prompt.js'
import { formatDate } from '@/libs/parse.js'
import { HTTP_CODES } from "@/libs/constants.js";

import PromptDetail from '@/components/Playground/PromptDetail.vue'
import Loading from "@/components/Modal/Loading.vue";

const { t } = useI18n()
const router = useRouter()
const modal = inject('$modal')
const emits = defineEmits(['disable'])
const props = defineProps({
  isDropdown: {
    type: Boolean
  },
})

const promptVersionList = ref({})
const prompt = ref({})
const latestPrompt = ref({})
const promptInputData = ref({})
const isLoading = ref({})
const roleName = ref()
const greetingData = ref(null)
const isGreetingEdit = ref(true)

const initialPrompt = {
  memo: '',
  prompt: ''
}

onMounted(async () => {
  await getGreetingData()
  await getPromptVersionList('prompt')
})

watch(roleName, (newRoleName, oldRoleName) => {
  if (newRoleName !== oldRoleName) {
    getPromptVersionList('prompt')
  }
})

const setInitialPrompt = (kind) => {
  latestPrompt.value[kind] = JSON.parse(JSON.stringify(initialPrompt))
  promptInputData.value[kind] = JSON.parse(JSON.stringify(initialPrompt))
}

const getPromptVersionList = async (kind) => {
  const data = { kind }
  modal.open(Loading)

  try {
    const res = await getVersionList(data)
    if (res.code === HTTP_CODES.SUCCESS) {
      modal.close()
      const versionList = res.data

      if (versionList.length > 0) {
        for (let i in versionList) {
          versionList[i]['version'] =
              (versionList[i].version ? '* ' : '- ') + formatDate(versionList[i].version, 'num')
        }

        promptVersionList.value[kind] = versionList
        const promptId = versionList[0].prompt_id

        setCurrentPrompt(kind, promptId, true)
      } else {
        promptVersionList.value[kind] = versionList
        prompt.value[kind] = initialPrompt
        setInitialPrompt(kind)
      }
    } else {
      promptVersionList.value = {}
      modal.close()
      alert(res.message)
      console.log('Error: ', res)
    }
  } catch (e) {
    modal.close()
    alert(e)
    console.error('Error: ',e)
  }
}

const getPromptbyId = async (kind, id) => {
  const params = {
    "prompt_id": id
  }

  try {
    const res = await getPrompt(params)
    return res.data
  } catch (e) {
    console.log(e)
  }
}

const setCurrentPrompt = async (kind, id, isInit = false) => {
  isLoading.value[kind] = true

  const currentPrompt = await getPromptbyId(kind, id)
  prompt.value[kind] = currentPrompt

  isLoading.value[kind] = false

  if (isInit) {
    latestPrompt.value[kind] = promptVersionList.value[kind][0]
    promptInputData.value[kind] = JSON.parse(JSON.stringify(currentPrompt))
  }

  const latest = latestPrompt.value[kind]
  const isOutOfDate = id !== latest.prompt_id

  changeAskDisablity(isOutOfDate)
}

const handleSavePrompt = (kind) => {
  const params = {
    "prompt_name": 'default-contactus',
    "prompt": promptInputData.value[kind].prompt,
    "comment": promptInputData.value[kind].comment
  }

  insertPrompt(params)
      .then((res) => {
        alert(t('prompt.save'))
        console.log(res)
      })
      .catch((e) => {
        alert(t('prompt.failed'))
        console.log(e)
      })
      .finally(() => {
        getPromptVersionList(kind)
      })
}

const changeAskDisablity = (disabled) => {
  emits('disable', disabled)
}

const getGreetingData = async () => {
  try {
    const res = await getGreeting()

    if (res.code === 200) {
      greetingData.value = res.data || t('playground.defaultGreeting')
    } else {
      alert(res.message)
      console.log('Error: ', res)
    }
  } catch (e) {
    console.log('Error: ', e)
  }
}

const onSaveGreetings = async (params) => {
  try {
    const res = await updateGreeting(params)

    if (res.code === 200) {
      isGreetingEdit.value = false
      await getGreetingData()
    } else {
      alert(res.message)
      console.log('Error: ', res)
    }
  } catch (e) {
    console.log('Error: ', e)
  }
}
</script>

<template>
  <div
      class="prompt-container"
  >
    <PromptDetail
        kind="prompt"
        size="long"
        :prompt="prompt['prompt']"
        :latest-prompt="latestPrompt['prompt']"
        :list="promptVersionList['prompt']"
        :is-loading="isLoading['prompt']"
        :is-dropdown="props.isDropdown"
        :is-greeting-edit="isGreetingEdit"
        v-model:input-data="promptInputData['prompt']"
        v-model:greeting-data="greetingData"
        @select="setCurrentPrompt"
        @save="handleSavePrompt"
        @greetingSave="onSaveGreetings"
    />
  </div>
</template>

<style lang="scss" scoped>
.prompt-container {
  width: 100%;
  height: 100%;

}
</style>
