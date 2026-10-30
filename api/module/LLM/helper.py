import ast
import time
import asyncio
from datetime import timedelta
from uuid import uuid4
from pytz import timezone

from client.redis import RedisClient
from client.mysql import MySQLClient

from client.aws import S3Client
from domain.playground import chatDomain
from domain.chatbot import chatDomain as chatbotDomain
from module.LLM.dto import LLMArgs
from module.Retrieval.core import SearchScope
from module.Retrieval.service import Retriever
from utils.error import *
from utils.text import html_to_markdown, get_clean_text, remove_base64_images


def make_llmArgs(args:chatDomain|chatbotDomain) -> LLMArgs:
    """
    make llmArgs in order to seperated Action \n\n
    - redis_save:bool -> save conversation_history Y/n
    """
    try:
        return LLMArgs(
            service=args.service,
            vendor=args.vendor,
            model=args.model,
            question=args.question,
            answer_id=args.answer_id,
            session_key=args.session_key,
            company_key=args.company_key,
            credit_available=args.credit_available,
            lang=args.lang,
            info=args.info,
            start_time=args.start_time,
            vector_db_index=args.vector_db_index,
            vector_db_namespace=args.vector_db_namespace,
            vector_db_embedding_model=args.vector_db_embedding_model,
            llm_proxy_client=args.llm_proxy_client,
            main_db_client=args.main_db_client,
            vector_db_client=args.vector_db_client,
            memory_db_client=args.memory_db_client,
            s3_client=args.s3_client,
            redis_save=True,
            conversation_history=[],
            streaming=True,
            time_info={},
            is_mcp=getattr(args, "is_mcp", None),
            store_name=getattr(args, "store_name", None),
            file_id=args.file_id,
            on_llm_platform_system=getattr(args, "on_llm_platform_system", True)
        )
    except DataError as e:
        logging.error(f"[module.LLM.helper.make_llmArgs] DataError: {e}")
        raise e
    except Exception as e:
        logging.error(f"[module.LLM.helper.make_llmArgs] Exception: {e}")
        raise e


async def get_retrieval_data_for_client(refer_id:list, parser_id:list, email_id:list, sitemap_id:list, main_db_client:MySQLClient, s3_client:S3Client):
    """
    get Data which is used for RAG\n\n
    - Data From Pinecone\n
    - Operate when it is called by get_retrieval_data router
    """
    try:
        post_ids = [int(id) for id in refer_id]
        parser_ids = [int(id) for id in parser_id]
        email_ids = [int(id) for id in email_id]
        sitemap_ids = [int(id) for id in sitemap_id]

        tasks = [
            get_post_retrieval_data_from_main_db_for_client(post_ids, main_db_client),
            get_parser_retrieval_data_from_main_db_for_client(parser_ids, main_db_client, s3_client),
            get_email_retrieval_data_from_main_db_for_client(email_ids, main_db_client),
            get_sitemap_retrieval_data_from_main_db_for_client(sitemap_ids, main_db_client)
        ]
        post_data, parser_data, email_data, sitemap_data = await asyncio.gather(*tasks)

        result = post_data + parser_data + email_data + sitemap_data
        return result or []

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_retrieval_data_for_client] DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[module.LLM.helper.get_retrieval_data_for_client] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_retrieval_data_for_client] Exception: {e}")
        raise e


async def get_post_retrieval_data_from_main_db_for_client(post_ids:list, main_db_client:MySQLClient):
    try:
        if not post_ids:
            return []

        placeholders = ','.join(['%s'] * len(post_ids))
        query = f"""
            SELECT
                title, content, image_url, id, is_show
            FROM
                post
            WHERE
                id IN ({placeholders}) and is_on = 1 and is_show = 1
        """
        rows = await main_db_client.fetch_all(
            query=query,
            params=post_ids
        )
        return [
            {
                "title": row[0],
                "content": row[1],
                "url": row[3] if row[4] else None,
                "image_url": row[2],
                "data_type": "post"
            }
            for row in rows
        ]

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_post_retrieval_data_from_main_db_for_client] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_post_retrieval_data_from_main_db_for_client] Exception: {e}")
        raise e


