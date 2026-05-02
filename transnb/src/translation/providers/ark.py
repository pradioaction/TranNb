import asyncio
import logging
from typing import Any, Dict

from .base import BaseTranslationProvider, ProviderType
from .api_key_resolve import resolve_ark_api_key

logger = logging.getLogger(__name__)

DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


class CustomArkProvider(BaseTranslationProvider):
    """火山引擎方舟：使用官方 Ark Runtime（OpenAI 兼容 Chat）。"""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, ProviderType.CUSTOM)
        self.update_config(config)
        self._normalize_config()

    def _normalize_config(self) -> None:
        self.config.setdefault("timeout", 120)
        ep = (self.config.get("endpoint") or "").strip()
        if ep:
            self.config["base_url"] = ep.rstrip("/")
        else:
            self.config["base_url"] = DEFAULT_ARK_BASE_URL

    def _resolved_api_key(self) -> str:
        return resolve_ark_api_key(self.config)

    def _client(self):
        try:
            from volcenginesdkarkruntime import Ark
        except ImportError as e:
            raise ImportError(
                "未安装方舟 SDK，请执行: pip install volcengine-python-sdk"
            ) from e
        return Ark(
            api_key=self._resolved_api_key(),
            base_url=self.config["base_url"],
        )

    def _chat_sync(self, user_content: str) -> str:
        model = (self.config.get("model") or "").strip()
        if not model:
            raise ValueError("未配置模型（方舟推理接入点 ID / 模型 ID）")
        api_key = self._resolved_api_key()
        if not api_key:
            env_name = (self.config.get("api_key_env") or "").strip()
            if env_name:
                raise ValueError(
                    f"未读取到 API Key：请在系统环境中设置变量「{env_name}」，或在设置中检查变量名"
                )
            raise ValueError(
                "未配置 API Key：请在模型中填写「API 密钥环境变量名」，或保留旧版 api_key / 环境变量 ARK_API_KEY"
            )

        client = self._client()
        timeout = int(self.config.get("timeout") or 120)
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": user_content}],
                timeout=timeout,
            )
        except TypeError:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": user_content}],
            )
        msg = completion.choices[0].message
        content = getattr(msg, "content", None)
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
            logger.error(f"Ark connection test failed: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.provider_type.value,
            "backend": "ark",
            "base_url": self.config.get("base_url"),
            "model": self.config.get("model"),
        }
