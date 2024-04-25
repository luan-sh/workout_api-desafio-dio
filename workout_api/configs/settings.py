from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str = Field(default="postgresql+asyncpg://postgresuser:postgres@localhost/postgres")

settings = Settings()