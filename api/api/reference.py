from fastapi import APIRouter, Depends

from models import get_db, close_db
from auth.dependencies import get_user_info
from helper.reference import *
from queries.domain_sitemap_info import DomainSitemapInfoQuery
from queries.domain_sitemap_link_info import DomainSitemapLinkInfoQuery
from utils.error import *
from client.milvus import MilvusClient



router = APIRouter(
    prefix="/reference",
    tags=["reference"],
)



@router.post("/insert_post")
@handle_errors()
async def insert_post(
    payload:insertPostPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    server_stage = os.getenv("SERVER_STAGE", "development")

    if user_info["plan_info_id"] == EXPIRED_PLAN_INFO_ID:
        logging.info(f"[reference.insert_post] Occured ExpiredPlanError. user_id: {user_info['user_id']}, plan_info_id: {user_info['plan_info_id']}")
        raise ExpiredPlanError

    # set client
    post_query = PostQuery()

    # business logic
    domain_data:insertPostDomain = helper_insert_post_make_domain_data(payload, user_info, server_stage)
    helper_insert_post_check_payload_and_build_condition_state(domain_data)
    await helper_insert_post(db, post_query, domain_data)
    if domain_data.is_save_to_pinecone: # save to pinecone
        vector_db_client = PineconeClient(index_name=domain_data.vector_db_index, namespace=domain_data.vector_db_namespace) if server_stage != DOCKER else MilvusClient(collection_name=f"_{domain_data.vector_db_namespace}")
        llm_proxy_client = LLMProxyClient()
        vector_query = VectorQuery()
        await helper_insert_post_save_to_vectordb(db, vector_db_client, llm_proxy_client, vector_query, domain_data)
    if domain_data.is_save_to_filesearch:
        s3_client = S3Client()
        llm_proxy_client = LLMProxyClient()
        upload_file_query = UploadFileQuery()
        await helper_insert_post_save_to_filesearch(db, s3_client, llm_proxy_client, upload_file_query, domain_data)

    # make response and return
    await close_db(db)
    return Response200().to_dict()


@router.post("/insert_post_temporary")
@handle_errors()
async def insert_post_temporary(
    payload:insertPostPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    if user_info["plan_info_id"] == EXPIRED_PLAN_INFO_ID:
        logging.info(f"[reference.insert_post_temporary] Occured ExpiredPlanError. user_id: {user_info['user_id']}, plan_info_id: {user_info['plan_info_id']}")
        raise ExpiredPlanError

    # set client
    post_query = PostQuery()

    # business logic
    domain_data = helper_insert_post_temporary_make_domain_data(payload, user_info)
    await helper_insert_post_temporary_check_has_temp_post(db, post_query, domain_data)
    await helper_insert_post_temporary_in_to_post_table(db, post_query, domain_data)

    # make response and return
    return Response200().to_dict()


@router.post("/insert_category")
@handle_errors()
async def insert_category(
    payload:insertCategoryPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    if user_info["plan_info_id"] == EXPIRED_PLAN_INFO_ID:
        logging.info(f"[reference.insert_category] Occured ExpiredPlanError. user_id: {user_info['user_id']}, plan_info_id: {user_info['plan_info_id']}")
        raise ExpiredPlanError

    # set client
    post_category_query = PostCategoryQuery()

    # business logic
    domain_data = helper_insert_category_make_domain_data(payload, user_info)
    await helper_insert_category_to_db(db, post_category_query, domain_data)
    return Response200().to_dict()


@router.post("/get_post")
@handle_errors()
async def get_post(
    payload:getPostPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    post_query = PostQuery()
    post_category_query = PostCategoryQuery()

    # business logic
    domain_data:getPostDomain = await helper_get_post_make_domain_data(db, post_category_query, payload, user_info)
    await helper_get_post_from_db_and_reform(db, post_query, domain_data)

    # make response and return
    data = {"post": domain_data.reform_row, "count": domain_data.count}
    return Response200(data=data).to_dict()


@router.post("/get_post_detail")
@handle_errors()
async def get_post_detail(
    payload:getPostDetailPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    post_query = PostQuery()
    post_category_query = PostCategoryQuery()

    # business logic
    domain_data:getPostDetailDomain = helper_get_post_detail_make_domain_data(payload, user_info)
    await helper_get_post_detail_from_db(db, post_query, post_category_query, domain_data)

    # make response and return
    helper_get_post_detail_reform(domain_data)
    data:dict = domain_data.row
    return Response200(data=data).to_dict()


@router.get("/get_post_temporary_detail")
@handle_errors()
async def get_post_temporary(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    post_query = PostQuery()
    post_category_query = PostCategoryQuery()

    # business logic
    domain_data:getPostTemporaryDomain = helper_get_post_temporary_make_query_data(user_info)
    await helper_get_post_temporary_from_db(db, post_query, post_category_query, domain_data)

    # make response and return
    if domain_data.row:
        helper_get_post_temporary_reform(domain_data)
        data:dict = domain_data.row
    else:
        data = None
    return Response200(data=data).to_dict()


@router.get("/get_all_categories")
@handle_errors()
async def get_all_categories(
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    post_category_query = PostCategoryQuery()

    # business logic
    domain_data:getAllCategoriesDomain = getAllCategoriesDomain(company_key=user_info["company_key"])
    await helper_get_all_categories_from_db(db, post_category_query, domain_data)


    # make response and return
    helper_get_all_categories_reform(domain_data)
    data:dict = domain_data.reform_row
    return Response200(data=data).to_dict()


@router.post("/update_post")
@handle_errors()
async def update_post(
    payload:updatePostPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # check server stage
    server_stage = os.getenv("SERVER_STAGE", "development")

    # set client
    post_query = PostQuery()

    # business logic
    domain_data:updatePostDomain = helper_update_post_make_domain_data(payload, user_info, server_stage)
    await helper_update_post_to_db(db, post_query, domain_data)
    helper_update_post_check_payload_and_build_condition_state(domain_data)
    if domain_data.is_save_to_pinecone:
        vector_db_client = PineconeClient(index_name=domain_data.vector_db_index, namespace=domain_data.vector_db_namespace) if domain_data.server_stage != DOCKER else MilvusClient(collection_name=f"_{domain_data.vector_db_namespace}")
        llm_proxy_client = LLMProxyClient()
        vector_query = VectorQuery()
        await helper_update_post_save_to_vectordb(db, vector_db_client, llm_proxy_client, vector_query, domain_data)
    if domain_data.is_save_to_filesearch:
        s3_client = S3Client()
        llm_proxy_client = LLMProxyClient()
        upload_file_query = UploadFileQuery()
        await helper_update_post_save_to_filesearch(db, s3_client, llm_proxy_client, upload_file_query, domain_data)

    # make response and return
    await close_db(db)
    return Response200().to_dict()


@router.post("/update_category")
@handle_errors()
async def update_category(
    payload:updateCategoryPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    post_category_query = PostCategoryQuery()

    # business logic
    domain_data:updateCategoryDomain = helper_update_category_make_domain_data(payload, user_info)
    await helper_update_category_make_seperate_categories_data(db, post_category_query, domain_data)
    await helper_update_category_to_db(db, post_category_query, domain_data)

    # make response and return
    return Response200().to_dict()


@router.post("/delete_post")
@handle_errors()
async def delete_post(
    payload:deletePostPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # check server stage
    server_stage = os.getenv("SERVER_STAGE", "development")

    # set client
    vector_db_client = PineconeClient(index_name=user_info["vector_db_index"], namespace=user_info["vector_db_namespace"]) if server_stage != DOCKER else MilvusClient(collection_name=f"_{user_info['vector_db_namespace']}")
    post_query = PostQuery()
    vector_query = VectorQuery()

    # business logic
    domain_data:deletePostDomain = helper_delete_post_make_domain_data(payload, user_info)
    await helper_delete_post_get_vector(db, vector_query, domain_data)
    await helper_delete_vector_in_vector_db(vector_db_client, domain_data)
    await helper_delete_post_get_sitemap_ids(db, post_query, domain_data)
    if domain_data.sitemap_ids:
        domain_sitemap_info_query = DomainSitemapInfoQuery()
        domain_sitemap_link_info_query = DomainSitemapLinkInfoQuery()
        await helper_delete_post_delete_crawler_row(db, domain_sitemap_info_query, domain_sitemap_link_info_query, domain_data)
    await helper_delete_post_in_db(db, post_query, vector_query, domain_data)

    # make response and return
    await close_db(db)
    return Response200().to_dict()


@router.post("/delete_category")
@handle_errors()
async def delete_category(
    payload:deleteCategoryPayload,
    user_info:dict = Depends(get_user_info),
    db:AsyncSession = Depends(get_db)
):
    # set client
    post_query = PostQuery()
    post_category_query = PostCategoryQuery()

    # business logic
    domain_data:deleteCategoryDomain = helper_delete_category_make_domain_data(payload, user_info)
    is_not_able_delete = await post_query.get_post_by_category_id(db, domain_data)
    if is_not_able_delete:
        return Response998().to_dict() #TODO: change to raise error and add error response to handle_errors()
    await post_category_query.delete_category(db, domain_data)
    return Response200().to_dict()


@router.post("/image_upload_base64")
@handle_errors()
async def upload_base64(
    payload:uploadBase64Payload,
    user_info:dict = Depends(get_user_info),
):
    # set client
    s3_client = S3Client()

    # business logic
    result = await helper_upload_base64_to_s3(s3_client, payload, user_info)

    # make response and return
    return ORJSONResponse(content=result)


# token calculate
@router.post("/get_tokensize")
@handle_errors()
async def get_tokensize(
    payload:getTokensizePayload,
    user_info:dict = Depends(get_user_info),
):
    # business logic
    target_content = html_to_text(payload.content) if not payload.title else payload.title + "\n\n" + html_to_text(payload.content)
    token_size = get_token_length(target_content, EMBEDDING_MODEL)
    is_able = True if token_size <= 8150 else False

    # make response and return
    data = {
        "is_able": is_able,
        "token_size": token_size
    }
    message = f"token limit is 8150. your token of title + content is {token_size}"
    return Response200(data=data, message=message).to_dict() if is_able else Response999(data=data, message=message).to_dict()
