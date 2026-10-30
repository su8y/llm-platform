from fastapi import Form
from pydantic import BaseModel, Field
from typing import Optional



class uploadFileFormData:
    def __init__(
            self,
            current_dir_id: Optional[str] = Form(None, alias="currentDirId")
    ):
        self.current_dir_id = current_dir_id


class retryPayload(BaseModel):
    file_id: list[int] | int = Field(..., alias="fileId")


class makeDirectoryPayload(BaseModel):
    dir_name: str = Field(..., alias="dirName")
    current_dir_id: int = Field(..., alias="currentDirId")


class copyFilePayload(BaseModel):
    to_dir_id: int = Field(..., alias="toDirId")
    dir_id: Optional[int] = Field(None, alias="dirId")
    file_id: Optional[int] = Field(None, alias="fileId")


class GetStatusQueryParams(BaseModel):
    file_id: int = Field(..., alias="fileId")
    status: int = Field(..., alias="status")


class getPageQueryParams(BaseModel):
    page: Optional[int] = Field(1, alias="page")
    per_page: Optional[int] = Field(10, alias="perPage")
    dir_id: Optional[int] = Field(None, alias="currentDirId")
    name: Optional[str] = Field(None, alias="name")
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")


class searchPayload(BaseModel):
    is_on: Optional[bool] = Field(None, alias="isOn")
    is_show: Optional[bool] = Field(None, alias="isShow")
    filetype: Optional[str] = Field(None, alias="filetype")
    name: Optional[str] = Field(None, alias="name")
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")
    page: Optional[int] = Field(1, alias="page")
    per_page: Optional[int] = Field(10, alias="perPage")


class searchFilePayload(BaseModel):
	name: Optional[str] = Field(None, alias="name")
	filetype: Optional[str] = Field(None, alias="filetype")
	is_on: Optional[bool] = Field(None, alias="isOn")
	is_show: Optional[bool] = Field(None, alias="isShow")
	start_date: Optional[str] = Field(None, alias="startDate")
	end_date: Optional[str] = Field(None, alias="endDate")
	page: Optional[int] = Field(1, alias="page")
	per_page: Optional[int] = Field(10, alias="perPage")


class getFileInfoQueryParams(BaseModel):
    file_id: int = Field(..., alias="fileId")


class fileViewQueryParams(BaseModel):
    file_id: int = Field(..., alias="fileId")
    page: Optional[int] = Field(1, alias="page")


class GetFilenamesQueryParams(BaseModel):
    page: Optional[int] = Field(1, alias="page")
    per_page: Optional[int] = Field(10, alias="per_page")


class downloadFileQueryParams(BaseModel):
    file_id: int = Field(..., alias="fileId")


class moveToDirectoryPayload(BaseModel):
    file_id: Optional[int] = Field(None, alias="fileId")
    dir_id: Optional[int] = Field(None, alias="dirId")
    to_dir_id: int = Field(..., alias="toDirId")


class renamePayload(BaseModel):
    file_id: Optional[int] = Field(None, alias="fileId")
    dir_id: Optional[int] = Field(None, alias="dirId")
    new_name: str = Field(..., alias="newName")


class updateParserCreditAvailablePayload(BaseModel):
    parser_credit_available: int = Field(..., alias="parserCreditAvailable")


class updateFileContentPayload(BaseModel):
    file_id: int = Field(..., alias="fileId")
    current_page: list[int] | list[str] = Field(..., alias="currentPage")
    content: list[str] = Field(..., alias="content")


class EnrollFileSearchStorePayload(BaseModel):
    company_key: Optional[str] = Field(None, alias="companyKey")


class deletePayload(BaseModel):
    file_id: Optional[int] = Field(None, alias="fileId")
    dir_id: Optional[int] = Field(None, alias="dirId")


class deleteFilePayload(BaseModel):
    file_id: int = Field(..., alias="fileId")


class chargeCreditPayload(BaseModel):
    charge_credit: int = Field(..., alias="chargeCredit")


class callbackFromParserPayload(BaseModel):
    status: str = Field(..., alias="status")
    id: int = Field(..., alias="id")
    company_key: str = Field(..., alias="companyKey")
    file_s3_path: str = Field(..., alias="fileS3Path")
    vector_db_index: str = Field(..., alias="vectorDbIndex")
    vector_db_namespace: str = Field(..., alias="vectorDbNamespace")
    error_page: Optional[list] = Field(None, alias="errorPages")
