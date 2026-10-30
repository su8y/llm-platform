<script setup>
import { supportContact } from '@/libs/support.js'
import { reactive, inject } from "vue";
import { useI18n } from 'vue-i18n'

const modal = inject('$modal')
const { t } = useI18n()

const planDesc = reactive([
    t('plan.subscribe.desc[0]'),
    t('plan.subscribe.desc[1]'),
    t('plan.subscribe.desc[2]'),
    t('plan.subscribe.desc[3]'),
    t('plan.subscribe.desc[4]', { email: supportContact() })
])
const planInfo = reactive([
    t('plan.subscribe.info.id'),
    t('plan.subscribe.info.company'),
    t('plan.subscribe.info.desiredPlan'),
    t('plan.subscribe.info.invoiceEmail'),
    t('plan.subscribe.info.invoiceDate'),
    t('plan.subscribe.info.expectedPaymentDate'),
    t('plan.subscribe.info.businessRegistrationNumber')
])
</script>

<template>
  <div class="subscribe-plan-wrapper">
    <span class="title">{{ t('plan.subscribe.title') }}</span>
    <div class="plan-name-wrapper">
      <div class="plans">
        <span class="plan-name">Basic</span>
        <div class="plan-price-wrapper">
          <span class="plan-question">{{ t('plan.subscribe.plan.basic.questionCount') }}</span>
          <span class="plan-price">{{ t('plan.subscribe.plan.basic.price') }}</span>
        </div>
      </div>
      <div class="plans">
        <span class="plan-name">Premium</span>
        <div class="plan-price-wrapper">
          <span class="plan-question">{{ t('plan.subscribe.plan.premium.questionCount') }}</span>
          <span class="plan-price">{{ t('plan.subscribe.plan.premium.price') }}</span>
        </div>
      </div>
      <div class="plans">
        <span class="plan-name">Pro</span>
        <div class="plan-price-wrapper">
          <span class="plan-question">{{ t('plan.subscribe.plan.pro.questionCount') }}</span>
          <span class="plan-price">{{ t('plan.subscribe.plan.pro.price') }}</span>
        </div>
      </div>
    </div>
    <div class="plan-desc-wrapper">
      <ul class="desc">
        <template v-for="item in planDesc" :key="item" >
          <li v-html="item"></li>
        </template>
      </ul>
    </div>
    <div class="plan-info-wrapper">
      <ul class="plan-info">
        <template v-for="item in planInfo" :key="item">
          <li>{{ item }}</li>
        </template>
      </ul>
    </div>
    <div class="line horizontal"></div>
    <div class="btn-wrap">
      <UiButton :type="'outline'" @click="modal.close()">
        {{ t('common.close') }}
      </UiButton>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.subscribe-plan-wrapper {
  width: 490px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 24px;

  .title {
    color: #2F2F2F;
    font-size: 15px;
    font-weight: $semiBold;
  }

  .plan-name-wrapper {
    margin-top: 12px;
    display: flex;
    gap: 9px;
    text-align: center;

    .plans {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 10px;

      .plan-name {
        color: $mainColor;
        font-size: 32px;
        font-weight: $bold;
      }

      .plan-price-wrapper {
        display: flex;
        flex-direction: column;
        span {
          color: #000;
          font-size: 13px;
          font-weight: $semiBold;
          line-height: 120%; /* 15.6px */
        }
      }
    }
  }

  .plan-desc-wrapper {
    margin-top: 8px;
    border-radius: 5px;
    border: 1px solid #D7D7D7;
    background: #F4F4F4;
    padding: 20px 20px 24px;

    .desc {
      display: flex;
      flex-direction: column;
      gap: 12px;

      li {
        list-style-type: square;
        color: #444;
        font-size: 15px;
        font-weight: 400;
        line-height: 150%; /* 22.5px */
      }
    }
  }

  .plan-info-wrapper {
    .plan-info {
      display: flex;
      flex-direction: column;
      gap: 6px;

      li {
        color: #666;
        font-size: 13px;
        font-weight: 400;
        line-height: 150%; /* 19.5px */
        list-style-type: square;
      }
    }
  }

  .btn-wrap {
    text-align: center;
  }
}
</style>
