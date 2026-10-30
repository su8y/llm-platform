from module.Mail.dto import LLMEmailArgs

from utils.error import *
from client.groxy import LLMProxyClient



async def agent_judge_language(args:LLMEmailArgs):
	try:
		service = args.service or "llm-platform-staging"
		model = args.model or "gpt-4o-mini"
		vendor = args.vendor or OPENAI
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
		human_message = args.question
		system_message_placeholder = {}
		conversation_history = []
		temperature = 0

		answer = str()
		async for chunk in args.llm_proxy_client.stream(
			service=service,
			vendor=vendor,
			model=model,
			system_message=system_message,
			system_message_placeholder=system_message_placeholder,
			conversation_history=conversation_history,
			human_message=human_message,
			temperature=temperature
		):
			if chunk and chunk.get("text"):
				answer += chunk["text"]

		return answer
	except LLMProxyError as e:
		logging.error(f"[module.LLM.agent.agent_judge_language] LLMProxyError: {e}")
		raise LLMProxyError(e)
	except Exception as e:
		logging.error(f"[module.LLM.agent.agent_judge_language] Exception: {e}")
		return False
