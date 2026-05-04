from PyQt5.QtCore import QThread, pyqtSignal as Signal
import asyncio


class GenerateArticleWorker(QThread):
    finished = Signal(bool, str, str)
    progress = Signal(str)

    def __init__(self, translation_service, words, prompt_template=None):
        super().__init__()
        self.translation_service = translation_service
        self.words = words
        self.prompt_template = prompt_template

    def run(self):
        try:
            self.progress.emit("正在生成文章...")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                article = loop.run_until_complete(
                    self.translation_service.generate_scene_text(
                        self.words,
                        self.prompt_template
                    )
                )
                loop.close()
                self.finished.emit(True, article, "")
            except Exception as e:
                loop.close()
                self.finished.emit(False, "", str(e))

        except Exception as e:
            self.finished.emit(False, "", str(e))
