<script setup>
import { ref, defineProps, defineEmits, watch } from 'vue'
import { format } from "date-fns";

const props = defineProps({
  wrapStyle: {
    type: String,
    default: null
  },
  inputStyle: {
    type: String,
    default: null
  },
  type: {
    type: String,
    default: null,
    required: true
  },
  placeholder: {
    type: String,
    default: null
  },
  value: {
    type: String,
    default: null
  },
  index: {
    type: Number,
    default: null
  },
  dateRange: {
    type: Object,
    default: () => {
      return { start: null, end: null }
    }
  },
  disabled: {
    type: Boolean,
    default: false
  },
  hidden: {
    type: Boolean,
    default: false
  },
  maxLength: {
    type: Number
  },
  modelValue: {
    type: String
  }
})
const emit = defineEmits(['updateValue', 'focus', 'dateReset', 'update:modelValue'])
const inputValue = ref(props.value || props.modelValue)

// Watch for changes in the prop and update the local state
watch(() => props.modelValue, (newValue) => {
  inputValue.value = newValue
})

watch(() => props.dateRange, (newDate) => {
  if (props.inputStyle === 'date') {
    if (newDate.start && newDate.end) {
      inputValue.value = `${format(newDate.start, 'yyyy.MM.dd')} ~ ${format(newDate.end, 'yyyy.MM.dd')}`
    } else {
      inputValue.value = `----.--.-- ~ ----.--.--`
    }
  }
}, { deep: true, immediate: true })

const onEnter = (e) => {
  if (e.key === 'Enter') {
    emit('enter')
  }
}

const handleFocus = (index) => {
  emit('focus', index)
}

const onKeyDown = () => {
  emit('update:modelValue', inputValue.value)
  emit('updateValue', inputValue.value)
}

const dateReset = () => {
  emit('dateReset')
}

const inputReset = () => {
  inputValue.value = ''
  emit('updateValue', inputValue.value)
  emit('update:modelValue', inputValue.value)
}

</script>

<template>
  <div class="be-input-wrapper" :class="wrapStyle">
    <label class="be-label">
      <slot name="label" />
    </label>
    <template v-if="props.inputStyle === 'date'">
      <div class="date-input">
        <input
            class="be-input"
            :class="inputStyle"
            :type="props.type"
            :placeholder="props.placeholder"
            :value="inputValue"
            :disabled="disabled"
            readonly
            v-model="inputValue"
            @focus="handleFocus(index)"
            @keyup="onEnter"
            @input="onKeyDown" />
        <span class="be-icon size-16 icon-grey-sm date-reset" @click.stop="dateReset">
          <i class="font-icon-refresh" />
        </span>
      </div>
    </template>
    <template v-else>
      <slot name="icon" />
      <input
          class="be-input"
          :class="inputStyle"
          :type="props.type"
          :placeholder="props.placeholder"
          :value="inputValue"
          :readonly="props.inputStyle === 'date'"
          :disabled="disabled"
          :hidden="props.hidden"
          :maxlength="maxLength"
          v-model="inputValue"
          @focus="handleFocus(index)"
          @keyup="onEnter"
          @input="onKeyDown">
      <template v-if="inputValue && !disabled">
        <i class="delete-text font-icon-close" @click="inputReset" />
      </template>
    </template>
    <slot name="error" />
  </div>
</template>

<style lang="scss" scoped>
</style>
