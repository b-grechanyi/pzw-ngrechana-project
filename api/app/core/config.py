from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Library API"
    ENV: str = "dev"
    DATABASE_URL: str
    JWT_SECRET: str = "change-me"
    JWT_ISSUER: str = "library"

    class Config:
        env_file = "../.env"

settings = Settings()