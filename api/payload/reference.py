from pydantic import BaseModel, Field
from typing import Optional



class insertPostPayload(BaseModel):
	title: Optional[str] = Field(None, alias="title")
	content: Optional[str] = Field(None, alias="content")
	id: Optional[int] = Field(None, alias="id")
	files: Optional[list] = Field(None, alias="files")
	image_url: Optional[list] = Field(None, alias="image_url")
	is_on: Optional[bool] = Field(True, alias="is_on")
	is_show: Optional[bool] = Field(True, alias="is_show")
	lang: Optional[str] = Field("ko", alias="lang")
	post_category_id: Optional[int] = Field(None, alias="post_category_id")
	category_depth_1_id: Optional[int] = Field(None, alias="category_depth_1_id")
	category_depth_2_id: Optional[int] = Field(None, alias="category_depth_2_id")


class insertPostTemporaryPayload(BaseModel):
	title: Optional[str] = Field(None, alias="title")
	content: Optional[str] = Field(None, alias="content")
	id: Optional[int] = Field(None, alias="id")
	image_url: Optional[str] = Field(None, alias="image_url")
	is_on: Optional[bool] = Field(True, alias="is_on")
	is_show: Optional[bool] = Field(True, alias="is_show")
	lang: Optional[str] = Field("ko", alias="lang")
	post_category_id: Optional[int] = Field(None, alias="post_category_id")
	category_depth_1_id: Optional[int] = Field(None, alias="category_depth_1_id")
	category_depth_2_id: Optional[int] = Field(None, alias="category_depth_2_id")


class insertCategoryPayload(BaseModel):
	name: str = Field(..., alias="name")
	parentId: Optional[int] = Field(0, alias="parentId")
	depth: Optional[int] = Field(1, alias="depth")
	order: Optional[int] = Field(0, alias="order")
	isOn: Optional[bool] = Field(True, alias="isOn")
	isShow: Optional[bool] = Field(True, alias="isShow")


class getPostPayload(BaseModel):
	is_on: Optional[bool] = Field(None, alias="is_on")
	is_show: Optional[bool] = Field(None, alias="is_show")
	author: Optional[str] = Field(None, alias="author")
	title: Optional[str] = Field(None, alias="title")
	start_date: Optional[str] = Field(None, alias="start_date")
	end_date: Optional[str] = Field(None, alias="end_date")
	page: Optional[int] = Field(1, alias="page")
	per_page: Optional[int] = Field(20, alias="per_page")
	category_id: Optional[int] = Field(None, alias="category_id")


class getPostDetailPayload(BaseModel):
	id: int = Field(..., alias="id")


class updatePostPayload(BaseModel):
	id: int = Field(..., alias="id")
	title: Optional[str] = Field(None, alias="title")
	content: Optional[str] = Field(None, alias="content")
	image_url: Optional[list | str] = Field(None, alias="image_url")
	is_on: Optional[int|bool] = Field(True, alias="isOn")
	is_show: Optional[int|bool] = Field(True, alias="is_show")
	lang: Optional[str] = Field("ko", alias="lang")
	post_category_id: Optional[int] = Field(None, alias="post_category_id")
	category_depth_1_id: Optional[int] = Field(None, alias="category_depth_1_id")
	category_depth_2_id: Optional[int] = Field(None, alias="category_depth_2_id")


class updateCategoryPayload(BaseModel):
	categories: list = Field(..., alias="categories")


class deletePostPayload(BaseModel):
	id: list[int] | int = Field(..., alias="id")


class deleteCategoryPayload(BaseModel):
	id: int = Field(..., alias="id")


class uploadBase64Payload(BaseModel):
	image: str = Field(..., alias="image")
 

class getTokensizePayload(BaseModel):
	title: Optional[str] = Field(None, alias="title")
	content: str = Field(..., alias="content")