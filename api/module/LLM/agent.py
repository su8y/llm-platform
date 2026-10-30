from module.LLM.dto import LLMArgs
from module.LLM.helper import get_elapsed
from utils.error import *
from client.groxy import LLMProxyClient



async def agent_judge_language(llmArgs:LLMArgs):
	try:
		service = llmArgs.service or "llm-platform-staging"
		model = llmArgs.model or "gpt-4o-mini"
		vendor = llmArgs.vendor or OPENAI
		system_message = """
		당신은 사용자 질문의 언어를 판단하는 AI AGENT입니다.
		사용자 질문의 언어를 판단하여
		1. 한국어라면 "사용자가 한글로 질문했으니, 한글로 답변해주세요.",
		2. 영어라면 "Since the user asked in English, please respond in English.",
		3. 일본어라면 "ユーザーが日本語で質問したので、日本語で答えてください。"
		
		당신의 답변은 위에 언급한 내용 중 하나여야하며 이 외 다른 답변을 해선 안됩니다.
		당신의 답변은 answer라는 변수에 담겨 아래 코드와 같이 답변하는 agent에 전달되기 때문입니다.
		messages = [
			{{"role": "system", "content": system_message}},
			{{"role": "user", "content": answer}},
			{{"role": "user", "content": str(user_message)}}
		]
	
		따라서, 사용자 질문의 언어를 판단하여 위에 언급한 답변만 반환해주셔야 합니다.
		그래야 답변하는 agent가 사용자 질문의 언어를 판단하여 적절한 답변을 할 수 있습니다.
		"""
		human_message = llmArgs.question
		system_message_placeholder = {}
		conversation_history = []
		temperature = 0

		answer = str()
		async for chunk in llmArgs.llm_proxy_client.stream(
			service=service,
			vendor=vendor,
			model=model,
			system_message=system_message,
			system_message_placeholder=system_message_placeholder,
			conversation_history=conversation_history,
			human_message=human_message,
			temperature=temperature
		):
			if chunk and chunk.get('text'):
				answer += chunk['text']

		get_elapsed(llmArgs, "ElapsedLangAgent")

		return answer
	except LLMProxyError as e:
		logging.error(f"[module.LLM.agent.agent_judge_language] LLMProxyError: {e}")
		raise LLMProxyError(e)
	except Exception as e:
		logging.error(f"[module.LLM.agent.agent_judge_language] Exception: {e}")
		return False


async def agent_make_title(
		llm_proxy_client:LLMProxyClient,
		chat_history:list,
		service:str=None,
		model:str=None,
		vendor:str=None
):
	try:
		service = service or "llm-platform-staging"
		model = model or "gpt-4o-mini"
		vendor = vendor or OPENAI
		system_message = """
		당신은 채팅 내용을 바탕으로 채팅 제목을 만들어주는 AI AGENT입니다.
		
  		채팅 내용을 바탕으로 채팅 제목을 만들어주세요.
		If the chat content is in English, please create the chat title in English.
		チャットの内容が日本語の場合は、日本語でチャットのタイトルを作成してください。
		채팅 내용이 한글이면 한글로 채팅 제목을 만들어주세요.
		
  		채팅 내용은 아래와 같습니다.
		"""
		human_message = f"""채팅내용: {chat_history}
		---

		If the chat content is in English, please create the chat title in English.
		チャットの内容が日本語の場合は、日本語でチャットのタイトルを作成してください。
		채팅 내용이 한글이면 한글로 채팅 제목을 만들어주세요."""
		system_message_placeholder = {}
		conversation_history = []
		temperature = 0

		async for chunk in llm_proxy_client.stream(
			service=service,
			vendor=vendor,
			model=model,
			system_message=system_message,
			system_message_placeholder=system_message_placeholder,
			conversation_history=conversation_history,
			human_message=human_message,
			temperature=temperature
		):
			if chunk and chunk.get('text'):
				yield chunk['text']

	except LLMProxyError as e:
		logging.error(f"[module.LLM.agent.agent_make_title] LLMProxyError: {e}")
		raise LLMProxyError(e)

	except Exception:
		message = "채팅 제목 생성 실패했습니다."
		for chunk in message:
			yield chunk
