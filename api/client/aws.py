import os
import json
import asyncio
import logging
import mimetypes
from typing import Optional, BinaryIO, Dict, Any, List, Tuple
from urllib.parse import quote
from uuid import uuid4

from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email import encoders

import aioboto3
from botocore.config import Config
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi import UploadFile

from utils.error import AppError, AWSError, DataError
from utils.constants import REAL, BUCKET, PARSER_S3_BUCKET_NAME



# 환경 변수 설정
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'ba-journey')
S3_BACKUP_BUCKET = os.getenv('S3_BACKUP', 'llm-platform-backup')
CX_S3_BUCKET_NAME = os.getenv('CX_S3_BUCKET_NAME', 'cx-email-html')

# 로컬 S3 호환 스토리지(MinIO 컨테이너). 비어 있으면 AWS S3를 사용한다.
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL', '').rstrip('/')
# 브라우저가 presigned/public URL로 접근할 때 쓰는 주소 (컨테이너 밖에서 도달 가능해야 한다)
S3_PUBLIC_ENDPOINT_URL = os.getenv('S3_PUBLIC_ENDPOINT_URL', S3_ENDPOINT_URL).rstrip('/')

# 로컬 스토리지 기동 시 생성할 버킷: (버킷명, 익명 읽기 허용 여부)
# 익명 읽기는 public URL로 서빙하는 버킷에만 허용한다 (AWS의 public-read ACL 대체)
LOCAL_BUCKET_LIST = [
    (S3_BUCKET_NAME, False),
    (S3_BACKUP_BUCKET, False),
    (PARSER_S3_BUCKET_NAME, False),
    (BUCKET, True),
    (CX_S3_BUCKET_NAME, True),
]



class AWSClient:
    _session = None
    _ses_session = None
    _config = None
    _lock = asyncio.Lock()

    @classmethod
    async def initialize(cls):
        async with cls._lock:
            if cls._session is None:
                config_kwargs = {
                    'retries': {
                        'max_attempts': 3,
                        'mode': 'standard'
                    },
                    'connect_timeout': 10,
                    'read_timeout': 10,
                }
                if S3_ENDPOINT_URL:
                    # MinIO는 virtual-host 스타일(bucket.host)을 쓰지 않으므로 path 스타일 고정
                    config_kwargs['signature_version'] = 's3v4'
                    config_kwargs['s3'] = {'addressing_style': 'path'}
                cls._config = Config(**config_kwargs)

                cls._session = aioboto3.Session(
                    region_name=os.getenv('AWS_REGION', 'ap-northeast-2')
                )

                cls._ses_session = aioboto3.Session(
                    region_name=os.getenv('AWS_SES_REGION', 'ap-northeast-2')
                )
        logging.info("✅ connected s3 Client")


    @classmethod
    async def get_session(cls):
        if cls._session is None:
            await cls.initialize()
        return cls._session


    @classmethod
    async def get_ses_session(cls):
        if cls._ses_session is None:
            await cls.initialize()
        return cls._ses_session


    @classmethod
    async def get_config(cls):
        if cls._config is None:
            await cls.initialize()
        return cls._config


    @classmethod
    async def close(cls):
        async with cls._lock:
            if cls._session:
                cls._session = None
                cls._config = None
        logging.info("🔴 disconnected s3 Client")



