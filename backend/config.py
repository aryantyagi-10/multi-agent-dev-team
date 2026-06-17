from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    POSTGRES_USER: str = "agentuser"
    POSTGRES_PASSWORD: str = "agentpass"
    POSTGRES_DB: str = "agentdb"
    POSTGRES_HOST: str = "postgres_db"
    POSTGRES_PORT: int = 5432

    REDIS_HOST: str = "redis_cache"
    REDIS_PORT: int = 6379

    KAFKA_BOOTSTRAP_SERVERS: str = "kafka_broker:9092"
    KAFKA_JOB_TOPIC: str = "agent_jobs"

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 120

    OPENAI_API_KEY: str = "sk-replace-me"
    OPENAI_BASE_URL: str = "[api.openai.com](https://api.openai.com/v1)"
    LLM_MODEL: str = "gpt-4o-mini"

    @property
    def async_db_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_db_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"


settings = Settings()
