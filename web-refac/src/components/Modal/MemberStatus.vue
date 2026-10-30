<script setup>
import { inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const modal = inject('$modal')
const type = inject('modalContent')
const { t, locale } = useI18n()
const isStatus = ref(type.value.content === 'status')

</script>

<template>
  <div class="members-info-container">
    <template v-if="isStatus">
      <div class="members-info-wrap flex flex-column xy-center">
        <div class="title-wrap">
          <i class="icon icon--info-write"></i>
          <h3 class="title be-font size-20 semi-bold text-grey-lg">
            {{ t('members.modal.status.title') }}
          </h3>
        </div>
        <div class="desc flex flex-column xy-center">
          <ul>
            <li v-html="t('members.modal.status.waiting')"></li>
            <li v-html="t('members.modal.status.complete')"></li>
            <li v-html="t('members.modal.status.expired')"></li>
            <li v-html="t('members.modal.status.false')"></li>
          </ul>
        </div>
      </div>
    </template>
    <template v-else>
      <div class="members-info-wrap flex flex-column xy-center">
        <div class="title-wrap">
          <i class="icon icon--info-write"></i>
          <h3 class="title be-font size-20 semi-bold text-grey-lg" v-html="t('members.modal.authority.title')">
          </h3>
        </div>
        <div class="desc flex flex-column xy-center not-status">
          <ul>
            <li :class="locale">
              <span class="icon-wrap">
                <i class="icon icon--master" />
              </span>
              <span v-html="t('members.modal.authority.master')"></span>
            </li>
            <li :class="locale">
              <span class="icon-wrap">
                <i class="icon icon--manager" />
              </span>
              <span v-html="t('members.modal.authority.manager')"></span>
            </li>
            <li :class="locale">
              <span class="icon-wrap">
                <i class="icon icon--viewer" />
              </span>
              <span v-html="t('members.modal.authority.viewer')"></span>
            </li>
          </ul>
        </div>
      </div>
      <p class="members-info" v-html="t('members.modal.authority.desc')">
      </p>
    </template>
    <div class="btn-wrap flex x-center">
      <UiButton class="cancel-btn" :type="'outline'" @click="modal.close()">{{ t('common.close') }}</UiButton>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.members-info-container {
  padding: 30px 10px 5px;
  min-width: 430px;
  text-align: center;

  .members-info-wrap {
    width: 100%;
    height: 100%;
    margin-bottom: 25px;
    gap: 25px;

    .title-wrap {
      text-align: center;
      .title {
        margin-top: 12px;
      }
    }

    .desc {
      max-width: 370px;
      padding: 20px;
      border-radius: 6px;
      border: 1px solid #D7D7D7;
      background: #F4F4F4;

      ul {
        display: flex;
        flex-direction: column;
        gap: 10px;
        text-align: left;

        li {
          color: #666;
          font-size: 13px;
          font-weight: 400;
          line-height: 19px; /* 146.154% */
          list-style-type: square;
        }
      }

      &.not-status {
        ul {
          padding: 0;

          li {
            list-style: none;
            display: flex;
            align-items: center;
            gap: 5px;

            &.ja {
              align-items: flex-start;

              .icon-wrap {
                margin-top: 2px;
              }
            }

            .icon-wrap {
              display: inline-block;
              width: 16px;
              height: 16px;
            }
          }
        }
      }
    }
  }

  .members-info {
    margin-bottom: 25px;
  }

  .btn-wrap {
    gap: 10px;
  }
}
</style>

