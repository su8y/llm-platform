<script setup>


import {computed} from "vue";

const props = defineProps({
  termsContent: Object,
  type: String
})


const filterTermsList = computed(() => {
  const list = Object.values(props.termsContent.list|| {})

  return list.filter(item => item.subhead && item.subhead.trim() !== '')
})
</script>

<template>
  <div class="terms-wrap">
    <div class="terms-inner">
      <h2 class="terms-title">
        {{props.termsContent.title}}
      </h2>
      <section class="terms-section">
        <div class="terms-content" v-for="(terms, idx) in filterTermsList" :key="`${props.type}-${idx}`">
          <h3 class="terms-subhead" v-html="terms.subhead" ></h3>
          <p class="terms-desc" v-html="terms.desc"></p>
        </div>
      </section>




    </div>
  </div>
</template>

<style scoped lang="scss">
.terms {
  &-inner {
    max-width: 1002px;
    padding: 196px 16px 200px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 100px;
    .dot-list {
      li {
        color: $n-gray-700;
        font-size: $font-15;
        font-weight: $regular;
        line-height: 27px;
      }
    }
    br {
      line-height: 1;
    }
  }
  &-title {
    color: $n-gray-900;
    font-size: 48px;
    font-weight: $bold;
    line-height: 100%;
  }
  &-section {
    display: flex;
    flex-direction: column;
    gap: 80px;
  }
  &-content {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  &-subhead {
    color: $n-gray-900;
    font-size: $font-15;
    font-weight: $semiBold;
    line-height: 27px;
  }
  &-desc {
    color: $n-gray-700;
    font-size: $font-15;
    font-weight: $regular;
    line-height: 27px;
    &:deep {
      a {
        font: inherit;
        color: inherit;
        text-decoration: underline;
      }
    }
  }
}
</style>