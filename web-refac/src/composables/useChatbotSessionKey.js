
import {HTTP_CODES} from "@/libs/constants.js";
import {getChatbotCookie, setChatbotCookie} from "@/libs/auth-helper.js";
import {chatbotKeyCheck, getChatbotKey} from "@/api/chatbot.js";
import ChatBot from "@/components/Modal/ChatBot.vue";
import {ref, inject} from "vue";

export function useChatbotSessionKey () {
    const chatbotKey = ref('')
    const modal = inject('$modal')

   async function getChatbotSessionKey (isOpen = false) {
        try {
            if (getChatbotCookie()) {
                const params = {
                    chatbotKey: getChatbotCookie().chatbotKey
                }

                const res = await chatbotKeyCheck(params)

                if (res.code === HTTP_CODES.SUCCESS) {
                    if (res.data.isLive) {
                        chatbotKey.value = getChatbotCookie()
                        if(isOpen) {
                            modal.open(ChatBot, chatbotKey.value)
                        }
                    } else {
                        const res = await getChatbotKey()

                        if (res.code === HTTP_CODES.SUCCESS) {
                            setChatbotCookie(res.data)
                            chatbotKey.value = res.data
                            if(isOpen) {
                                modal.open(ChatBot, chatbotKey.value)
                            }
                        }
                    }
                } else {
                    alert(res.message)
                    console.log('Error: ', res)
                }
            } else {
                const res = await getChatbotKey()

                if (res.code === HTTP_CODES.SUCCESS) {
                    setChatbotCookie(res.data)
                    chatbotKey.value = res.data
                    if(isOpen) {
                        modal.open(ChatBot, chatbotKey.value)
                    }
                } else {
                    alert(res.message)
                    console.log('Error: ', res)
                }
            }
        } catch (e) {
            alert(e)
            console.error('Error: ', e)
        }
    }

    return {
        getChatbotSessionKey,
        chatbotKey
    }

}