async def get_parser_retrieval_data_from_main_db_for_client(parser_ids:list, main_db_client:MySQLClient, s3_client:S3Client):
    try:
        if not parser_ids or len(parser_ids) == 0:
            return []

        placeholders = ','.join(['%s'] * len(parser_ids))
        rows = await main_db_client.fetch_all(
            query=f"""
                SELECT
                    uf.filename as filename,
                    uf.post_id as post_id,
                    d.filename as drive_filename,
                    uf.s3_path as s3_path,
                    v.page as page,
                    (SELECT MAX(page) FROM vector WHERE upload_file_id = v.upload_file_id) as max_page,
                    v.upload_file_id as upload_file_id,
                    d.id as drive_id,
                    (
                        SELECT GROUP_CONCAT(DISTINCT v2.page) 
                        FROM vector v2 
                        WHERE v2.upload_file_id = v.upload_file_id
                    ) as pages
                FROM
                    vector v
                LEFT JOIN
                    upload_file uf ON uf.id = v.upload_file_id
                LEFT JOIN
                    drive d ON d.upload_file_id = v.upload_file_id
                WHERE
                    v.id IN ({placeholders})
            """,
            params=parser_ids
        )

        results = list()
        tasks = list()
        for row in rows:
            results.append(
                {
                    "title": row[0] if row[1] else row[2],
                    "url": row[1] or row[7],
                    "image_url": None,
                    "data_type": "post" if row[1] else "parser"
                }
            )
            if row[8]:
                page_tuple_in_db = tuple(int(p) for p in row[8].split(','))
                tasks.append(download_parser_file(s3_client=s3_client, s3_path=row[3], page=row[4], max_page=row[5], page_tuple_in_db=page_tuple_in_db))
        contents = await asyncio.gather(*tasks)
        for result, content in zip(results, contents):
            result["content"] = content

        return results

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_parser_retrieval_data_from_main_db_for_client] DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[module.LLM.helper.get_parser_retrieval_data_from_main_db_for_client] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_parser_retrieval_data_from_main_db_for_client] Exception: {e}")
        raise e


async def get_sitemap_retrieval_data_from_main_db_for_client(sitemap_ids:list, main_db_client:MySQLClient):
    try:
        if not sitemap_ids or len(sitemap_ids) == 0:
            return []

        placeholders = ','.join(['%s'] * len(sitemap_ids))
        select_query = f"""
            SELECT
                title, content, id
            FROM
                post
            WHERE
                id IN ({placeholders})
        """

        rows = await main_db_client.fetch_all(
            query=select_query,
            params=sitemap_ids
        )

        return [
            {
                "title": row[0],
                "content": get_clean_text(row[1], keep_html_tags=True),
                "url": row[2],
                "image_url": None,
                "data_type": "sitemap"
            } for row in rows
        ]

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_sitemap_retrieval_data_from_main_db] DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[module.LLM.helper.get_sitemap_retrieval_data_from_main_db] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_sitemap_retrieval_data_from_main_db] Exception: {e}")
        raise e


async def get_email_retrieval_data_from_main_db_for_client(email_ids:list, main_db_client:MySQLClient):
    try:
        if not email_ids or len(email_ids) == 0:
            return []

        placeholders = ','.join(['%s'] * len(email_ids))
        query = f"""
            SELECT
                send.last_content_for_llm,
                receive.last_content as question,
                receive.subject as receive_subject,
                temp.answering_content as answer,
                temp.subject as reply_answer,
                send.id as id
            FROM llm_platform.email_send_history send
            INNER JOIN cx_email receive ON send.in_reply_to COLLATE utf8mb4_unicode_ci = receive.message_id COLLATE utf8mb4_unicode_ci
            INNER JOIN cx_email_temp temp ON receive.id COLLATE utf8mb4_unicode_ci = temp.cx_email_id COLLATE utf8mb4_unicode_ci
            WHERE send.id IN ({placeholders})
        """
        params = email_ids
        rows = await main_db_client.fetch_all(query, params)
        return [
            {
                "title": row[2],
                "content": row[0] if row[0] else str({"received": {"title": row[2], "content": row[1]}, "sent": {"title": row[4], "content": remove_base64_images(html_to_markdown(row[3]).split(EMAIL_THREAD_SPLITTER)[0])}}),
                "url": row[5],
                "data_type": "email"
            } for row in rows
        ] if rows else []

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_email_retrieval_data_from_main_db] DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[module.LLM.helper.get_email_retrieval_data_from_main_db] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_email_retrieval_data_from_main_db] Exception: {e}")
        raise e


