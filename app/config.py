from decouple import config

class Settings:
    SUPABASE_URL: str = config("SUPABASE_URL")
    SUPABASE_KEY: str = config("SUPABASE_KEY")
    SUPABASE_SERVICE_KEY: str = config("SUPABASE_SERVICE_KEY")
    JWT_SECRET: str = config("JWT_SECRET")
    JWT_ALGORITHM: str = config("JWT_ALGORITHM", default="HS256")
    ANTHROPIC_API_KEY: str = config("ANTHROPIC_API_KEY")
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    class Config:
        env_file = ".env"

settings = Settings()