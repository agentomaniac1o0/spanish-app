from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/spanish.db"
    api_key: str = ""
    cors_origins: list[str] = ["http://localhost:8080", "http://localhost:3000"]

    openrouter_api_key: str = ""
    openrouter_model: str = "deepseek/deepseek-v4-flash"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    telegram_bot_token: str = ""

    hermes_ssh_host: str = "192.168.0.144"
    hermes_ssh_user: str = "hermes"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
