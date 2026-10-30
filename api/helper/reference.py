import re
import io
import base64
import asyncio
from uuid import uuid4

from PIL import Image
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from client.pinecone import PineconeClient
from client.milvus import MilvusClient
from client.aws import S3Client
from client.groxy import LLMProxyClient
from queries.domain_sitemap_info import DomainSitemapInfoQuery
from queries.domain_sitemap_link_info import DomainSitemapLinkInfoQuery
from queries.post import PostQuery
from queries.post_category import PostCategoryQuery
from queries.vector import VectorQuery
from queries.upload_file import UploadFileQuery
from utils.date import *
from utils.error import *
from utils.vector import *
from utils.text import *
from payload.reference import *
from domain.reference import *



def helper_insert_post_make_domain_data(payload:insertPostPayload, user_info:dict, server_stage:str):
    try:
        current_time = get_utc_now()
        domain_data = insertPostDomain(
            author=user_info["user_id"],
            company_key=user_info["company_key"],
            title=payload.title,
            content=payload.content,
            reg_date=current_time,
            update_date=current_time,
            image_url=str(payload.image_url) if payload.image_url else "",
            is_on=payload.is_on,
            is_show=payload.is_show,
            lang=payload.lang,
            post_category_id=payload.post_category_id,
            category_depth_1_id=payload.category_depth_1_id,
            category_depth_2_id=payload.category_depth_2_id,
            vector_db_index=user_info["vector_db_index"],
            vector_db_namespace=user_info["vector_db_namespace"],
            server_stage=server_stage,
            store_name=user_info["store_name"]
        )
        if payload.id: # 임시 작성 글에서 실제 글 저장으로 이어질 때, payload에 id가 담겨있음
            domain_data.id = payload.id

        return domain_data

    except DBError as e:
        logging.error(f"[helper.reference.helper_insert_post_make_row] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_insert_post_make_row] Exception: {e}")
        raise e


def helper_insert_post_check_payload_and_build_condition_state(domain_data:insertPostDomain):
    """
    1. check token size: over 8192, raise OverTokenError
    2. build is_from_temp: True if payload.get("id") else False
    3. build is_file: True if payload.get("files") else False
    """

    try:
        domain_data.is_from_temp = True if domain_data.id else False
        domain_data.is_save_to_pinecone = domain_data.content is not None
        domain_data.is_save_to_filesearch = domain_data.store_name is not None and domain_data.content is not None
        if domain_data.content:
            token_size = get_token_length(domain_data.title + "\n\n" + domain_data.content, EMBEDDING_MODEL)
            if token_size > 8192:
                raise OverTokenError(message=f"token_size: {token_size}")
    except OverTokenError as e:
        logging.error(f"[helper.reference.helper_insert_post_check_payload_and_build_condition_state] OverTokenError: {e}")
        raise OverTokenError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_insert_post_check_payload_and_build_condition_state] Exception: {e}")
        raise e


async def helper_insert_post(db:AsyncSession, post_query:PostQuery, domain_data:insertPostDomain):
    try:
        if domain_data.is_from_temp:
            domain_data.is_temp = None
            result = await post_query.update_post(db, domain_data)
        else:
            result = await post_query.insert_post(db, domain_data)

        domain_data.id = result["id"]

    except DBError as e:
        logging.error(f"[helper.reference.helper_insert_post] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_insert_post] Exception: {e}")
        raise e


