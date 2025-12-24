from contextlib import asynccontextmanager
from typing import AsyncIterator
import logging

from aiobotocore.session import get_session
from types_aiobotocore_s3 import S3Client as S3ClientAnnotated
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from app.config import settings

log = logging.getLogger(__name__)


class S3Client:
    def __init__(
            self,
            access_key: str,
            secret_key: str,
            endpoint_url: str,
            bucket_name: str
    ):
        self.config = dict(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url
        )
        self.endpoint_url = endpoint_url
        self.bucket_name = bucket_name

    @asynccontextmanager
    async def _get_client(self) -> AsyncIterator[S3ClientAnnotated]:
        session = get_session()
        async with session.create_client("s3", **self.config) as raw_client:
            client: S3ClientAnnotated = raw_client
            yield client


    async def upload_file(
            self,
            file: bytes,
            object_name: str,
            content_type: str
    ) -> str:
        log.info("Uploading file to S3", extra={"object_name": object_name, "content_type": content_type})
        try:
            async with self._get_client() as client:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=file,
                    ContentType=content_type
                )
            log.info("File uploaded to S3 successfully", extra={"object_name": object_name})
        except ClientError as e:
            log.error(f"S3 upload error: {str(e)}", extra={"object_name": object_name})
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="S3 upload error")
        except Exception as e:
            log.error(f"Unexpected S3 error: {str(e)}", extra={"object_name": object_name})
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unexpected S3 error")

        return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"


    async def download_file(
            self,
            object_name: str
    ) -> bytes:
        log.info("Downloading file from S3", extra={"object_name": object_name})
        try:
            async with self._get_client() as client:
                response = await client.get_object(
                    Bucket=self.bucket_name,
                    Key=object_name
                )
                log.info("File downloaded from S3 successfully", extra={"object_name": object_name})
                return await response["Body"].read()

        except ClientError as ex:
            log.error(f"S3 download error: {str(ex)}", extra={"object_name": object_name})
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="S3 download error")
        except Exception as e:
            log.error(f"Unexpected S3 error: {str(e)}", extra={"object_name": object_name})
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unexpected S3 error")


    async def delete_file(self, object_name: str) -> None:
        log.info("Deleting file from S3", extra={"object_name": object_name})
        try:
            async with self._get_client() as client:
                await client.delete_object(
                    Bucket=self.bucket_name,
                    Key=object_name
                )
            log.info("File deleted from S3 successfully", extra={"object_name": object_name})
        except ClientError as e:
            log.error(f"S3 delete error: {str(e)}", extra={"object_name": object_name})
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="S3 delete error")
        except Exception as e:
            log.error(f"Unexpected S3 error: {str(e)}", extra={"object_name": object_name})
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unexpected S3 error")


    async def delete_files(self, object_names: list[str]) -> None:
        if not object_names:
            return

        log.info("Deleting multiple files from S3", extra={"count": len(object_names)})
        try:
            async with self._get_client() as client:
                delete_payload = {
                    "Objects": [{'Key': name} for name in object_names],
                    "Quiet": True
                }
                await client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete=delete_payload
                )
            log.info("Files deleted from S3 successfully", extra={"count": len(object_names)})
        except ClientError as e:
            log.error(f"S3 batch delete error: {str(e)}", extra={"count": len(object_names)})
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="S3 batch delete error"
            )
        except Exception as e:
            log.error(f"Unexpected S3 error: {str(e)}", extra={"count": len(object_names)})
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unexpected S3 error"
            )