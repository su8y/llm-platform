from pydantic import BaseModel, Field
from typing import Optional



class checkChatbotKeyPayload(BaseModel):
	chatbot_key: str = Field(..., alias="chatbotKey")


class chatPayload(BaseModel):
	chatbot_key: str = Field(..., alias="chatbotKey")
	question: str = Field(..., alias="question")
	model: Optional[str] = Field(None, alias="model")
	streaming: Optional[bool] = Field(True, alias="streaming")
	lang: Optional[str] = Field(None, alias="lang")

class getConversationHistoryPayload(BaseModel):
	session_key: str = Field(..., alias="chatbotKey")