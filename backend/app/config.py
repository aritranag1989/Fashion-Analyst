from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../infra/env/.env", env_file_encoding="utf-8", extra="ignore"
    )

    environment: str = "local"
    log_level: str = "INFO"

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    voyage_api_key: str = ""

    claude_model_high_accuracy: str = "claude-opus-4-8"
    claude_model_standard: str = "claude-sonnet-5"

    embedding_provider: str = "voyage"
    voyage_embedding_model: str = "voyage-3-large"
    openai_embedding_model: str = "text-embedding-3-large"
    embedding_dim: int = 1024

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "fashion_analyst"
    postgres_user: str = "fashion_analyst"
    postgres_password: str = "change-me"
    database_url: str = (
        "postgresql+asyncpg://fashion_analyst:change-me@localhost:5432/fashion_analyst"
    )

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "change-me-too"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    un_comtrade_api_key: str = ""

    confidence_threshold: float = 0.6

    imagegen_provider: str = "openai"
    openai_image_model: str = "gpt-image-1"
    pattern_data_dir: str = "data"


@lru_cache
def get_settings() -> Settings:
    return Settings()
