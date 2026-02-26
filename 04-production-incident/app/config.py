"""Application configuration settings."""

import os


class Config:
    """Configuration for the production server."""

    # Database connection pool settings
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = int(os.environ.get("DB_PORT", "5432"))
    DB_NAME = os.environ.get("DB_NAME", "orders_prod")
    DB_USER = os.environ.get("DB_USER", "app_user")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "s3cur3_p@ss")

    # Connection pool limits
    POOL_MIN_SIZE = int(os.environ.get("POOL_MIN_SIZE", "5"))
    POOL_MAX_SIZE = int(os.environ.get("POOL_MAX_SIZE", "20"))
    POOL_TIMEOUT = int(os.environ.get("POOL_TIMEOUT", "5"))  # seconds

    # Server settings
    SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.environ.get("SERVER_PORT", "8080"))
    WORKER_COUNT = int(os.environ.get("WORKER_COUNT", "4"))

    # Health check
    HEALTH_CHECK_TIMEOUT = int(os.environ.get("HEALTH_CHECK_TIMEOUT", "3"))

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FILE = os.environ.get("LOG_FILE", "logs/error.log")

    @classmethod
    def get_db_url(cls):
        """Build the database connection URL."""
        return (
            f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}"
            f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        )
