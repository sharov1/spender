from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str
    #DATABASE_URL: str = "postgresql://postgres:postgres@postgres:5432/expenses"

    class Config:
        env_file = ".env"

settings = Settings()
