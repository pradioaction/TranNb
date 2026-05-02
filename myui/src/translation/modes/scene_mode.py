import logging
from typing import Any
from ..base_engine import BaseTranslationEngine

logger = logging.getLogger(__name__)


class SceneMode(BaseTranslationEngine):
    """造景模式 - 预留接口，暂不实现真实功能
    
    该模式目前只打印日志，等待后续开发
    """
    def __init__(self):
        super().__init__("scene")
    
    def process(self, input_data: Any, prompt_template: str = "") -> Any:
        logger.info(f"[造景模式] 预留接口被调用 - 暂不实现真实功能")
        logger.info(f"[造景模式] 输入数据: {input_data}")
        logger.info(f"[造景模式] 提示词: {prompt_template}")
        return None
