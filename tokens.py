import os
from pathlib import Path


def _normalize_token(value):
    token = (value or "").strip().strip('"').strip("'")
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    return token


def _load_dotenv_local():
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv_local()


GITHUB_TOKEN = _normalize_token(os.getenv("GITHUB_TOKEN", "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"))
GITHUB_MODEL = os.getenv("GITHUB_MODEL", "openai/gpt-4o").strip()
GITHUB_API_BASE_URL = os.getenv("GITHUB_API_BASE_URL", "https://models.github.ai/inference").strip()
GITHUB_API_VERSION = os.getenv("GITHUB_API_VERSION", "2024-08-01-preview").strip()
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
MAX_HTTP_RETRIES = int(os.getenv("MAX_HTTP_RETRIES", "3"))
VALIDATION_RETRIES = int(os.getenv("VALIDATION_RETRIES", "2"))
