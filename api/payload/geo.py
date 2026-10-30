from pydantic import BaseModel, Field
from typing import Optional



class GetGeoInfoParams(BaseModel):
    client_ip: Optional[str] = Field(None, alias="clientIp", description="For Test")