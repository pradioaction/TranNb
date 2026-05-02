from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTranslationEngine(ABC):
    def __init__(self, name: str):
        self.name = name
        self.config: Dict[str, Any] = {}
    
    @abstractmethod
    def process(self, input_data: Any, prompt_template: str = "") -> Any:
        pass
    
    def set_config(self, key: str, value: Any):
        self.config[key] = value
    
    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