async def query_vector(llmArgs: LLMArgs) -> list:
    if llmArgs.store_name:
        return []
    retriever = Retriever(
        llmArgs.vector_db_client, llmArgs.llm_proxy_client, llmArgs.service,
        llmArgs.vendor, llmArgs.model, llmArgs.session_key,
    )
    matches = await retriever.find(
        llmArgs.question,
        SearchScope(llmArgs.company_key, llmArgs.file_id, ("parser",) if llmArgs.file_id is not None else ()),
        history=llmArgs.conversation_history or [],
    )
    get_elapsed(llmArgs, "ElapsedRAGQuery")
    return matches


async def get_retrieval_data(match_docs:dict, llmArgs:LLMArgs):
    try:
        # gathering ids
        post_ids = list()
        parser_ids = list()
        sitemap_ids = list()
        email_ids = list()
        for doc in match_docs:
            if (doc.metadata.get('data_type') == "post" or doc.metadata.get('date_type') == "post") and doc.metadata.get("id") is not None and not doc.metadata.get("sitemap_id"):
                post_ids.append(int(float(doc.metadata.get("id"))))
            elif (doc.metadata.get('data_type') == "post" or doc.metadata.get('date_type') == "post") and doc.metadata.get("id") is not None and doc.metadata.get("sitemap_id"):
                sitemap_ids.append(int(float(doc.metadata.get("id"))))
            elif doc.metadata.get('data_type') == "parser" and doc.metadata.get("id") is not None:
                parser_ids.append(int(float(doc.metadata.get("id"))))
            elif doc.metadata.get('data_type') == "email" and doc.metadata.get("id") is not None:
                email_ids.append(int(float(doc.metadata.get("id"))))

        # reduce same id. bcs chunk.
        post_ids = list(dict.fromkeys(post_ids))
        parser_ids = list(dict.fromkeys(parser_ids))
        sitemap_ids = list(dict.fromkeys(sitemap_ids))
        email_ids = list(dict.fromkeys(email_ids))
        if len(post_ids) > 4:
            post_ids = post_ids[:4]
        if len(parser_ids) > 5:
            parser_ids = parser_ids[:5]
        if len(sitemap_ids) > 1:
            sitemap_ids = sitemap_ids[:1]
        if len(email_ids) > 1:
            email_ids = email_ids[:1]

        # get and reform rag data
        tasks = [
            get_post_retrieval_data_from_main_db(post_ids, llmArgs),
            get_parser_retrieval_data_from_main_db(parser_ids, llmArgs),
            get_sitemap_retrieval_data_from_main_db(sitemap_ids, llmArgs),
            get_email_retrieval_data_from_main_db(email_ids, llmArgs),
            get_common_sense_data(llmArgs)
        ]
        post_data, parser_data, sitemap_data, email_data, common_data = await asyncio.gather(*tasks)

        # result
        retrieval_data = post_data + parser_data + sitemap_data + email_data + common_data
        return post_ids, parser_ids, sitemap_ids, email_ids, retrieval_data

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_retrieval_data] DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[module.LLM.helper.get_retrieval_data] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_retrieval_data] Exception: {e}")
        raise e


async def get_post_retrieval_data_from_main_db(post_ids:list, llmArgs:LLMArgs):
    try:
        if not post_ids or len(post_ids) == 0 or llmArgs.store_name:
            return []

        tasks = list()
        placeholders = ','.join(['%s'] * len(post_ids))

        update_query = f"""
            UPDATE
                post
            SET
                use_count = COALESCE(use_count, 0) + 1
            WHERE
                id IN ({placeholders})
        """
        tasks.append(llmArgs.main_db_client.execute(
            query=update_query,
            params=post_ids
        ))

        select_query = f"""
            SELECT
                title, content, image_url
            FROM
                post
            WHERE
                id IN ({placeholders})
        """
        tasks.append(llmArgs.main_db_client.fetch_all(
            query=select_query,
            params=post_ids
        ))
        _, rows = await asyncio.gather(*tasks)

        get_elapsed(llmArgs, "ElapsedPostMySQLQuery")

        return [
            {
                "title": row[0],
                "content": html_to_markdown(row[1]),
                "image_url": row[2],
                "data_type": "post"
            } for row in rows
        ]

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_post_retrieval_data_from_main_db] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_post_retrieval_data_from_main_db] Exception: {e}")
        raise e


