"""Application configuration classes for different environments."""

import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    """Base configuration shared across all environments."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    DEBUG = False
    TESTING = False

    # SQLAlchemy
    # Render provides DATABASE_URL as "postgres://" but SQLAlchemy 2.0 requires "postgresql://"
    _db_url = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/medassist")
    SQLALCHEMY_DATABASE_URI = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-change-me-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ["headers"]

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # EURI API Gateway (OpenAI-compatible) — https://euron.one/euri
    EURI_BASE_URL = os.getenv("EURI_BASE_URL", "https://api.euron.one/api/v1/euri")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", os.getenv("EURI_API_KEY", ""))
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", os.getenv("EURI_BASE_URL", "https://api.euron.one/api/v1/euri"))
    OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
    OPENAI_MODEL_PRIMARY = os.getenv("OPENAI_MODEL_PRIMARY", "gpt-4o-mini")
    OPENAI_MODEL_FAST = os.getenv("OPENAI_MODEL_FAST", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

    # Pinecone
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "medical-knowledge")

    # InfluxDB
    INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")
    INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "medassist")
    INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "vitals")

    # Elasticsearch
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

    # S3 / MinIO
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "medassist-reports")
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")

    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

    # SendGrid
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "")

    # Daily.co
    DAILY_API_KEY = os.getenv("DAILY_API_KEY", "")
    DAILY_DOMAIN = os.getenv("DAILY_DOMAIN", "")

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

    # Encryption
    PHI_ENCRYPTION_KEY = os.getenv("PHI_ENCRYPTION_KEY", "")

    # Rate Limiting — fall back to in-memory when Redis is not available (e.g. Render free tier)
    RATELIMIT_DEFAULT = "200/hour"
    RATELIMIT_STORAGE_URI = os.getenv("REDIS_URL", "memory://")


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""

    DEBUG = True
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    RATELIMIT_DEFAULT = "1000/hour"
    RATELIMIT_STORAGE_URI = os.getenv("REDIS_URL", "memory://")


class TestingConfig(BaseConfig):
    """Testing environment configuration.

    Uses SQLite for local testing (no Docker needed).
    CI overrides with TEST_DATABASE_URL pointing to real PostgreSQL.
    """

    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        os.getenv("DATABASE_URL", "sqlite:///test.db"),
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    RATELIMIT_ENABLED = False


class ProductionConfig(BaseConfig):
    """Production environment configuration."""

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": 20,
        "max_overflow": 40,
        "pool_recycle": 3600,
    }

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)

    @classmethod
    def init_app(cls, app: object) -> None:
        """Validate that secrets have been changed from defaults."""
        if cls.SECRET_KEY == "change-me-in-production":
            raise RuntimeError(
                "SECRET_KEY is still the default value. "
                "Set a secure SECRET_KEY environment variable before running in production."
            )
        if cls.JWT_SECRET_KEY == "jwt-change-me-in-production":
            raise RuntimeError(
                "JWT_SECRET_KEY is still the default value. "
                "Set a secure JWT_SECRET_KEY environment variable before running in production."
            )


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
