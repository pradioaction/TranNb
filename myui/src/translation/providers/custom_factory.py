"""
自定义翻译后端工厂。

设计要点：
- custom_models 数组中的每条记录复用现有表单字段；用 backend 区分实现（默认 ollama 兼容旧数据）。
- 新增后端时在此处分流，避免 TranslationService 堆积分支逻辑。
"""
from typing import Any, Dict

from .base import BaseTranslationProvider
from .ollama import CustomOllamaProvider


def build_custom_provider(name: str, model: Dict[str, Any]) -> BaseTranslationProvider:
    backend = (model.get("backend") or "ollama").strip().lower()
    if backend == "ark":
        from .ark import CustomArkProvider

        return CustomArkProvider(name, model)
    return CustomOllamaProvider(name, model)
