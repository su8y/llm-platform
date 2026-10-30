import { useI18n } from 'vue-i18n'

export function useLocalizedPrice() {
    const { t, locale } = useI18n()

    return function (amountMap) {
        const lang = locale.value
        const amount = amountMap[lang] || amountMap['en']
        return t('common.unit2', { amount: amount.toLocaleString() })
    }
}