async def get_parser_retrieval_data_from_main_db(parser_ids:list, llmArgs:LLMArgs):
    try:
        if not parser_ids or len(parser_ids) == 0 or llmArgs.store_name:
            return []
        else:
            placeholders = ','.join(['%s'] * len(parser_ids))
            rows = await llmArgs.main_db_client.fetch_all(
                query=f"""
                    SELECT
                        d.filename as filename,
                        uf.s3_path as s3_path,
                        v.page as page,
                        (SELECT MAX(page) FROM vector WHERE upload_file_id = v.upload_file_id) as max_page,
                        (
                            SELECT GROUP_CONCAT(DISTINCT v2.page) 
                            FROM vector v2 
                            WHERE v2.upload_file_id = v.upload_file_id
                        ) as pages
                    FROM
                        vector v
                    INNER JOIN upload_file uf ON uf.id = v.upload_file_id
                    INNER JOIN drive d ON d.upload_file_id = v.upload_file_id
                    WHERE
                        v.id IN ({placeholders})
                """,
                params=parser_ids
            )

            results = []
            tasks = []
            for row in rows:
                results.append({"title": row[0], "image_url": None, "data_type": "parser"})
                if row[4]:
                    page_tuple_in_db = tuple(int(p) for p in row[4].split(','))
                    tasks.append(download_parser_file(s3_client=llmArgs.s3_client, s3_path=row[1], page=row[2], max_page=row[3], page_tuple_in_db=page_tuple_in_db))
            contents = await asyncio.gather(*tasks)
            for result, content in zip(results, contents):
                result["content"] = content

            get_elapsed(llmArgs, "ElapsedParserS3")

            return results

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_parser_retrieval_data_from_main_db] DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[module.LLM.helper.get_parser_retrieval_data_from_main_db] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_parser_retrieval_data_from_main_db] Exception: {e}")
        raise e


async def get_sitemap_retrieval_data_from_main_db(sitemap_ids:list, llmArgs:LLMArgs):
    try:
        if not sitemap_ids or len(sitemap_ids) == 0 or llmArgs.store_name:
            return []

        tasks = list()
        placeholders = ','.join(['%s'] * len(sitemap_ids))

        update_query = f"""
            UPDATE
                post
            SET
                use_count = COALESCE(use_count, 0) + 1
            WHERE
                id IN ({placeholders})
        """
        tasks.append(llmArgs.main_db_client.execute(
            query=update_query,
            params=sitemap_ids
        ))

        select_query = f"""
            SELECT
                title, content
            FROM
                post
            WHERE
                id IN ({placeholders})
        """

        tasks.append(llmArgs.main_db_client.fetch_all(
            query=select_query,
            params=sitemap_ids
        ))
        _, rows = await asyncio.gather(*tasks)

        get_elapsed(llmArgs, "ElapsedCrawlerMySQLQuery")

        return [
            {
                "title": row[0],
                "content": get_clean_text(row[1], keep_html_tags=True),
                "data_type": "sitemap"
            } for row in rows
        ]

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_sitemap_retrieval_data_from_main_db] DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[module.LLM.helper.get_sitemap_retrieval_data_from_main_db] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_sitemap_retrieval_data_from_main_db] Exception: {e}")
        raise e


async def get_email_retrieval_data_from_main_db(email_ids:list, llmArgs:LLMArgs):
    try:
        if not email_ids or len(email_ids) == 0 or llmArgs.store_name:
            return []
        else:
            placeholders = ','.join(['%s'] * len(email_ids))
            query = f"""
                SELECT
                    send.last_content_for_llm,
                    receive.last_content as question,
                    receive.subject as receive_subject,
                    temp.answering_content as answer,
                    temp.subject as reply_answer
                FROM llm_platform.email_send_history send
                INNER JOIN cx_email receive ON send.in_reply_to COLLATE utf8mb4_unicode_ci = receive.message_id COLLATE utf8mb4_unicode_ci
                INNER JOIN cx_email_temp temp ON receive.id COLLATE utf8mb4_unicode_ci = temp.cx_email_id COLLATE utf8mb4_unicode_ci
                WHERE send.id IN ({placeholders})
            """
            params = email_ids

            rows = await llmArgs.main_db_client.fetch_all(query, params)
            get_elapsed(llmArgs, "ElapsedEmailS3")
            return [
                {
                    "content": row[0] if row[0] else {"received": {"title": row[2], "content": row[1]}, "sent": {"title": row[4], "content": remove_base64_images(html_to_markdown(row[3]).split(EMAIL_THREAD_SPLITTER)[0])}},
                    "data_type": "email"
                } for row in rows
            ] if rows else []

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_email_retrieval_data_from_main_db] DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[module.LLM.helper.get_email_retrieval_data_from_main_db] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_email_retrieval_data_from_main_db] Exception: {e}")
        raise e