async def helper_insert_post_save_to_vectordb(db:AsyncSession, vector_db_client:PineconeClient | MilvusClient, llm_proxy_client:LLMProxyClient, vector_query:VectorQuery, domain_data:insertPostDomain):
    try:
        # original_content = re.sub(r'&\S+?;', ' ', strip_html_tags(domain_data.content))
        original_content = html_to_text(domain_data.content)
        content_before_chunking = domain_data.title + "\n\n" + original_content
        content_after_chunking = chunking_text(content_before_chunking, EMBEDDING_MODEL, 500, 150)

        if domain_data.server_stage == DOCKER:
            service = "llm-platform-install"
        elif domain_data.server_stage == REAL:
            service = "llm-platform-production"
        else:
            service = "llm-platform-staging"

        tasks = [llm_proxy_client.embeddings(text=content, service=service) for content in content_after_chunking]
        batch_size = 10
        domain_data.vector_values = []
        for i in range(0, len(tasks), batch_size):
            batched_vector_values_tasks = tasks[i:i+batch_size]
            vector_values_per_batch = await asyncio.gather(*batched_vector_values_tasks)
            domain_data.vector_values.extend(vector_values_per_batch)

        for chunk, _value in enumerate(domain_data.vector_values, start=1):
            domain_data.vector_metadatas.append({
                "id": domain_data.id,
                "company_key": domain_data.company_key,
                "is_show": bool(domain_data.is_show),
                "is_on": bool(domain_data.is_on),
                "page": 1,
                "data_type": "post",
                "chunk": chunk,
                "content": content_after_chunking[chunk - 1]
            })
            # for update, delete
            domain_data.vector_table_datas.append({
                "post_id": domain_data.id,
                "company_key": domain_data.company_key,
                "is_show": bool(domain_data.is_show),
                "is_on": bool(domain_data.is_on),
                "page": 1,
                "data_type": "post",
                "chunk": chunk
            })
        ids_int = await vector_query.bulk_insert_vector_from_post(db, domain_data)
        domain_data.vector_ids = [f"post-{str(id)}" for id in ids_int]
        if len(domain_data.vector_ids) == len(domain_data.vector_values) == len(domain_data.vector_metadatas):
            await vector_db_client.insert_many(ids=domain_data.vector_ids, values=domain_data.vector_values, metadatas=domain_data.vector_metadatas)
        else:
            logging.error(f"[helper.reference.helper_insert_post_save_to_pinecone] vector_ids, vector_values, vector_metadatas length is not same")
            logging.info(f"vector_ids: {len(domain_data.vector_ids)}")
            logging.info(f"vector_values: {len(domain_data.vector_values)}")
            logging.info(f"vector_metadatas: {len(domain_data.vector_metadatas)}")
            raise Exception("vector_ids, vector_values, vector_metadatas length is not same")

    except VectorDBError as e:
        logging.error(f"[helper.reference.helper_insert_post_save_to_vectordb] VectorDBError: {e}")
        raise VectorDBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_insert_post_save_to_vectordb] Exception: {e}")
        raise e


async def helper_insert_post_save_to_filesearch(
        db: AsyncSession,
        s3_client: S3Client,
        llm_proxy_client: LLMProxyClient,
        upload_file_query: UploadFileQuery,
        domain_data: insertPostDomain
):
    try:
        service = SERVICE_LLM_PLATFORM_REAL if domain_data.server_stage == REAL else SERVICE_LLM_PLATFORM_STAGING
        bucket = PARSER_S3_BUCKET_NAME
        key = f"{domain_data.server_stage}/{domain_data.company_key}/post-{domain_data.id}/{domain_data.title}.md"

        content_md = html_to_markdown(domain_data.content)
        content_md_to_byte = content_md.encode("utf-8")

        await s3_client.put_object_to_s3(bucket_name=bucket, object_name=key, file_data=content_md_to_byte)

        domain_data.filesearch_payload["buckets"] = [bucket]
        domain_data.filesearch_payload["keys"] = [key]
        domain_data.filesearch_response = await llm_proxy_client.import_files(
            service=service,
            store_name=domain_data.store_name,
            buckets=domain_data.filesearch_payload["buckets"],
            keys=domain_data.filesearch_payload["keys"]
        )

        await upload_file_query.record_upload_file_history_for_filesearch(db, domain_data)

    except AWSError as e:
        logging.error(f"[helper.reference.helper_insert_post_save_to_filesearch] AWSError: {e}")
        raise AWSError(e)
    except LLMProxyError as e:
        logging.error(f"[helper.reference.helper_insert_post_save_to_filesearch] LLMProxyError: {e}")
        raise LLMProxyError(e)
    except DBError as e:
        logging.error(f"[helper.reference.helper_insert_post_save_to_filesearch] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_insert_post_save_to_filesearch] Exception: {e}")
        raise e


def helper_insert_post_temporary_make_domain_data(payload:insertPostTemporaryPayload, user_info:dict):
    try:
        current_time = get_utc_now()
        return insertPostTemporaryDomain(
            id=payload.id,
            author=user_info["user_id"],
            company_key=user_info["company_key"],
            is_temp=True,
            title=payload.title,
            content=payload.content,
            reg_date=current_time,
            update_date=current_time,
            image_url=str(payload.image_url) if payload.image_url else "0",
            is_on=payload.is_on,
            is_show=payload.is_show,
            lang=payload.lang,
            post_category_id=payload.post_category_id,
            category_depth_1_id=payload.category_depth_1_id,
            category_depth_2_id=payload.category_depth_2_id
        )
    except Exception as e:
        logging.error(f"[helper.reference.helper_insert_post_temporary_make_domain_data] Exception: {e}")
        raise e


async def helper_insert_post_temporary_check_has_temp_post(db:AsyncSession, post_query:PostQuery, domain_data:insertPostTemporaryDomain):
    try:
        check_data = await post_query.get_post_temporary(db, domain_data)
        if check_data and check_data["id"] != domain_data.id:
            raise DataError("already has temp post")
    except DBError as e:
        logging.error(f"[helper.reference.helper_insert_post_temporary_check_has_temp_post] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_insert_post_temporary_check_has_temp_post] Exception: {e}")
        raise e


