import os
from pathlib import Path
from typing import Tuple


PROJECT_ROOT = Path(__file__).resolve().parent
_ENV_LOADED = False

VOLCES_MODELS = {"deepseek-v3-250324", "deepseek-r1-250120"}
DEEPSEEK_MODELS = {"deepseek-chat", "deepseek-reasoner"}
ALIYUN_MODELS = {
    "deepseek-v3",
    "deepseek-v3.1",
    "deepseek-v3.2-exp",
    "deepseek-r1",
    "deepseek-r1-0528",
}


def load_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

    _ENV_LOADED = True


def get_project_root() -> Path:
    return PROJECT_ROOT


def get_dataset_root() -> Path:
    load_env()
    configured = os.environ.get("ASTRA_DATASET_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (PROJECT_ROOT.parent / "dataset").resolve()


def get_default_embedding_path() -> str | None:
    load_env()
    value = os.environ.get("ASTRA_EMBEDDING_MODEL_PATH", "").strip()
    return value or None


def get_local_model_base_url(default: str = "http://localhost:8000") -> str:
    load_env()
    return os.environ.get("ASTRA_LOCAL_MODEL_BASE_URL", default).strip()


def get_cache_root() -> Path:
    return PROJECT_ROOT / "cache"


def get_record_root() -> Path:
    return PROJECT_ROOT / "record"


def resolve_openai_client_config(
    model: str,
    api_key: str = "",
    base_url: str = "",
) -> Tuple[str, str]:
    load_env()

    explicit_api_key = api_key.strip()
    explicit_base_url = base_url.strip()
    if explicit_api_key:
        resolved_base_url = explicit_base_url or os.environ.get(
            "OPENAI_BASE_URL", "https://api.openai.com/v1"
        )
        return explicit_api_key, resolved_base_url

    if model in VOLCES_MODELS:
        return (
            os.environ.get("VOLCES_API_KEY", "").strip(),
            explicit_base_url or "https://ark.cn-beijing.volces.com/api/v3",
        )

    if model in DEEPSEEK_MODELS:
        return (
            os.environ.get("DEEPSEEK_API_KEY", "").strip(),
            explicit_base_url or "https://api.deepseek.com",
        )

    if model in ALIYUN_MODELS:
        return (
            os.environ.get("ALIYUN_API_KEY", "").strip(),
            explicit_base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    return (
        os.environ.get("OPENAI_API_KEY", "").strip(),
        explicit_base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )


def require_openai_client_config(model: str, api_key: str = "", base_url: str = "") -> Tuple[str, str]:
    resolved_api_key, resolved_base_url = resolve_openai_client_config(
        model=model,
        api_key=api_key,
        base_url=base_url,
    )
    if not resolved_api_key:
        raise ValueError(
            "Missing API key. Set OPENAI_API_KEY for OpenAI-compatible models, "
            "or VOLCES_API_KEY / DEEPSEEK_API_KEY / ALIYUN_API_KEY for the matching provider."
        )
    return resolved_api_key, resolved_base_url
