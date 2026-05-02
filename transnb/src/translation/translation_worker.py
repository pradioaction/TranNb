import asyncio
import logging
from PyQt5.QtCore import QThread, pyqtSignal as Signal
from .translation_service import TranslationService

logger = logging.getLogger(__name__)


class TranslationWorker(QThread):
    """翻译工作线程 - 在后台执行翻译任务"""
    
    started = Signal()
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int)
    
    def __init__(
        self,
        translation_service: TranslationService,
        text: str,
        prompt_template: str = "",
        provider_name: str = None,
        timeout: int = 30
    ):
        super().__init__()
        self.translation_service = translation_service
        self.text = text
        self.prompt_template = prompt_template
        self.provider_name = provider_name
        self.timeout = timeout
    
    def run(self):
        """执行翻译任务"""
        try:
            self.started.emit()
            logger.info(f"[TranslationWorker] 开始翻译，文本长度: {len(self.text)}")
            
            # 使用 asyncio 运行异步翻译
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    asyncio.wait_for(
                        self.translation_service.translate(
                            self.text,
                            self.prompt_template,
                            self.provider_name
                        ),
                        timeout=self.timeout
                    )
                )
                self.finished.emit(result)
                logger.info(f"[TranslationWorker] 翻译完成")
            finally:
                loop.close()
                
        except asyncio.TimeoutError:
            error_msg = f"翻译超时（{self.timeout}秒）"
            logger.error(f"[TranslationWorker] {error_msg}")
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"翻译失败: {str(e)}"
            logger.error(f"[TranslationWorker] {error_msg}", exc_info=True)
            self.error.emit(error_msg)
