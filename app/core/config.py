from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    NEO4J_URI: str
    NEO4J_USERNAME: str
    NEO4J_PASSWORD: str
    JWT_SECRET_KEY: str
    TWILIO_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONEAUTH_SERVICE_SID: str
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
