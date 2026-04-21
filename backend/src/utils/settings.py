from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    google_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash-latest"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    llm_provider: str = "gemini"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048
    llm_timeout: int = 30
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_db: str = "realestate_db"
    mysql_user: str = "root"
    mysql_password: str = "password"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "realestate_docs"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:3000"
    log_level: str = "INFO"
    mlflow_tracking_uri: str = "mlruns"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    faiss_index_path: str = "data/documents/faiss_index"
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k_final: int = 5
    min_score_threshold: float = 0.25

    @property
    def mysql_url(self) -> str:
        return f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
    @property
    def active_api_key(self) -> str:
        return self.groq_api_key if self.llm_provider == "groq" else self.google_api_key
    @property
    def active_model(self) -> str:
        return self.groq_model if self.llm_provider == "groq" else self.gemini_model

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
