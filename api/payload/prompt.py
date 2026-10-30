from pydantic import BaseModel, Field
from typing import Optional



class insertPromptPayload(BaseModel):
    prompt_name: str = Field(..., alias="prompt_name")
    prompt: str = Field(..., alias="prompt")
    comment: str = Field(..., alias="comment")
    

class getVersionPayload(BaseModel):
    kind: str = Field(..., alias="kind")


class getPromptPayload(BaseModel):
    prompt_id: int = Field(..., alias="prompt_id")


class updateGreetingsPayload(BaseModel):
    greetings: str = Field(..., alias="greetings")