async def get_common_sense_data(llmArgs):
    try:
        results = []
        if llmArgs.info.get("init_date"):
            current_time = llmArgs.info["init_date"]
            time_info = f"\n\n\n[현재 시간]:(UTC) {current_time.year}년 {current_time.month}월 {current_time.day}일, {current_time.hour}시 {current_time.minute}분 {current_time.second}초입니다."
            results.append({"title": "현재 UTC 시간", "content": time_info, "data_type": "common_sense"})
        return results

    except Exception as e:
        logging.error(f"[module.LLM.helper.get_common_sense_data] Exception: {e}")
        raise e



async def download_parser_file(s3_client:S3Client, s3_path:str, page:int, max_page:int, page_tuple_in_db:tuple):
    try:
        bucket_name = s3_path.split(":")[0]
        dir_path = "/".join(s3_path.split(":")[1].split("/")[:-1])
        page_path = "pages"
        file_type = "text"
        if max_page == 1:
            target_pages = [1]
        elif max_page > 1 and page == 1:
            target_pages = [1, 2]
        elif page >= 2 and page < max_page:
            target_pages = [page-1, page, page+1]
        else:
            target_pages = [max_page-1, max_page]

        tasks = list()
        result = ""
        for target_page in target_pages:
            if target_page in page_tuple_in_db:
                object_name = f"{dir_path}/{page_path}/{target_page}.{file_type}"
                tasks.append(s3_client.get_file_from_s3(bucket_name=bucket_name, object_name=object_name))

        tasks_results = await asyncio.gather(*tasks)
        for response, _ in tasks_results:
            result += str(response.decode("utf-8"))

        return result

    except AWSError as e:
        logging.error(f"[module.LLM.helper.download_parser_file] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.download_parser_file] Exception: {e}")
        raise e


async def get_system_prompt(llmArgs:LLMArgs):
    """
    get prompt from db.epic.prompt_history
    """
    try:
        prompt_result = await llmArgs.main_db_client.fetch_one(
            query="""
                SELECT
                    id,
                    prompt
                FROM prompt_history
                WHERE company_key = %s
                ORDER BY reg_date DESC
                LIMIT 1
            """,
            params=(llmArgs.company_key)
        )
        pid = prompt_result[0] if prompt_result else None
        prompt = prompt_result[1] if prompt_result else DEFAULT_PROMPT

        get_elapsed(llmArgs, "ElapsedPromptMySQLQuery")

        return prompt, pid

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_system_prompt] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_system_prompt] Exception: {e}")
        raise e


async def get_conversation_history_for_client(memory_db_client:RedisClient, session_key:str):
    """get conversation history from Redis"""
    try:
        conversations = await memory_db_client.lrange(session_key, 0, -1)
        return decode_data_from_redis(conversations)

    except MemoryDBError as e:
        logging.error(f"[module.LLM.helper.get_conversation_history_for_client] MemoryDBError: {e}")
        raise MemoryDBError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_conversation_history_for_client] Exception: {e}")
        raise e


async def get_conversation_history(llmArgs:LLMArgs):
    """get conversation history from Redis"""
    try:
        count = await llmArgs.memory_db_client.llen(llmArgs.session_key)
        if count == 0:
            conversations = []
        else:
            conversations = await llmArgs.memory_db_client.lrange(llmArgs.session_key, -40, -1)

        get_elapsed(llmArgs, "ElapsedConvHistoryRedis")

        return decode_data_from_redis(conversations)

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_conversation_history] DBError: {e}")
        raise DBError(e)
    except MemoryDBError as e:
        logging.error(f"[module.LLM.helper.get_conversation_history] MemoryDBError: {e}")
        raise MemoryDBError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_conversation_history] Exception: {e}")
        raise e


def decode_data_from_redis(list_data):
    """
    decode string data from redis -> dict
    """
    try:
        if len(list_data) == 0:
            result = []
        else:
            result = list(map(lambda string_data: ast.literal_eval(string_data), list_data))
        return result

    except Exception as e:
        logging.error(f"[module.LLM.helper.decode_data_from_redis] Exception: {e}")
        raise e


