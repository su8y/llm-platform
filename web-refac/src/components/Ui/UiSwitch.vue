<script setup>
import { computed, watch, ref, onBeforeMount } from 'vue'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  },
  default: {
    default: true
  },
  value: {
    default: undefined
  },
  onValue: {
    default: true
  },
  offValue: {
    default: false
  },
  onLabel: {
    type: String,
    default: 'ON'
  },
  offLabel: {
    type: String,
    default: 'OFF'
  },
  onColor: {
    type: String,
    default: '#64b950'
  },
  offDarkColor: {
    type: String,
    default: '#555555'
  },
  onDarkColor: {
    type: String,
    default: '#64b950'
  },
  offColor: {
    type: String,
    default: '#d7d7d7'
  },
  onIcon: {
    type: String
  },
  theme: {
    type: String
  },
  offIcon: {
    type: String
  },
  width: {
    type: Number,
    default: 53
  },
  size: {
    type: String,
    default: 'medium'
  }
})

const emits = defineEmits(['change'])

const realValue = ref(null)

onBeforeMount(() => {
  let initValue = props.value || props.default
  if (initValue === props.onValue) {
    realValue.value = true
  } else {
    realValue.value = false
  }
})

watch(props.value, (value) => {
  if (value === props.onValue) {
    realValue.value = true
  } else {
    realValue.value = false
  }
})

const color = computed(() => {
  if (props.theme === 'dark') {
    return realValue.value ? props.onDarkColor || props.onColor : props.offDarkColor || props.offColor
  }
  return realValue.value ? props.onColor : props.offColor
})

const offPinPosition = computed(() => {
  if (props.size === 'xsmall') {
    return realValue.value ? props.width - 14 - 2 : 2
  } else if (props.size === 'small') {
    return realValue.value ? props.width - 16 - 3 : 3
  }
  return realValue.value ? props.width - 19 - 3 : 3
})

const onChange = () => {
  if (!props.disabled) {
    if (props.value === undefined) {
      realValue.value = !realValue.value
    }
    emits('change', realValue.value ? props.onValue : props.offValue)
  }
}
</script>

<template>
  <div class="knit-switch"
       :class="[size, theme]">
    <button :class="{ active: realValue, disabled: disabled }"
            :style="{ width: width + 'px', 'background-color': color }"
            @click="onChange">
      <span class="pin"
            :class="{ on: realValue, off: !realValue}"
            :style="{ left: offPinPosition + 'px' }">
        <template v-if="onIcon">
          <i class="icon on" :class="onIcon"/>
        </template>
        <template v-if="offIcon">
          <i class="icon off" :class="offIcon"/>
        </template>
      </span>
      <label class="on" v-html="onLabel"></label>
      <label class="off" v-html="offLabel"></label>
    </button>
  </div>
</template>

<style lang="scss" scoped>
.knit-switch {
  display: inline-block;
  vertical-align: middle;

  &.dark {
    .pin.off {
      background-color: #bbbbbb;
    }

    label.off {
      color: #bbbbbb;
    }
  }

  button {
    position: relative;
    height: 25px;
    border-radius: 13px;
    transition: background-color 0.2s ease;
    vertical-align: middle;
    margin-top: -0.5px;

    * {
      cursor: pointer;
    }

    .pin {
      position: absolute;
      top: 3px;
      left: 3px;
      display: block;
      width: 19px;
      height: 19px;
      border-radius: 10px;
      box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.18);
      background-color: #ffffff;
      transition: left 0.3s cubic-bezier(.28,.12,.42,.94);

      i {
        transition: opacity 0.3s ease;

        &.on {
          opacity: 0;
        }

        &.off {
          opacity: 1;
        }
      }
    }

    label {
      position: absolute;
      top: 0;
      line-height: 25px;
      display: block;
      color: #ffffff;
      font-size: 12px;
      font-weight: 500;
      text-align: center;
      transition: width 0.3s cubic-bezier(.28,.12,.42,.94);
      overflow: hidden;

      &.on {
        left: 0;
        width: 0;
      }

      &.off {
        right: 0;
        width: calc(100% - 19px);
      }
    }

    &.active {
      .pin {
        i {
          &.on {
            opacity: 1;
          }

          &.off {
            opacity: 0;
          }
        }
      }

      label {
        &.on {
          width: calc(100% - 19px);
        }

        &.off {
          width: 0 !important;
        }
      }
    }

    &.disabled {
      cursor: not-allowed;

      * {
        cursor: not-allowed;
      }
    }
  }

  &.xsmall {
    button {
      height: 18px;

      .pin {
        top: 2px;
        left: 2px;
        width: 14px;
        height: 14px;
      }

      label {
        font-size: 10px;
        line-height: 22px;

        &.off {
          width: calc(100% - 14px);
        }
      }

      &.active {
        label {
          &.on {
            width: calc(100% - 16px);
          }
        }
      }
    }
  }

  &.small {
    button {
      height: 22px;

      .pin {
        width: 16px;
        height: 16px;
      }

      label {
        font-size: 10px;
        line-height: 23px;

        &.off {
          width: calc(100% - 16px);
        }
      }

      &.active {
        label {
          &.on {
            width: calc(100% - 16px);
          }
        }
      }
    }
  }
}
</style>