async def helper_insert_post_temporary_in_to_post_table(db:AsyncSession, post_query:PostQuery, domain_data:insertPostTemporaryDomain):
    try:
        if domain_data.id:
            # update data to Database
            result = await post_query.update_post(db, domain_data)
        else:
            # insert data to Database
            result = await post_query.insert_post(db, domain_data)
        return result

    except DBError as e:
        logging.error(f"[helper.reference.helper_insert_post_temporary_in_to_post_table] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_insert_post_temporary_in_to_post_table] Exception: {e}")
        raise e


def helper_insert_category_make_domain_data(payload:insertCategoryPayload, user_info:dict):
    try:
        current_time = get_utc_now()
        return insertCategoryDomain(
            company_key=user_info["company_key"],
            lang=user_info["lang"],
            name=payload.name,
            parent_id=payload.parentId,
            depth=payload.depth,
            order=payload.order,
            is_on=payload.isOn,
            is_show=payload.isShow,
            reg_date=current_time,
            update_date=current_time
        )
    except Exception as e:
        logging.error(f"[helper.reference.helper_insert_category_make_query_data] Exception: {e}")
        raise DataError(e)


async def helper_insert_category_to_db(db:AsyncSession, post_category_query:PostCategoryQuery, domain_data:insertCategoryDomain):
    try:
        await post_category_query.insert_category(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.reference.helper_insert_category_to_db] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_insert_category_to_db] Exception: {e}")
        raise e


async def helper_get_post_make_domain_data(db:AsyncSession, post_category_query:PostCategoryQuery, payload:getPostPayload, user_info:dict):
    try:
        start_date = string_to_datetime(payload.start_date, "UTC")
        end_date = get_last_hour_of_day(payload.end_date, "UTC")
        category_ids = await post_category_query.get_categories_for_search_by_subquery(db, payload.category_id)

        return getPostDomain(
            company_key=user_info["company_key"],
            is_temp=None,
            is_on=payload.is_on,
            is_show=payload.is_show,
            author=payload.author,
            title=payload.title,
            page=int(payload.page),
            per_page=int(payload.per_page),
            start_date=start_date,
            end_date=end_date,
            category_ids=category_ids
        )

    except DBError as e:
        logging.error(f"[helper.reference.helper_get_post_make_query_data] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_get_post_make_query_data] Exception: {e}")
        raise e


async def helper_get_post_from_db_and_reform(db:AsyncSession, post_query:PostQuery, domain_data:getPostDomain):
    try:
        domain_data.row, domain_data.count = await post_query.get_post(
            db=db,
            domain_data=domain_data
        )
        domain_data.reform_row = reform_post_data(domain_data.row)
    except DBError as e:
        logging.error(f"[helper.reference.helper_get_post_from_db_and_reform] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_get_post_from_db_and_reform] Exception: {e}")
        raise e


def helper_get_post_detail_make_domain_data(payload:getPostDetailPayload, user_info:dict):
    try:
        return getPostDetailDomain(
            id=payload.id,
            company_key=user_info["company_key"]
        )
    except Exception as e:
        logging.error(f"[helper.reference.helper_get_post_detail_make_query_data] Exception: {e}")
        raise DataError(e)


async def helper_get_post_detail_from_db(
    db:AsyncSession,
    post_query:PostQuery,
    post_category_query:PostCategoryQuery,
    domain_data:getPostDetailDomain
):
    try:
        domain_data.row = await post_query.get_post_detail(db, domain_data)
        domain_data.category_row = await post_category_query.get_categories(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.reference.helper_get_post_detail_from_db_and_reform] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_get_post_detail_from_db_and_reform] Exception: {e}")
        raise e


def helper_get_post_detail_reform(
    domain_data:getPostDetailDomain
):
    try:
        domain_data.row["categories"] = reform_categories_data(domain_data)
        domain_data.reform_category_row = reform_categories_data_for_post_detail(domain_data)
        domain_data.row["category"] = reform_category_data(domain_data)
    except Exception as e:
        logging.error(f"[helper.reference.helper_get_post_detail_reform] Exception: {e}")
        raise e


def helper_get_post_temporary_make_query_data(user_info:dict):
    try:
        return getPostTemporaryDomain(
            company_key=user_info["company_key"],
            author=user_info["user_id"],
            is_temp=True
        )
    except Exception as e:
        logging.error(f"[helper.reference.helper_get_post_temporary_make_query_data] Exception: {e}")
        raise DataError(e)


async def helper_get_post_temporary_from_db(
    db:AsyncSession,
    post_query:PostQuery,
    post_category_query:PostCategoryQuery,
    domain_data:getPostTemporaryDomain
):
    try:
        domain_data.row = await post_query.get_post_temporary(db, domain_data)
        if not domain_data.row:
            domain_data.row = None
        else:
            domain_data.category_row = await post_category_query.get_categories(db, domain_data)

    except DBError as e:
        logging.error(f"[helper.reference.helper_get_post_temporary_from_db_and_reform] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_get_post_temporary_from_db_and_reform] Exception: {e}")
        raise e


