import os
from asyncio import timeout

from typing import List
from pathlib import Path
import pytz
from fastmcp import FastMCP, Context
from pinecone import Pinecone
from openai import OpenAI
import json
import requests
from dotenv import load_dotenv
import pymysql
from clickhouse_driver import Client as ClickHouseClient
import base64
from datetime import datetime
from decimal import Decimal
from urllib.parse import quote
from typing import Dict, Any, Optional
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
# import tweepy

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Environment configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'debug')  # debug or production
IS_DEBUG = ENVIRONMENT == 'debug'

mysql_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER'),
    'port': int(os.getenv('MYSQL_PORT')),
    'password': os.getenv('MYSQL_PASSWORD'),
    'database': os.getenv('MYSQL_DATABASE'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

clickhouse_config = {
    'host': os.getenv('CLICKHOUSE_HOST', 'localhost'),
    'user': os.getenv('CLICKHOUSE_USER'),
    'port': int(os.getenv('CLICKHOUSE_PORT', '9000')),
    'password': os.getenv('CLICKHOUSE_PASSWORD'),
}

SCRIPT_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = SCRIPT_DIR / "geo_prompts"
INDUSTRY_DIR = PROMPTS_DIR / "industry"
CATEGORY_DIR = PROMPTS_DIR / "category"

# Authentication setup - only use verifier in production
if IS_DEBUG:
    # Debug mode: no authentication
    mcp = FastMCP("llm-platform-mcp-server", stateless_http=True)
else:
    # Production mode: use JWT verifier
    # 토큰은 환경변수로만 받는다 (env/secret.yaml). 코드에 적지 않는다.
    tokens = {}
    admin_token = os.getenv("MCP_ADMIN_TOKEN", "").strip()
    if admin_token:
        tokens[admin_token] = {"client_id": "admin", "scopes": ["read:data", "write:data", "admin:users"]}
    for item in filter(None, (part.strip() for part in os.getenv("MCP_READ_TOKENS", "").split(","))):
        token, _, client_id = item.partition(":")
        tokens[token] = {"client_id": client_id or token, "scopes": ["read:data"]}
    if not tokens:
        raise RuntimeError("MCP_ADMIN_TOKEN or MCP_READ_TOKENS must be set when not in debug mode")
    verifier = StaticTokenVerifier(tokens=tokens, required_scopes=["read:data"])
    mcp = FastMCP("llm-platform-mcp-server", auth=verifier, stateless_http=True)


def get_db_connection():
    """MySQL 데이터베이스 연결을 반환"""
    try:
        return pymysql.connect(**mysql_config)
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")


def get_clickhouse_connection():
    """ClickHouse 데이터베이스 연결을 반환"""
    try:
        return ClickHouseClient(**clickhouse_config)
    except Exception as e:
        raise Exception(f"ClickHouse connection failed: {str(e)}")


# Initialize clients immediately
pinecone_client = None
openai_client = None
index = None

# Initialize on module load
print("Initializing clients...")
print(f"PINECONE_API_KEY exists: {bool(os.getenv('PINECONE_API_KEY'))}")
print(f"OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")

# Pinecone setup
pinecone_api_key = os.getenv("PINECONE_API_KEY")
if pinecone_api_key:
    print("Initializing Pinecone client...")
    pinecone_client = Pinecone(api_key=pinecone_api_key)
    index_name = os.getenv("PINECONE_INDEX_NAME", "knowledge-base")
    print(f"Connecting to index: {index_name}")
    index = pinecone_client.Index(index_name)
    print("Pinecone client initialized successfully")
else:
    print("PINECONE_API_KEY not found in environment variables")

# OpenAI setup
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    print("Initializing OpenAI client...")
    openai_client = OpenAI(api_key=openai_api_key)
    print("OpenAI client initialized successfully")
else:
    print("OPENAI_API_KEY not found in environment variables")


# conn = get_db_connection()
# cursor = conn.cursor()

def create_embedding(text: str) -> List[float]:
    """Create vector embedding for text"""
    if not openai_client:
        raise ValueError("OpenAI client not initialized")

    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-large"
    )
    return response.data[0].embedding


@mcp.tool()
def search_knowledge_base(
        query: str,
        top_k: int = 5,
        include_metadata: bool = True,
        filter_conditions: Optional[str] = None
) -> str:
    """
    Search Pinecone vector database for relevant knowledge

    Args:
        query: Search query text
        top_k: Number of results to return (default: 5)
        include_metadata: Whether to include metadata in results (default: True)
        filter_conditions: JSON string of filter conditions (optional)

    Returns:
        JSON string containing search results
    """
    try:
        if not index:
            return json.dumps({
                "error": "Pinecone not initialized. Check PINECONE_API_KEY and PINECONE_INDEX_NAME environment variables."
            })

        # Create query vector
        query_vector = create_embedding(query)

        # Prepare search parameters
        search_params = {
            "vector": query_vector,
            "top_k": top_k,
            "include_metadata": include_metadata
        }

        # Add filter if provided
        if filter_conditions:
            try:
                filter_dict = json.loads(filter_conditions)
                search_params["filter"] = filter_dict
            except json.JSONDecodeError:
                return json.dumps({
                    "error": "Invalid filter_conditions JSON format"
                })

        # Perform search
        results = index.query(**search_params)

        # Format results
        formatted_results = []
        for match in results.matches:
            result_item = {
                "id": match.id,
                "score": float(match.score),
            }

            if include_metadata and match.metadata:
                result_item["metadata"] = match.metadata
                # Include text content if available in metadata
                if "text" in match.metadata:
                    result_item["content"] = match.metadata["text"]

            formatted_results.append(result_item)

        return json.dumps({
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "search_params": {
                "top_k": top_k,
                "include_metadata": include_metadata,
                "filter_applied": filter_conditions is not None
            }
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "error": f"Search failed: {str(e)}",
            "query": query
        })


