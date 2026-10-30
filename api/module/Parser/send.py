import io
import ast
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from client.rabbit import RabbitMQClient
from client.aws import S3Client
from queries.drive import DriveQuery
from queries.upload_file import UploadFileQuery
from module.Parser.dto import sendArgs
from utils.date import get_utc_now
from utils.constants import *
from utils.error import DBError, AWSError, MessageQueueError



class ToParser:
	def __init__(
		self,
		db: AsyncSession,
		cloud_storage_client: S3Client,
		upload_file_query: UploadFileQuery,
		drive_query: DriveQuery,
		message_broker_client: RabbitMQClient,
		info: dict,
		init_from: str
	):
	
		self.args = sendArgs(
			db=db,
			cloud_storage_client=cloud_storage_client,
			upload_file_query=upload_file_query,
			drive_query=drive_query,
			message_broker_client=message_broker_client,
			drive_ids=info.get("drive_ids"),
			file_data=info.get("file_data"),
			company_key=info.get("company_key"),
			stage=info.get("stage"),
			vector_db_index=info.get("vector_db_index"),
			vector_db_namespace=info.get("vector_db_namespace"),
			queue_name=info.get("queue_name"),
			init_from=init_from,
			all_page=None
		)


	async def activate(self):
		try:
			if len(self.args.drive_ids) != len(self.args.file_data):
				raise Exception("drive_ids and file_data must be same")
			else:
				for self.file, self.drive_id in zip(self.args.file_data, self.args.drive_ids):
					try:
						await self.upload_file_to_s3()
						await self.record_upload_file_in_db()
						await self.update_drive_row_after_upload()
						await self.send_message_to_file_parser()
						await self.update_drive_row_after_send_message()
			
					except AWSError as e:
						logging.error(f"[Parser.send.activate] Failed to activate: {e}")
						await self.update_drive_row_status_fail_upload_to_s3()
					except DBError as e:
						logging.error(f"[Parser.send.activate] Failed to activate: {e}")
						await self.update_drive_row_status_fail_record_upload_file_in_db()
					except MessageQueueError as e:
						logging.error(f"[Parser.send.activate] Failed to activate: {e}")
						await self.update_drive_row_status_fail_send_message_to_file_parser()
					except Exception as e:
						logging.error(f"[Parser.send.activate] Failed to activate: {e}")
						await self.update_drive_row_status_fail_upload_to_s3()
		except Exception as e:
			logging.error(f"[Parser.send.activate] Failed to activate: {e}")
			await self.update_drive_row_status_fail_upload_to_s3()


	async def reactivate(self, status:int):
		logging.info(f"[Parser.send.reactivate] status: {status}")
		logging.info(f"[Parser.send.reactivate] self.args: {self.args}")
		for self.drive_id in self.args.drive_ids:
			try:
				if status == FAIL_TO_DB:
					await self.get_file_from_s3_for_retry()
					await self.record_upload_file_in_db()
					await self.update_drive_row_after_upload()
					await self.send_message_to_file_parser()			
					await self.update_drive_row_after_send_message()
				elif status == FAIL_TO_SEND_MESSAGE or status == PARSER_FAILED:
					await self._retry_get_row_before_send_message()
					await self.send_message_to_file_parser()
					await self.update_drive_row_after_send_message()
				elif status == PARSER_PARTIAL_ERROR:
					await self._get_error_page()
					await self._retry_get_row_before_send_message()
					await self._get_all_page()
					await self.send_message_to_file_parser()
					await self.update_drive_row_after_send_message()
				return True

			except DBError as e:
				logging.error(f"[Parser.send.reactivate] Failed to reactivate: {e}")
				await self.update_drive_row_status_fail_record_upload_file_in_db()
			except MessageQueueError as e:
				logging.error(f"[Parser.send.reactivate] Failed to reactivate: {e}")
				await self.update_drive_row_status_fail_send_message_to_file_parser()
			except Exception as e:
				logging.error(f"[Parser.send.reactivate] Failed to reactivate: {e}")
				await self.update_drive_row_status_fail_upload_to_s3()


	async def upload_file_to_s3(self):
		try:
			self.upload_file_data = await self._create_upload_file_data(
				s3_client=self.args.cloud_storage_client,
				company_key=self.args.company_key,
				file=self.file,
				id=self.drive_id,
				bucket_name="llm-platform-file-parser",
				stage=self.args.stage,
				init_from=self.args.init_from
			)
		
		except AWSError as e:
			logging.error(f"[Parser.send.helper_upload_file_to_s3] Failed to upload file to s3: {e}")
			raise AWSError(f"[Parser.send.helper_upload_file_to_s3] Failed to upload file to s3: {e}")
		except Exception as e:
			logging.error(f"[Parser.send.helper_upload_file_to_s3] Failed to upload file to s3: {e}")
			raise AWSError(f"[Parser.send.helper_upload_file_to_s3] Failed to upload file to s3: {e}")


	async def get_file_from_s3_for_retry(self):
		self.upload_file_data = await self._retry_get_file_from_s3(
			s3_client=self.args.cloud_storage_client,
			company_key=self.args.company_key,
			id=self.drive_id,
			bucket_name="llm-platform-file-parser",
			stage=self.args.stage,
			init_from=self.args.init_from
		)


	async def record_upload_file_in_db(self):
		try:
			self.upload_file_id = await self.args.upload_file_query.record_upload_file_history_for_parser(db=self.args.db, data=self.upload_file_data)
			self.upload_file_result = {**self.upload_file_data, **{"id": self.upload_file_id}}
		
		except DBError as e:
			logging.error(f"[Parser.send.helper_record_upload_file_in_db] Failed to record upload file in db: {e}")
			raise DBError(f"[Parser.send.helper_record_upload_file_in_db] Failed to record upload file in db: {e}")
		except Exception as e:
			logging.error(f"[Parser.send.helper_record_upload_file_in_db] Failed to record upload file in db: {e}")
			raise DBError(f"[Parser.send.helper_record_upload_file_in_db] Failed to record upload file in db: {e}")


	async def update_drive_row_after_upload(self):
		try:
			await self.args.drive_query.update_drive_row_after_upload(db=self.args.db, id=self.upload_file_result.get("drive_id"), status=PENDING, upload_file_id=self.upload_file_result.get("id"))

		except DBError as e:
			logging.error(f"[Parser.send.helper_update_drive_row_after_upload] Failed to update drive row: {e}")
			raise DBError(f"[Parser.send.helper_update_drive_row_after_upload] Failed to update drive row: {e}")
		except Exception as e:
			logging.error(f"[Parser.send.helper_update_drive_row_after_upload] Failed to update drive row: {e}")
			raise DBError(f"[Parser.send.helper_update_drive_row_after_upload] Failed to update drive row: {e}")


	async def send_message_to_file_parser(self):
		try:
			await self.args.message_broker_client.send_message(
				message=self._create_parser_payload_data(self.upload_file_result, self.args),
				queue_name=self.args.queue_name
			)
		except MessageQueueError as e:
			logging.error(f"[Parser.send.helper_send_message_to_file_parser] Failed to send message to file parser: {e}")
			raise MessageQueueError(f"[Parser.send.helper_send_message_to_file_parser] Failed to send message to file parser: {e}")
		except Exception as e:
			logging.error(f"[Parser.send.helper_send_message_to_file_parser] Failed to send message to file parser: {e}")
			raise MessageQueueError(f"[Parser.send.helper_send_message_to_file_parser] Failed to send message to file parser: {e}")
	

	async def update_drive_row_after_send_message(self):
		try:
			await self.args.drive_query.update_drive_row_after_upload(db=self.args.db, id=self.upload_file_result.get("drive_id"), status=PENDING, upload_file_id=self.upload_file_result.get("id"))
			
		except DBError as e:
			logging.error(f"[Parser.send.helper_update_drive_row_after_send_message] Failed to update drive row: {e}")
			raise DBError(f"[Parser.send.helper_update_drive_row_after_send_message] Failed to update drive row: {e}")
		except Exception as e:
			logging.error(f"[Parser.send.helper_update_drive_row_after_send_message] Failed to update drive row: {e}")
			raise Exception(f"[Parser.send.helper_update_drive_row_after_send_message] Failed to update drive row: {e}")
		

	async def _create_upload_file_data(self, s3_client:S3Client, company_key:str, file:dict, id:int, bucket_name:str, stage:str, init_from:str) -> dict:
		file_type = file.get("filetype")
		file_obj = io.BytesIO(file.get("fileobject"))
		current_time = get_utc_now()
		timestamp_filename = int(current_time.timestamp())
		object_name = f"{stage}/{company_key}/{init_from}-{id}/{timestamp_filename}.{file_type}"
		await s3_client.upload_to_s3(file_obj, bucket_name, object_name)	
		return {
			"drive_id": id if init_from == "drive" else None,
			"post_id": id if init_from == "post" else None,
			"filetype": file_type,
			"s3_path": f"{bucket_name}:{object_name}",
			"reg_date": current_time,
		}


	def _create_parser_payload_data(self, upload_file_result:dict, args:sendArgs):
		api_address = REAL_API_URL if args.stage == REAL else STAGING_API_URL if args.stage == STAGING else DEV_API_URL
		callback_route = "drive/callback_from_parser"
		callback_url = f"{api_address}{callback_route}"
		s3_path = upload_file_result.get("s3_path")
		bucket_name = s3_path.split(":")[0]
		object_name = s3_path.split(":")[1]
		fileS3Path = f"s3://{bucket_name}/{object_name}"

		payload = {
			"id": upload_file_result.get("id"),
			"companyKey": args.company_key,
			"vectorDbIndex": args.vector_db_index,
			"vectorDbNamespace": args.vector_db_namespace,
			"fileS3Path": fileS3Path,
			"fileType": upload_file_result.get("filetype") or upload_file_result.get("s3_path").split(".")[-1],
			"callbackUrl": callback_url,
			"retryPages": args.error_page,
		}
		if args.error_page:
			payload["allPageCount"] = self.args.all_page
		
		return payload


	async def _retry_get_file_from_s3(self, s3_client:S3Client, company_key:str, id:int, bucket_name:str, stage:str, init_from:str) -> dict:
		object_name = f"{stage}/{company_key}/{init_from}-{id}"
		_, file_list = await s3_client.get_file_from_parser(bucket_name, object_name)
		result_key = file_list[0].get("key")
		filetype = result_key.split(".")[-1]
		return {
			"drive_id": id if init_from == "drive" else None,
			"post_id": id if init_from == "post" else None,
			"filetype": filetype,
			"s3_path": f"{bucket_name}:{result_key}",
			"reg_date": get_utc_now(),
		}


	async def _retry_get_row_before_send_message(self):
		try:
			self.upload_file_result = await self.args.upload_file_query.get_row_by_drive_id(db=self.args.db, drive_id=self.drive_id)
			self.upload_file_id = self.upload_file_result.get("id")
   
		except DBError as e:
			logging.error(f"[Parser.send.helper_retry_get_row_before_send_message] Failed to get row before send message: {e}")
			raise DBError(f"[Parser.send.helper_retry_get_row_before_send_message] Failed to get row before send message: {e}")
		except Exception as e:
			logging.error(f"[Parser.send.helper_retry_get_row_before_send_message] Failed to get row before send message: {e}")
			raise Exception(f"[Parser.send.helper_retry_get_row_before_send_message] Failed to get row before send message: {e}")
		

	async def _get_all_page(self):
		try:
			self.args.all_page = await self.args.drive_query.get_all_page(db=self.args.db, domain_data=self.args)
		except DBError as e:
			logging.error(f"[Parser.send.helper_retry_get_all_page] Failed to get all page: {e}")
			raise DBError(f"[Parser.send.helper_retry_get_all_page] Failed to get all page: {e}")
		except Exception as e:
			logging.error(f"[Parser.send.helper_retry_get_all_page] Failed to get all page: {e}")
			raise Exception(f"[Parser.send.helper_retry_get_all_page] Failed to get all page: {e}")
		
	
	async def _get_error_page(self):
		try:
			result = await self.args.drive_query.get_error_page_by_drive_id(self.args.db, self.args)
			if result and result[0] == "[" and result[-1] == "]" and len(result) > 2:
				self.args.error_page = ast.literal_eval(result)
		except DBError as e:
			logging.error(f"[module.parser.send._get_error_page] error: {e}")
			raise DBError(e)
		except Exception as e:
			logging.error(f"[module.parser.send._get_error_page] error: {e}")
			raise e



	async def update_drive_row_status_fail_upload_to_s3(self):
		await self.args.drive_query.update_drive_row_status_by_upload_file_id(db=self.args.db, id=self.upload_file_id, status=FAILED)

	async def update_drive_row_status_fail_record_upload_file_in_db(self):
		await self.args.drive_query.update_drive_row_status_by_upload_file_id(db=self.args.db, id=self.upload_file_id, status=FAIL_TO_DB)

	async def update_drive_row_status_fail_send_message_to_file_parser(self):
		await self.args.drive_query.update_drive_row_status_by_upload_file_id(db=self.args.db, id=self.upload_file_id, status=FAIL_TO_SEND_MESSAGE)

	async def update_drive_row_status_fail_update_drive_row_after_send_message(self):
		await self.args.drive_query.update_drive_row_status_by_upload_file_id(db=self.args.db, id=self.upload_file_id, status=FAIL_TO_DB)