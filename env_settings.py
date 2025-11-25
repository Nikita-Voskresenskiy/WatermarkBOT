from pydantic_settings import BaseSettings
class EnvSettings(BaseSettings):
    BOT_TOKEN: str  
    BOT_ADMIN_ID: int
    CHANNEL_ID: int # Private channel ID (negative for channels)
    CHANNEL_USERNAME: str # admin ID

    class Config:
        env_file = ".env"

env = EnvSettings()