def helper_get_post_temporary_reform(domain_data:getPostTemporaryDomain):
    try:
        domain_data.row["categories"] = reform_categories_data(domain_data)
        domain_data.reform_category_row = reform_categories_data_for_post_detail(domain_data)
        domain_data.row["category"] = reform_category_data(domain_data)
    except Exception as e:
        logging.error(f"[helper.reference.helper_get_post_temporary_reform] Exception: {e}")
        raise e

async def helper_get_all_categories_from_db(db:AsyncSession, post_category_query:PostCategoryQuery, domain_data:getAllCategoriesDomain):
    try:
        domain_data.category_row = await post_category_query.get_categories(db, domain_data)
    except DBError as e:
        logging.error(e)
        raise DBError(e)
    except Exception as e:
        logging.error(e)
        raise e


def helper_get_all_categories_reform(domain_data:getAllCategoriesDomain):
    try:
        domain_data.reform_row = reform_categories_data(domain_data)
    except Exception as e:
        logging.error(e)
        raise e


def helper_update_post_make_domain_data(payload:updatePostPayload, user_info:dict, server_stage:str):
    try:
        return updatePostDomain(
            author=user_info["user_id"],
            company_key=user_info["company_key"],
            id=payload.id,
            title=payload.title,
            content=payload.content,
            image_url=str(payload.image_url) if payload.image_url else "0",
            is_on=bool(payload.is_on),
            is_show=bool(payload.is_show),
            lang=payload.lang,
            post_category_id=payload.post_category_id,
            category_depth_1_id=payload.category_depth_1_id,
            category_depth_2_id=payload.category_depth_2_id,
            reg_date=None,
            update_date=get_utc_now(),
            is_update=True,
            is_temp=False,
            server_stage=server_stage,
            vector_db_index=user_info["vector_db_index"],
            vector_db_namespace=user_info["vector_db_namespace"],
            store_name=user_info["store_name"]
        )
    except Exception as e:
        logging.error(f"[helper.reference.helper_update_post_make_domain_data] Exception: {e}")
        raise DataError(e)


def helper_update_post_check_payload_and_build_condition_state(domain_data:updatePostDomain):
    try:
        domain_data.is_save_to_pinecone = True if domain_data.content and len(domain_data.content) > 0 else False
        domain_data.is_save_to_filesearch = True if domain_data.store_name and domain_data.content else False
    except Exception as e:
        logging.error(f"[helper.reference.helper_update_post_check_payload_and_build_condition_state] Exception: {e}")
        raise DataError(e)


async def helper_update_post_to_db(db:AsyncSession, post_query:PostQuery, domain_data:updatePostDomain):
    try:
        domain_data.row = await post_query.update_post(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.reference.helper_update_post_to_db] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_update_post_to_db] Exception: {e}")
        raise e


