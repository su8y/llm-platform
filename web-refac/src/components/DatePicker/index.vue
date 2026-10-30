<script setup>
import { ref, computed, defineEmits, defineProps } from 'vue'
import { useStore } from 'vuex'
import { useI18n } from 'vue-i18n'

const store = useStore()
const { locale } = useI18n()

const props = defineProps({
  dateRange: {
    type: Object,
    default: () => {
      return { start: null, end: null }
    }
  }
})

const range = computed(() => {
  return {
    start: props.dateRange.start,
    end: props.dateRange.end
  }
})

const emit = defineEmits(['selectDateRange'])

const popover = ref({
  visibility: 'click',
})

const selectDateRage = (date) => {
  emit('selectDateRange', date)
  store.commit('setSearchPeriod', {
    start: date.start,
    end: date.end
  })
}
</script>

<template>
  <div class="date-range-wrapper">
    <VDatePicker
        date="date"
        v-model.range="range"
        :color="'red'"
        :popover="popover"
        :columns="2"
        :max-date='new Date()'
        :locale="locale"
        @dayclick="
          (_, event) => {
            event.target.blur();
          }
        "
        @update:modelValue="selectDateRage($event)">
    </VDatePicker>
  </div>
</template>

<style lang="scss" scoped>
.date-range-wrapper {
  position: absolute;
  top: 100%;
  left: 0%;
  z-index: 9;
}
</style>
