import logging
from typing import Any, Dict, List, Optional
from .modes import TranslationMode, ParseMode, SceneMode
from .providers import (
    BaseTranslationProvider,
    ProviderType,
    OllamaTranslationProvider,
    OpenAITranslationProvider,
    build_custom_provider,
)

logger = logging.getLogger(__name__)


class TranslationService:
    def __init__(self):
        self.translation_mode = TranslationMode()
        self.parse_mode = ParseMode()
        self.scene_mode = SceneMode()
        
        self.providers: Dict[str, BaseTranslationProvider] = {}
        self.current_provider_id: Optional[str] = None
        self.settings_manager = None
        
        self._register_system_providers()
    
    def set_settings_manager(self, settings_manager):
        """设置设置管理器并应用配置"""
        self.settings_manager = settings_manager
        self._apply_settings()

    def reload_from_settings(self):
        """设置对话框保存后调用，使当前选用的 provider 与自定义模型立即生效（无需重启）。"""
        self._apply_settings()
    
    def _build_provider_id(self, provider_type: str, name: str) -> str:
        """构建 provider_id"""
        return f"{provider_type}_{name}"

    def _normalize_provider_id(self, provider_id: Optional[str]) -> Optional[str]:
        """与设置/UI 旧数据对齐（曾写入 system_ollama，注册名为 system_Ollama）。"""
        if not provider_id:
            return None
        if provider_id == "system_ollama":
            return self._build_provider_id("system", "Ollama")
        if provider_id == "system_openai":
            return self._build_provider_id("system", "OpenAI")
        return provider_id
    
    def _parse_provider_id(self, provider_id: str) -> tuple:
        """解析 provider_id，返回 (type, name) 元组"""
        if provider_id.startswith("system_"):
            return ("system", provider_id[7:])
        elif provider_id.startswith("custom_"):
            return ("custom", provider_id[7:])
        # 兼容旧格式
        return ("system", provider_id)
    
    def _apply_settings(self):
        """从设置管理器应用配置"""
        if not self.settings_manager:
            return
        
        # 更新 Ollama 配置
        ollama_settings = self.settings_manager.get_ollama_settings()
        ollama_provider_id = self._build_provider_id("system", "Ollama")
        ollama_provider = self.get_provider(ollama_provider_id)
        if ollama_provider:
            ollama_provider.update_config(ollama_settings)

        openai_settings = self.settings_manager.get_openai_settings()
        openai_provider_id = self._build_provider_id("system", "OpenAI")
        openai_provider = self.get_provider(openai_provider_id)
        if openai_provider:
            openai_provider.update_config(openai_settings)
        
        # 若已是注册 ID（仅系统 provider 在自定义加载前有效），先对齐
        raw_current = self.settings_manager.get_current_translation_provider()
        normalized = self._normalize_provider_id(raw_current)
        if normalized and normalized in self.providers:
            self.current_provider_id = normalized
        
        # 加载自定义模型（内部会按 settings 首选恢复当前 provider）
        custom_models = self.settings_manager.get_custom_models()
        self.load_custom_providers(custom_models)
    
    def _register_system_providers(self):
        ollama_provider = OllamaTranslationProvider()
        ollama_id = self._build_provider_id("system", "Ollama")
        self.register_provider(ollama_id, ollama_provider)

        openai_provider = OpenAITranslationProvider()
        openai_id = self._build_provider_id("system", "OpenAI")
        self.register_provider(openai_id, openai_provider)

        self.current_provider_id = ollama_id
    
    def register_provider(self, provider_id: str, provider: BaseTranslationProvider) -> bool:
        if provider_id in self.providers:
            logger.warning(f"Provider {provider_id} already exists")
            return False
        self.providers[provider_id] = provider
        logger.info(f"Registered provider: {provider_id}")
        return True
    
    def unregister_provider(self, provider_id: str) -> bool:
        if provider_id not in self.providers:
            logger.warning(f"Provider {provider_id} not found")
            return False
        del self.providers[provider_id]
        if self.current_provider_id == provider_id:
            self.current_provider_id = None
        logger.info(f"Unregistered provider: {provider_id}")
        return True
    
    def get_provider(self, provider_id: Optional[str] = None) -> Optional[BaseTranslationProvider]:
        pid = provider_id or self.current_provider_id
        if pid:
            pid = self._normalize_provider_id(pid)
        return self.providers.get(pid)
    
    def set_current_provider(self, provider_id: str) -> bool:
        pid = self._normalize_provider_id(provider_id) or provider_id
        if pid not in self.providers:
            logger.warning(f"Provider {provider_id} not found")
            return False
        self.current_provider_id = pid
        logger.info(f"Set current provider to: {provider_id}")
        return True
    
    def get_current_provider(self) -> Optional[BaseTranslationProvider]:
        return self.get_provider()

    def get_translation_timeout_seconds(self) -> int:
        """当前选用模型的超时（秒），供 UI 线程 wait_for 使用；与 Provider 内 HTTP/SDK 超时对齐。"""
        provider = self.get_current_provider()
        if not provider:
            return 120
        raw = provider.config.get("timeout")
        if raw is None:
            return 120
        try:
            return max(15, min(600, int(raw)))
        except (TypeError, ValueError):
            return 120
    
    def list_providers(self) -> List[str]:
        return list(self.providers.keys())
    
    def list_providers_by_type(self, provider_type: ProviderType) -> List[str]:
        return [
            pid for pid, provider in self.providers.items()
            if provider.provider_type == provider_type
        ]
    
    def load_custom_providers(self, custom_models: List[Dict[str, Any]]):
        """用热重载替换所有自定义 Provider，避免配置更新后仍沿用旧实例。"""
        saved_current = self.current_provider_id
        for pid in list(self.providers.keys()):
            if pid.startswith("custom_"):
                self.unregister_provider(pid)

        for model in custom_models:
            name = model.get("name")
            if not name or not model.get("enabled", True):
                continue
            provider_id = self._build_provider_id("custom", name)
            provider = build_custom_provider(name, model)
            self.register_provider(provider_id, provider)

        preferred = None
        if self.settings_manager:
            preferred = self._normalize_provider_id(
                self.settings_manager.get_current_translation_provider()
            )
        saved_norm = self._normalize_provider_id(saved_current)

        # 必须优先采用设置里的「默认翻译源」：saved_current 在启动时常仍为 system_Ollama
        if preferred and preferred in self.providers:
            self.current_provider_id = preferred
            logger.info(f"当前翻译 provider（来自设置）: {preferred}")
        elif saved_norm and saved_norm in self.providers:
            self.current_provider_id = saved_norm
        else:
            fallback = self._build_provider_id("system", "Ollama")
            if fallback in self.providers:
                self.current_provider_id = fallback
                if preferred:
                    logger.warning(
                        "设置的翻译 provider %s 未注册（名称是否与自定义模型一致、是否已勾选启用？），已回退到 %s",
                        preferred,
                        fallback,
                    )
    
    def get_all_providers_info(self) -> Dict[str, Dict[str, Any]]:
        return {
            pid: provider.get_info()
            for pid, provider in self.providers.items()
        }
    
    async def translate(
        self,
        text: str,
        prompt_template: str = "",
        provider_name: Optional[str] = None,
        **kwargs
    ) -> str:
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"No provider available (requested: {provider_name})")
        
        # 优先使用传入的提示词，如果没有则从设置管理器中读取
        if not prompt_template:
            if self.settings_manager:
                prompt_template = self.settings_manager.get_prompt_template("translation")
                if not prompt_template:
                    prompt_template = "请翻译{input}"
            else:
                prompt_template = "请翻译{input}"
        
        return await provider.translate(text, prompt_template, **kwargs)
    
    def process_with_parse_mode(self, input_data: Any, prompt_template: str = "") -> Any:
        logger.info("[TranslationService] 解析模式被调用（用于单元格翻译）")
        
        # 优先使用传入的提示词，如果没有则从设置管理器中读取
        if not prompt_template:
            if self.settings_manager:
                prompt_template = self.settings_manager.get_prompt_template("analysis")
                if not prompt_template:
                    prompt_template = "请解析{input}"
            else:
                prompt_template = "请解析{input}"
        
        return self.parse_mode.process(input_data, prompt_template)
    
    def get_translation_mode(self):
        logger.info("[TranslationService] 翻译模式被调用 - 预留接口，暂不实现")
        return self.translation_mode
    
    def get_scene_mode(self):
        logger.info("[TranslationService] 造景模式被调用 - 预留接口，暂不实现")
        return self.scene_mode
    
    async def generate_scene_text(
        self,
        words: List[str],
        prompt_template: str = None,
        provider_name: Optional[str] = None,
        **kwargs
    ) -> str:
        provider = self.get_provider(provider_name)
        if not provider:
            raise ValueError(f"No provider available (requested: {provider_name})")
        
        # 优先使用传入的提示词，如果没有则从设置管理器中读取
        if not prompt_template:
            if self.settings_manager:
                prompt_template = self.settings_manager.get_prompt_template("scenery")
                if not prompt_template:
                    prompt_template = "请完成一篇包含{input}的文章"
            else:
                prompt_template = "请完成一篇包含{input}的文章"
        
        words_text = ", ".join(words)
        prompt = prompt_template.format(input=words_text)
        
        logger.info(f"[TranslationService] 生成造景文章，单词列表: {words}")
        logger.info(f"[TranslationService] 造景提示词: {prompt}")
        
        # 打印提示词到控制台
        print("="*50)
        print("请求的完整提示词:")
        print(prompt)
        print("="*50)
        
        try:
            result = await provider.translate(words_text, prompt_template, **kwargs)
            logger.info(f"[TranslationService] 造景文章生成完成")
            
            # 只打印返回结果的第一句话
            print("\n模型返回的结果:")
            print("="*50)
            # 提取第一句话
            first_sentence = ""
            cleaned_result = result.strip()
            # 查找句子结束符
            end_positions = [
                cleaned_result.find('.'),
                cleaned_result.find('!'),
                cleaned_result.find('?'),
                cleaned_result.find('\n')
            ]
            # 过滤掉 -1 的位置
            valid_positions = [pos for pos in end_positions if pos != -1]
            if valid_positions:
                first_sentence = cleaned_result[:min(valid_positions) + 1].strip()
            else:
                # 如果没有找到句子结束符，取前 200 个字符
                first_sentence = cleaned_result[:200]
                if len(cleaned_result) > 200:
                    first_sentence += "..."
            print(first_sentence)
            print("="*50)
            
            return result
        except Exception as e:
            logger.error(f"[TranslationService] 造景文章生成失败: {e}")
            raise