async def helper_update_post_save_to_vectordb(
        db:AsyncSession,
        vector_db_client:PineconeClient | MilvusClient,
        llm_proxy_client:LLMProxyClient,
        vector_query:VectorQuery,
        domain_data:updatePostDomain
    ):
    try:
        # chunking text
        original_content = html_to_text(domain_data.content)
        content_before_chunking = domain_data.title + "\n\n" + original_content
        content_after_chunking = chunking_text(content_before_chunking, EMBEDDING_MODEL, 500, 150)

        if domain_data.server_stage == DOCKER:
            service = "llm-platform-install"
        elif domain_data.server_stage == REAL:
            service = "llm-platform-production"
        else:
            service = "llm-platform-staging"

        tasks = [llm_proxy_client.embeddings(text=content, service=service) for content in content_after_chunking]
        batch_size = 10
        domain_data.vector_values = []
        for i in range(0, len(tasks), batch_size):
            batched_vector_values_tasks = tasks[i:i+batch_size]
            vector_values_per_batch = await asyncio.gather(*batched_vector_values_tasks)
            domain_data.vector_values.extend(vector_values_per_batch)

        # check if the number of chunks is the same as the number of rows in the vector table
        vector_rows = await vector_query.get_vector_row_count(db, domain_data)
        vector_rows = sorted(vector_rows, key=lambda row: row["chunk"])
        if vector_rows: # 작성 당시, 혹은 이 후 청크화된 게시물일 경우
            is_replace = len(content_after_chunking) == len(vector_rows)
            domain_data.vector_ids = [f"post-{row['id']}" for row in vector_rows]
            domain_data.vector_metadatas = [] if not is_replace else [{
                "id": domain_data.id, # post_id
                "company_key": domain_data.company_key,
                "is_show": bool(domain_data.is_show),
                "is_on": bool(domain_data.is_on),
                "data_type": "post",
                "page": 1,
                "chunk": row['chunk']
            } for row in vector_rows]

            if not is_replace: # 청크 갯수가 다른 경우 -> 다 지우고 새로 넣어줌. 청크 갯수가 같은 여길 안타고 그대로 insert!
                for chunk in range(1, len(content_after_chunking) + 1):
                    domain_data.vector_metadatas.append({
                        "id": domain_data.id,
                        "company_key": domain_data.company_key,
                        "is_show": bool(domain_data.is_show),
                        "is_on": bool(domain_data.is_on),
                        "data_type": "post",
                        "page": 1,
                        "chunk": chunk
                    })
                    domain_data.vector_table_datas.append({
                        "post_id": domain_data.id,
                        "company_key": domain_data.company_key,
                        "is_show": bool(domain_data.is_show),
                        "is_on": bool(domain_data.is_on),
                        "data_type": "post",
                        "page": 1,
                        "chunk": chunk
                    })
                if domain_data.vector_ids:
                    await vector_db_client.remove(id=domain_data.vector_ids)
                await vector_query.delete_vector_by_post_id(db, domain_data)
                returning_ids = await vector_query.bulk_insert_vector_from_post(db, domain_data)
                domain_data.vector_ids = [f"post-{_id}" for _id in returning_ids]

        else: # 작성 당시, 혹은 이 후 청크화된 게시물이 없는 경우. 기존에 벡터에 저장된 데이터 지워주고 청크화한 데이터를 새로
            target_remove_ids = [str(domain_data.id)]
            if target_remove_ids:
                await vector_db_client.remove(id=target_remove_ids)

            for chunk, _value in enumerate(domain_data.vector_values, start=1):
                domain_data.vector_metadatas.append({
                    "id": domain_data.id,
                    "company_key": domain_data.company_key,
                    "is_show": bool(domain_data.is_show),
                    "is_on": bool(domain_data.is_on),
                    "page": 1,
                    "data_type": "post",
                    "chunk": chunk
                })
                domain_data.vector_table_datas.append({
                    "post_id": domain_data.id,
                    "company_key": domain_data.company_key,
                    "is_show": bool(domain_data.is_show),
                    "is_on": bool(domain_data.is_on),
                    "page": 1,
                    "data_type": "post",
                    "chunk": chunk
                })
            ids_int = await vector_query.bulk_insert_vector_from_post(db, domain_data)
            domain_data.vector_ids = [f"post-{str(_id)}" for _id in ids_int]

        for metadata, content in zip(domain_data.vector_metadatas, content_after_chunking):
            metadata["content"] = content

        await vector_db_client.insert_many(ids=domain_data.vector_ids, values=domain_data.vector_values, metadatas=domain_data.vector_metadatas)

    except VectorDBError as e:
        logging.error(f"[helper.reference.helper_update_post_save_to_vectordb] VectorDBError: {e}")
        raise VectorDBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_update_post_save_to_vectordb] Exception: {e}")
        raise e


async def helper_update_post_save_to_filesearch(
        db: AsyncSession,
        s3_client: S3Client,
        llm_proxy_client: LLMProxyClient,
        upload_file_query: UploadFileQuery,
        domain_data: updatePostDomain
):
    try:
        service = SERVICE_LLM_PLATFORM_REAL if domain_data.server_stage == REAL else SERVICE_LLM_PLATFORM_STAGING

        document_name = await upload_file_query.get_filesearch_document_name_by_post_id(db, domain_data)
        if document_name:
            await llm_proxy_client.delete_document(service=service, document_name=document_name)

        bucket = PARSER_S3_BUCKET_NAME
        key = f"{domain_data.server_stage}/{domain_data.company_key}/post-{domain_data.id}/{domain_data.title}.md"

        content_md = html_to_markdown(domain_data.content)
        content_md_to_byte = content_md.encode("utf-8")

        await s3_client.put_object_to_s3(bucket_name=bucket, object_name=key, file_data=content_md_to_byte)

        domain_data.filesearch_payload["buckets"] = [bucket]
        domain_data.filesearch_payload["keys"] = [key]
        domain_data.filesearch_response = await llm_proxy_client.import_files(
            service=service,
            store_name=domain_data.store_name,
            buckets=domain_data.filesearch_payload["buckets"],
            keys=domain_data.filesearch_payload["keys"]
        )

        await upload_file_query.record_upload_file_history_for_filesearch(db, domain_data)

    except AWSError as e:
        logging.error(f"[helper.reference.helper_insert_post_save_to_filesearch] AWSError: {e}")
        raise AWSError(e)
    except LLMProxyError as e:
        logging.error(f"[helper.reference.helper_insert_post_save_to_filesearch] LLMProxyError: {e}")
        raise LLMProxyError(e)
    except DBError as e:
        logging.error(f"[helper.reference.helper_insert_post_save_to_filesearch] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_insert_post_save_to_filesearch] Exception: {e}")
        raise e