class S3Client(AWSClient):
    _buckets_ready = False

    @classmethod
    async def initialize(cls):
        await super().initialize()
        if S3_ENDPOINT_URL and not cls._buckets_ready:
            await cls.ensure_buckets()


    @staticmethod
    def _local_client_kwargs(endpoint_url: str) -> Dict[str, str]:
        """로컬 S3 호환 스토리지용 client 인자. S3_ENDPOINT_URL이 없으면 빈 dict(AWS 기본 자격증명 체인)."""
        if not S3_ENDPOINT_URL:
            return {}
        access_key = os.getenv('S3_ACCESS_KEY')
        secret_key = os.getenv('S3_SECRET_KEY')
        if not access_key or not secret_key:
            raise DataError("S3_ACCESS_KEY / S3_SECRET_KEY are required when S3_ENDPOINT_URL is set")
        return {
            'endpoint_url': endpoint_url,
            'aws_access_key_id': access_key,
            'aws_secret_access_key': secret_key,
        }


    @classmethod
    async def get_client(cls):
        try:
            session = await cls.get_session()
            config = await cls.get_config()
            return session.client('s3', config=config, **cls._local_client_kwargs(S3_ENDPOINT_URL))
        except AppError:
            raise
        except NoCredentialsError:
            logging.error("S3 Credentials not available")
            raise AWSError("[NoCredentialsError] S3 Credentials not available")
        except Exception as e:
            logging.error(f"Failed to get S3 client: {e}")
            raise AWSError(e)


    @classmethod
    async def get_presign_client(cls):
        """presigned URL 서명용 client. 서명에 Host가 포함되므로 브라우저가 접근할 public 주소로 만든다."""
        try:
            session = await cls.get_session()
            config = await cls.get_config()
            return session.client('s3', config=config, **cls._local_client_kwargs(S3_PUBLIC_ENDPOINT_URL))
        except AppError:
            raise
        except Exception as e:
            logging.error(f"[client.aws.S3Client.get_presign_client] 🔴 Failed to get S3 presign client: {e}")
            raise AWSError(e)


    @classmethod
    def get_public_url(cls, bucket: str, key: str) -> str:
        """익명 읽기 가능한 객체의 public URL. 로컬 스토리지면 public 엔드포인트, 아니면 AWS S3 URL."""
        quoted_key = quote(key, safe='/')
        if S3_ENDPOINT_URL:
            return f"{S3_PUBLIC_ENDPOINT_URL}/{bucket}/{quoted_key}"
        region = os.getenv('AWS_DEFAULT_REGION', os.getenv('AWS_REGION', 'ap-northeast-2'))
        return f"https://{bucket}.s3.{region}.amazonaws.com/{quoted_key}"


    @classmethod
    async def ensure_buckets(cls):
        """로컬 스토리지에 필요한 버킷을 만들고, public 서빙 버킷에는 익명 읽기 정책을 건다."""
        try:
            async with await cls.get_client() as s3:
                for bucket, is_public in LOCAL_BUCKET_LIST:
                    try:
                        await s3.head_bucket(Bucket=bucket)
                    except ClientError as e:
                        if e.response.get('Error', {}).get('Code') not in ('404', 'NoSuchBucket'):
                            raise
                        await s3.create_bucket(Bucket=bucket)
                        logging.info(f"[client.aws.S3Client.ensure_buckets] ✅ created bucket: {bucket}")
                    if is_public:
                        policy = {
                            "Version": "2012-10-17",
                            "Statement": [{
                                "Effect": "Allow",
                                "Principal": {"AWS": ["*"]},
                                "Action": ["s3:GetObject"],
                                "Resource": [f"arn:aws:s3:::{bucket}/*"],
                            }],
                        }
                        await s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
            cls._buckets_ready = True
            logging.info(f"[client.aws.S3Client.ensure_buckets] ✅ buckets ready on {S3_ENDPOINT_URL}")
        except AppError:
            raise
        except Exception as e:
            logging.error(f"[client.aws.S3Client.ensure_buckets] 🔴 Failed to prepare buckets: {e}")
            raise AWSError(f"Failed to prepare local S3 buckets: {e}") from e


    @classmethod
    async def upload_to_s3(cls, image_bytes: BinaryIO, bucket_name: str, object_name: str):
        """파일 객체를 S3에 업로드하고 위치를 반환합니다."""
        try:
            async with await cls.get_client() as s3:
                await s3.upload_fileobj(
                    image_bytes,
                    bucket_name,
                    object_name,
                    ExtraArgs={'ACL': 'public-read'}
                )
                location = f"{bucket_name}:{object_name}"
                return location
        except NoCredentialsError:
            logging.error("S3 Credentials not available")
            raise AWSError("[NoCredentialsError] S3 Credentials not available")
        except Exception as e:
            logging.error(f"Failed to upload file to S3: {e}")
            raise AWSError(e)


    @classmethod
    async def upload_file(
        cls,
        file_data: BinaryIO,
        bucket: str,
        key: str,
        content_type: Optional[str] = None,
        extra_args: Optional[Dict[str, Any]] = None
    ):
        try:
            args = extra_args or {}
            if content_type:
                args['ContentType'] = content_type

            async with await cls.get_client() as s3:
                response = await s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=file_data,
                    **args
                )
                return {
                    "bucket": bucket,
                    "key": key,
                    "etag": response.get("ETag", "").strip('"'),
                    "version_id": response.get("VersionId")
                }
        except Exception as e:
            logging.error(f"🔴 [client.aws.S3Client.upload_file] Failed to upload file to S3: {e}")
            raise AWSError(e)


    @classmethod
    async def put_object_to_s3(cls, bucket_name: str, object_name: str, file_data: BinaryIO | str, acl: str = None):
        try:
            args = {}
            if acl is not None:
                args["acl"] = acl

            async with await cls.get_client() as s3:
                await s3.put_object(
                    Bucket=bucket_name,
                    Key=object_name,
                    Body=file_data,
                    **args
                )
                return True
        except NoCredentialsError:
            logging.error("S3 Credentials not available")
            raise AWSError("[NoCredentialsError] S3 Credentials not available")
        except Exception as e:
            logging.error(f"Failed to put object to S3: {e}")
            raise AWSError(e)


    @classmethod
    async def download_file(cls, bucket: str, key: str) -> bytes:
        try:
            async with await cls.get_client() as s3:
                response = await s3.get_object(Bucket=bucket, Key=key)
                async with response['Body'] as stream:
                    data = await stream.read()
                return data
        except Exception as e:
            logging.error(f"🔴 [client.aws.S3Client.download_file] Failed to download file from S3: {e}")
            raise AWSError(e)


    @classmethod
    async def stream_file(cls, bucket: str, key: str, chunk_size: int = 1024 * 1024):  # 1MB 청크
        try:
            async def stream_generator():
                async with await cls.get_client() as s3:
                    # 파일 크기 먼저 확인
                    head = await s3.head_object(Bucket=bucket, Key=key)
                    content_length = head.get("ContentLength", 0)

                    # Range 요청으로 청크 단위 다운로드
                    for offset in range(0, content_length, chunk_size):
                        end = min(offset + chunk_size - 1, content_length - 1)

                        s3_file = await s3.get_object(
                            Bucket=bucket,
                            Key=key,
                            Range=f"bytes={offset}-{end}"
                        )

                        # 각 Range 요청마다 새로운 연결이므로 안전
                        async with s3_file["Body"] as stream:
                            data = await stream.read()
                            yield data

            # 메타데이터는 별도로 가져오기
            async with await cls.get_client() as s3:
                head = await s3.head_object(Bucket=bucket, Key=key)
                content_type = head.get('ContentType', 'application/octet-stream')
                content_length = head.get('ContentLength', 0)

            return stream_generator(), content_type, content_length

        except Exception as e:
            logging.error(f"🔴 S3 Range streaming error: {e}")
            raise AWSError(e)


    @classmethod
    async def get_file_from_s3(cls, bucket_name: str, object_name: str) -> tuple[bytes, bool]:
        try:
            content = await cls.download_file(bucket_name, object_name)
            is_error = False
            return (content, is_error)
        except Exception as e:
            logging.error(f"🔴 [client.aws.S3Client.get_file_from_s3] bucket_name: {bucket_name} & key: {object_name} | Failed to get file from S3: {e}")
            content = ""
            is_error = True
            return (content, is_error)

    @classmethod
    async def get_file_list_cnt_in_bucket(cls, bucket_name:str, object_name:str):
        try:
            file_list = await cls._get_file_list_from_s3(bucket_name, object_name)
            return len(file_list)
        except NoCredentialsError:
            logging.error(f"[client.aws.S3Client.get_file_list_cnt_in_bucket] bucket_name: {bucket_name} & key: {object_name} | S3 Credentials not available")
            raise AWSError("[NoCredentialsError] S3 Credentials not available")
        except Exception as e:
            logging.error(f"[client.aws.S3Client.get_file_list_cnt_in_bucket] bucket_name: {bucket_name} & key: {object_name} | Exception: {e}")
            raise AWSError(e)


    @classmethod
    async def _get_file_from_s3(cls, bucket_name: str, object_name: str) -> bytes:
        try:
            return await cls.download_file(bucket_name, object_name)
        except Exception as e:
            logging.error(f"🔴 [client.aws.S3Client.get_file_from_s3] bucket_name: {bucket_name} & key: {object_name} | Failed to get file from S3: {e}")
            raise AWSError(e)


    @classmethod
    async def get_file_from_parser(cls, bucket_name: str, object_name: str) -> Tuple[List[bytes], List[Dict]]:
        try:
            file_list = await cls._get_file_list_from_s3(bucket_name, object_name)
            file_data_list = [await cls._get_file_from_s3(bucket_name, file['key']) for file in file_list]
            return (file_data_list, file_list)
        except NoCredentialsError:
            logging.error(f"[client.aws.S3Client.get_file_from_parser] bucket_name: {bucket_name} & key: {object_name} | S3 Credentials not available")
            raise AWSError("[NoCredentialsError] S3 Credentials not available")
        except Exception as e:
            logging.error(f"[client.aws.S3Client.get_file_from_parser] bucket_name: {bucket_name} & key: {object_name} | Exception: {e}")
            raise AWSError(e)


    @classmethod
    async def _get_file_list_from_s3(cls, bucket_name: str, object_name: str) -> List[Dict]:
        try:
            file_list = []
            async with await cls.get_client() as s3:
                paginator = s3.get_paginator('list_objects_v2')
                async for page in paginator.paginate(Bucket=bucket_name, Prefix=object_name):
                    if 'Contents' not in page:
                        continue

                    for obj in page['Contents']:
                        if not obj['Key'].endswith('/'):  # 폴더는 제외
                            file_info = {
                                'key': obj['Key'],
                                'size': obj['Size'],
                                'last_modified': obj['LastModified'].isoformat() if hasattr(obj['LastModified'], 'isoformat') else obj['LastModified']
                            }
                            file_list.append(file_info)

                return file_list

        except NoCredentialsError:
            logging.error(f"[client.aws.S3Client._get_file_list_from_s3] bucket_name: {bucket_name} & key: {object_name} | S3 Credentials not available")
            raise AWSError("[NoCredentialsError] S3 Credentials not available")
        except Exception as e:
            logging.error(f"[client.aws.S3Client._get_file_list_from_s3] bucket_name: {bucket_name} & key: {object_name} | Exception: {e}")
            raise AWSError(e)


    @classmethod
    async def list_files(cls, bucket: str, prefix: str = "", max_keys: int = 1000) -> List[Dict]:
        try:
            result = []
            async with await cls.get_client() as s3:
                paginator = s3.get_paginator('list_objects_v2')
                async for page in paginator.paginate(Bucket=bucket, Prefix=prefix, MaxKeys=max_keys):
                    if 'Contents' in page:
                        for obj in page['Contents']:
                            if not obj['Key'].endswith('/'):  # 폴더는 제외
                                result.append({
                                    "key": obj['Key'],
                                    "size": obj['Size'],
                                    "last_modified": obj['LastModified'].isoformat() if hasattr(obj['LastModified'], 'isoformat') else obj['LastModified'],
                                    "etag": obj['ETag'].strip('"') if 'ETag' in obj else None
                                })
            return result
        except Exception as e:
            logging.error(f"🔴 [client.aws.S3Client.list_files] Failed to list files from S3: {e}")
            raise AWSError(e)


    @classmethod
    async def delete_file(cls, bucket: str, key: str) -> Dict:
        try:
            async with await cls.get_client() as s3:
                await s3.delete_object(
                    Bucket=bucket,
                    Key=key
                )
                return {"message": "파일이 성공적으로 삭제되었습니다."}
        except Exception as e:
            logging.error(f"🔴 [client.aws.S3Client.delete_file] bucket_name: {bucket} & key: {key} | Exception: {e}")
            raise AWSError(e)


    @classmethod
    async def delete_on_s3(cls, bucket_name: str, object_name: str) -> bool:
        try:
            await cls.delete_file(bucket_name, object_name)
            return True
        except Exception as e:
            logging.error(f"🔴 [client.aws.S3Client.delete_file] bucket_name: {bucket_name} & key: {object_name} | Exception: {e}")
            return False


    @classmethod
    async def get_presigned_url(
        cls,
        bucket: str,
        key: str,
        expiration: int = 3600,
        operation: str = 'get_object',
        response_headers: Dict = None
    ) -> Dict:
        try:
            params = {
                'Bucket': bucket,
                'Key': key
            }

            # 응답 헤더가 제공된 경우 추가
            if response_headers:
                if 'response-content-disposition' in response_headers:
                    params['ResponseContentDisposition'] = response_headers['response-content-disposition']
                if 'response-content-type' in response_headers:
                    params['ResponseContentType'] = response_headers['response-content-type']

            async with await cls.get_presign_client() as s3:
                url = await s3.generate_presigned_url(
                    ClientMethod=operation,
                    Params=params,
                    ExpiresIn=expiration
                )
                return {"url": url, "expires_in": expiration}
        except Exception as e:
            logging.error(f"🔴 [client.aws.S3Client.get_presigned_url] Failed to generate presigned URL: {e}")
            raise AWSError(e)


    @classmethod
    async def generate_presigned_url(cls, bucket_name: str, object_name: str, expires_in: int, response_headers: Dict) -> str:
        """get_presigned_url의 별칭으로, 문자열 URL만 반환합니다."""
        try:
            result = await cls.get_presigned_url(
                bucket=bucket_name,
                key=object_name,
                expiration=expires_in,
                response_headers=response_headers
            )
            return result["url"]
        except Exception as e:
            logging.error(f"aws.s3.generate_presigned_url error: {e}")
            raise AWSError(e)



