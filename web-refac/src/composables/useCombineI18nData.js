
import { useI18n } from 'vue-i18n'
import {I18N_CUSTOM_MAPPING} from "@/libs/constants.js";

export function useCombineI18nData () {
    const { tm } = useI18n()


    function combine (listName, type, addKey = 'icon') {

        const list = tm(listName) || {};
        const targetIconList = I18N_CUSTOM_MAPPING[type] || []

        return Object.entries(list).reduce((acc, [key, value]) => {
            acc[key] = {
                ...(typeof value === 'string' ? { value } : { ...value }),
                [addKey]: targetIconList[key] || null,
            }
            return acc
        }, {})
    }

    return {
        combine,
    }
}