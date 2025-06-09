import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5433")
    DB_USER: str = os.getenv("DB_USER", "dev_user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "dev_password")
    DB_NAME: str = os.getenv("DB_NAME", "player_profiler_db")
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LENS Player Profiler"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000"]
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()