import ast
import asyncio
from bs4 import BeautifulSoup

from utils.error import *
from utils.text import html_to_markdown, remove_base64_images
from domain.email import *
from module.Mail.dto import *
from module.Retrieval.core import SearchScope
from module.Retrieval.service import Retriever



def make_llmEmailArgs(args:CreateEmailContentDomain) -> LLMEmailArgs:
    """
    make llmArgs in order to seperated Action \n\n
    - redis_save:bool -> save conversation_history Y/n
    """
    try:
        return LLMEmailArgs(
            id=args.id,
            service=args.service,
            vendor=args.vendor,
            model=args.model,
            session_key=args.session_key,
            company_key=args.company_key,
            user_id=args.user_id,
            action_code=args.action_code,
            current_time=args.current_time,
            credit_available=args.credit_available,
            start_time=args.start_time,
            vector_db_index=args.vector_db_index,
            vector_db_namespace=args.vector_db_namespace,
            vector_db_embedding_model=args.vector_db_embedding_model,
            llm_proxy_client=args.llm_proxy_client,
            main_db_client=args.main_db_client,
            vector_db_client=args.vector_db_client,
            s3_client=args.s3_client,
            redis_save=True,
            streaming=True
        )
    except DataError as e:
        logging.error(f"[module.Mail.helper.make_llmEmailArgs] DataError: {e}")
        raise e
    except Exception as e:
        logging.error(f"[module.Mail.helper.make_llmEmailArgs] Exception: {e}")
        raise e
    

async def make_error_message(streaming:bool=True):
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
    

async def get_reference(args:LLMEmailArgs) -> str:
    message_ids_query = """
        SELECT `references`
        FROM cx_email
        WHERE id = %s
    """
    ref_query = """
        SELECT from_mail, from_name, company, to_mail, to_name, last_content, received_at, status, subject
        FROM cx_email
        WHERE message_id IN ({})
        ORDER BY received_at DESC
    """
    try:
        result = await args.main_db_client.fetch_one(message_ids_query, (args.id,))  # 튜플로 수정
        if result and result[0]:
            message_ids = ast.literal_eval(result[0])
            if isinstance(message_ids, list) and message_ids:
                # SQL 인젝션 방지를 위한 안전한 플레이스홀더 생성
                placeholders = ','.join(['%s'] * len(message_ids))
                formatted_query = ref_query.format(placeholders)
                ref_result = await args.main_db_client.fetch_all(formatted_query, message_ids)
                ref_rows = []
                for row in ref_result:
                    ref_rows.append({
                        "subject": row[8],
                        "last_content": row[5],
                        "from_mail": row[0],
                        "from_name": row[1], 
                        "company": row[2],
                        "to_mail": row[3],
                        "to_name": row[4],
                        "received_at": row[6],
                        "status": row[7]
                    })
                return str(ref_rows)
            else:
                return "[]"
        else:
            return "[]"
    
    except DBError as e:
        logging.error(f"[module.Mail.helper.get_reference] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[module.Mail.helper.get_reference] Exception: {e}")
        raise e
    

async def get_question_by_last_content(args: LLMEmailArgs) -> str:
    if not args.company_key:
        raise DataError("Company scope is required")
    result = await args.main_db_client.fetch_one(
        "SELECT last_content FROM cx_email WHERE id = %s AND company_key = %s",
        (args.id, args.company_key),
    )
    if not result or not result[0]:
        raise DataError("Email content is unavailable")
    return result[0]


async def query_vector(args: LLMEmailArgs) -> list:
    retriever = Retriever(
        args.vector_db_client, args.llm_proxy_client, args.service,
        args.vendor, args.model, args.session_key,
    )
    return await retriever.find(
        args.question, SearchScope(args.company_key, data_types=("post", "parser")),
        history=args.conversation_history or [], limit=20,
    )


