from module.MCP.dto import MCPArgs
from module.MCP.helper import get_elapsed
from utils.error import *
from client.groxy import LLMProxyClient



async def agent_judge_language(mcpArgs:MCPArgs):
	try:
		service = mcpArgs.service or "llm-platform-staging"
		model = mcpArgs.model or "gpt-4o-mini"
		vendor = mcpArgs.vendor or OPENAI
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
		user_message = mcpArgs.question
		system_message_placeholder = {}
		conversation_history = []
		temperature = 0
		
		answer = str()
		async for chunk in mcpArgs.llm_proxy_client.stream(
			service=service,
			vendor=vendor,
			model=model,
			system_message=system_message,
			system_message_placeholder=system_message_placeholder,
			conversation_history=conversation_history,
			question=user_message,
			temperature=temperature
		):
			if chunk:
				answer += chunk

		get_elapsed(mcpArgs, "ElapsedLangAgent")

		return answer
	except LLMProxyError as e:
		logging.error(f"[module.LLM.agent.agent_judge_language] LLMProxyError: {e}")
		raise LLMProxyError(e)
	except Exception as e:
		logging.error(f"[module.LLM.agent.agent_judge_language] Exception: {e}")
		return False


async def agent_translate_system_prompt(llm_proxy_client:LLMProxyClient, target_system_prompt:str, question:str, service:str=None, vendor:str=None, model:str=None):
	try:
		service = service or "llm-platform-staging"
		model = model or "gpt-4o-mini" 
		vendor = vendor or OPENAI
		
		system_message = f"""
		당신은 시스템 프롬프트를 사용자 언어에 맞게 번역해주는 AI AGENT입니다.
		사용자가 질문한 언어에 맞춰 프롬프트를 정확히 번역해주세요.
		
		사용자가 질문한 언어와 프롬프트에 작성된 언어가 동일하다면 번역없이 target에 작성된 프롬프트를 그대로 답변해주시면 됩니다.
		사용자가 질문한 언어가 프롬프트와 다르다면, 프롬프트를 사용자가 질문한 언어로 정확히 번역해 답변해주세요.
		
		당신이 번역한 프롬프트는 system_prompt로 사용될 것이며, system_prompt에 따라 답변 agent의 성능이 좌우되니
		target에 작성된 프롬프트를 천천히 읽고 정확히 번역해 답변해주시길 바랍니다.
		
		만약 일본어로 사용자가 질문했고 프롬프트가 한글이라면, 프롬프트를 일본어로 작성해 답변해주시면 됩니다.
		사용자가 영어로 질문했고 프롬프트도 영어라면, 번역없이 기존 프롬프트를 그대로 작성해 답변해주시면 됩니다.

		번역해야할 프롬프트는 아래와 같습니다.
		target: {target_system_prompt}
		"""
		
		user_message = question
		system_message_placeholder = {"target_system_prompt": target_system_prompt}
		conversation_history = []
		temperature = 0
		
		answer = str()
		async for chunk in llm_proxy_client.stream(
			service=service,
			vendor=vendor,
			model=model,
			system_message=system_message,
			system_message_placeholder=system_message_placeholder,
			conversation_history=conversation_history,
			question=user_message,
			temperature=temperature
		):
			if chunk:
				answer += chunk
		
		return answer
	
	except LLMProxyError as e:
		logging.error(f"[module.LLM.agent.agent_translate_system_prompt] LLMProxyError: {e}")
		raise LLMProxyError(e)
	except Exception as e:
		logging.error(f"[module.LLM.agent.agent_translate_system_prompt] Exception: {e}")
		return False


async def agent_make_title(llm_proxy_client:LLMProxyClient, chat_history:list, service:str=None, model:str=None, vendor:str=None):
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
		user_message = f"""채팅내용: {chat_history}
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
			question=user_message,
			temperature=temperature
		):
			if chunk:
				yield chunk

	except LLMProxyError as e:
		logging.error(f"[module.LLM.agent.agent_make_title] LLMProxyError: {e}")
		raise LLMProxyError(e)

	except Exception as e:
		message = "채팅 제목 생성 실패했습니다."
		async for chunk in message:
			yield chunk