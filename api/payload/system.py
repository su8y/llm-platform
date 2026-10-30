from pydantic import BaseModel, Field
from typing import Optional



class InsertEmailPromptPayload(BaseModel):
    company_key: str = Field(..., alias="companyKey", description="Company Key")
    prompt: str = Field(..., alias="prompt", description="SystemPromptContent for Email Create")
    prompt_name: Optional[str] = Field(None, alias="promptName", description="Name for Prompt")
    comment: Optional[str] = Field(None, alias="comment", description="Comment of prompt")
    writer: Optional[str] = Field(None, alias="writer", description="Writer")