async def get_retrieval_data(args:LLMEmailArgs, match_docs:list):
    try:
        # gathering ids
        post_ids = [int(float(doc.metadata.get("id"))) for doc in match_docs if (doc.metadata.get('data_type') == "post" or doc.metadata.get('date_type') == "post") and doc.metadata.get("id") is not None]
        parser_ids = [int(float(doc.metadata.get("id"))) for doc in match_docs if doc.metadata.get('data_type') == "parser" and doc.metadata.get("id") is not None]
        non_post_data = [doc for doc in match_docs if doc.metadata.get('data_type') not in ("post", "parser") and not doc.metadata.get('date_type')] # temporary code.

        # reduce same id. bcs chunk.
        post_ids = list(dict.fromkeys(post_ids))
        parser_ids = list(dict.fromkeys(parser_ids))
        if len(post_ids) > 5:
            post_ids = post_ids[:5]
        if len(parser_ids) > 7:
            parser_ids = parser_ids[:7]

        # get and reform rag data
        post_data = await get_post_retrieval_data_from_main_db(post_ids, args.main_db_client) if post_ids else []
        parser_data = await get_parser_retrieval_data_from_main_db(parser_ids, args.main_db_client, args.s3_client) if parser_ids else []
        other_data = [format_docs(doc) for doc in non_post_data] if non_post_data else []

        # result
        retrieval_data = post_data + parser_data + other_data

        return retrieval_data

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_retrieval_data] DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[module.LLM.helper.get_retrieval_data] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_retrieval_data] Exception: {e}")
        raise e


async def get_post_retrieval_data_from_main_db(post_ids:list, main_db_client:MySQLClient):
    try:
        placeholders = ','.join(['%s'] * len(post_ids))

        update_query = f"""
            UPDATE
                post
            SET
                use_count = COALESCE(use_count, 0) + 1
            WHERE
                id IN ({placeholders})
        """
        await main_db_client.execute(
            query=update_query,
            params=post_ids
        )

        select_query = f"""
            SELECT
                title, content, image_url
            FROM
                post
            WHERE
                id IN ({placeholders})
        """
        rows = await main_db_client.fetch_all(
            query=select_query,
            params=post_ids
        )
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


async def get_parser_retrieval_data_from_main_db(parser_ids:list, main_db_client:MySQLClient, s3_client:S3Client):
    try:
        if not parser_ids or len(parser_ids) == 0:
            return []
        else:
            placeholders = ','.join(['%s'] * len(parser_ids))
            rows = await main_db_client.fetch_all(
                query=f"""
                    SELECT
                        uf.filename as filename,
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
                    INNER JOIN
                        upload_file uf ON uf.id = v.upload_file_id
                    WHERE
                        v.id IN ({placeholders})
                """,
                params=parser_ids
            )

            pages_in_db = []
            for row in rows:
                if row[4]:
                    pages = tuple(int(p) for p in row[4].split(','))
                    pages_in_db.append(pages)

            return [
                {
                    "title": row[0],
                    "content": await download_parser_file(s3_client=s3_client, s3_path=row[1], page=row[2], max_page=row[3], page_tuple_in_db=page_tuple_in_db),
                    "image_url": None,
                    "data_type": "parser"
                }
                for row, page_tuple_in_db in zip(rows, pages_in_db)
            ]

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_parser_retrieval_data_from_main_db] DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[module.LLM.helper.get_parser_retrieval_data_from_main_db] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_parser_retrieval_data_from_main_db] Exception: {e}")
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

        result = str()
        tasks = list()
        for target_page in target_pages:
            if target_page in page_tuple_in_db:
                object_name = f"{dir_path}/{page_path}/{target_page}.{file_type}"
                tasks.append(s3_client.get_file_from_s3(bucket_name=bucket_name, object_name=object_name))

        results = await asyncio.gather(*tasks)
        for response, _ in results:
            result += str(response.decode("utf-8"))

        return result

    except AWSError as e:
        logging.error(f"[module.LLM.helper.download_parser_file] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.download_parser_file] Exception: {e}")
        raise e


async def query_vector_for_email_rag(args: LLMEmailArgs) -> list:
    retriever = Retriever(
        args.vector_db_client, args.llm_proxy_client, args.service,
        args.vendor, args.model, args.session_key,
    )
    return await retriever.find(
        args.question, SearchScope(args.company_key, data_types=("email",)),
        history=args.conversation_history or [], limit=20,
    )


async def get_retrieval_data_for_email_rag(args:LLMEmailArgs, match_docs:list):
    try:
        # gathering ids
        email_ids = [int(float(doc.metadata.get("id"))) for doc in match_docs if doc.metadata.get('data_type') == "email" and doc.metadata.get("id") is not None]

        # reduce same id. bcs chunk.
        email_ids = list(dict.fromkeys(email_ids))
        if len(email_ids) > 2:
            email_ids = email_ids[:2]

        # get and reform rag data
        retrieval_data = await get_email_retrieval_data_from_main_db(args.main_db_client, email_ids) if email_ids else []
        return retrieval_data

    except DBError as e:
        logging.error(f"[module.LLM.helper.get_retrieval_data] DBError: {e}")
        raise DBError(e)
    except AWSError as e:
        logging.error(f"[module.LLM.helper.get_retrieval_data] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.get_retrieval_data] Exception: {e}")
        raise e


