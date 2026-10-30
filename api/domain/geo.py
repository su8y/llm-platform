from pydantic import BaseModel



class GetGeoDomain(BaseModel):
    client_ip: str|None = None
    geo_info: dict|None = None