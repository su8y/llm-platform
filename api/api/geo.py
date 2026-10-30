from fastapi import APIRouter, Depends

from client.ipapi import get_ip_geolocation_cached
from client.redis import RedisClient
from payload.geo import *
from helper.geo import *
from domain.geo import GetGeoDomain
from utils.response import Response200
from utils.error import handle_errors


router = APIRouter(
    prefix="/geo",
    tags=["geo"],
)


@router.get("/get_geo_info")
@handle_errors()
async def get_geo_info(
    request:Request,
    query_params: GetGeoInfoParams = Depends()
):
    # set domain_data
    domain_data = GetGeoDomain(client_ip=query_params.client_ip)

    # set client
    memory_db_client = RedisClient()

    # business logic
    if not domain_data.client_ip:
        domain_data.client_ip = get_client_ip_from_request(request)
    domain_data.geo_info = await get_ip_geolocation_cached(memory_db_client=memory_db_client, ip=domain_data.client_ip)

    # make response and return
    return Response200(data={"ip": domain_data.client_ip, "geo_info": domain_data.geo_info}).to_dict()