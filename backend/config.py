from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    JWT_SECRET_KEY: str
    PAYSTACK_SECRET_KEY: str
    PAYSTACK_PUBLIC_KEY: str
    DATABASE_URL: str = "sqlite:///./podcast.db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RATE_LIMIT_PER_MINUTE: int = 100
    PAYSTACK_WEBHOOK_SECRET: str

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = AppSettings()
