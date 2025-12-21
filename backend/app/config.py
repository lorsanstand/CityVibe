from typing import Literal, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    MODE: Literal["DEV", "TEST", "PROD"]

    DB_HOST: str
    DB_PORT: int
    DB_PASS: str
    DB_USER: str
    DB_NAME: str


    @property
    def DATABASE_URL(self) -> str:
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'


    TEST_DB_HOST: str
    TEST_DB_PORT: int
    TEST_DB_PASS: str
    TEST_DB_USER: str
    TEST_DB_NAME: str


    @property
    def TEST_DATABASE_URL(self) -> str:
        return f'postgresql+asyncpg://{self.TEST_DB_USER}:{self.TEST_DB_PASS}@{self.TEST_DB_HOST}:{self.TEST_DB_PORT}/{self.TEST_DB_NAME}'
    

    RMQ_HOST: str
    RMQ_USER: str
    RMQ_PASS: str
    RMQ_PORT: int

    @property
    def BROKER_URL(self) -> str:
        return f"amqp://{self.RMQ_USER}:{self.RMQ_PASS}@{self.RMQ_HOST}:{self.RMQ_PORT}//"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    VERIFY_EMAIL_TOKEN_HOURS: int = 2

    SECRET: str
    ALGORITHMS: str = "HS256"

    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_EMAIL: str
    SMTP_PASSWORD: str

    URL: str

    S3_URL: str
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str

    CORS_ORIGINS: List[str]
    CORS_HEADERS: List[str]
    CORS_METHODS: List[str]

    FIRST_SUPERUSER_EMAIL: str
    FIRST_SUPERUSER_PASS: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()