def helper_update_category_make_domain_data(payload:updateCategoryPayload, user_info:dict):
    try:
        return updateCategoryDomain(
            lang = user_info["lang"],
            company_key = user_info["company_key"],
            categories = payload.categories
        )
    except Exception as e:
        logging.error(f"[helper.reference.helper_update_category_make_domain_data] Exception: {e}")
        raise e


async def helper_update_category_make_seperate_categories_data(db:AsyncSession, post_category_query:PostCategoryQuery, domain_data:updateCategoryDomain):
    try:
        await seperate_categories_for_update(db, post_category_query, domain_data)
    except DBError as e:
        logging.error(f"[helper.reference.helper_update_category_make_seperate_categories_data] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_update_category_make_seperate_categories_data] Exception: {e}")
        raise e


async def helper_update_category_to_db(db:AsyncSession, post_category_query:PostCategoryQuery, domain_data:updateCategoryDomain):
    try:
        if domain_data.insert_list:
            await post_category_query.insert_categories(db, domain_data)
        if domain_data.update_id_list:
            await post_category_query.update_categories(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.reference.helper_update_category_to_db] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_update_category_to_db] Exception: {e}")
        raise e


def helper_delete_post_make_domain_data(payload:deletePostPayload, user_info:dict):
    try:
        return deletePostDomain(
            id=payload.id,
            company_key=user_info["company_key"],
            vector_db_index=user_info["vector_db_index"],
            vector_db_namespace=user_info["vector_db_namespace"]
        )
    except Exception as e:
        logging.error(f"[helper.reference.helper_delete_post_make_domain_data] Exception: {e}")
        raise e


async def helper_delete_post_get_vector(db: AsyncSession, vector_query:VectorQuery, domain_data:deletePostDomain):
    try:
        domain_data.vector_ids_in_db = await vector_query.get_vector_ids_by_post_id(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.reference.helper_delete_post_get_vector] DBError: {e}")
    except Exception as e:
        logging.error(f"[helper.reference.helper_delete_post_get_vector] Exception: {e}")


async def helper_delete_vector_in_vector_db(vector_db_client:PineconeClient|MilvusClient, domain_data:deletePostDomain):
    try:
        if isinstance(domain_data.vector_ids_in_db, list):
            domain_data.vector_ids = [f"post-{post_id_ea}" for post_id_ea in domain_data.vector_ids_in_db]
        else:
            domain_data.vector_ids = str(domain_data.id)
        await vector_db_client.remove(id=domain_data.vector_ids)
    except VectorDBError as e:
        logging.error(f"[helper.reference.helper_delete_vector_in_vector_db] VectorDBError: {e}")
        raise VectorDBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_delete_vector_in_vector_db] Exception: {e}")
        raise e


async def helper_delete_post_get_sitemap_ids(db:AsyncSession, post_query:PostQuery, domain_data:deletePostDomain):
    try:
        domain_data.sitemap_ids = await post_query.get_sitemap_ids_by_id(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.reference.helper_delete_post_get_sitemap_id] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_delete_post_get_sitemap_id] Exception: {e}")
        raise e


async def helper_delete_post_delete_crawler_row(db:AsyncSession, domain_sitemap_info_query:DomainSitemapInfoQuery, domain_sitemap_link_info_query: DomainSitemapLinkInfoQuery, domain_data: deletePostDomain):
    try:
        await domain_sitemap_link_info_query.delete_row_by_parent_sitemap_id(db, domain_data)
        await domain_sitemap_link_info_query.delete_row_by_sitemap_id(db, domain_data)
        await domain_sitemap_info_query.delete_row_by_sitemap_id(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.reference.helper_delete_post_delete_crawler_row] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_delete_post_delete_crawler_row] Exception: {e}")
        raise e



async def helper_delete_post_in_db(db:AsyncSession, post_query:PostQuery, vector_query:VectorQuery, domain_data:deletePostDomain):
    try:
        await vector_query.delete_vector_by_post_id(db, domain_data)
        await post_query.delete_post(db, domain_data)
    except DBError as e:
        logging.error(f"[helper.reference.helper_delete_post_in_db] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_delete_post_in_db] Exception: {e}")
        raise e


def helper_delete_category_make_domain_data(payload:deleteCategoryPayload, user_info:dict):
    try:
        return deleteCategoryDomain(
            id=payload.id,
            company_key=user_info["company_key"]
        )
    except Exception as e:
        logging.error(f"[helper.reference.helper_delete_category_make_domain_data] Exception: {e}")
        raise e