@mcp.tool()
async def get_current_time(timezone: str = "Asia/Seoul") -> str:
    """
    현재 시각을 반환합니다.

    Args:
        timezone: 시간대 (기본값: UTC)
                 예시: "Asia/Seoul", "America/New_York", "Europe/London"

    Returns:
        현재 시각 문자열
    """
    try:
        # 시간대 객체 생성
        tz = pytz.timezone(timezone)
        # 현재 시각 구하기
        current_time = datetime.now(tz)

        # 포맷팅된 시간 반환
        return json.dumps({
            "timezone": timezone,
            "current_time": current_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "iso_format": current_time.isoformat(),
            "timestamp": int(current_time.timestamp())
        }, ensure_ascii=False, indent=2)
    except pytz.exceptions.UnknownTimeZoneError:
        return json.dumps({
            "error": f"Unknown timezone: {timezone}",
            "available_timezones": "Use pytz.all_timezones to see all available timezones"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_scroll_analytics(
        aid: str,
        device: str = "phone",
        event: str = "scroll",
        start_date: str = "2025-05-15",
        end_date: str = "2025-05-21",
        api_base_url: str = "http://localhost:8000"
) -> str:
    """
    Get scroll event analytics from heatmap API

    Args:
        aid: Analytics ID for the target application
        device: Device type (default: "phone")
        event: Event type (default: "scroll")
        start_date: Start date in YYYY-MM-DD format (default: "2025-05-15")
        end_date: End date in YYYY-MM-DD format (default: "2025-05-21")
        api_base_url: Base URL for the API (default: "http://localhost:8000")

    Returns:
        JSON string containing scroll analytics data
    """
    try:
        url = f"{api_base_url}/v1/heatmap/analytics/scroll"

        headers = {
            "BEU-API-Key": os.getenv("BEU_API_KEY", ""),
            "Content-Type": "application/json"
        }

        payload = {
            "aid": aid,
            "device": device,
            "event": event,
            "startDate": start_date,
            "endDate": end_date
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            return json.dumps({
                "status": "success",
                "data": response.json(),
                "request_params": payload
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "status_code": response.status_code,
                "error_message": response.text,
                "request_params": payload
            }, ensure_ascii=False, indent=2)

    except requests.exceptions.RequestException as e:
        return json.dumps({
            "status": "error",
            "error_type": "request_exception",
            "error_message": str(e),
            "request_params": payload
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_type": "unexpected_error",
            "error_message": str(e)
        })


@mcp.prompt()
def analyze_scroll_behavior(analytics_data: str) -> str:
    """
    Analyze scroll behavior from analytics data and provide insights

    Args:
        analytics_data: JSON string containing scroll analytics data

    Returns:
        Analysis prompt for understanding user scroll patterns
    """
    return f"""
    Please analyze the following scroll analytics data and provide insights:
    
    {analytics_data}
    
    Focus on:
    1. User engagement patterns
    2. Content areas with high/low interaction
    3. Device-specific behavior differences
    4. Time-based trends
    5. Recommendations for UI/UX improvements
    
    Provide actionable insights for improving user experience.
    """


@mcp.tool()
def get_post_statistics(
        ctx: Context,
        start_date: str,
        end_date: str,
        group_by: str = "date"
) -> str:
    """
    고객문의 통계를 조회합니다.

    Args:
        ctx: Context
        start_date: 시작일자 (YYYY-MM-DD 형식)
        end_date: 종료일자 (YYYY-MM-DD 형식)
        group_by: 그룹화 기준 ("date", "category", "author")

    Returns:
        JSON 형식의 통계 결과
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get company_key based on environment
        if IS_DEBUG:
            company_key = os.getenv('COMPANY_KEY', 'default-company')
        else:
            company_key = ctx.request_context.request.user.username

        base_query = """
            SELECT COUNT(*) as count
            FROM post
            WHERE company_key = %s AND reg_date >= %s AND reg_date <= %s
        """
        params = [company_key, f"{start_date} 00:00:00", f"{end_date} 23:59:59"]

        # 그룹별 통계 쿼리
        if group_by == "date":
            query = """
                SELECT 
                    DATE(reg_date) as date,
                    COUNT(*) as count
                FROM post
                WHERE company_key = %s AND reg_date >= %s AND reg_date <= %s
                GROUP BY DATE(reg_date)
                ORDER BY date
            """
        elif group_by == "category":
            query = """
                SELECT 
                    post_category_id,
                    COUNT(*) as count
                FROM post
                WHERE company_key = %s AND reg_date >= %s AND reg_date <= %s
                AND post_category_id IS NOT NULL
                GROUP BY post_category_id
                ORDER BY count DESC
            """
        elif group_by == "author":
            query = """
                SELECT 
                    author,
                    COUNT(*) as count
                FROM post
                WHERE company_key = %s AND reg_date >= %s AND reg_date <= %s
                AND author IS NOT NULL
                GROUP BY author
                ORDER BY count DESC
                LIMIT 20
            """
        else:
            query = base_query

        cursor.execute(query, params)
        results = cursor.fetchall()

        # 날짜 형식 변환
        if group_by == "date":
            for result in results:
                if result['date']:
                    result['date'] = result['date'].strftime('%Y-%m-%d')

        # 전체 건수 조회
        cursor.execute(base_query, params)
        total_count = cursor.fetchone()['count']

        # 가장 많이 사용된 키워드 분석 (제목 기준)
        keyword_query = """
            SELECT title
            FROM post
            WHERE company_key = %s AND reg_date >= %s AND reg_date <= %s
            AND title IS NOT NULL
            LIMIT 1000
        """
        cursor.execute(keyword_query, params)
        titles = cursor.fetchall()

        # 간단한 키워드 빈도 분석
        word_count = {}
        for title in titles:
            words = title['title'].split()
            for word in words:
                if len(word) > 2:  # 2글자 이상만
                    word_count[word] = word_count.get(word, 0) + 1

        top_keywords = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:10]

        return json.dumps({
            "status": "success",
            "total_count": total_count,
            "statistics": results,
            "top_keywords": [{"keyword": k, "count": v} for k, v in top_keywords],
            "query_params": {
                "start_date": start_date,
                "end_date": end_date,
                "group_by": group_by
            }
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, ensure_ascii=False, indent=2)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@mcp.tool()
def query_customer_emails(
        ctx: Context,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        from_mail: Optional[str] = None,
        status: Optional[str] = None,
        search_keyword: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        order_by: str = "received_at DESC"
) -> str:
    """
    고객문의 이메일을 조회합니다. context가 지나치게 커지지 않도록 적당한 limit으로 조회하고 필요하면 반복작업 할 수 있도록 도와주세요.
    limit이 0이더라도 전체 count 값을 같이 return 합니다.

    Args:
        ctx: Context
        start_date: 시작일자 (YYYY-MM-DD 형식)
        end_date: 종료일자 (YYYY-MM-DD 형식)
        from_mail: 발신자 이메일
        status: 처리상태
        search_keyword: 제목/내용 검색 키워드
        limit: 조회할 최대 건수 (기본: 10)
        offset: 조회 시작 위치 (기본: 0)
        order_by: 정렬 기준 (기본: "received_at DESC")

    Returns:
        JSON 형식의 조회 결과
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get company_key based on environment
        if IS_DEBUG:
            company_key = os.getenv('COMPANY_KEY', 'default-company')
        else:
            company_key = ctx.request_context.request.user.username

        # 기본 쿼리
        query = """
            SELECT 
                id,
                subject,
                from_mail,
                from_name,
                to_mail,
                to_name,
                received_at,
                processed_at,
                status,
                created_at,
                company,
                keyword,
                last_content,
                comment
            FROM cx_email
            WHERE company_key = %s
        """
        params = [company_key]

        # 날짜 필터
        if start_date:
            query += " AND received_at >= %s"
            params.append(f"{start_date} 00:00:00")

        if end_date:
            query += " AND received_at <= %s"
            params.append(f"{end_date} 23:59:59")

        # 발신자 이메일 필터
        if from_mail:
            query += " AND from_mail = %s"
            params.append(from_mail)

        # 상태 필터
        if status:
            query += " AND status = %s"
            params.append(status)

        # 키워드 검색
        if search_keyword:
            query += " AND (subject LIKE %s OR content LIKE %s)"
            keyword_param = f"%{search_keyword}%"
            params.extend([keyword_param, keyword_param])

        # 정렬 및 페이징
        query += f" ORDER BY {order_by} LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        emails = cursor.fetchall()

        # 전체 건수 조회
        count_query = """
            SELECT COUNT(*) as total
            FROM cx_email
            WHERE company_key = %s
        """
        count_params = [company_key]

        if start_date:
            count_query += " AND received_at >= %s"
            count_params.append(f"{start_date} 00:00:00")

        if end_date:
            count_query += " AND received_at <= %s"
            count_params.append(f"{end_date} 23:59:59")

        if from_mail:
            count_query += " AND from_mail = %s"
            count_params.append(from_mail)

        if status:
            count_query += " AND status = %s"
            count_params.append(status)

        if search_keyword:
            count_query += " AND (subject LIKE %s OR content LIKE %s)"
            count_params.extend([keyword_param, keyword_param])

        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()['total']

        # 날짜 형식 변환
        for email in emails:
            if email['received_at']:
                email['received_at'] = email['received_at'].strftime('%Y-%m-%d %H:%M:%S')
            if email['processed_at']:
                email['processed_at'] = email['processed_at'].strftime('%Y-%m-%d %H:%M:%S')
            if email['created_at']:
                email['created_at'] = email['created_at'].strftime('%Y-%m-%d %H:%M:%S')

        return json.dumps({
            "status": "success",
            "total_count": total_count,
            "returned_count": len(emails),
            "emails": emails,
            "query_params": {
                "start_date": start_date,
                "end_date": end_date,
                "from_mail": from_mail,
                "status": status,
                "search_keyword": search_keyword,
                "limit": limit,
                "offset": offset
            }
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, ensure_ascii=False, indent=2)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@mcp.tool()
def get_email_statistics(
        ctx: Context,
        start_date: str,
        end_date: str,
        group_by: str = "date"
) -> str:
    """
    고객문의 이메일 통계를 조회합니다.

    Args:
        ctx: Context
        start_date: 시작일자 (YYYY-MM-DD 형식)
        end_date: 종료일자 (YYYY-MM-DD 형식)
        group_by: 그룹화 기준 ("date", "status", "company")

    Returns:
        JSON 형식의 통계 결과
    """

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get company_key based on environment
        if IS_DEBUG:
            company_key = os.getenv('COMPANY_KEY', 'default-company')
        else:
            company_key = ctx.request_context.request.user.username
        print(f"get_email_statistics query : {start_date}, {end_date}, {group_by}, {company_key}")

        base_query = """
            SELECT COUNT(*) as count
            FROM cx_email
            WHERE company_key = %s AND received_at >= %s AND received_at <= %s
        """
        params = [company_key, f"{start_date} 00:00:00", f"{end_date} 23:59:59"]

        # 그룹별 통계 쿼리
        if group_by == "date":
            query = """
                SELECT 
                    DATE(received_at) as date,
                    COUNT(*) as count
                FROM cx_email
                WHERE company_key = %s AND received_at >= %s AND received_at <= %s
                GROUP BY DATE(received_at)
                ORDER BY date
            """
        elif group_by == "status":
            query = """
                SELECT 
                    status,
                    COUNT(*) as count
                FROM cx_email
                WHERE company_key = %s AND received_at >= %s AND received_at <= %s
                AND status IS NOT NULL
                GROUP BY status
                ORDER BY count DESC
            """
        elif group_by == "company":
            query = """
                SELECT 
                    company,
                    COUNT(*) as count
                FROM cx_email
                WHERE company_key = %s AND received_at >= %s AND received_at <= %s
                AND from_mail IS NOT NULL
                GROUP BY domain
                ORDER BY count DESC
                LIMIT 20
            """
        else:
            query = base_query

        cursor.execute(query, params)
        results = cursor.fetchall()

        # 날짜 형식 변환
        if group_by == "date":
            for result in results:
                if result['date']:
                    result['date'] = result['date'].strftime('%Y-%m-%d')

        # 전체 건수 조회
        cursor.execute(base_query, params)
        total_count = cursor.fetchone()['count']

        # 응답률 분석
        response_rate_query = """
            SELECT 
                CAST(SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as unsigned) as processed_count,
                CAST(SUM(CASE WHEN answering_content IS NOT NULL AND answering_content != '' THEN 1 ELSE 0 END) as unsigned)  as answered_count,
                COUNT(*) as total_count
            FROM cx_email
            WHERE company_key = %s AND received_at >= %s AND received_at <= %s
        """
        cursor.execute(response_rate_query, params)
        response_stats = cursor.fetchone()
        print(f"get_email_statistics response : {response_stats}")

        return json.dumps({
            "status": "success",
            "total_count": total_count,
            "statistics": results,
            "response_analysis": {
                "processed_rate": round(response_stats['processed_count'] / response_stats['total_count'] * 100, 2) if
                response_stats['total_count'] > 0 else 0,
                "answer_rate": round(response_stats['answered_count'] / response_stats['total_count'] * 100, 2) if
                response_stats['total_count'] > 0 else 0,
                "processed_count": response_stats['processed_count'],
                "answered_count": response_stats['answered_count']
            },
            "query_params": {
                "start_date": start_date,
                "end_date": end_date,
                "group_by": group_by
            }
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, ensure_ascii=False, indent=2)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@mcp.tool()
def analyze_email_response_time(
        ctx: Context,
        start_date: str,
        end_date: str,
        manager: Optional[str] = None
) -> str:
    """
    이메일 응답시간 분석

    Args:
        ctx: Context
        start_date: 시작일자 (YYYY-MM-DD 형식)
        end_date: 종료일자 (YYYY-MM-DD 형식)
        manager: 담당자 (선택사항)

    Returns:
        JSON 형식의 응답시간 분석 결과
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get company_key based on environment
        if IS_DEBUG:
            company_key = os.getenv('COMPANY_KEY', 'default-company')
        else:
            company_key = ctx.request_context.request.user.username

        # 응답시간 분석 쿼리
        query = """
            SELECT 
                AVG(TIMESTAMPDIFF(HOUR, received_at, processed_at)) as avg_response_hours,
                MIN(TIMESTAMPDIFF(HOUR, received_at, processed_at)) as min_response_hours,
                MAX(TIMESTAMPDIFF(HOUR, received_at, processed_at)) as max_response_hours,
                COUNT(*) as total_processed,
                SUM(CASE WHEN TIMESTAMPDIFF(HOUR, received_at, processed_at) <= 24 THEN 1 ELSE 0 END) as within_24h,
                SUM(CASE WHEN TIMESTAMPDIFF(HOUR, received_at, processed_at) <= 48 THEN 1 ELSE 0 END) as within_48h
            FROM cx_email
            WHERE company_key = %s
            AND received_at >= %s AND received_at <= %s
            AND processed_at IS NOT NULL
            AND processed_at > received_at
        """

        params = [company_key, f"{start_date} 00:00:00", f"{end_date} 23:59:59"]

        if manager:
            query += " AND manager = %s"
            params.append(manager)

        cursor.execute(query, params)
        response_stats = cursor.fetchone()

        # 미처리 건수
        unprocessed_query = """
            SELECT COUNT(*) as unprocessed_count
            FROM cx_email
            WHERE company_key = %s
            AND received_at >= %s AND received_at <= %s
            AND (processed_at IS NULL OR status != 'processed')
        """
        unprocessed_params = [company_key, f"{start_date} 00:00:00", f"{end_date} 23:59:59"]
        if manager:
            unprocessed_query += " AND manager = %s"
            unprocessed_params.append(manager)

        cursor.execute(unprocessed_query, unprocessed_params)
        unprocessed = cursor.fetchone()

        # 담당자별 응답시간
        if not manager:
            manager_response_query = """
                SELECT 
                    manager,
                    AVG(TIMESTAMPDIFF(HOUR, received_at, processed_at)) as avg_response_hours,
                    COUNT(*) as count
                FROM cx_email
                WHERE company_key = %s
                AND received_at >= %s AND received_at <= %s
                AND processed_at IS NOT NULL
                AND processed_at > received_at
                AND manager IS NOT NULL
                GROUP BY manager
                ORDER BY avg_response_hours ASC
            """
            cursor.execute(manager_response_query, [company_key, f"{start_date} 00:00:00", f"{end_date} 23:59:59"])
            manager_response = cursor.fetchall()
        else:
            manager_response = []

        return json.dumps({
            "status": "success",
            "response_time_stats": {
                "average_hours": round(response_stats['avg_response_hours'], 2) if response_stats[
                    'avg_response_hours'] else 0,
                "min_hours": response_stats['min_response_hours'],
                "max_hours": response_stats['max_response_hours'],
                "total_processed": response_stats['total_processed'],
                "response_rate_24h": round(response_stats['within_24h'] / response_stats['total_processed'] * 100, 2) if
                response_stats['total_processed'] > 0 else 0,
                "response_rate_48h": round(response_stats['within_48h'] / response_stats['total_processed'] * 100, 2) if
                response_stats['total_processed'] > 0 else 0
            },
            "unprocessed_count": unprocessed['unprocessed_count'],
            "manager_response_times": manager_response,
            "analysis_period": {
                "start_date": start_date,
                "end_date": end_date,
                "manager": manager
            }
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        }, ensure_ascii=False, indent=2)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


@mcp.tool()
def publish_wordpress_post(
        title: str,
        content: str,
        status: str = "publish",
        categories: Optional[str] = None,
        tags: Optional[str] = None
) -> str:
    """
    워드프레스에 글을 배포합니다.

    Args:
        title: 글 제목
        content: 글 내용 (HTML 가능)
        status: 글 상태 (publish, draft, private)
        categories: 카테고리 리스트 (쉼표로 구분)
        tags: 태그 리스트 (쉼표로 구분)

    Returns:
        JSON 형식의 배포 결과
    """
    try:
        # 환경변수에서 워드프레스 설정 가져오기
        wp_url = os.getenv('WORDPRESS_URL', None)
        wp_username = os.getenv('WORDPRESS_USERNAME', None)
        wp_password = os.getenv('WORDPRESS_PASSWORD', None)

        if not wp_url or not wp_username or not wp_password:
            return json.dumps({
                "status": "error",
                "error_message": "워드프레스 연결 정보가 없습니다. WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_PASSWORD 환경변수를 설정하거나 파라미터로 직접 전달해주세요."
            }, ensure_ascii=False, indent=2)

        # WordPress REST API 엔드포인트
        api_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"

        # Basic Auth 헤더 생성
        credentials = f"{wp_username}:{wp_password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode('utf-8')

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }

        # 포스트 데이터 준비
        post_data = {
            "title": title,
            "content": content,
            "status": status
        }

        # 카테고리 처리 (먼저 카테고리 목록을 가져와서 매핑)
        if categories:
            category_names = [cat.strip() for cat in categories.split(',')]
            category_ids = []

            # 기존 카테고리 가져오기
            categories_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/categories?per_page=100"
            cat_response = requests.get(categories_url, headers=headers, timeout=30)

            if cat_response.status_code == 200:
                existing_categories = cat_response.json()
                existing_cat_map = {cat['name'].lower(): cat['id'] for cat in existing_categories}

                for cat_name in category_names:
                    if cat_name.lower() in existing_cat_map:
                        category_ids.append(existing_cat_map[cat_name.lower()])
                    else:
                        # 새 카테고리 생성
                        new_cat_data = {"name": cat_name}
                        new_cat_response = requests.post(categories_url,
                                                         json=new_cat_data,
                                                         headers=headers,
                                                         timeout=30)
                        if new_cat_response.status_code == 201:
                            category_ids.append(new_cat_response.json()['id'])

                if category_ids:
                    post_data["categories"] = category_ids

        # 태그 처리
        if tags:
            tag_names = [tag.strip() for tag in tags.split(',')]
            tag_ids = []

            # 기존 태그 가져오기
            tags_url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/tags?per_page=100"
            tag_response = requests.get(tags_url, headers=headers, timeout=30)

            if tag_response.status_code == 200:
                existing_tags = tag_response.json()
                existing_tag_map = {tag['name'].lower(): tag['id'] for tag in existing_tags}

                for tag_name in tag_names:
                    if tag_name.lower() in existing_tag_map:
                        tag_ids.append(existing_tag_map[tag_name.lower()])
                    else:
                        # 새 태그 생성
                        new_tag_data = {"name": tag_name}
                        new_tag_response = requests.post(tags_url,
                                                         json=new_tag_data,
                                                         headers=headers,
                                                         timeout=30)
                        if new_tag_response.status_code == 201:
                            tag_ids.append(new_tag_response.json()['id'])

                if tag_ids:
                    post_data["tags"] = tag_ids

        # 포스트 생성
        response = requests.post(api_url, json=post_data, headers=headers, timeout=30)

        if response.status_code == 201:
            post_info = response.json()
            return json.dumps({
                "status": "success",
                "message": "포스트가 성공적으로 배포되었습니다.",
                "post_info": {
                    "id": post_info.get("id"),
                    "title": post_info.get("title", {}).get("rendered"),
                    "url": post_info.get("link"),
                    "status": post_info.get("status"),
                    "date": post_info.get("date"),
                    "categories": post_info.get("categories", []),
                    "tags": post_info.get("tags", [])
                },
                "wordpress_url": wp_url
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "status_code": response.status_code,
                "error_message": response.text,
                "post_data": post_data,
                "wordpress_url": wp_url
            }, ensure_ascii=False, indent=2)

    except requests.exceptions.RequestException as e:
        return json.dumps({
            "status": "error",
            "error_type": "request_exception",
            "error_message": str(e)
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_type": "unexpected_error",
            "error_message": str(e)
        })


@mcp.tool()
def publish_to_facebook(
        message: str,
        link: Optional[str] = None,
        page_id: Optional[str] = None,
        access_token: Optional[str] = None
) -> str:
    """
    Facebook 페이지에 글을 배포합니다.

    Args:
        message: 게시할 메시지
        link: 공유할 링크 (선택사항)
        page_id: Facebook 페이지 ID (환경변수 우선)
        access_token: 페이지 액세스 토큰 (환경변수 우선)

    Returns:
        JSON 형식의 배포 결과
    """
    try:
        # 환경변수에서 Facebook 설정 가져오기
        fb_page_id = page_id or os.getenv('FACEBOOK_PAGE_ID')
        fb_access_token = access_token or os.getenv('FACEBOOK_ACCESS_TOKEN')

        if not fb_page_id or not fb_access_token:
            return json.dumps({
                "status": "error",
                "error_message": "Facebook 연결 정보가 없습니다. FACEBOOK_PAGE_ID, FACEBOOK_ACCESS_TOKEN 환경변수를 설정해주세요."
            }, ensure_ascii=False, indent=2)

        # Facebook Graph API 엔드포인트
        api_url = f"https://graph.facebook.com/v18.0/{fb_page_id}/feed"

        # 포스트 데이터 준비
        post_data = {
            "message": message,
            "access_token": fb_access_token
        }

        if link:
            post_data["link"] = link

        response = requests.post(api_url, data=post_data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            return json.dumps({
                "status": "success",
                "message": "Facebook에 포스트가 성공적으로 배포되었습니다.",
                "post_info": {
                    "id": result.get("id"),
                    "platform": "facebook"
                }
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "status_code": response.status_code,
                "error_message": response.text
            }, ensure_ascii=False, indent=2)

    except requests.exceptions.RequestException as e:
        return json.dumps({
            "status": "error",
            "error_type": "request_exception",
            "error_message": str(e)
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_type": "unexpected_error",
            "error_message": str(e)
        })


@mcp.tool()
def publish_to_threads(
        text: str,
        access_token: Optional[str] = None,
) -> str:
    """
    Threads(쓰레드)에 글을 배포합니다.

    Args:
        text: 글 내용 (500자 제한)
        access_token: Access Token (환경변수 우선)

    Returns:
        JSON 형식의 배포 결과
    """
    try:
        # 환경변수에서 Threads 설정 가져오기
        th_access_token = access_token or os.getenv('THREADS_ACCESS_TOKEN')
        print(th_access_token)
        if not th_access_token:
            return json.dumps({
                "status": "error",
                "error_message": "Threads 연결 정보가 없습니다. THREADS_ACCESS_TOKEN 환경변수를 설정해주세요."
            }, ensure_ascii=False, indent=2)

        # Threads API  엔드포인트
        api_url = "https://graph.threads.net/v1.0"

        threads_user_id = "24676979681970771"

        encoded = quote(text, safe="")
        print(encoded)
        get_container_url = f"{api_url}/{threads_user_id}/threads?media_type=TEXT&text={encoded}&access_token={th_access_token}"

        container_response = requests.post(get_container_url, timeout=30)

        if container_response.status_code == 200:
            container_id = container_response.json().get('id')
            publish_url = f"{api_url}/{threads_user_id}/threads_publish?creation_id={container_id}&access_token={th_access_token}"
            publish_response = requests.post(publish_url, timeout=30)
            if publish_response.status_code == 200:
                return json.dumps({
                    "status": "success",
                    "message": "Threads에 글이 성공적으로 배포되었습니다.",
                    "post_info": {
                        "text": publish_response.json(),
                    }
                }, ensure_ascii=False, indent=2)
            else:
                return json.dumps({
                    "status": "error",
                    "status_code": publish_response.status_code,
                    "error_message": publish_response.json()
                }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "status_code": container_response.status_code,
                "error_message": container_response.json()
            }, ensure_ascii=False, indent=2)

    except requests.exceptions.RequestException as e:
        return json.dumps({
            "status": "error",
            "error_type": "request_exception",
            "error_message": str(e)
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_type": "unexpected_error",
            "error_message": str(e)
        })


# @mcp.tool()
# def publish_to_twitter(
#         text: str,
#         media_urls: Optional[str] = None,
#         bearer_token: Optional[str] = None,
#         api_key: Optional[str] = None,
#         api_secret: Optional[str] = None,
#         access_token: Optional[str] = None,
#         access_token_secret: Optional[str] = None
# ) -> str:
#     """
#     X(구 Twitter)에 트윗을 배포합니다. 140자 제한이 있으니 명심하도록 해.
#
#     Args:
#         text: 트윗 내용 (140자 제한)
#         media_urls: 미디어 URL 목록 (쉼표로 구분, 선택사항)
#         bearer_token: Bearer Token (환경변수 우선)
#         api_key: API Key (환경변수 우선)
#         api_secret: API Secret (환경변수 우선)
#         access_token: Access Token (환경변수 우선)
#         access_token_secret: Access Token Secret (환경변수 우선)
#
#     Returns:
#         JSON 형식의 배포 결과
#     """
#     try:
#         # 환경변수에서 Twitter 설정 가져오기
#         tw_bearer_token = bearer_token or os.getenv('TWITTER_BEARER_TOKEN')
#         tw_api_key = api_key or os.getenv('TWITTER_API_KEY')
#         tw_api_secret = api_secret or os.getenv('TWITTER_API_SECRET')
#         tw_access_token = access_token or os.getenv('TWITTER_ACCESS_TOKEN')
#         tw_access_token_secret = access_token_secret or os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
#
#         if not tw_bearer_token:
#             return json.dumps({
#                 "status": "error",
#                 "error_message": "Twitter 연결 정보가 없습니다. TWITTER_BEARER_TOKEN 환경변수를 설정해주세요."
#             }, ensure_ascii=False, indent=2)
#
#         tw_client = tweepy.Client(
#             access_token=tw_access_token,
#             access_token_secret=tw_access_token_secret,
#             consumer_key=tw_api_key,
#             consumer_secret=tw_api_secret,
#             bearer_token=tw_bearer_token
#         )
#
#
#         result = tw_client.create_tweet(text=text[:140])
#
#         if result and result.data:
#             return json.dumps({
#                 "status": "success",
#                 "message": "X(Twitter)에 트윗이 성공적으로 배포되었습니다."
#             }, ensure_ascii=False, indent=2)
#         else:
#             return json.dumps({
#                 "status": "error",
#                 "error_message": result.errors
#             }, ensure_ascii=False, indent=2)
#
#     except requests.exceptions.RequestException as e:
#         return json.dumps({
#             "status": "error",
#             "error_type": "request_exception",
#             "error_message": str(e)
#         })
#     except Exception as e:
#         return json.dumps({
#             "status": "error",
#             "error_type": "unexpected_error",
#             "error_message": str(e)
#         })


@mcp.tool()
def publish_to_linkedin(
        text: str,
        link_url: Optional[str] = None,
        link_title: Optional[str] = None,
        link_description: Optional[str] = None,
        access_token: Optional[str] = None,
        person_id: Optional[str] = None
) -> str:
    """
    LinkedIn에 글을 배포합니다.

    Args:
        text: 게시할 내용
        link_url: 공유할 링크 URL (선택사항)
        link_title: 링크 제목 (선택사항)
        link_description: 링크 설명 (선택사항)
        access_token: LinkedIn Access Token (환경변수 우선)
        person_id: LinkedIn Person ID (환경변수 우선)

    Returns:
        JSON 형식의 배포 결과
    """
    try:
        # 환경변수에서 LinkedIn 설정 가져오기
        li_access_token = access_token or os.getenv('LINKEDIN_ACCESS_TOKEN')
        li_person_id = person_id or os.getenv('LINKEDIN_PERSON_ID')

        if not li_access_token or not li_person_id:
            return json.dumps({
                "status": "error",
                "error_message": "LinkedIn 연결 정보가 없습니다. LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_ID 환경변수를 설정해주세요."
            }, ensure_ascii=False, indent=2)

        # LinkedIn API v2 엔드포인트
        api_url = "https://api.linkedin.com/v2/ugcPosts"

        headers = {
            "Authorization": f"Bearer {li_access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

        # 포스트 데이터 준비
        post_data = {
            "author": f"urn:li:person:{li_person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        # 링크가 있는 경우 미디어 추가
        if link_url:
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
            post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [{
                "status": "READY",
                "description": {
                    "text": link_description or ""
                },
                "originalUrl": link_url,
                "title": {
                    "text": link_title or ""
                }
            }]

        response = requests.post(api_url, json=post_data, headers=headers, timeout=30)

        if response.status_code == 201:
            result = response.json()
            return json.dumps({
                "status": "success",
                "message": "LinkedIn에 포스트가 성공적으로 배포되었습니다.",
                "post_info": {
                    "id": result.get("id"),
                    "platform": "linkedin"
                }
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "status_code": response.status_code,
                "error_message": response.text
            }, ensure_ascii=False, indent=2)

    except requests.exceptions.RequestException as e:
        return json.dumps({
            "status": "error",
            "error_type": "request_exception",
            "error_message": str(e)
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_type": "unexpected_error",
            "error_message": str(e)
        })


@mcp.tool()
def publish_to_multiple_sns(
        title: str,
        content: str,
        platforms: str = "facebook,twitter,linkedin",
        hashtags: Optional[str] = None,
        link_url: Optional[str] = None
) -> str:
    """
    여러 SNS 플랫폼에 동시에 글을 배포합니다.

    Args:
        title: 글 제목
        content: 글 내용
        platforms: 배포할 플랫폼 목록 (쉼표로 구분, 예: "facebook,twitter,linkedin")
        hashtags: 해시태그 (쉼표로 구분, 선택사항)
        link_url: 공유할 링크 (선택사항)

    Returns:
        JSON 형식의 배포 결과
    """
    try:
        platform_list = [p.strip().lower() for p in platforms.split(',')]
        results = {}

        # 플랫폼별 최적화된 메시지 생성
        full_content = f"{title}\n\n{content}"
        if hashtags:
            full_content += f"\n\n{hashtags}"

        # Facebook 배포
        if "facebook" in platform_list:
            fb_message = full_content
            fb_result = json.loads(publish_to_facebook(fb_message, link_url))
            results["facebook"] = fb_result

        # Twitter 배포 (280자 제한)
        if "twitter" in platform_list:
            twitter_text = full_content
            if len(twitter_text) > 250:  # 링크 공간 확보
                twitter_text = twitter_text[:247] + "..."
            if link_url:
                twitter_text += f" {link_url}"

            tw_result = json.loads(publish_to_twitter(twitter_text))
            results["twitter"] = tw_result

        # LinkedIn 배포
        if "linkedin" in platform_list:
            li_result = json.loads(publish_to_linkedin(
                full_content,
                link_url,
                title,
                content[:200] + "..." if len(content) > 200 else content
            ))
            results["linkedin"] = li_result

        # 결과 요약
        successful_platforms = []
        failed_platforms = []

        for platform, result in results.items():
            if result.get("status") == "success":
                successful_platforms.append(platform)
            else:
                failed_platforms.append(platform)

        return json.dumps({
            "status": "success" if successful_platforms else "error",
            "message": f"{len(successful_platforms)}개 플랫폼에 배포 완료",
            "successful_platforms": successful_platforms,
            "failed_platforms": failed_platforms,
            "detailed_results": results
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_type": "unexpected_error",
            "error_message": str(e)
        })


@mcp.tool()
def test_tool(message: str = "Hello") -> str:
    """
    테스트용 tool입니다. 의미 없는 응답을 반환합니다.

    Args:
        message: 테스트 메시지 (기본값: "Hello")

    Returns:
        의미 없는 테스트 응답
    """
    return json.dumps({
        "status": "success",
        "message": f"Test response for: {message}",
        "random_data": {
            "items": ["abcde"] * 1000
        }
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def query_prescription_data(
        ctx: Context,
        sql_query: str,
        limit: int = 10
) -> str:
    """
    처방전 데이터베이스에 대해 원하는 Clickhouse SQL 쿼리를 실행합니다.
    이 도구는 의료기관의 처방전 정보를 조회할 수 있습니다.
    지나치게 큰 결과가 나오지 않도록 최대 Limit 이 200으로 설정되어있다는 점을 유념하세요.
    그래서 결과가 200 row에 도달한다면 더 작은 단위나 작은 결과를 낼 수 있도록 다시 시도하세요.

    테이블 필드 DDL 및 설명

    create table POC_REAL
    (
    `대지역`         String, # 처방이 발생한 광역 지역 (예: 서울특별시, 강원도)
    `Business No` String, # 미사용
    `처방년도`        Int32, # 처방 발생 연도 (YYYY)
    `처방일자`        Int32, # 처방 발생 년월 (YYYYMM)
    `종별`          String, # 의료기관 종류 (병원, 의원, 약국 등)
    `요양기관명`       String, # 의료기관 이름
    Ephmra        String, # EphMRA 분류 코드 (국제 의약품 분류 체계)
    Originalinfo  String, # 오리지널/제네릭 구분 (Original, Generic 등)
    `단위`          String, # 제형 단위 (정, 캡슐 등)
    `진료과`         String, # 진료 과목 (내과, 정신건강의학과 등)
    `성별`          String, # 환자 성별 (남자, 여자)
    `브랜드명`        String, # 환자 연령대 (0~9, 20~29, 90~99, 기타 등)
    `주성분코드`       String, # 신환/재환 구분
    `성분명`         String, # 상품명
    `성분명 상세`      String, # 주성분 표준 코드
    `신재환구분`       String, # 주성분명
    `약품코드`        Int32, # 성분명 및 함량 상세
    `의약품명`        String, # 약품 표준 코드
    `약가`          Int32, # 의약품 정식 명칭
    `제조사`         String, # 단위당 약가 (원)
    `판매사`         String, # 제조업체
    `제형`          String, # 판매업체
    `투여경로`        String, # 제형 분류 (정제/저작정, 서방캡슐제 등)
    `연령대`         String, # 투여 방법 (내복제 등)
    `처방금액`        Int32, # 총 처방 금액 (원)
    `처방건수`        Int32, # 처방 건수
    `처방량`         Float64 # 처방된 총 수량
    )
    engine = MergeTree ORDER BY (`처방년도`, `처방일자`)

    Sample Row:
    강원도,,2025,202501,병원,서울아산병원,A5A2,Original,정,"",남자,우루사 정,246501ATB,ursodeoxycholic acid,ursodeoxycholic acid 100㎎,신환,641602040,우루사 정 100mg,90,(주)대웅제약,(주)대웅제약,"정제, 저작정",내복제,50~59,18900,210,1
    강원도,,2025,202501,병원,국군춘천병원,N6A5,Original,캡슐,"",남자,이팩사 엑스알 서방캡슐,247502ACR,venlafaxine hydrochloride,venlafaxine hydrochloride 84.85㎎ (75㎎ as venlafaxine),신환,73400030,이팩사 엑스알 서방캡슐 75mg,706,비아트리스코리아(주),비아트리스코리아(주),서방캡슐제,내복제,20~29,44478,63,1



    쿼리 예시:
    - SELECT `처방일자`, sum(`처방금액`) as `총처방금액`, sum(`처방건수`) as `총처방건수`, sum(`처방량`) as `총처방량` FROM POC_REAL WHERE `처방년도` = 2025 GROUP BY `처방일자` ORDER BY `처방일자`
    - SELECT `제조사`, count(DISTINCT `의약품명`) as `제품수`, sum(`처방금액`) as `총매출`, sum(`처방건수`) as `총처방건수`, round(avg(`약가`), 2) as `평균약가` FROM POC_REAL WHERE `처방년도` = 2025 GROUP BY `제조사` ORDER BY sum(`처방금액`) DESC LIMIT 10

    Args:
        ctx: Context
        sql_query: 실행할 SQL 쿼리 (SELECT 문만 허용)
        limit: 최대 결과 건수 (기본: 10, 최대: 200)

    Returns:
        JSON 형식의 쿼리 결과
    """
    # 입력 로그 출력
    print(f"[query_prescription_data] INPUT - sql_query: {sql_query}, limit: {limit}")

    try:
        # 보안: 조회 쿼리만 허용 (SELECT, WITH 등)
        query_upper = sql_query.strip().upper()
        # UPDATE, DELETE, DROP, TRUNCATE, ALTER, INSERT 등 데이터 변경 쿼리 차단
        forbidden_keywords = ['UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 'ALTER', 'INSERT', 'CREATE']
        for keyword in forbidden_keywords:
            if keyword in query_upper:
                error_result = json.dumps({
                    "status": "error",
                    "error": f"보안상의 이유로 {keyword} 쿼리는 허용되지 않습니다. 조회(SELECT, WITH) 쿼리만 사용 가능합니다."
                }, ensure_ascii=False, indent=2)
                print(f"[query_prescription_data] OUTPUT - Error: Forbidden keyword {keyword}")
                return error_result

        # Limit 검증
        if limit > 200:
            limit = 200

        # 시작 시간 기록
        import time
        start_time = time.time()

        client = get_clickhouse_connection()

        # Get company_key based on environment
        if IS_DEBUG:
            company_key = os.getenv('COMPANY_KEY', 'default-company')
        else:
            company_key = ctx.request_context.request.user.username

        # LIMIT이 쿼리에 없으면 자동으로 추가
        # if 'LIMIT' not in query_upper:
        #     sql_query = f"{sql_query.rstrip(';')} LIMIT {limit}"

        # 쿼리 실행 (ClickHouse 드라이버는 튜플 리스트를 반환하므로 with_column_types=True 사용)
        results, columns = client.execute(sql_query, with_column_types=True)

        # 종료 시간 기록
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 3)

        # 컬럼명 추출
        column_names = [col[0] for col in columns]

        # 결과를 딕셔너리 리스트로 변환
        formatted_results = []
        for row in results:
            row_dict = {}
            for idx, col_name in enumerate(column_names):
                value = row[idx]
                # 날짜/시간/Decimal 타입 변환
                if isinstance(value, datetime):
                    row_dict[col_name] = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, Decimal):
                    row_dict[col_name] = float(value)
                else:
                    row_dict[col_name] = value
            formatted_results.append(row_dict)

        result_json = json.dumps({
            "status": "success",
            "row_count": len(formatted_results),
            "elapsed_time_sec": elapsed_time,
            "data": formatted_results
        }, ensure_ascii=False, indent=2)

        # 출력 로그 (데이터 일부만 출력)
        print(f"[query_prescription_data] OUTPUT - status: success, elapsed_time: {elapsed_time}s")
        return result_json

    except Exception as e:
        error_result = json.dumps({
            "status": "error",
            "error": str(e),
            "query": sql_query
        }, ensure_ascii=False, indent=2)
        print(f"[query_prescription_data] OUTPUT - Error: {str(e)}")
        return error_result
    finally:
        if 'client' in locals():
            client.disconnect()


@mcp.prompt()
def analyze_customer_inquiries(query_results: str) -> str:
    """
    고객문의 조회 결과를 분석하여 인사이트를 제공합니다.

    Args:
        query_results: 고객문의 조회 결과 JSON

    Returns:
        분석 프롬프트
    """
    return f"""
    다음 고객문의 데이터를 분석하여 주요 인사이트를 제공해주세요:

    {query_results}

    다음 관점에서 분석해주세요:
    1. 주요 문의 유형 및 트렌드
    2. 시간대별/날짜별 문의 패턴
    3. 자주 나타나는 키워드와 문제점
    4. 카테고리별 분포 및 특징
    5. 고객 서비스 개선을 위한 제안사항

    구체적이고 실행 가능한 인사이트를 제공해주세요.
    """

@mcp.tool()
async def geo_analyze_page(url: str, wait_for_selector: Optional[str] = None, timeout: int = 30000) -> dict:
    """
    Analyze webpage content and structure using Playwright.

    Args:
        url: Full URL of the webpage to analyze
        wait_for_selector: Optional CSS selector to wait for before analyzing (e.g., ".main-content")
        timeout: Timeout in milliseconds (default: 30000)

    Returns:
        Dictionary with page title, meta tags, heading structure, and text content
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()

            # Navigate to the page (use 'domcontentloaded' instead of 'networkidle' to avoid hanging)
            response = await page.goto(url, wait_until='domcontentloaded', timeout=timeout)

            # Wait a bit for initial content to render
            await page.wait_for_timeout(1000)

            if not response or response.status >= 400:
                await browser.close()
                return {
                    'success': False,
                    'error': f'Failed to load page. Status: {response.status if response else "unknown"}',
                    'url': url
                }

            # Wait for specific selector if provided
            if wait_for_selector:
                try:
                    await page.wait_for_selector(wait_for_selector, timeout=5000)
                except PlaywrightTimeoutError:
                    pass  # Continue anyway

            # Extract page information
            title = await page.title()

            # Meta tags
            meta_tags = await page.evaluate("""
                () => {
                    const metas = {};
                    document.querySelectorAll('meta').forEach(meta => {
                        const name = meta.getAttribute('name') || meta.getAttribute('property');
                        const content = meta.getAttribute('content');
                        if (name && content) {
                            metas[name] = content;
                        }
                    });
                    return metas;
                }
            """)

            # Heading structure
            headings = await page.evaluate("""
                () => {
                    const headings = [];
                    document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
                        headings.push({
                            level: h.tagName.toLowerCase(),
                            text: h.innerText.trim()
                        });
                    });
                    return headings;
                }
            """)

            # Main content text
            main_content = await page.evaluate("""
                () => {
                    // Try to find main content area
                    const mainSelectors = ['main', 'article', '[role="main"]', '.content', '#content'];
                    for (const selector of mainSelectors) {
                        const element = document.querySelector(selector);
                        if (element) {
                            return element.innerText.trim();
                        }
                    }
                    // Fallback to body
                    return document.body.innerText.trim();
                }
            """)

            # Extract links
            links = await page.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        links.push({
                            text: a.innerText.trim(),
                            href: a.href
                        });
                    });
                    return links.slice(0, 50); // Limit to first 50 links
                }
            """)

            # Check for existing JSON-LD
            existing_schemas = await page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    const schemas = [];
                    scripts.forEach(script => {
                        try {
                            schemas.push(JSON.parse(script.textContent));
                        } catch (e) {
                            // Invalid JSON
                        }
                    });
                    return schemas;
                }
            """)

            await browser.close()

            # Analyze content length and structure
            content_length = len(main_content)
            word_count = len(main_content.split())

            return {
                'success': True,
                'url': url,
                'title': title,
                'meta_tags': meta_tags,
                'headings': headings,
                'main_content': main_content[:5000],  # Limit to first 5000 chars
                'content_stats': {
                    'total_chars': content_length,
                    'word_count': word_count,
                    'heading_count': len(headings)
                },
                'links': links[:20],  # Return first 20 links
                'existing_schemas': existing_schemas,
                'analysis': {
                    'has_h1': any(h['level'] == 'h1' for h in headings),
                    'has_meta_description': 'description' in meta_tags or 'og:description' in meta_tags,
                    'has_og_tags': any(k.startswith('og:') for k in meta_tags.keys()),
                    'has_existing_schema': len(existing_schemas) > 0
                }
            }

    except PlaywrightTimeoutError:
        return {
            'success': False,
            'error': 'Page load timeout',
            'url': url,
            'suggestion': 'Try increasing timeout or checking if the URL is accessible'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'url': url,
            'error_type': type(e).__name__
        }

@mcp.tool()
def get_main_page_guide() -> str:
    """Get JSON-LD schema guide for main/home pages"""
    file_path = CATEGORY_DIR / "main.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_list_page_guide() -> str:
    """Get JSON-LD schema guide for list/catalog pages (product listings, blog archives, etc.)"""
    file_path = CATEGORY_DIR / "list.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_detail_page_guide() -> str:
    """Get JSON-LD schema guide for detail pages (product pages, blog posts, articles)"""
    file_path = CATEGORY_DIR / "detail.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_info_page_guide() -> str:
    """Get JSON-LD schema guide for information pages (about, contact, FAQ, policy pages)"""
    file_path = CATEGORY_DIR / "info.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_form_page_guide() -> str:
    """Get JSON-LD schema guide for form/interactive pages (signup, contact forms, calculators)"""
    file_path = CATEGORY_DIR / "form.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_cta_page_guide() -> str:
    """Get JSON-LD schema guide for CTA/landing pages (promotional, conversion-focused pages)"""
    file_path = CATEGORY_DIR / "cta.md"
    return file_path.read_text(encoding='utf-8')


# INDUSTRY TOOLS (산업별 가이드)

@mcp.tool()
def get_technology_industry_guide() -> str:
    """Get JSON-LD schema guide for Technology industry (SaaS, software, tech products)"""
    file_path = INDUSTRY_DIR / "technology.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_healthcare_industry_guide() -> str:
    """Get JSON-LD schema guide for Healthcare industry (medical, health services, wellness)"""
    file_path = INDUSTRY_DIR / "healthcare.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_finance_industry_guide() -> str:
    """Get JSON-LD schema guide for Finance industry (banking, fintech, investment)"""
    file_path = INDUSTRY_DIR / "finance.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_education_industry_guide() -> str:
    """Get JSON-LD schema guide for Education industry (schools, courses, e-learning)"""
    file_path = INDUSTRY_DIR / "education.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_entertainment_industry_guide() -> str:
    """Get JSON-LD schema guide for Entertainment industry (media, streaming, games)"""
    file_path = INDUSTRY_DIR / "entertainment.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_consumer_industry_guide() -> str:
    """Get JSON-LD schema guide for Consumer industry (e-commerce, retail, products)"""
    file_path = INDUSTRY_DIR / "consumer.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_it_industry_guide() -> str:
    """Get JSON-LD schema guide for IT industry (infrastructure, cloud, enterprise tech)"""
    file_path = INDUSTRY_DIR / "it.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_information_industry_guide() -> str:
    """Get JSON-LD schema guide for Information industry (news, publishing, media)"""
    file_path = INDUSTRY_DIR / "information.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_leisure_industry_guide() -> str:
    """Get JSON-LD schema guide for Leisure industry (travel, hospitality, tourism)"""
    file_path = INDUSTRY_DIR / "leisure.md"
    return file_path.read_text(encoding='utf-8')


@mcp.tool()
def get_public_industry_guide() -> str:
    """Get JSON-LD schema guide for Public sector (government, non-profit, civic organizations)"""
    file_path = INDUSTRY_DIR / "public.md"
    return file_path.read_text(encoding='utf-8')


if __name__ == "__main__":
    """Main entry point for the MCP server"""
    # Run the server
    if IS_DEBUG:
        mcp.run()
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8002, path="/mcp")
