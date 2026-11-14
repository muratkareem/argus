from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ARGUS_", env_file=".env", extra="ignore", validate_assignment=True
    )
    database_url: str = "sqlite:///./argus.db"
    artifact_dir: Path = Path("ml/artifacts")
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    max_upload_bytes: int = 192 * 1024 * 1024
    api_key: SecretStr | None = Field(default=None, repr=False)
