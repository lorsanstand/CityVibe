from datetime import datetime, timezone
from contextlib import asynccontextmanager

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from string import Template

from aiobotocore.session import get_session
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
import smtplib

from app.config import settings

class Email:
    @classmethod
    def render_template_from_file(cls, path: str, **context):
        with open(path, "r", encoding="utf-8") as file:
            tpl = Template(file.read())
        return  tpl.safe_substitute(**context)


    @classmethod
    def send_verify_email(cls, username: str, email: str, url: str):
        with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)

            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_EMAIL
            msg["To"] = email
            msg["Subject"] = "Подтверждение регистрации"

            # Тело письма — осмысленное и форматированное
            body = f"""
            Здравствуйте, {username}!
    
            Для подтверждения вашей регистрации перейдите по ссылке:
            {url}
    
            Если вы не создавали аккаунт — просто проигнорируйте это письмо.
    
            С уважением,  
            Команда CityVibe
                """

            html = cls.render_template_from_file(
                "app/templates/mail.html",
                user_name=username,
                confirmation_url=url,
                expiry_minutes=120,
                site_name="CityVibe",
                site_url="https://example.com",
                support_email="support@example.com",
                year=datetime.now(timezone.utc).year
            )

            msg.attach(MIMEText(html, "html", "utf-8"))
            msg.attach(MIMEText(body, "plain", "utf-8"))

            server.send_message(msg, settings.SMTP_EMAIL, email)


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
        self.session = get_session()

    @asynccontextmanager
    async def _get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client # AioBaseClient


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


s3_client = S3Client(
    access_key=settings.S3_ACCESS_KEY_ID,
    secret_key=settings.S3_SECRET_ACCESS_KEY,
    endpoint_url=settings.S3_URL,
    bucket_name=settings.S3_BUCKET_NAME
)