class SESClient(AWSClient):
    @classmethod
    async def get_client(cls, is_v2:bool=False):
        try:
            session = await cls.get_ses_session()
            config = await cls.get_config()
            return session.client('sesv2', config=config) if is_v2 else session.client('ses', config=config)
        except NoCredentialsError:
            logging.error("S3 Credentials not available")
            raise AWSError("[NoCredentialsError] S3 Credentials not available")
        except Exception as e:
            logging.error(f"Failed to get SES client: {e}")
            raise AWSError(e)


    @classmethod
    async def send_mail(cls, from_address:list, to_address_list:list, subject:str, body_html:str, cc_address_list:list=None, bcc_address_list:list=None):
        try:
            destination = {"ToAddresses": to_address_list}
            if cc_address_list:
                destination["CcAddresses"] = cc_address_list
            if bcc_address_list:
                destination["BccAddresses"] = bcc_address_list

            async with await cls.get_client() as ses:
                response = await ses.send_email(
                    Source=from_address,
                    Destination= destination,
                    Message={
                        "Subject": {
                            "Data": subject,
                            "Charset": "UTF-8"
                        },
                        "Body": {
                            "Html": {
                                "Data": body_html,
                                "Charset": "UTF-8"
                            }
                        }
                    }
                )

            return {"message_id": response["MessageId"]}

        except Exception as e:
            logging.error(f"[client.aws.SESClient.send_mail] AWSError: {e}")
            raise AWSError(e)


    @classmethod
    async def send_mail_with_raw(cls, from_address:list, to_address_list:list, subject:str, body_html:str, attachments:list, cc_address_list:list=None, bcc_address_list:list=None, in_reply_to:str=None, references:list=None, image_data:list=None):
        try:
            msg = MIMEMultipart()
            destination = {"ToAddresses": to_address_list}
            msg["Subject"] = subject
            msg["From"] = from_address
            msg["To"] = ", ".join(to_address_list)
            if cc_address_list:
                msg["Cc"] = ", ".join(cc_address_list)
                destination["CcAddresses"] = cc_address_list
            if bcc_address_list:
                msg["Bcc"] = ", ".join(bcc_address_list)
                destination["BccAddresses"] = bcc_address_list
            if in_reply_to:
                msg["In-Reply-To"] = in_reply_to
            if references:
                msg["References"] = " ".join(references)

            alt_part = MIMEMultipart("alternative")
            text_part = MIMEText(body_html, "html", "utf-8")
            alt_part.attach(text_part)
            msg.attach(alt_part)

            if image_data:
                for image_data_each in image_data:
                    mime_type = image_data_each.get("mimeType", "image/png")
                    mime_subtype = mime_type.split('/')[-1]

                    image_part = MIMEBase('image', mime_subtype)
                    image_part.set_payload(image_data_each["image"])
                    image_part.add_header("Content-ID", f'<{image_data_each["cid"]}>')
                    image_part.add_header("Content-Disposition", "inline", filename=image_data_each["filename"])
                    image_part.add_header("Content-Transfer-Encoding", "base64")
                    msg.attach(image_part)

            if attachments:
                for file in attachments:
                    file_content = file["file_data"]
                    filename = file.get("filename", "attachment")

                    content_type, _ = mimetypes.guess_type(filename)
                    if content_type is None:
                        content_type = file.get("content_type", "application/octet-stream")

                    part = MIMEApplication(file_content, _subtype=content_type.split('/')[-1])
                    part.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=filename
                    )
                    msg.attach(part)

            async with await cls.get_client(is_v2=True) as ses:
                response = await ses.send_email(
                    FromEmailAddress=from_address,
                    Content={
                        "Raw": {
                            "Data": msg.as_bytes()
                        }
                    }
                )
            return response["MessageId"]

        except Exception as e:
            logging.error(f"[client.aws.SESClient.send_mail_with_raw] AWSError: {e}")
            raise AWSError(e)
