import httpx
import asyncio
import json
import logging

from client.redis import RedisClient

from utils.error import MemoryDBError



async def get_location_ipapi(ip: str):
    """
    ip-api.com을 사용한 IP 지리정보 조회
    - 무료: 월 45,000 요청 (분당 45 요청)
    - API 키 불필요
    - 한국어 지원
    """
    try:
        url = f"http://ip-api.com/json/{ip}?lang=ko"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "success": True,
                        "ip": ip,
                        "country": data.get("country"),
                        "country_code": data.get("countryCode"),
                        "region": data.get("regionName"),
                        "city": data.get("city"),
                        "timezone": data.get("timezone"),
                        "isp": data.get("isp"),
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                        "service": "ip-api.com"
                    }

        return {"success": False, "error": "위치 정보를 찾을 수 없습니다"}

    except Exception as e:
        return {"success": False, "error": f"API 요청 실패: {str(e)}"}

async def get_location_freeipapi(ip: str):
    """
    freeipapi.com을 사용한 IP 지리정보 조회
    - 무료: 분당 60 요청
    - API 키 불필요
    - 상업적 이용 가능
    """
    try:
        url = f"https://freeipapi.com/api/json/{ip}"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "ip": ip,
                    "country": data.get("countryName"),
                    "country_code": data.get("countryCode"),
                    "region": data.get("regionName"),
                    "city": data.get("cityName"),
                    "timezone": data.get("timeZone"),
                    "isp": None,
                    "lat": data.get("latitude"),
                    "lon": data.get("longitude"),
                    "service": "freeipapi.com"
                }

        return {"success": False, "error": "위치 정보를 찾을 수 없습니다"}

    except Exception as e:
        return {"success": False, "error": f"API 요청 실패: {str(e)}"}

async def get_location_ipwhois(ip: str):
    """
    ipwhois.io를 사용한 IP 지리정보 조회
    - 무료: 월 10,000 요청
    - API 키 불필요
    - 다국어 지원
    """
    try:
        url = f"https://ipwhois.app/json/{ip}?lang=ko"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                if data.get("success", False):
                    return {
                        "success": True,
                        "ip": ip,
                        "country": data.get("country"),
                        "country_code": data.get("country_code"),
                        "region": data.get("region"),
                        "city": data.get("city"),
                        "timezone": data.get("timezone"),
                        "isp": data.get("isp"),
                        "lat": data.get("latitude"),
                        "lon": data.get("longitude"),
                        "service": "ipwhois.io"
                    }

        return {"success": False, "error": "위치 정보를 찾을 수 없습니다"}

    except Exception as e:
        return {"success": False, "error": f"API 요청 실패: {str(e)}"}

async def get_location_ipapi_co(ip: str):
    """
    ipapi.co를 사용한 IP 지리정보 조회
    - 무료: 일 1,000 요청 (월 약 30,000)
    - API 키 불필요 (무료 플랜)
    - 정확도 높음
    """
    try:
        url = f"https://ipapi.co/{ip}/json/"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                if not data.get("error"):
                    return {
                        "success": True,
                        "ip": ip,
                        "country": data.get("country_name"),
                        "country_code": data.get("country_code"),
                        "region": data.get("region"),
                        "city": data.get("city"),
                        "timezone": data.get("timezone"),
                        "isp": data.get("org"),
                        "lat": data.get("latitude"),
                        "lon": data.get("longitude"),
                        "service": "ipapi.co"
                    }

        return {"success": False, "error": "Can not get geo info"}

    except Exception as e:
        return {"success": False, "error": f"API 요청 실패: {str(e)}"}

async def get_ip_geolocation(ip: str, services: list = None):
    if (
            ip in ["127.0.0.1", "::1"] or
            ip.startswith(("192.168.", "10.")) or
            any(ip.startswith(f"172.{i}.") for i in range(16, 32))
    ):
        return {
            "success": True,
            "ip": ip,
            "country": "Local",
            "country_code": "LOCAL",
            "region": "Local Network",
            "city": "Local",
            "timezone": None,
            "isp": "Local Network",
            "lat": None,
            "lon": None,
            "service": "local"
        }

    if services is None:
        services = [
            get_location_ipapi,
            get_location_ipapi_co,
            get_location_freeipapi,
            get_location_ipwhois
        ]

    # 각 서비스를 순서대로 시도
    for service in services:
        try:
            result = await service(ip)
            if result.get("success", False):
                return result
        except Exception as e:
            logging.info(f"서비스 {service.__name__} 실패: {e}")
            continue

    return {
        "success": False,
        "ip": ip,
        "error": "Can not get geo info from all services!"
    }


async def get_ip_geolocation_cached(memory_db_client:RedisClient, ip: str, ttl: int = 86400):
    cache_key = f"geo:ip:{ip}"
    
    try:
        cached_result = await memory_db_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)

        result = await get_ip_geolocation(ip)
        if result.get("success", False):
            await memory_db_client.set_with_expire(
                cache_key, 
                json.dumps(result), 
                ttl
            )
        
        return result

    except MemoryDBError as e:
        logging.error(f"[client.ipapi.get_ip_geolocation_cached] MemoryDBError: {e}")
        raise MemoryDBError(e)
    except Exception as e:
        logging.error(f"[client.ipapi.get_ip_geolocation_cached] Exception: {e}")
        raise Exception(e)