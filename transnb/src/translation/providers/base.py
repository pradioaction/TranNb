from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum


class ProviderType(Enum):
    SYSTEM = "system"
    CUSTOM = "custom"


class BaseTranslationProvider(ABC):
    def __init__(self, name: str, provider_type: ProviderType = ProviderType.SYSTEM):
        self.name = name
        self.provider_type = provider_type
        self.config: Dict[str, Any] = {}
    
    @abstractmethod
    async def translate(self, text: str, prompt_template: str = "", **kwargs) -> str:
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        pass
    
    def set_config(self, key: str, value: Any):
        self.config[key] = value
    
    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
    
    def update_config(self, config: Dict[str, Any]):
        self.config.update(config)
    
    def get_display_name(self) -> str:
        if self.provider_type == ProviderType.CUSTOM:
            return f"自定义: {self.name}"
        return self.name
