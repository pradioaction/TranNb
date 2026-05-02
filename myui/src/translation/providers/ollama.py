import logging
import httpx
from typing import Any, Dict, List
from .base import BaseTranslationProvider, ProviderType

logger = logging.getLogger(__name__)


class OllamaTranslationProvider(BaseTranslationProvider):
    def __init__(self, name: str = "Ollama", provider_type: ProviderType = ProviderType.SYSTEM):
        super().__init__(name, provider_type)
        self.config.setdefault("base_url", "http://localhost:11434")
        self.config.setdefault("model", "qwen2.5:0.5b")
        self.config.setdefault("timeout", 30)
    
    async def translate(self, text: str, prompt_template: str = "", **kwargs) -> str:
        if not prompt_template:
            prompt_template = "请翻译{input}"
        prompt = prompt_template.format(input=text)
        
        logger.info(f"[Ollama] 输入文本: {text}")
        logger.info(f"[Ollama] 完整提示词: {prompt}")

        base = (self.config.get("base_url") or "").lower()
        if "volces.com" in base or "ark.cn-beijing" in base:
            raise ValueError(
                "检测到接口地址为火山方舟域名，但当前仍按 Ollama 调用（会请求 …/api/generate，导致 401 或无效响应）。"
                "请在「设置 → 翻译服务」中编辑该自定义模型，将「后端」选为「火山方舟 Ark」，"
                "填写「API 密钥环境变量名」与推理接入点 ID，并在系统中配置对应环境变量。"
            )
        
        try:
            async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                response = await client.post(
                    f"{self.config['base_url']}/api/generate",
                    json={
                        "model": self.config["model"],
                        "prompt": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()
                translated_text = result.get("response", "")
                logger.info(f"[Ollama] 翻译结果: {translated_text}")
                return translated_text
        except Exception as e:
            logger.error(f"Ollama translation failed: {e}")
            raise
    
    def list_models(self) -> List[str]:
        """获取 Ollama 本地已下载的模型列表"""
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(f"{self.config['base_url']}/api/tags")
                response.raise_for_status()
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                logger.info(f"[Ollama] 发现模型: {models}")
                return models
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    def test_connection(self) -> bool:
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(f"{self.config['base_url']}/api/tags")
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Ollama connection test failed: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.provider_type.value,
            "base_url": self.config["base_url"],
            "model": self.config["model"]
        }


class CustomOllamaProvider(OllamaTranslationProvider):
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, ProviderType.CUSTOM)
        self.update_config(config)
        ep = (self.config.get("endpoint") or "").strip()
        if ep:
            self.config["base_url"] = ep.rstrip("/")
