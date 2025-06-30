"""Application configuration."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""

    # Reddit API Configuration
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "reddit-analyzer/0.1.0")
    REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
    REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

    # Database Configuration
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://reddit_user:password@localhost:5432/reddit_analyzer",
    )
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Application Configuration
    APP_ENV = os.getenv("APP_ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Authentication Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    @classmethod
    def validate(cls):
        """Validate required configuration values."""
        required_fields = [
            "REDDIT_CLIENT_ID",
            "REDDIT_CLIENT_SECRET",
            "REDDIT_USER_AGENT",
            "DATABASE_URL",
        ]

        missing_fields = []
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_fields)}"
            )

        return True


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


class TestConfig(Config):
    """Test configuration."""

    TESTING = True
    DATABASE_URL = "postgresql://test_user:password@localhost:5432/reddit_analyzer_test"


def get_config():
    """Get configuration based on environment."""
    env = os.getenv("APP_ENV", "development")

    if env == "production":
        return ProductionConfig
    elif env == "test":
        return TestConfig
    else:
        return DevelopmentConfig
