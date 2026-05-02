from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QFormLayout, QComboBox, QGroupBox, QScrollArea,
    QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal as Signal
from PyQt5.QtGui import QFont
from .env_widgets import EnvVarsEditorWidget
from ..settings_workers import OllamaAsyncWorker, OpenAITestWorker
from translation.providers.api_key_resolve import openai_api_key_configured


class TranslationConfigWidget(QWidget):
    test_connection = Signal(dict)
    refresh_models = Signal(dict)
    
    def __init__(self, service_name, parent=None, settings_manager=None):
        super().__init__(parent)
        self.service_name = service_name
        self.settings_manager = settings_manager
        self.theme_manager = None
        self.is_ollama = "ollama" in service_name.lower() or service_name == "Ollama"
        self.api_key_env_combo = None
        self.init_ui()
    
    def set_theme_manager(self, theme_manager):
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
            self.apply_theme(self.theme_manager.get_current_theme_name())
    
    def apply_theme(self, theme_name=None):
        if not self.theme_manager:
            return
        theme = self.theme_manager.get_theme()
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                color: {theme['foreground']};
            }}
            QLineEdit {{
                background-color: {theme['input_background']};
                color: {theme['foreground']};
                border: 1px solid {theme['input_border']};
                padding: 5px;
                border-radius: 3px;
            }}
            QComboBox {{
                background-color: {theme['input_background']};
                color: {theme['foreground']};
                border: 1px solid {theme['input_border']};
                padding: 5px;
                border-radius: 3px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['input_background']};
                color: {theme['foreground']};
                selection-background-color: {theme['list_item_selected']};
                selection-color: white;
                border: 1px solid {theme['input_border']};
            }}
            QPushButton {{
                background-color: {theme['button_background']};
                color: {theme['foreground']};
                border: 1px solid {theme['input_border']};
                padding: 6px 15px;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover']};
            }}
            QPushButton#refreshBtn {{
                background-color: {theme['secondary_button'] if 'secondary_button' in theme else theme['button_background']};
                color: {theme['foreground']};
            }}
            QPushButton#refreshBtn:hover {{
                background-color: {theme['secondary_button_hover'] if 'secondary_button_hover' in theme else theme['button_hover']};
            }}
            QSpinBox {{
                background-color: {theme['input_background']};
                color: {theme['foreground']};
                border: 1px solid {theme['input_border']};
                padding: 3px;
                border-radius: 3px;
            }}
            QCheckBox {{
                color: {theme['foreground']};
            }}
            QLabel {{
                color: {theme['foreground']};
            }}
        """)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        self.title_label = QLabel(self.service_name)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        self.enabled_checkbox = QCheckBox("启用此服务")
        form_layout.addRow("", self.enabled_checkbox)

        if not self.is_ollama:
            key_row = QWidget()
            key_layout = QVBoxLayout(key_row)
            key_layout.setContentsMargins(0, 0, 0, 0)
            self.api_key_env_combo = QComboBox()
            self.api_key_env_combo.setEditable(True)
            self.api_key_env_combo.setToolTip("从上方登记的变量名中选择，或直接输入系统环境变量名")
            key_layout.addWidget(self.api_key_env_combo)
            key_hint = QLabel("密钥从环境变量读取，设置文件中仅保存变量名。")
            key_hint.setWordWrap(True)
            key_layout.addWidget(key_hint)
            form_layout.addRow("API 密钥环境变量:", key_row)
            self._refresh_api_key_env_combo()
        
        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText("https://api.example.com")
        form_layout.addRow("接口地址:", self.endpoint_input)
        
        # Ollama 使用下拉选择模型，其他服务使用输入框
        if self.is_ollama:
            model_row = QWidget()
            model_layout = QHBoxLayout(model_row)
            model_layout.setContentsMargins(0, 0, 0, 0)
            
            self.model_combo = QComboBox()
            self.model_combo.setEditable(True)
            self.model_combo.setPlaceholderText("选择或输入模型")
            model_layout.addWidget(self.model_combo, 1)
            
            self.refresh_btn = QPushButton("刷新模型")
            self.refresh_btn.setObjectName("refreshBtn")
            self.refresh_btn.clicked.connect(self._on_refresh_models)
            model_layout.addWidget(self.refresh_btn)
            
            form_layout.addRow("模型:", model_row)
        else:
            self.model_input = QLineEdit()
            self.model_input.setPlaceholderText("模型名称 (可选)")
            form_layout.addRow("模型:", self.model_input)
        
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(1, 300)
        self.timeout_spinbox.setValue(30)
        self.timeout_spinbox.setSuffix(" 秒")
        form_layout.addRow("超时时间:", self.timeout_spinbox)
        
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("http://127.0.0.1:7890 (可选)")
        form_layout.addRow("代理地址:", self.proxy_input)
        
        layout.addLayout(form_layout)
        
        test_btn_layout = QHBoxLayout()
        test_btn_layout.addStretch()
        self.test_button = QPushButton("测试连接")
        self.test_button.setMinimumWidth(120)
        self.test_button.clicked.connect(self._on_test_clicked)
        test_btn_layout.addWidget(self.test_button)
        layout.addLayout(test_btn_layout)
        
        layout.addStretch()

    def _refresh_api_key_env_combo(self):
        if self.api_key_env_combo is None:
            return
        keep = self.api_key_env_combo.currentText().strip()
        self.api_key_env_combo.blockSignals(True)
        self.api_key_env_combo.clear()
        entries = []
        if self.settings_manager:
            entries = self.settings_manager.get_env_vars()
        seen = set()
        for e in entries:
            name = (e.get("name") or "").strip()
            if name and name not in seen:
                seen.add(name)
                self.api_key_env_combo.addItem(name)
        self.api_key_env_combo.setEditText(keep)
        self.api_key_env_combo.blockSignals(False)
    
    def _on_test_clicked(self):
        config = self.get_config()
        self.test_connection.emit(config)
    
    def _on_refresh_models(self):
        """刷新 Ollama 模型列表"""
        config = self.get_config()
        self.refresh_models.emit(config)
    
    def refresh_model_list(self, models):
        """刷新下拉框中的模型列表"""
        if hasattr(self, 'model_combo'):
            current_text = self.model_combo.currentText()
            self.model_combo.clear()
            for model in models:
                self.model_combo.addItem(model)
            if current_text:
                index = self.model_combo.findText(current_text)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)
                else:
                    if self.model_combo.count() > 0:
                        self.model_combo.setCurrentIndex(0)
    
    def get_config(self):
        model_value = ''
        if hasattr(self, 'model_combo'):
            model_value = self.model_combo.currentText().strip()
        elif hasattr(self, 'model_input'):
            model_value = self.model_input.text().strip()
        api_key_env = ""
        if self.api_key_env_combo is not None:
            api_key_env = self.api_key_env_combo.currentText().strip()
        return {
            'name': self.service_name,
            'enabled': self.enabled_checkbox.isChecked(),
            'api_key_env': api_key_env,
            'endpoint': self.endpoint_input.text().strip(),
            'model': model_value,
            'timeout': self.timeout_spinbox.value(),
            'proxy': self.proxy_input.text().strip()
        }
    
    def set_config(self, config):
        self.enabled_checkbox.setChecked(config.get('enabled', False))
        if self.api_key_env_combo is not None:
            self._refresh_api_key_env_combo()
            env_name = (config.get("api_key_env") or "").strip()
            if not env_name and (config.get("api_key") or "").strip():
                env_name = "OPENAI_API_KEY"
            self.api_key_env_combo.setEditText(env_name)
        self.endpoint_input.setText(config.get('endpoint', ''))
        if hasattr(self, 'model_combo'):
            self.model_combo.clear()
            if config.get('model', ''):
                self.model_combo.addItem(config.get('model', ''))
                self.model_combo.setCurrentText(config.get('model', ''))
        elif hasattr(self, 'model_input'):
            self.model_input.setText(config.get('model', ''))
        self.timeout_spinbox.setValue(config.get('timeout', 30))
        self.proxy_input.setText(config.get('proxy', ''))


class TranslationSettingsPanel(QWidget):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.service_widgets = {}
        self.theme_manager = None
        self.init_ui()
        self.load_settings()
        
        # 连接模型管理器的变化信号
        if hasattr(self, 'model_manager_widget'):
            self.model_manager_widget.models_changed.connect(self._on_models_changed)
    
    def set_theme_manager(self, theme_manager):
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
            self.apply_theme(self.theme_manager.get_current_theme_name())
            for widget in self.service_widgets.values():
                widget.set_theme_manager(self.theme_manager)
            if hasattr(self, 'model_manager_widget'):
                self.model_manager_widget.set_theme_manager(self.theme_manager)
            if hasattr(self, 'env_vars_editor'):
                self.env_vars_editor.set_theme_manager(self.theme_manager)
    
    def apply_theme(self, theme_name=None):
        if not self.theme_manager:
            return
        theme = self.theme_manager.get_theme()
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['dialog_background']};
                color: {theme['foreground']};
            }}
            QScrollArea {{
                border: none;
                background-color: {theme['dialog_background']};
            }}
            QGroupBox {{
                background-color: {theme['group_box']};
                border: 1px solid {theme['input_border']};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme['foreground']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QComboBox {{
                background-color: {theme['input_background']};
                color: {theme['foreground']};
                border: 1px solid {theme['input_border']};
                padding: 5px;
                border-radius: 3px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['input_background']};
                color: {theme['foreground']};
                selection-background-color: {theme['list_item_selected']};
                selection-color: white;
                border: 1px solid {theme['input_border']};
            }}
            QLabel {{
                color: {theme['foreground']};
            }}
        """)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)
        
        self.header_label = QLabel("翻译服务设置")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        self.header_label.setFont(header_font)
        container_layout.addWidget(self.header_label)
        
        # 默认翻译服务选择
        default_group = QGroupBox("默认翻译源")
        default_layout = QVBoxLayout(default_group)
        
        self.default_service_combo = QComboBox()
        default_layout.addWidget(QLabel("选择翻译服务："))
        default_layout.addWidget(self.default_service_combo)
        
        container_layout.addWidget(default_group)
        
        # 系统翻译服务配置组
        system_services_group = QGroupBox("系统翻译服务配置")
        system_services_layout = QVBoxLayout(system_services_group)
        
        # 定义系统服务（展示名, service_widgets 键）
        self.system_services = [
            ("Ollama", "ollama"),
            ("OpenAI", "openai"),
        ]
        
        for display_name, service_id in self.system_services:
            group = QGroupBox(display_name)
            group_layout = QVBoxLayout(group)
            
            widget = TranslationConfigWidget(display_name, settings_manager=self.settings_manager)
            widget.test_connection.connect(self._on_test_system_service)
            widget.refresh_models.connect(self._on_refresh_ollama_models)
            group_layout.addWidget(widget)
            
            self.service_widgets[service_id] = widget
            system_services_layout.addWidget(group)
        
        container_layout.addWidget(system_services_group)

        env_group = QGroupBox("API 密钥环境变量名（仅存变量名）")
        env_group_layout = QVBoxLayout(env_group)
        self.env_vars_editor = EnvVarsEditorWidget()
        env_group_layout.addWidget(self.env_vars_editor)
        container_layout.addWidget(env_group)
        
        # 自定义模型管理组
        model_group = QGroupBox("自定义模型管理")
        model_group_layout = QVBoxLayout(model_group)
        from .model_widgets import ModelManagerWidget
        self.model_manager_widget = ModelManagerWidget(self.settings_manager)
        model_group_layout.addWidget(self.model_manager_widget)
        container_layout.addWidget(model_group)
        
        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # 更新默认服务下拉框
        self._update_default_service_combo()
    
    def _update_default_service_combo(self):
        """更新默认翻译服务下拉框，支持分组显示"""
        self.default_service_combo.clear()
        
        # 添加系统服务
        self.default_service_combo.addItem("--- 系统内置服务 ---", None)
        for display_name, service_id in self.system_services:
            provider_id = self.settings_manager.build_provider_id("system", display_name)
            self.default_service_combo.addItem(display_name, provider_id)
        
        # 添加自定义模型
        self.default_service_combo.addItem("--- 自定义模型 ---", None)
        custom_models = self.settings_manager.get_custom_models()
        for model in custom_models:
            if not model.get("enabled", True):
                continue
            model_name = model.get("name", "未命名")
            provider_id = self.settings_manager.build_provider_id("custom", model_name)
            self.default_service_combo.addItem(model_name, provider_id)
    
    def _on_refresh_ollama_models(self, config):
        """异步刷新 Ollama 模型列表"""
        base_url = config.get("endpoint", "http://localhost:11434")
        if not base_url:
            base_url = "http://localhost:11434"
        
        # 禁用刷新按钮防止重复点击
        if "ollama" in self.service_widgets:
            self.service_widgets["ollama"].refresh_btn.setEnabled(False)
            self.service_widgets["ollama"].refresh_btn.setText("刷新中...")
        
        # 创建并启动 worker
        self.refresh_worker = OllamaAsyncWorker(base_url, operation="list_models")
        self.refresh_worker.models_fetched.connect(self._on_models_fetched)
        self.refresh_worker.models_fetch_failed.connect(self._on_models_fetch_failed)
        self.refresh_worker.finished.connect(self._on_refresh_finished)
        self.refresh_worker.start()
    
    def _on_models_fetched(self, models):
        """成功获取模型列表"""
        if models:
            if "ollama" in self.service_widgets:
                self.service_widgets["ollama"].refresh_model_list(models)
            QMessageBox.information(self, "刷新成功", f"成功获取 {len(models)} 个模型！")
        else:
            QMessageBox.warning(self, "提示", "未获取到任何模型。请检查 Ollama 是否下载了模型。")
    
    def _on_models_fetch_failed(self, error_msg):
        """获取模型列表失败"""
        QMessageBox.warning(self, "刷新失败", f"无法获取模型列表！错误信息: {error_msg}")
    
    def _on_refresh_finished(self):
        """刷新完成，恢复按钮状态"""
        if "ollama" in self.service_widgets:
            self.service_widgets["ollama"].refresh_btn.setEnabled(True)
            self.service_widgets["ollama"].refresh_btn.setText("刷新模型")
    
    def _on_test_system_service(self, config):
        """测试系统服务连接"""
        service_name = config.get("name", "")
        
        if service_name == "Ollama":
            # 异步测试 Ollama 连接
            base_url = config.get("endpoint", "http://localhost:11434")
            if not base_url:
                base_url = "http://localhost:11434"
            
            # 禁用测试按钮防止重复点击
            if "ollama" in self.service_widgets:
                self.service_widgets["ollama"].test_button.setEnabled(False)
                self.service_widgets["ollama"].test_button.setText("测试中...")
            
            # 创建并启动 worker
            self.test_worker = OllamaAsyncWorker(base_url, operation="test")
            self.test_worker.test_success.connect(self._on_test_success)
            self.test_worker.test_failed.connect(self._on_test_failed)
            self.test_worker.finished.connect(self._on_test_finished)
            self.test_worker.start()
        elif service_name == "OpenAI":
            env_name = (config.get("api_key_env") or "").strip()
            if not env_name:
                QMessageBox.warning(self, "错误", "请填写 API 密钥对应的环境变量名。")
                return
            if not openai_api_key_configured(config):
                QMessageBox.warning(
                    self,
                    "错误",
                    f"未能从环境中读取密钥，请确认已设置「{env_name}」且本进程可继承该变量。",
                )
                return
            if "openai" in self.service_widgets:
                self.service_widgets["openai"].test_button.setEnabled(False)
                self.service_widgets["openai"].test_button.setText("测试中...")
            self.openai_test_worker = OpenAITestWorker(config)
            self.openai_test_worker.test_success.connect(self._on_openai_test_success)
            self.openai_test_worker.test_failed.connect(self._on_openai_test_failed)
            self.openai_test_worker.finished.connect(self._on_openai_test_finished)
            self.openai_test_worker.start()
        else:
            QMessageBox.information(
                self,
                "测试连接",
                f"服务「{config.get('name', '')}」暂无内置连通性测试。",
            )
    
    def _on_test_success(self, models_count):
        """测试连接成功"""
        QMessageBox.information(self, "测试成功", f"Ollama 连接成功！发现 {models_count} 个模型。")
    
    def _on_test_failed(self, error_msg):
        """测试连接失败"""
        QMessageBox.warning(self, "测试失败", f"Ollama 连接失败！错误信息: {error_msg}")
    
    def _on_test_finished(self):
        """测试完成，恢复按钮状态"""
        if "ollama" in self.service_widgets:
            self.service_widgets["ollama"].test_button.setEnabled(True)
            self.service_widgets["ollama"].test_button.setText("测试连接")

    def _on_openai_test_success(self):
        QMessageBox.information(self, "测试成功", "OpenAI Chat 调用成功。")

    def _on_openai_test_failed(self, error_msg):
        QMessageBox.warning(self, "测试失败", f"连接失败：{error_msg}")

    def _on_openai_test_finished(self):
        if "openai" in self.service_widgets:
            self.service_widgets["openai"].test_button.setEnabled(True)
            self.service_widgets["openai"].test_button.setText("测试连接")
    
    def _on_models_changed(self):
        """当模型发生变化时，更新默认服务下拉框"""
        # 保存当前选中的值
        current_provider = self.default_service_combo.currentData()
        # 更新下拉框
        self._update_default_service_combo()
        # 恢复之前选中的值
        if current_provider:
            index = self.default_service_combo.findData(current_provider)
            if index >= 0:
                self.default_service_combo.setCurrentIndex(index)
    
    def load_settings(self):
        translation_settings = self.settings_manager.get('translation', {})
        current_provider = self.settings_manager.get_current_translation_provider()
        
        # 更新下拉框
        self._update_default_service_combo()
        
        # 设置当前选中的 provider
        index = self.default_service_combo.findData(current_provider)
        if index >= 0:
            self.default_service_combo.setCurrentIndex(index)
        else:
            # 如果找不到，尝试设置默认值
            default_provider = self.settings_manager.build_provider_id("system", "Ollama")
            index = self.default_service_combo.findData(default_provider)
            if index >= 0:
                self.default_service_combo.setCurrentIndex(index)
        
        self.env_vars_editor.set_entries(self.settings_manager.get_env_vars())

        # 加载系统服务配置
        # Ollama 配置
        ollama_config = self.settings_manager.get_ollama_settings()
        if "ollama" in self.service_widgets:
            widget_config = {
                "enabled": True,
                "endpoint": ollama_config.get("base_url", "http://localhost:11434"),
                "model": ollama_config.get("model", "qwen2.5:0.5b"),
                "timeout": ollama_config.get("timeout", 30),
                "proxy": ""
            }
            self.service_widgets["ollama"].set_config(widget_config)

        if "openai" in self.service_widgets:
            oa = self.settings_manager.get_openai_settings()
            self.service_widgets["openai"].set_config({
                "enabled": True,
                "api_key_env": oa.get("api_key_env", ""),
                "endpoint": oa.get("base_url", "https://api.openai.com/v1"),
                "model": oa.get("model", "gpt-3.5-turbo"),
                "timeout": oa.get("timeout", 60),
                "proxy": oa.get("proxy", ""),
            })
    
    def save_settings(self):
        translation_settings = self.settings_manager.get('translation', {})
        
        # 保存当前选择的 provider
        current_provider = self.default_service_combo.currentData()
        if current_provider:
            self.settings_manager.set_current_translation_provider(current_provider)
        
        # 保存 Ollama 配置
        if "ollama" in self.service_widgets:
            ollama_widget_config = self.service_widgets["ollama"].get_config()
            ollama_config = {
                "base_url": ollama_widget_config.get("endpoint", "http://localhost:11434"),
                "model": ollama_widget_config.get("model", "qwen2.5:0.5b"),
                "timeout": ollama_widget_config.get("timeout", 30)
            }
            self.settings_manager.set_ollama_settings(ollama_config)

        if "openai" in self.service_widgets:
            ow = self.service_widgets["openai"].get_config()
            self.settings_manager.set_openai_settings({
                "base_url": ow.get("endpoint", "").strip() or "https://api.openai.com/v1",
                "model": ow.get("model", "").strip(),
                "timeout": ow.get("timeout", 60),
                "api_key_env": ow.get("api_key_env", "").strip(),
                "proxy": ow.get("proxy", "").strip(),
            })

        self.settings_manager.set_env_vars(self.env_vars_editor.get_entries())
        
        # 保存自定义模型
        self.settings_manager.set_custom_models(self.model_manager_widget.get_models())


__all__ = ['TranslationConfigWidget', 'TranslationSettingsPanel']
