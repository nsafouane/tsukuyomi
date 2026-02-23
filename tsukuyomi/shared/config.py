"""
Configuration management for Tsukuyomi.

Centralized configuration for logging, LLM providers, and system settings.
"""

import logging
import os
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    provider: str = "groq"
    api_key: Optional[str] = None
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 30


@dataclass
class DatabaseConfig:
    """Database configuration."""
    connection_string: Optional[str] = None
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class VectorStoreConfig:
    """Vector store configuration."""
    provider: str = "qdrant"
    host: str = "localhost"
    port: int = 6333
    collection_name: str = "tsukuyomi_memories"


@dataclass
class Config:
    """Main configuration class."""
    llm: LLMConfig = field(default_factory=LLMConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    debug: bool = False
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        llm_config = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "groq"),
            api_key=os.getenv("LLM_API_KEY"),
            model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30")),
        )

        database_config = DatabaseConfig(
            connection_string=os.getenv("DATABASE_URL"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        )

        vector_config = VectorStoreConfig(
            provider=os.getenv("VECTOR_PROVIDER", "qdrant"),
            host=os.getenv("VECTOR_HOST", "localhost"),
            port=int(os.getenv("VECTOR_PORT", "6333")),
            collection_name=os.getenv("VECTOR_COLLECTION", "tsukuyomi_memories"),
        )

        return cls(
            llm=llm_config,
            database=database_config,
            vector_store=vector_config,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def configure_logging(level: str = "INFO") -> None:
    """Configure logging for Tsukuyomi.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
