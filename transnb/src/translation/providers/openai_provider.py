import asyncio
import logging
from typing import Any, Dict

import httpx

from .api_key_resolve import resolve_openai_api_key
from .base import BaseTranslationProvider, ProviderType

logger = logging.getLogger(__name__)


class OpenAITranslationProvider(BaseTranslationProvider):
    """OpenAI 兼容 Chat Completions（密钥仅从环境变量解析）。"""

    def __init__(self):
        super().__init__("OpenAI", ProviderType.SYSTEM)
        self.config.setdefault("base_url", "https://api.openai.com/v1")
        self.config.setdefault("model", "gpt-3.5-turbo")
        self.config.setdefault("timeout", 60)

    def _base_url(self) -> str:
        return (self.config.get("base_url") or "https://api.openai.com/v1").rstrip("/")

    def _model(self) -> str:
        return (self.config.get("model") or "").strip() or "gpt-3.5-turbo"

    def _timeout(self) -> float:
        try:
            return float(self.config.get("timeout") or 60)
        except (TypeError, ValueError):
            return 60.0

    def _client_kwargs(self) -> Dict[str, Any]:
        kw: Dict[str, Any] = {"timeout": self._timeout()}
        proxy = (self.config.get("proxy") or "").strip()
        if proxy:
            kw["proxy"] = proxy
        return kw

    def _chat_sync(self, user_content: str) -> str:
        key = resolve_openai_api_key(self.config)
        if not key:
            env_name = (self.config.get("api_key_env") or "").strip()
            if env_name:
                raise ValueError(f"未读取到 API Key：请设置环境变量「{env_name}」")
            raise ValueError("未配置 OpenAI 密钥：请填写「API 密钥环境变量名」或设置 OPENAI_API_KEY")

        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": self._model(),
            "messages": [{"role": "user", "content": user_content}],
        }
        url = f"{self._base_url()}/chat/completions"
        with httpx.Client(**self._client_kwargs()) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        return content if isinstance(content, str) else str(content or "")

    async def translate(self, text: str, prompt_template: str = "", **kwargs) -> str:
        if not prompt_template:
            prompt_template = "请翻译{input}"
        prompt = prompt_template.format(input=text)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._chat_sync, prompt)

    def test_connection(self) -> bool:
        try:
            self._chat_sync("Hi")
            return True
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.provider_type.value,
            "backend": "openai",
            "base_url": self._base_url(),
            "model": self._model(),
        }
