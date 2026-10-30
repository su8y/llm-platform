from pydantic import BaseModel, Field
from typing import Optional



class chatPayload(BaseModel):
    question: str = Field(..., alias="question", description="Question")
    model: Optional[str] = Field(None, alias="model", description="Model")
    vendor: Optional[str] = Field(None, alias="vendor", description="Vendor")
    info: Optional[dict] = Field({}, alias="info", description="Info")
    streaming: bool = Field(True, alias="streaming", description="Streaming")
    is_mcp: Optional[bool] = Field(False, alias="isMCP", description="isOnMCP")
    lang: Optional[str] = Field(None, alias="lang", description="language client set")
    user_num: Optional[str] = Field(None, alias="user_num", description="User Number")
    file_id: Optional[int] = Field(None, alias="file_id", description="target File ID")

class GetMcpToolsPayload(BaseModel):
    answer_id: str = Field(..., alias="answerId", description="Answer ID From chat")

class retrievalPayload(BaseModel):
    id: str = Field(..., alias="id", description="Chat ID")
    is_mcp: Optional[bool] = Field(False, alias="isMCP", description="isOnMCP")
    model: Optional[str] = Field(None, alias="model", description="Model")
    vector_db_index: Optional[str] = Field(None, alias="vector_db_index", description="Vector Index Name")
    vector_db_namespace: Optional[str] = Field(None, alias="vector_db_namespace", description="Vector Name Space")

class GetConversationHistoryQueryParams(BaseModel):
    is_mcp: Optional[int] = Field(0, alias="isMCP", description="isMCP")

class getConversationHistoryTitleQueryParams(BaseModel):
    page: int = Field(..., alias="page", description="Page")
    per_page: int = Field(..., alias="perPage", description="Per Page")

class updateRatingPayload(BaseModel):
    id: str = Field(..., alias="id", description="Chat ID")
    rating: int = Field(..., alias="rating", description="Rating")

class updateCommentPayload(BaseModel):
    id: str = Field(..., alias="id", description="Chat ID")
    comment: str = Field(..., alias="comment", description="Comment")

class updateTitlePayload(BaseModel):
    id: str = Field(..., alias="id", description="Chat ID")
    title: str = Field(..., alias="title", description="Title")

class setHistoryPayload(BaseModel):
    session_key: str = Field(..., alias="sessionKey", description="Session Key")
    user_id: str = Field(..., alias="userId", description="User ID")
