import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ModelManager:
    def __init__(self):
        self.models: Dict[str, Dict[str, Any]] = {}
        self.current_model: Optional[str] = None
    
    def add_model(self, model_name: str, model_config: Dict[str, Any]) -> bool:
        if model_name in self.models:
            logger.warning(f"ModelManager: 模型 {model_name} 已存在")
            return False
        self.models[model_name] = model_config
        logger.info(f"ModelManager: 添加模型 {model_name}")
        return True
    
    def update_model(self, model_name: str, model_config: Dict[str, Any]) -> bool:
        if model_name not in self.models:
            logger.warning(f"ModelManager: 模型 {model_name} 不存在")
            return False
        self.models[model_name] = model_config
        logger.info(f"ModelManager: 更新模型 {model_name}")
        return True
    
    def delete_model(self, model_name: str) -> bool:
        if model_name not in self.models:
            logger.warning(f"ModelManager: 模型 {model_name} 不存在")
            return False
        del self.models[model_name]
        if self.current_model == model_name:
            self.current_model = None
        logger.info(f"ModelManager: 删除模型 {model_name}")
        return True
    
    def enable_model(self, model_name: str) -> bool:
        if model_name not in self.models:
            logger.warning(f"ModelManager: 模型 {model_name} 不存在")
            return False
        self.models[model_name]['enabled'] = True
        logger.info(f"ModelManager: 启用模型 {model_name}")
        return True
    
    def disable_model(self, model_name: str) -> bool:
        if model_name not in self.models:
            logger.warning(f"ModelManager: 模型 {model_name} 不存在")
            return False
        self.models[model_name]['enabled'] = False
        if self.current_model == model_name:
            self.current_model = None
        logger.info(f"ModelManager: 禁用模型 {model_name}")
        return True
    
    def set_model_enabled(self, model_name: str, enabled: bool) -> bool:
        if model_name not in self.models:
            return False
        self.models[model_name]['enabled'] = enabled
        if not enabled and self.current_model == model_name:
            self.current_model = None
        return True
    
    def register_model(self, model_name: str, model_config: Dict[str, Any]):
        self.add_model(model_name, model_config)
    
    def set_current_model(self, model_name: str) -> bool:
        if model_name in self.models:
            if not self.models[model_name].get('enabled', False):
                logger.warning(f"ModelManager: 模型 {model_name} 未启用")
                return False
            self.current_model = model_name
            logger.info(f"ModelManager: 设置当前模型为 {model_name}")
            return True
        logger.warning(f"ModelManager: 模型 {model_name} 不存在")
        return False
    
    def get_current_model(self) -> Optional[str]:
        return self.current_model
    
    def get_model_config(self, model_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        name = model_name or self.current_model
        return self.models.get(name)
    
    def list_models(self) -> List[str]:
        return list(self.models.keys())
    
    def list_enabled_models(self) -> List[str]:
        return [name for name, config in self.models.items() if config.get('enabled', False)]
    
    def get_all_models(self) -> Dict[str, Dict[str, Any]]:
        return self.models.copy()
    
    def load_models(self, models_list: List[Dict[str, Any]]):
        self.models.clear()
        for model in models_list:
            name = model.get('name')
            if name:
                self.models[name] = model
    
    def export_models(self) -> List[Dict[str, Any]]:
        return list(self.models.values())