# =============================
# legacy method + helper method
# =============================
def strip_html_tags(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return text


async def seperate_categories_for_update(db:AsyncSession, post_category_query:PostCategoryQuery, domain_data:updateCategoryDomain):
    try: # categories:list, company_key:str, lang:str
        current_time = get_utc_now()
        datetime_format = "%a, %d %b %Y %H:%M:%S %z"
        async def process_category(category, order, parent_id=None):
            if category.get("id"):
                domain_data.update_id_list.append(category["id"])
                domain_data.update_data_list.append(
                    {
                        "depth": category["depth"],
                        "is_on": category["is_on"],
                        "is_show": category["is_show"],
                        "lang": category["lang"],
                        "name": category["name"],
                        "order": order,
                        "parent_id": category["parent_id"],
                        "reg_date": adapt_timezone_str_to_datetime(category["reg_date"], "UTC", datetime_format=datetime_format) if category.get("reg_date") else current_time
                    }
                )
            else:
                domain_data.name = category["name"]
                domain_data.depth = category["depth"]
                domain_data.parent_id = parent_id if parent_id else 0
                domain_data.order = order
                domain_data.is_on = True
                domain_data.is_show = True
                domain_data.reg_date = adapt_timezone_str_to_datetime(category["reg_date"], "UTC", datetime_format=datetime_format) if category.get("reg_date") else current_time
                await post_category_query.insert_category(db, domain_data)


        async def make_first_category(category, order, parent_id=None):
            if category.get("id"):
                data = {
                    "id": category["id"],
                    "depth": category["depth"],
                    "is_on": category.get("is_on", True),
                    "is_show": category.get("is_show", True),
                    "lang": domain_data.lang,
                    "name": category["name"],
                    "parent_id": category.get("parent_id", 0),
                    "reg_date": category["reg_date"]
                }
            else:
                domain_data.depth = category["depth"]
                domain_data.is_on = category.get("is_on", True)
                domain_data.is_show = category.get("is_show", True)
                domain_data.lang = domain_data.lang
                domain_data.name = category["name"]
                domain_data.parent_id = parent_id if parent_id else 0
                domain_data.reg_date = adapt_timezone_str_to_datetime(category["reg_date"], "UTC", datetime_format=datetime_format) if category.get("reg_date") else current_time
                domain_data.order = order

                data = await post_category_query.insert_category(db, domain_data)
                data["reg_date"] = datetime_to_string(datetime_obj=data["reg_date"], datetime_format=datetime_format, timezone_str="UTC")
            return data


        parent_order = 0
        for category in domain_data.categories:
            parent_category = await make_first_category(category, parent_order)
            await process_category(parent_category, parent_order)
            parent_id = parent_category.get("id")
            parent_order += 1
            child_order = 0
            for child in category.get("children", []):
                if not child.get("children"):
                    await process_category(child, child_order, parent_id)
                    child_order += 1
                else:
                    child_category = await make_first_category(child, child_order, parent_id)
                    await process_category(child_category, child_order, parent_id)
                    child_id = child_category.get("id")
                    child_order += 1
                    grandchild_order = 0
                    for grandchild in child.get("children", []):
                        await process_category(grandchild, grandchild_order, child_id)
                        grandchild_order += 1

    except DBError as e:
        logging.error(f"[helper.reference.seperate_categories_for_update] DBError: {e}")
        raise DBError(e)
    except Exception as e:
        logging.error(f"[helper.reference.seperate_categories_for_update] Exception: {e}")
        raise e


def reform_categories_data(domain_data:getPostDetailDomain | getAllCategoriesDomain):
    if domain_data.category_row is None:
        return []
    else:
        first_depth = {}
        second_depth = {}
        third_depth = []
        for data in domain_data.category_row:
            if data["depth"] == 1:
                if not data.get("children"):
                    data["children"] = []
                first_depth[data["id"]] = data
            elif data["depth"] == 2:
                if not data.get("children"):
                    data["children"] = []
                second_depth[data["id"]] = data
            elif data["depth"] == 3:
                third_depth.append(data)

        third_depth.sort(key=lambda x: x["order"])
        for third_data in third_depth:
            if second_depth[third_data['parent_id']].get("children"):
                second_depth[third_data["parent_id"]]["children"].append(third_data)
            else:
                second_depth[third_data["parent_id"]]["children"] = [third_data]
            second_depth[third_data["parent_id"]]["children"].sort(key=lambda x: x["order"])

        for second_data in second_depth.values():
            if first_depth[second_data["parent_id"]].get("children"):
                first_depth[second_data["parent_id"]]["children"].append(second_data)
            else:
                first_depth[second_data["parent_id"]]["children"] = [second_data]
            first_depth[second_data["parent_id"]]["children"].sort(key=lambda x: x["order"])
        result = sorted(first_depth.values(), key=lambda x: x["order"])
        return result


def reform_categories_data_for_post_detail(domain_data:getPostDetailDomain):
    result = {1:[], 2:[], 3:[]}
    if domain_data.category_row:
        for data in domain_data.category_row:
            if data["depth"] == 1:
                result[1].append(data)
            elif data["depth"] == 2:
                result[2].append(data)
            elif data["depth"] == 3:
                result[3].append(data)
    return result


def reform_post_data(datas):
    results = []
    for data in datas:
        result = {
            "id": data["id"],
            "title": data["title"],
            "reg_date": data["reg_date"],
            "update_date": data["update_date"],
            "is_on": data["is_on"],
            "lang": data["lang"],
            "source": data["source"],
            "use_count": data["use_count"],
            "author": data["author"]
        }
        if not data["post_category_id"]:
            result["depth1"] = {"id": None, "name": None}
            result["depth2"] = {"id": None, "name": None}
            result["depth3"] = {"id": None, "name": None}
        elif data["post_category_depth"] == 1:
            result["depth1"] = {"id": data["post_category_id"], "name": data["post_category_name"]}
            result["depth2"] = {"id": None, "name": None}
            result["depth3"] = {"id": None, "name": None}
        elif data["post_category_depth"] == 2:
            result["depth1"] = {"id": data["category_depth_1_id"], "name": data["category_depth_1_name"]}
            result["depth2"] = {"id": data["post_category_id"], "name": data["post_category_name"]}
            result["depth3"] = {"id": None, "name": None}
        elif data["post_category_depth"] == 3:
            result["depth1"] = {"id": data["category_depth_1_id"], "name": data["category_depth_1_name"]}
            result["depth2"] = {"id": data["category_depth_2_id"], "name": data["category_depth_2_name"]}
            result["depth3"] = {"id": data["post_category_id"], "name": data["post_category_name"]}
        results.append(result)
    return results


def reform_category_data(domain_data:getPostDetailDomain):
    if not domain_data.row['post_category_depth']:
        result = {1: None, 2: None, 3: None}

    elif domain_data.row['post_category_depth'] == 1:
        result = {1: domain_data.row["post_category_name"], 2: None, 3: None}

    elif domain_data.row['post_category_depth'] == 2:
        result = {2: domain_data.row["post_category_name"], 3: None}
        parent_id = domain_data.row["post_category_parent_id"]
        for parent_data in domain_data.reform_category_row[1]:
            if parent_data["id"] == parent_id:
                result[1] = parent_data["name"]

    elif domain_data.row['post_category_depth'] == 3:
        result = {3: domain_data.row["post_category_name"]}
        parent_id = domain_data.row["post_category_parent_id"]
        for parent_data in domain_data.reform_category_row[2]:
            if parent_data["id"] == parent_id:
                result[2] = parent_data["name"]
                grand_parent_id = parent_data["parent_id"]
                for grand_parent_data in domain_data.reform_category_row[1]:
                    if grand_parent_data["id"] == grand_parent_id:
                        result[1] = grand_parent_data["name"]
    return result


async def helper_upload_base64_to_s3(s3_client:S3Client, payload:uploadBase64Payload, user_info:dict):
    try:
        base64_data = payload.image

        # Base64 데이터에서 메타데이터 제거
        base64_data = base64_data.replace("data:image/png;base64,", "").replace("data:image/jpeg;base64,", "")
        base64_data = base64_data.replace("data:image/webp;base64,", "").replace("data:image/jpg;base64,", "")

        # Base64를 바이트로 변환
        image_data = base64.b64decode(base64_data)

        if len(image_data) > 1024 * 1024 * 10:
            return {
                "success": False,
                "error": {
                    "name": "MulterError",
                    "message": "File too large",
                    "code": "LIMIT_FILE_SIZE",
                    "field": "upload",
                    "storageErrors": []
                }
            }

        # 이미지 처리
        image = Image.open(io.BytesIO(image_data))
        image_meta = {
            "width": image.width,
            "height": image.height,
            "format": image.format.lower()
        }

        quality_width_limit = 820
        if image_meta["width"] > quality_width_limit:
            image = image.resize((quality_width_limit, int(image_meta["height"] * (quality_width_limit / image_meta["width"]))))

        quality_size_limit = 1024 * 300
        if len(image_data) >= quality_size_limit:
            image.save(io.BytesIO(), format=image_meta["format"], quality=80)

        # S3에 업로드
        buffer = io.BytesIO()
        image.save(buffer, format=image_meta["format"])
        buffer.seek(0)
        filename = f"{user_info['company_key']}/" + str(uuid4()).replace("-", "") + ".png"
        bucket_name = BUCKET
        await s3_client.upload_to_s3(buffer, bucket_name, filename)
        location = S3Client.get_public_url(bucket_name, filename)

        return {
            "success": True,
            "url": location,
            "fileName": 'test',
            "uploaded": 1
        }

    except AWSError as e:
        logging.error(f"[helper.reference.helper_upload_base64_to_s3] AWSError: {e}")
        raise AWSError(e)
    except Exception as e:
        logging.error(f"[helper.reference.helper_upload_base64_to_s3] Exception: {e}")
        raise e
