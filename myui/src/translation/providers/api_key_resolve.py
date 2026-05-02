"""从自定义模型配置解析 Ark API Key（环境变量名 / 兼容旧版明文）。"""
import os
from typing import Any, Dict


def resolve_ark_api_key(config: Dict[str, Any]) -> str:
    env_var = (config.get("api_key_env") or "").strip()
    if env_var:
        return (os.environ.get(env_var) or "").strip()
    legacy = (config.get("api_key") or "").strip()
    if legacy:
        return legacy
    return (os.environ.get("ARK_API_KEY") or "").strip()


def ark_api_key_configured(config: Dict[str, Any]) -> bool:
    return bool(resolve_ark_api_key(config))


def resolve_openai_api_key(config: Dict[str, Any]) -> str:
    env_var = (config.get("api_key_env") or "").strip()
    if env_var:
        return (os.environ.get(env_var) or "").strip()
    legacy = (config.get("api_key") or "").strip()
    if legacy:
        return legacy
    return (os.environ.get("OPENAI_API_KEY") or "").strip()


def openai_api_key_configured(config: Dict[str, Any]) -> bool:
    return bool(resolve_openai_api_key(config))
