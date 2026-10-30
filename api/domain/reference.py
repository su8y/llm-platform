from pydantic import BaseModel
from datetime import datetime

from utils.date import get_utc_now



class insertPostDomain(BaseModel):
    title: str
    content: str
    image_url: str | None = None
    author: str
    company_key: str
    reg_date: datetime = get_utc_now()
    update_date: datetime = get_utc_now()
    is_on: bool = True
    is_show: bool
    lang: str
    post_category_id: int | None = None
    category_depth_1_id: int | None = None
    category_depth_2_id: int | None = None
    id: int | None = None
    is_temp: bool | None = False
    vector_db_index: str
    vector_db_namespace: str
    server_stage: str
    store_name: str | None = None

    is_from_temp: bool | None = None
    is_save_to_pinecone: bool | None = None
    is_save_to_filesearch: bool | None = None

    vector_ids: list[str] = []
    vector_values: list = []
    vector_metadatas: list[dict] = []
    vector_table_datas: list[dict] = []

    filesearch_payload: dict = {}
    filesearch_response: dict = {}



class insertPostTemporaryDomain(BaseModel):
    title: str
    content: str
    image_url: str | None = None
    author: str
    company_key: str
    reg_date: datetime = get_utc_now()
    update_date: datetime = get_utc_now()
    is_on: bool = True
    is_show: bool
    lang: str
    post_category_id: int | None = None
    category_depth_1_id: int | None = None
    category_depth_2_id: int | None = None
    id: int | None = None

    is_temp: bool = True
    is_from_temp: bool = True
    is_save_to_pinecone: bool = False


class insertCategoryDomain(BaseModel):
    company_key: str
    lang: str
    name: str
    parent_id: int | None = None
    depth: int
    order: int
    is_on: bool
    is_show: bool
    reg_date: datetime
    update_date: datetime


class getPostDomain(BaseModel):
    company_key: str
    is_temp: bool | None = None
    is_on: bool | None = None
    is_show: bool | None = None
    author: str | None = None
    title: str | None = None
    page: int | None = None
    per_page: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    category_ids: list[int] | None = None

    row: dict | None = None
    reform_row: dict | None = None
    count: int | None = None


class getPostDetailDomain(BaseModel):
    id: int
    company_key: str

    row: dict | None = None
    category_row: dict | None = None
    reform_category_row: dict | None = None


class getPostTemporaryDomain(BaseModel):
    company_key: str
    author: str
    is_temp: bool

    row: dict | None = None
    category_row: dict | None = None
    reform_category_row: int | None = None


class getAllCategoriesDomain(BaseModel):
    company_key: str

    category_row: dict | None = None
    reform_row: dict | None = None


class updatePostDomain(BaseModel):
    author: str
    company_key: str
    id: int
    title: str
    content: str
    image_url: str
    is_on: bool
    is_show: bool
    lang: str
    post_category_id: int | None = None
    category_depth_1_id: int | None = None
    category_depth_2_id: int | None = None
    reg_date: datetime | None = None
    update_date: datetime
    is_update: bool
    is_temp: bool
    server_stage: str
    vector_db_index: str
    vector_db_namespace: str
    store_name: str | None = None

    row: dict | None = None
    is_save_to_pinecone: bool | None = None
    is_save_to_filesearch: bool | None = None

    vector_ids: list[str] = []
    vector_values: list = []
    vector_metadatas: list[dict] = []
    vector_table_datas: list[dict] = []

    filesearch_payload: dict = {}
    filesearch_response: dict = {}


class updateCategoryDomain(BaseModel):
    company_key: str
    lang: str
    categories: list[dict]

    name: str | None = None
    depth: int | None = None
    parent_id: int | None = None
    order: int | None = None
    is_on: bool | None = None
    is_show: bool | None = None
    reg_date: datetime | None = None
    update_date: datetime | None = None

    insert_list: list[dict] = []
    update_id_list: list[int] = []
    update_data_list: list[dict] = []


class deletePostDomain(BaseModel):
    id: list[int] | int
    company_key: str
    vector_db_index: str
    vector_db_namespace: str

    post_ids: list[str] | str | None = None
    vector_ids_in_db: list[int] | None = None
    vector_ids: list[str] | str | None = None

    sitemap_ids: list[int]|None = None


class deleteCategoryDomain(BaseModel):
    id: int
    company_key: str
