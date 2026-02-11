from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://terptracker:terptracker@localhost:5432/terptracker"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Cannlytics API
    cannlytics_api_key: str = ""
    cannlytics_base_url: str = "https://cannlytics.com/api"

    # Otreeba API (service currently offline)
    otreeba_api_key: str = ""

    # Application
    debug: bool = False
    log_level: str = "INFO"
    rate_limit_per_minute: int = 30

    # CORS origins (comma-separated for multiple origins)
    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
