import ast
import logging
import asyncio
from markdown import markdown
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from client.aws import S3Client
from client.pinecone import PineconeClient
from client.groxy import LLMProxyClient
from client.mysql import MySQLClient
from queries.vector import VectorQuery
from queries.drive import DriveQuery
from queries.company_info import CompanyInfoQuery
from queries.file_credit_history import FileCreditHistoryQuery
from payload.drive import callbackFromParserPayload
from module.Parser.dto import callbackArgs
from utils.vector import chunking_text
from utils.error import VectorDBError, DBError, AWSError, LLMProxyError
from utils.constants import *


class FromParser:
    """
    FOR DRIVE, POST.
    THERE ARE 2 WAY TO UPLOAD FILE.
    1. UPLOAD FILE FROM POST
    2. UPLOAD FILE FROM DRIVE
    """
    def __init__(
        self,
        db: AsyncSession,
        s3_client: S3Client,
        vector_db_client: PineconeClient,
        llm_proxy_client: LLMProxyClient,
        vector_query: VectorQuery,
        drive_query: DriveQuery,
        company_info_query: CompanyInfoQuery,
        file_credit_query: FileCreditHistoryQuery,
        info: callbackFromParserPayload,
        server_stage: str
    ):

        self.args = callbackArgs(
            db=db,
            s3_client=s3_client,
            vector_db_client=vector_db_client,
            llm_proxy_client=llm_proxy_client,
            vector_query=vector_query,
            drive_query=drive_query,
            company_info_query=company_info_query,
            file_credit_query=file_credit_query,
            status=info.status,
            id=info.id,
            company_key=info.company_key,
            file_s3_path=info.file_s3_path,
            vector_db_index=info.vector_db_index,
            vector_db_namespace=info.vector_db_namespace,
            error_page=info.error_page,
            server_stage=server_stage
        )



    async def activate(self):
        try:
            logging.info(f"[module.parser.callback.FromParser.activate] upload_file_id: {self.args.id}, status: {self.args.status}, server_stage: {self.args.server_stage}, company_key: {self.args.company_key}, error_page: {self.args.error_page}")
            if self.args.status == SUCCESS:
                logging.info(f"[module.parser.callback.FromParser.activate] upload_file_id={self.args.id}: parser complete to parse all documents")
                await self.delete_vector_by_upload_file_id()
                await self.get_error_page()
                await self.get_file_datas_from_s3()
                await self.insert_row_vector_data_in_db()
                await self.upsert_file_parser_result_in_vector_db()
                await self.decrease_parser_credit_available()
                await self.update_drive_row_status_success()
                logging.info(f"[module.parser.callback.FromParser.activate] upload_file_id={self.args.id}: all success callback action is finished")
            
            elif self.args.status == ERROR and self.args.error_page:
                logging.info(f"[module.parser.callback.FromParser.activate] upload_file_id={self.args.id}: parser complete parse, but failed some pages")
                await self.get_error_page()
                await self.update_drive_row_status_partial_error()
                if self.args.file_s3_path:
                    await self.delete_vector_by_upload_file_id()
                    await self.get_file_datas_from_s3()
                    await self.insert_row_vector_data_in_db()
                    await self.upsert_file_parser_result_in_vector_db()
                    await self.decrease_parser_credit_available()
                logging.info(f"[module.parser.callback.FromParser.activate] upload_file_id={self.args.id}: complete callback action if page is success to parse")
            
            else:
                logging.info(f"[module.parser.callback.FromParser.activate] upload_file_id={self.args.id}: Whole Error")
                await self.get_error_page()
                if self.error_page:
                    await self.update_drive_row_status_partial_error()
                else:
                    await self.update_drive_row_status_fail()
                logging.info(f"[module.parser.callback.FromParser.activate] upload_file_id={self.args.id}: update Whole Error status for Database")

            logging.info(f"[module.parser.callback.FromParser.activate] upload_file_id={self.args.id} is finished")
            return True

        except AWSError as e:
            logging.error(f"[module.parser.callback.FromParser.activate] AWSError: {e}")
            await self.update_drive_row_status_fail()
        except VectorDBError as e:
            logging.error(f"[module.parser.callback.FromParser.activate] VectorDBError: {e}")
            await self.update_drive_row_status_fail_from_vector_db()
        except DBError as e:
            logging.error(f"[module.parser.callback.FromParser.activate] DBError: {e}")
            await self.update_drive_row_status_fail()
        except LLMProxyError as e:
            logging.error(f"[module.parser.callback.FromParser.activate] LLMProxyError: {e}")
            await self.update_drive_row_status_fail_count_not_same()
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.activate] Exception: {e}")
            await self.update_drive_row_status_fail()


    async def reactivate(self, status:int):
        try:
            if status == PARSER_FAILED or status == PARSER_FAILED_UPDATE_TO_VECTOR_DB:
                await self.get_file_datas_from_s3()
                await self.insert_row_vector_data_in_db()
                await self.upsert_file_parser_result_in_vector_db()
                await self.get_error_page()
                await self.decrease_parser_credit_available()
                await self.update_drive_row_status_success()
                return True
            elif status == PARSER_FAILED_NOT_SAME_COUNT:
                await self.delete_vector_by_upload_file_id()
                await self.get_file_datas_from_s3()
                await self.insert_row_vector_data_in_db()
                await self.upsert_file_parser_result_in_vector_db()
                await self.get_error_page()
                await self.decrease_parser_credit_available()
                await self.update_drive_row_status_success()
                return True
            #TODO: 부분 에러에 대한 재시작은 파서쪽에서 동작해야하므로 ToParser에서 진행하도록 한다.
                raise Exception("status is not valid")

        except AWSError as e:
            logging.error(f"[module.parser.callback.FromParser.reactivate] error: {e}")
            await self.update_drive_row_status_fail()
            raise AWSError(e)
        except VectorDBError as e:
            logging.error(f"[module.parser.callback.FromParser.reactivate] error: {e}")
            await self.update_drive_row_status_fail_from_vector_db()
            raise VectorDBError(e)
        except DBError as e:
            logging.error(f"[module.parser.callback.FromParser.reactivate] error: {e}")
            await self.update_drive_row_status_fail()
            raise DBError(e)
        except LLMProxyError as e:
            logging.error(f"[module.parser.callback.FromParser.reactivate] error: {e}")
            await self.update_drive_row_status_fail_count_not_same()
            raise LLMProxyError(e)
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.reactivate] error: {e}")
            await self.update_drive_row_status_fail_count_not_same()
            raise e


    async def get_file_datas_from_s3(self):
        try:
            s3_path = self.args.file_s3_path
            bucket_name = s3_path.split(":")[0]
            object_name = s3_path.split(":")[1]
            s3_data, s3_data_list = await self.args.s3_client.get_file_from_parser(bucket_name, object_name)
            self.file_datas_from_s3 = {
                "upload_file_id": self.args.id,
                "company_key": self.args.company_key,
                "s3_data": s3_data,
                "s3_data_list": s3_data_list
            }
        except AWSError as e:
            logging.error(f"[module.parser.callback.FromParser.get_file_datas_from_s3] error: {e}")
            raise AWSError(e)
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.get_file_datas_from_s3] error: {e}")
            raise e


    async def insert_row_vector_data_in_db(self):
        try:
            self.vector_insert_data, self.page_count = self._create_vector_data(self.file_datas_from_s3)
            self.args.vector_metadatas = self.vector_insert_data["metadata"]
            self.vector_insert_data["ids"] = await self.args.vector_query.get_vector_by_upload_file_id(self.args.db, self.args.id)
            if not self.vector_insert_data["ids"]:
                if len(self.args.vector_metadatas) == 1:
                    self.vector_insert_data["ids"] = await self.args.vector_query.insert_vector(self.args.db, self.args)
                else:
                    self.vector_insert_data["ids"] = await self.args.vector_query.bulk_insert_vector(self.args.db, self.args)

        except DBError as e:
            logging.error(f"[module.parser.callback.FromParser.insert_row_vector_data_in_db] error: {e}")
            raise DBError(e)
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.insert_row_vector_data_in_db] error: {e}")
            raise DBError(e)


    def _create_vector_data(self, file_datas_from_s3:dict):
        try:
            s3_data:list = file_datas_from_s3.get("s3_data")
            s3_data_list:list = file_datas_from_s3.get("s3_data_list")
            parsed_data, parsed_page = self._parsing_parser_result(s3_data, s3_data_list)

            string_data_for_vector = []
            metadata = []
            page_count = 0
            if len(s3_data_list) > 1:
                for parser_result_per_page, page in zip(parsed_data, parsed_page):
                    page_count += 1
                    chunk_datas:list = chunking_text(parser_result_per_page, EMBEDDING_MODEL, 500, 150)
                    for chunk, chunk_data in enumerate(chunk_datas, start=1):
                        metadata_each = {
                            "company_key": file_datas_from_s3.get("company_key"),
                            "upload_file_id": file_datas_from_s3.get("upload_file_id"),
                            "page": page,
                            "data_type": "parser",
                            "is_show": True,
                            "is_on": True,
                            "chunk": chunk
                        }
                        string_data_for_vector.append(chunk_data)
                        metadata.append(metadata_each)

            else:
                page_count = 1
                chunk_datas = chunking_text(parsed_data[0], EMBEDDING_MODEL, 500, 150)
                for chunk, chunk_data in enumerate(chunk_datas, start=1):
                    metadata_each = {
                        "company_key": file_datas_from_s3.get("company_key"),
                        "upload_file_id": file_datas_from_s3.get("upload_file_id"),
                        "page": 1,
                        "data_type": "parser",
                        "is_show": True,
                        "is_on": True,
                        "chunk": chunk
                    }
                    string_data_for_vector.append(chunk_data)
                    metadata.append(metadata_each)

            return (
                {"string_data_for_vector": string_data_for_vector, "metadata": metadata},
                page_count
            )

        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser._create_vector_data] error: {e}")
            raise e


    async def upsert_file_parser_result_in_vector_db(self):
        try:
            vector_ids = []
            vector_contents = []
            vector_metadatas = []

            for id, content, metadata in zip(self.vector_insert_data["ids"], self.vector_insert_data["string_data_for_vector"], self.vector_insert_data["metadata"]):
                if content:
                    vector_ids.append(f"parser-{id}")
                    vector_contents.append(content)
                    metadata["id"] = id
                    metadata["content"] = content
                    vector_metadatas.append(metadata)

            if self.args.server_stage == DOCKER:
                service = "llm-platform-install"
            elif self.args.server_stage == REAL:
                service = "llm-platform-production"
            else:
                service = "llm-platform-staging"

            try:
                logging.info("[module.parser.callback.FromParser.upsert_file_parser_result_in_vector_db] start to create Tasks")
                batch_size = 10
                vector_values = []
                for i in range(0, len(vector_contents), batch_size):
                    batched_vector_contents = vector_contents[i:i+batch_size]
                    logging.info(f"[module.parser.callback.upsert_file_parser_result_in_vector_db] generate async tasks: {i}:{i+batch_size}")
                    coroutine_tasks = [self.args.llm_proxy_client.embeddings(text=vector_content, service=service) for vector_content in batched_vector_contents]
                    vector_values_per_batch = await asyncio.gather(*coroutine_tasks)
                    logging.info(f"[module.parser.callback.upsert_file_parser_result_in_vector_db] finished: {i}:{i+batch_size}")
                    vector_values.extend(vector_values_per_batch)
            except LLMProxyError as e:
                logging.error(f"[module.parser.callback.FromParser.upsert_file_parser_result_in_vector_db] LLMProxyError-EmbeddingError: {e}")
                raise LLMProxyError(e)
            except Exception as e:
                logging.error(f"[module.parser.callback.FromParser.upsert_file_parser_result_in_vector_db] Exception: {e}")
                raise e

            count_checker = len(vector_ids) == len(vector_metadatas) == len(vector_values)
            if not count_checker:
                logging.error(f"[module.parser.callback.upsert_file_parser_result_in_vector_db] count of ids, metadata, text is not same")
                logging.error(f"ids: {len(self.args.vector_ids)}, metadata: {len(self.args.vector_metadatas)}, contents: {len(self.args.vector_values)}")
                raise Exception("count of ids, metadata, text is not same")
            await self.args.vector_db_client.insert_many(vector_ids, vector_values, vector_metadatas)

        except VectorDBError as e:
            logging.error(f"[module.parser.callback.FromParser.upsert_file_parser_result_in_vector_db] error: {e}")
            raise VectorDBError(e)
        except LLMProxyError as e:
            logging.error(f"[module.parser.callback.FromParser.upsert_file_parser_result_in_vector_db] error: {e}")
            raise LLMProxyError(e)
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.upsert_file_parser_result_in_vector_db] error: {e}")
            raise e


    async def get_error_page(self):
        try:
            result = await self.args.drive_query.get_error_page(self.args.db, self.args)
            if result and result[0] == "[" and result[-1] == "]":
                self.error_page = ast.literal_eval(result)
            else:
                self.error_page = None
        except DBError as e:
            logging.error(f"[module.parser.callback.FromParser.check_has_error_page] error: {e}")
            raise DBError(e)
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.check_has_error_page] error: {e}")
            raise e


    async def decrease_parser_credit_available(self):
        try:
            if not self.error_page:
                page_count = self.page_count
            else:
                page_count = len(self.error_page) - len(self.args.error_page)
            drive_id = await self.args.drive_query.get_drive_id_by_drive_id_upload_file_id(self.args.db, self.args.id)
            await self.args.file_credit_query.decrease_parser_credit_available(self.args.db, self.args.company_key, page_count, drive_id)
        except DBError as e:
            logging.error(f"[module.parser.callback.FromParser.decrease_parser_credit_available] error: {e}")
            logging.error(f"company_key: {self.args.company_key}, upload_file_id: {self.args.id}, use_parser_credit: {self.page_count}")
            await self.update_drive_row_status_fail_decrease_parser_credit_available()
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.decrease_parser_credit_available] error: {e}")
            logging.error(f"company_key: {self.args.company_key}, upload_file_id: {self.args.id}, use_parser_credit: {self.page_count}")
            await self.update_drive_row_status_fail_decrease_parser_credit_available()


    async def delete_vector_by_upload_file_id(self):
        try:
            target_ids_from_db = await self.args.vector_query.get_vector_by_upload_file_id(self.args.db, self.args.id)
            if target_ids_from_db:
                target_ids = [f"parser-{id}" for id in target_ids_from_db]
                if len(target_ids) > 1000:
                    batch_size = 1000
                    for i in range(0, len(target_ids), batch_size):
                        batch_target_ids = target_ids[i:i+batch_size]
                        await self.args.vector_db_client.remove(batch_target_ids)
                else:
                    await self.args.vector_db_client.remove(target_ids)
                await self.args.vector_query.delete_vector_by_upload_file_id(self.args.db, self.args.company_key, self.args.id)
        except VectorDBError as e:
            logging.error(f"[module.parser.callback.FromParser.delete_vector_by_upload_file_id] error: {e}")
            raise VectorDBError(e)
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.delete_vector_by_upload_file_id] error: {e}")
            raise e


    async def update_drive_row_status_success(self):
        try:
            # await self.args.drive_query.update_drive_row_status_by_upload_file_id(self.args.db, self.args.id, FINISHED)
            client = MySQLClient()
            query = "UPDATE drive SET status = %s, error_page = %s WHERE upload_file_id = %s"
            params = (FINISHED, None, self.args.id)
            await client.execute(query, params)
            logging.info(f"[module.parser.callback.FromParser.update_drive_row_status_success] upload_file_id={self.args.id} success update status -> SUCCESS!")
        except DBError as e:
            logging.error(f"[module.parser.callback.FromParser.update_drive_row_status_success] error: {e}")
            raise DBError(e)
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.update_drive_row_status_success] error: {e}")
            raise e


    async def update_drive_row_status_fail(self):
        try:
            await self.args.drive_query.update_drive_row_status_by_upload_file_id(self.args.db, self.args.id, PARSER_FAILED)
        except DBError as e:
            logging.error(f"[module.parser.callback.FromParser.update_drive_row_status_fail] error: {e}")
            raise DBError(e)
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.update_drive_row_status_fail] error: {e}")
            raise e


    async def update_drive_row_status_partial_error(self):
        try:
            await self.args.drive_query.update_drive_row_status_and_err_page_by_upload_file_id(self.args.db, self.args.id, PARSER_PARTIAL_ERROR, self.args.error_page)
        except DBError as e:
            logging.error(f"[module.parser.callback.FromParser.update_drive_row_status_partial_error] error: {e}")
            raise DBError(e)
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.update_drive_row_status_partial_error] error: {e}")
            raise e


    async def update_drive_row_status_fail_from_vector_db(self):
        try:
            await self.args.drive_query.update_drive_row_status_by_upload_file_id(self.args.db, self.args.id, PARSER_FAILED_UPDATE_TO_VECTOR_DB)
        except DBError as e:
            logging.error(f"[module.parser.callback.FromParser.update_drive_row_status_fail_from_vector_db] error: {e}")
            raise DBError(e)
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.update_drive_row_status_fail_from_vector_db] error: {e}")
            raise e


    async def update_drive_row_status_fail_decrease_parser_credit_available(self):
        try:
            await self.args.drive_query.update_drive_row_status_by_upload_file_id(self.args.db, self.args.id, PARSER_FAILED_DECREASE_PARSER_CREDIT_AVAILABLE)
        except DBError as e:
            logging.error(f"[module.parser.callback.FromParser.update_drive_row_status_fail_decrease_parser_credit_available] error: {e}")
            raise DBError(e)
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.update_drive_row_status_fail_decrease_parser_credit_available] error: {e}")
            raise e


    async def update_drive_row_status_fail_count_not_same(self):
        try:
            await self.args.drive_query.update_drive_row_status_by_upload_file_id(self.args.db, self.args.id, PARSER_FAILED_NOT_SAME_COUNT)
        except DBError as e:
            logging.error(f"[module.parser.callback.FromParser.update_drive_row_status_fail_count_not_same] DBError: {e}")
            raise DBError(e)
        except Exception as e:
            logging.error(f"[module.parser.callback.FromParser.update_drive_row_status_fail_count_not_same] Exception: {e}")
            raise e


    def _parsing_parser_result(self, s3_data:list, s3_data_list:list):
        try:
            parsed_data =[]
            parsed_page = []
            for data, page in zip(s3_data, s3_data_list):
                soup = BeautifulSoup(data, 'html.parser')
                for img in soup.find_all('img'):
                    alt_text = img.get('alt', '')
                    if alt_text:
                        img.replace_with(alt_text)
                text = soup.get_text()
                parsed_data.append(text)
                parsed_page.append(int(page['key'].split("/")[-1].split(".")[0]))
            return (parsed_data, parsed_page)
        except Exception as e:
            logging.error(f"[module.parser.callback._parsing_parser_result] Exception: {e}")
            raise e


    def _parsing_markdown_parser_result(self, s3_data:list, s3_data_list:list):
        try:
            parsed_data = []
            parsed_page = []
            for data, page in zip(s3_data, s3_data_list):
                html = markdown(data)
                logging.info(html)
                soup = BeautifulSoup(html, 'html.parser')
                for img in soup.find_all('img'):
                    alt_text = img.get('alt', '')
                    if alt_text:
                        img.replace_with(alt_text)
                text = soup.get_text()
                parsed_data.append(text)
                parsed_page.append(int(page['key'].split("/")[-1].split(".")[0]))
            return (parsed_data, parsed_page)
        except Exception as e:
            logging.error(f"[module.parser.callback._parsing_markdown_parser_result] Exception: {e}")
            raise e
