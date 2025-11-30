from pydantic_settings import BaseSettings
import os


class EnvSettings(BaseSettings):
    BOT_TOKEN: str
    BOT_ADMIN_ID: int
    CHANNEL_ID: int  # Private channel ID (negative for channels)
    CHANNEL_USERNAME: str  # admin ID
    LOG_LEVEL: str = "ERROR"  # Default to INFO

    class Config:
        env_file = ".env" if os.getenv("ENVIRONMENT") == "dev" else None


try:
    env = EnvSettings()
except Exception as e:
    exit(1)
