from contextlib import asynccontextmanager
from typing import AsyncIterator

from aiobotocore.session import get_session
from types_aiobotocore_s3 import S3Client as S3ClientAnnotated
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from app.config import settings


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
        try:
            async with self._get_client() as client:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=object_name,
                    Body=file,
                    ContentType=content_type
                )
        except ClientError:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="S3 upload error")
        except Exception:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unexpected S3 error")

        return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"


    async def download_file(
            self,
            object_name: str
    ) -> bytes:
        try:
            async with self._get_client() as client:
                response = await client.get_object(
                    Bucket=self.bucket_name,
                    Key=object_name
                )
                return await response["Body"].read()

        except ClientError as ex:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="S3 download error")
        except Exception:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unexpected S3 error")


    async def delete_file(self, object_name: str) -> None:
        try:
            async with self._get_client() as client:
                await client.delete_object(
                    Bucket=self.bucket_name,
                    Key=object_name
                )
        except ClientError as e:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="S3 delete error")
        except Exception:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Unexpected S3 error")


    async def delete_files(self, object_names: list[str]) -> None:
        if not object_names:
            return

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
        except ClientError:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="S3 batch delete error"
            )
        except Exception:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unexpected S3 error"
            )