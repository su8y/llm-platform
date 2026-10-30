<script setup>
import {useI18n} from "vue-i18n";

const emits = defineEmits(['submitQuestion','close'])

const { tm } = useI18n()
const handleSubmit = (questionValue) => {
  emits('submitQuestion', {prompt: questionValue})
}

</script>

<template>
  <div class="side-bar">
    <div class="side-bar-header">
      <h1 class="side-bar-header-title">
        {{ $t('chatBot.listTitle') }}
      </h1>
      <button class="close-button" @click="emits('close')">
        {{ $t('common.close') }}
        <i class="icon icon--close-size16"></i>
      </button>
    </div>
    <div class="side-bar-body">
      <section class="section" v-for="({label, list}) in tm('chatBot.questionList')" :key="label">
        <h2 class="section-title">
          {{ label }}
        </h2>
        <ul class="section-list">
          <li class="section-list-item" v-for="(question, idx) in list" :key="`question-${idx}`" @click="handleSubmit(question)">
            {{ question }}
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<style scoped lang="scss">


</style>