from PyQt5.QtCore import pyqtSignal as Signal, QThread
import httpx


class OllamaAsyncWorker(QThread):
    """异步处理 Ollama 连接测试和模型获取"""
    test_success = Signal(int)  # 返回模型数量
    test_failed = Signal(str)  # 返回错误信息
    models_fetched = Signal(list)  # 返回模型列表
    models_fetch_failed = Signal(str)  # 返回错误信息

    def __init__(self, base_url, operation="test", timeout=10):
        super().__init__()
        self.base_url = base_url
        self.operation = operation  # "test" 或 "list_models"
        self.timeout = timeout

    def run(self):
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                models = [model.get("name", "") for model in data.get("models", [])]
                
                if self.operation == "test":
                    self.test_success.emit(len(models))
                else:
                    self.models_fetched.emit(models)
        except Exception as e:
            error_msg = str(e)
            if self.operation == "test":
                self.test_failed.emit(error_msg)
            else:
                self.models_fetch_failed.emit(error_msg)


class GenericTestWorker(QThread):
    """通用的异步测试连接 worker"""
    test_success = Signal(int)  # 返回状态码
    test_failed = Signal(str)  # 返回错误信息

    def __init__(self, base_url, timeout=10):
        super().__init__()
        self.base_url = base_url
        self.timeout = timeout

    def run(self):
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(self.base_url)
                self.test_success.emit(response.status_code)
        except Exception as e:
            self.test_failed.emit(str(e))


class ArkTestWorker(QThread):
    """火山方舟：在后台线程调用 Chat 完成连通性检测。"""

    test_success = Signal()
    test_failed = Signal(str)

    def __init__(self, model_config: dict):
        super().__init__()
        self.model_config = model_config

    def run(self):
        try:
            from translation.providers.ark import CustomArkProvider

            name = self.model_config.get("name") or "ark"
            provider = CustomArkProvider(name, self.model_config)
            if provider.test_connection():
                self.test_success.emit()
            else:
                self.test_failed.emit("请求未完成，请检查模型 ID、密钥与网络")
        except Exception as e:
            self.test_failed.emit(str(e))


class OpenAITestWorker(QThread):
    """内置 OpenAI：后台线程调用 Chat Completions 做连通性检测。"""

    test_success = Signal()
    test_failed = Signal(str)

    def __init__(self, ui_config: dict):
        super().__init__()
        self.ui_config = ui_config

    def run(self):
        try:
            from translation.providers.openai_provider import OpenAITranslationProvider

            ep = (self.ui_config.get("endpoint") or "").strip()
            provider = OpenAITranslationProvider()
            provider.update_config({
                "base_url": ep or "https://api.openai.com/v1",
                "model": (self.ui_config.get("model") or "").strip(),
                "api_key_env": (self.ui_config.get("api_key_env") or "").strip(),
                "timeout": self.ui_config.get("timeout", 60),
                "proxy": (self.ui_config.get("proxy") or "").strip(),
            })
            if provider.test_connection():
                self.test_success.emit()
            else:
                self.test_failed.emit("请求未完成，请检查模型名、环境变量与网络")
        except Exception as e:
            self.test_failed.emit(str(e))


__all__ = [
    'OllamaAsyncWorker',
    'GenericTestWorker',
    'ArkTestWorker',
    'OpenAITestWorker'
]
