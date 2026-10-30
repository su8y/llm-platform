from pydantic import BaseModel, Field
from typing import Optional



class UserInfo(BaseModel):
	user_id: str
	session_key: str