def redis_format(role, message, id=None, mcp_tools=None):
    """Redis input data format"""
    try:
        form = {
            "message": message,
            "role": role
        }
        if mcp_tools and role == "human":
            form["mcp_tools"] = mcp_tools
            form["id"] = id
        if id != None and role == "ai":
            form["id"] = id
            form["rating"] = None
        return str(form)
    except Exception as e:
        logging.error(f"[module.LLM.helper.redis_format] Exception: {e}")
        raise e


def make_chat_history_data(chat_info:dict, role:str, message:str, token:int, reg_date:datetime=None, id:str=None, elapsed_info:str=None):
    try:
        chat_info['reg_date'] = reg_date or datetime.now(timezone('UTC'))
        chat_info['issue_status'] = "needSolve"
        chat_info['role'] = role
        chat_info['message'] = message
        chat_info['id'] = id or str(uuid4()).replace("-", "")
        chat_info['token'] = token
        chat_info['elapsed_info'] = elapsed_info
        return chat_info
    except Exception as e:
        logging.error(f"[module.LLM.helper.make_chat_history_data] Exception: {e}")
        raise e


async def record_credit_history(main_db_client:MySQLClient, company_key:str, credit_available:int, current_time:datetime):
    try:
        await main_db_client.execute(
            query="UPDATE payment SET use_credit = use_credit + 1 WHERE company_key = %s AND start_date <= %s AND end_date >= %s",
            params=(company_key, current_time, current_time)
        )

        row = await main_db_client.fetch_one(
            query="SELECT id FROM credit_history WHERE company_key = %s AND credit_type = %s AND DATE(reg_date) = DATE(%s);",
            params=(company_key, 0, current_time)
        )
        if row:
            credit_history_id = row[0]
            await main_db_client.execute(
                query="UPDATE credit_history SET credit = credit + 1, after_credit_available = after_credit_available - 1 WHERE id = %s",
                params=(credit_history_id)
            )
        else:
            payment_id_row = await main_db_client.fetch_one(
                query="SELECT id FROM payment WHERE company_key = %s AND start_date <= %s AND end_date >= %s",
                params=(company_key, current_time, current_time)
            )
            payment_id = payment_id_row[0]
            await main_db_client.execute(
                query="INSERT INTO credit_history (company_key, reg_date, credit_type, credit, after_credit_available, payment_id) VALUES (%s, %s, %s, %s, %s, %s)",
                params=(company_key, current_time, 0, 1, credit_available - 1, payment_id)
            )
    except DBError as e:
        logging.error(f"[module.LLM.helper.record_credit_history] DBError: {e}")
    except Exception as e:
        logging.error(e)
        # send_slack_message(message=f"[llm-platform-api][faild record_credit_history] {e}🫠", channel="#casual")


def make_human_message(question, retrieval_data=None, language_message=None):
    result = f"<{USER_QUESTION_NAME}>\n{question}\n</{USER_QUESTION_NAME}>"
    if retrieval_data:
        result = f"<{RAG_NAME}>\n{retrieval_data}\n</{RAG_NAME}>\n\n\n{result}"
    if language_message:
        result = result + f"\n\n\n<{LANG_NAME}>\n{language_message}\n</{LANG_NAME}>"
    return result


async def make_error_message_for_LLM(streaming:bool=True):
    """
    make streaming error message
    """
    try:
        message = "죄송합니다. 에러가 발생해 답변을 제공할 수 없습니다. 계속 같은 메세지를 받으신다면 담당자에게 연락주시면 감사하겠습니다."
        if streaming:
            for m in message:
                await asyncio.sleep(0.025)
                yield m
        else:
            yield message

    except Exception as e:
        logging.error(f"[module.LLM.helper.make_error_message] Exception: {e}")
        raise e


def get_elapsed(llmArgs:LLMArgs, key:str):
    try:
        end_time = time.time()
        elapsed = timedelta(seconds=float(end_time - llmArgs.start_time)).total_seconds()
        llmArgs.time_info[key] = elapsed
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_elapsed] Exception: {e}")
        raise e


def write_log_for_debug_message(system_message=None, conversation_history=None, human_message=None):
    logging.info("*"*100)
    logging.info(f"[시스템 프롬프트] {system_message}")
    logging.info("*"*100)
    logging.info(f"[대화 이력] {conversation_history}")
    logging.info("*"*100)
    logging.info(f"[사용자 프롬프트] {human_message}")
    logging.info("*"*100)
