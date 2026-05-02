import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal


class SettingsManager(QObject):
    reading_font_size_changed = pyqtSignal(int)
    def __init__(self, app_name: str = "QSDReader"):
        super().__init__()
        self.app_name = app_name
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "settings.json"
        self._settings: Dict[str, Any] = {}
        self._load_settings()

    def _get_config_dir(self) -> Path:
        config_dir = Path(__file__).parent.parent.parent
        return config_dir

    def _load_settings(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
                    self._merge_default_settings()
            except (json.JSONDecodeError, IOError):
                self._settings = self._get_default_settings()
        else:
            self._settings = self._get_default_settings()
            self._save_settings()
        self._sanitize_persistent_settings()

    def _merge_default_settings(self):
        default_settings = self._get_default_settings()
        self._settings = self._deep_merge(default_settings, self._settings)

    def _deep_merge(self, default: Dict, current: Dict) -> Dict:
        result = default.copy()
        for key, value in current.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _sanitize_persistent_settings(self) -> None:
        """写入磁盘前不应保留明文密钥：迁移 translation.openai.api_key。"""
        t = self._settings.get("translation")
        if not isinstance(t, dict):
            return
        oa = t.get("openai")
        if not isinstance(oa, dict):
            return
        if (oa.get("api_key") or "").strip() and not (oa.get("api_key_env") or "").strip():
            oa["api_key_env"] = "OPENAI_API_KEY"
        oa.pop("api_key", None)

    def _get_default_settings(self) -> Dict[str, Any]:
        return {
            "translation": {
                "enabled": False,
                "current_provider": "system_Ollama",
                "ollama": {
                    "base_url": "http://localhost:11434",
                    "model": "qwen2.5:0.5b"
                },
                "openai": {
                    "api_key_env": "",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-3.5-turbo",
                    "timeout": 60,
                    "proxy": ""
                }
            },
            "theme": "light",
            "window": {
                "width": 1200,
                "height": 800
            },
            "prompt_templates": {
                "translation": "请翻译{input}",
                "analysis": "请解析{input}",
                "scenery": "请完成一篇包含{input}的文章"
            },
            "custom_models": [],
            "workspace": {
                "current_path": "",
                "recent_files": [],
                "cell_states": {}
            },
            "reading": {
                "font_size": 12
            },
            "env_vars": [
                {"name": "ARK_API_KEY", "description": "火山方舟 API 密钥"},
                {"name": "OPENAI_API_KEY", "description": "OpenAI API 密钥"},
            ],
        }

    def _save_settings(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Failed to save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._settings
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any, auto_save: bool = True):
        keys = key.split('.')
        settings = self._settings
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        settings[keys[-1]] = value
        if auto_save:
            self._save_settings()

    def save(self):
        self._save_settings()

    def get_translation_settings(self) -> Dict[str, Any]:
        return self._settings.get("translation", {})

    def set_translation_settings(self, settings: Dict[str, Any], auto_save: bool = True):
        self._settings["translation"] = settings
        if auto_save:
            self._save_settings()

    def get_all_settings(self) -> Dict[str, Any]:
        return self._settings.copy()

    def reset_to_default(self):
        self._settings = self._get_default_settings()
        self._save_settings()

    def get_prompt_templates(self) -> Dict[str, str]:
        return self._settings.get("prompt_templates", {})

    def set_prompt_templates(self, templates: Dict[str, str], auto_save: bool = True):
        self._settings["prompt_templates"] = templates
        if auto_save:
            self._save_settings()

    def get_prompt_template(self, template_type: str) -> str:
        return self._settings.get("prompt_templates", {}).get(template_type, "")

    def set_prompt_template(self, template_type: str, template: str, auto_save: bool = True):
        if "prompt_templates" not in self._settings:
            self._settings["prompt_templates"] = {}
        self._settings["prompt_templates"][template_type] = template
        if auto_save:
            self._save_settings()

    def get_custom_models(self) -> list:
        return self._settings.get("custom_models", [])

    def set_custom_models(self, models: list, auto_save: bool = True):
        cleaned = []
        for m in models:
            d = dict(m)
            backend = (d.get("backend") or "").lower()
            if backend == "ark":
                has_legacy = bool((d.get("api_key") or "").strip())
                if has_legacy and not (d.get("api_key_env") or "").strip():
                    d["api_key_env"] = "ARK_API_KEY"
            d.pop("api_key", None)
            cleaned.append(d)
        self._settings["custom_models"] = cleaned
        if auto_save:
            self._save_settings()

    def get_env_vars(self) -> list:
        return list(self._settings.get("env_vars", []))

    def set_env_vars(self, entries: list, auto_save: bool = True):
        self._settings["env_vars"] = list(entries or [])
        if auto_save:
            self._save_settings()

    def add_custom_model(self, model: Dict[str, Any], auto_save: bool = True):
        if "custom_models" not in self._settings:
            self._settings["custom_models"] = []
        clean = dict(model)
        backend = (clean.get("backend") or "").lower()
        if backend == "ark":
            if (clean.get("api_key") or "").strip() and not (clean.get("api_key_env") or "").strip():
                clean["api_key_env"] = "ARK_API_KEY"
        clean.pop("api_key", None)
        self._settings["custom_models"].append(clean)
        if auto_save:
            self._save_settings()

    def get_workspace(self) -> Dict[str, Any]:
        return self._settings.get("workspace", {})

    def set_workspace(self, workspace: Dict[str, Any], auto_save: bool = True):
        self._settings["workspace"] = workspace
        if auto_save:
            self._save_settings()

    def get_workspace_path(self) -> str:
        return self._settings.get("workspace", {}).get("current_path", "")

    def set_workspace_path(self, path: str, auto_save: bool = True):
        if "workspace" not in self._settings:
            self._settings["workspace"] = {}
        self._settings["workspace"]["current_path"] = path
        if auto_save:
            self._save_settings()

    def get_recent_files(self) -> list:
        return self._settings.get("workspace", {}).get("recent_files", [])

    def set_recent_files(self, files: list, auto_save: bool = True):
        if "workspace" not in self._settings:
            self._settings["workspace"] = {}
        self._settings["workspace"]["recent_files"] = files
        if auto_save:
            self._save_settings()

    def get_cell_states(self) -> Dict[str, Any]:
        return self._settings.get("workspace", {}).get("cell_states", {})

    def set_cell_states(self, states: Dict[str, Any], auto_save: bool = True):
        if "workspace" not in self._settings:
            self._settings["workspace"] = {}
        self._settings["workspace"]["cell_states"] = states
        if auto_save:
            self._save_settings()

    def get_current_file(self) -> str:
        return self._settings.get("workspace", {}).get("current_file", "")

    def set_current_file(self, file_path: str, auto_save: bool = True):
        if "workspace" not in self._settings:
            self._settings["workspace"] = {}
        self._settings["workspace"]["current_file"] = file_path
        if auto_save:
            self._save_settings()

    def get_file_browser_path(self) -> str:
        return self._settings.get("workspace", {}).get("file_browser_path", "")

    def set_file_browser_path(self, path: str, auto_save: bool = True):
        if "workspace" not in self._settings:
            self._settings["workspace"] = {}
        self._settings["workspace"]["file_browser_path"] = path
        if auto_save:
            self._save_settings()
    
    def get_current_translation_provider(self) -> str:
        return self._settings.get("translation", {}).get("current_provider", "system_Ollama")
    
    def set_current_translation_provider(self, provider_id: str, auto_save: bool = True):
        if "translation" not in self._settings:
            self._settings["translation"] = {}
        self._settings["translation"]["current_provider"] = provider_id
        if auto_save:
            self._save_settings()
    
    def parse_provider_id(self, provider_id: str) -> tuple:
        """解析 provider_id，返回 (type, name) 元组"""
        if provider_id.startswith("system_"):
            return ("system", provider_id[7:])
        elif provider_id.startswith("custom_"):
            return ("custom", provider_id[7:])
        # 兼容旧格式
        return ("system", provider_id)
    
    def build_provider_id(self, provider_type: str, name: str) -> str:
        """构建 provider_id"""
        return f"{provider_type}_{name}"
    
    def get_ollama_settings(self) -> Dict[str, Any]:
        return self._settings.get("translation", {}).get("ollama", {
            "base_url": "http://localhost:11434",
            "model": "qwen2.5:0.5b"
        })
    
    def set_ollama_settings(self, settings: Dict[str, Any], auto_save: bool = True):
        if "translation" not in self._settings:
            self._settings["translation"] = {}
        self._settings["translation"]["ollama"] = settings
        if auto_save:
            self._save_settings()

    def get_openai_settings(self) -> Dict[str, Any]:
        return self._settings.get("translation", {}).get("openai", {
            "api_key_env": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-3.5-turbo",
            "timeout": 60,
            "proxy": "",
        })

    def set_openai_settings(self, settings: Dict[str, Any], auto_save: bool = True):
        if "translation" not in self._settings:
            self._settings["translation"] = {}
        d = dict(settings)
        if (d.get("api_key") or "").strip() and not (d.get("api_key_env") or "").strip():
            d["api_key_env"] = "OPENAI_API_KEY"
        d.pop("api_key", None)
        self._settings["translation"]["openai"] = d
        if auto_save:
            self._save_settings()
    
    def get_reading_font_size(self):
        return self._settings.get("reading", {}).get("font_size", 12)
    
    def set_reading_font_size(self, font_size, auto_save=True):
        if "reading" not in self._settings:
            self._settings["reading"] = {}
        self._settings["reading"]["font_size"] = max(8, min(24, font_size))
        if auto_save:
            self._save_settings()
        self.reading_font_size_changed.emit(self._settings["reading"]["font_size"])
