import logging
from typing import Any
from ..base_engine import BaseTranslationEngine

logger = logging.getLogger(__name__)


class ParseMode(BaseTranslationEngine):
    """解析模式 - 绑定单元格翻译功能
    
    该模式用于单元格旁边的翻译按钮调用
    """
    def __init__(self):
        super().__init__("parse")
    
    def process(self, input_data: Any, prompt_template: str = "") -> Any:
        """
        处理输入数据
        
        Args:
            input_data: 输入数据（通常是单元格内容）
            prompt_template: 提示词模板
            
        Returns:
            处理结果
        """
        logger.info(f"[解析模式] 开始处理单元格翻译")
        logger.info(f"[解析模式] 输入内容: {input_data}")
        logger.info(f"[解析模式] 提示词模板: {prompt_template}")
        
        # 构建完整提示词
        if prompt_template and "{input}" in prompt_template:
            full_prompt = prompt_template.replace("{input}", str(input_data))
        else:
            full_prompt = f"请解析{input_data}"
        
        logger.info(f"[解析模式] 完整提示词: {full_prompt}")
        logger.info(f"[解析模式] 预留位置 - 调用真实翻译 API")
        
        # 返回占位结果，等待真实翻译 API 集成
        result = f"(解析结果)\n{input_data}"
        logger.info(f"[解析模式] 处理完成")
        return result