async def get_email_retrieval_data_from_main_db(main_db_client:MySQLClient, email_ids:list):
    try:
        if not email_ids or len(email_ids) == 0:
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

            rows = await main_db_client.fetch_all(query, params)
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


async def download_email_file(s3_client:S3Client, s3_path:str):
    try:
        s3_path_split = s3_path.split(":")
        bucket = s3_path_split[0]
        key = s3_path_split[1]
        response, _ = await s3_client.get_file_from_s3(bucket_name=bucket, object_name=key)
        result = str(response.decode("utf-8"))

        return result

    except AWSError as e:
        logging.error(f"[module.LLM.helper.download_parser_file] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[module.LLM.helper.download_parser_file] Exception: {e}")
        raise e


def format_docs(document):
    try:
        image_url = document.metadata.get('image_url', None)
        dataframe = document.metadata.get('dataframe', False)
        result = {
            "content": document.metadata.get('content', ''),
            "data_type": document.metadata.get('data_type'),
            "title": document.metadata.get('title', ''),
        }
        if image_url:
            result['image_url'] = image_url
        if dataframe:
            result['dataframe'] = dataframe
        return result

    except Exception as e:
        logging.error(f"[module.LLM.helper.format_docs] Exception: {e}")
        raise e


async def get_retrieval_data_for_mail(args:LLMEmailArgs) -> dict:
    try:
        vector = await args.llm_proxy_client.embeddings(text=args.question, service=args.service)
        docs = await args.vector_db_client.find(vector, 4, filter={"isOn": True})
        return {"retrieval_data": format_docs_for_mail(docs)}
    except LLMProxyError as e:
        logging.error(f"[module.Mail.helper.get_retrieval_data_for_rag] LLMProxyError: {e}")
        raise LLMProxyError(e)
    except VectorDBError as e:
        logging.error(f"[module.Mail.helper.get_retrieval_data_for_rag] VectorDBError: {e}")
        raise VectorDBError(e)
    except Exception as e:
        logging.error(f"[module.Mail.helper.get_retrieval_data_for_rag] Exception: {e}")
        raise e

    
def format_docs_for_mail(docs):
    try:
        documents = list()
        for document in docs:
            image_url = document.metadata.get("imageURL")
            is_show = bool(document.metadata.get("isShow", False))
            content = document.metadata.get("text","")
            title = document.metadata.get("subject")
            contentAdmin = document.metadata.get("contentAdmin")
            
            if is_show:
                page_content = {
                    "title": title,
                    "content": content
                }
                if contentAdmin:
                    page_content["contentAdmin"] = contentAdmin
                if image_url:
                    page_content["imageURL"] = image_url
            else:
                page_content = {}
            
            documents.append(page_content)
        return str(documents)
    
    except Exception as e:
        logging.error(f"[module.Mail.helper.format_docs] Exception: {e}")
        raise e


def make_email_message(question, language_message=None, email_rag_data=None, retrieval_data=None, reference=None):
    result = f"<문의 메일>\n{question}\n</문의 메일>"
    if language_message:
        result += "\n\n\n" + f"<{LANG_NAME}>\n{language_message}\n</{LANG_NAME}>"
    if email_rag_data:
        question += f"<유사한 메일 답변 데이터>\n{email_rag_data}\n</유사한 메일 답변 데이터>\n\n\n{question}"
    if retrieval_data:
        result = f"<{RAG_NAME}>\n{retrieval_data}\n</{RAG_NAME}>\n\n\n{result}"
    if reference:
        result += f"<대화 이력 데이터>\n{reference}\n</대화 이력 데이터>\n\n\n{result}"
    return result


def write_log_for_debug_message(system_message=None, conversation_history=None, human_message=None):
    logging.info("*"*100)
    logging.info(f"[시스템 프롬프트] {system_message}")
    logging.info("*"*100)
    logging.info(f"[대화 이력] {conversation_history}")
    logging.info("*"*100)
    logging.info(f"[사용자 프롬프트] {human_message}")
    logging.info("*"*100)