from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QSpinBox, QFormLayout, QFrame, QScrollArea,
    QMessageBox, QComboBox, QGroupBox, QSplitter, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal as Signal, QThread
from PyQt5.QtGui import QFont
from settingmanager.settings_manager import SettingsManager
import httpx
import re
try:
    from recitation.ui import RecitationSettingsPanel
except ImportError:
    RecitationSettingsPanel = None


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


class UrlValidator:
    @staticmethod
    def is_valid(url):
        if not url:
            return True
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S*)?$', re.IGNORECASE)
        return bool(url_pattern.match(url))


class TranslationConfigWidget(QWidget):
    test_connection = Signal(dict)
    refresh_models = Signal(dict)
    
    def __init__(self, service_name, parent=None):
        super().__init__(parent)
        self.service_name = service_name
        self.theme_manager = None
        self.is_ollama = "ollama" in service_name.lower() or service_name == "Ollama"
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
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("请输入 API Key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("API Key:", self.api_key_input)
        
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
        return {
            'name': self.service_name,
            'enabled': self.enabled_checkbox.isChecked(),
            'api_key': self.api_key_input.text().strip(),
            'endpoint': self.endpoint_input.text().strip(),
            'model': model_value,
            'timeout': self.timeout_spinbox.value(),
            'proxy': self.proxy_input.text().strip()
        }
    
    def set_config(self, config):
        self.enabled_checkbox.setChecked(config.get('enabled', False))
        self.api_key_input.setText(config.get('api_key', ''))
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
    
    def set_theme_manager(self, theme_manager):
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
            self.apply_theme(self.theme_manager.get_current_theme_name())
            for widget in self.service_widgets.values():
                widget.set_theme_manager(self.theme_manager)
            if hasattr(self, 'model_manager_widget'):
                self.model_manager_widget.set_theme_manager(self.theme_manager)
    
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
        
        # 定义系统服务
        self.system_services = [
            ("Ollama", "ollama"),
        ]
        
        for display_name, service_id in self.system_services:
            group = QGroupBox(display_name)
            group_layout = QVBoxLayout(group)
            
            widget = TranslationConfigWidget(display_name)
            widget.test_connection.connect(self._on_test_system_service)
            widget.refresh_models.connect(self._on_refresh_ollama_models)
            group_layout.addWidget(widget)
            
            self.service_widgets[service_id] = widget
            system_services_layout.addWidget(group)
        
        container_layout.addWidget(system_services_group)
        
        # 自定义模型管理组
        model_group = QGroupBox("自定义模型管理")
        model_group_layout = QVBoxLayout(model_group)
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
            provider_id = self.settings_manager.build_provider_id("system", service_id)
            self.default_service_combo.addItem(display_name, provider_id)
        
        # 添加自定义模型
        self.default_service_combo.addItem("--- 自定义模型 ---", None)
        custom_models = self.settings_manager.get_custom_models()
        for model in custom_models:
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
        else:
            QMessageBox.information(self, "测试连接", 
                f"正在测试 {config['name']} 的连接...\n\n"
                f"API Key: {'*' * len(config['api_key']) if config['api_key'] else '未设置'}\n"
                f"Endpoint: {config['endpoint'] or '未设置'}\n"
                f"Model: {config['model'] or '未设置'}")
    
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
            default_provider = self.settings_manager.build_provider_id("system", "ollama")
            index = self.default_service_combo.findData(default_provider)
            if index >= 0:
                self.default_service_combo.setCurrentIndex(index)
        
        # 加载系统服务配置
        # Ollama 配置
        ollama_config = self.settings_manager.get_ollama_settings()
        if "ollama" in self.service_widgets:
            widget_config = {
                "enabled": True,
                "api_key": "",
                "endpoint": ollama_config.get("base_url", "http://localhost:11434"),
                "model": ollama_config.get("model", "qwen2.5:0.5b"),
                "timeout": ollama_config.get("timeout", 30),
                "proxy": ""
            }
            self.service_widgets["ollama"].set_config(widget_config)
    
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
        
        # 保存自定义模型
        self.settings_manager.set_custom_models(self.model_manager_widget.get_models())


class ModelEditDialog(QDialog):
    def __init__(self, model_data=None, parent=None):
        super().__init__(parent)
        self.model_data = model_data or {}
        self.theme_manager = None
        self.init_ui()
        if model_data:
            self.load_model_data(model_data)
    
    def set_theme_manager(self, theme_manager):
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.apply_theme(self.theme_manager.get_current_theme_name())
    
    def apply_theme(self, theme_name=None):
        if not self.theme_manager:
            return
        theme = self.theme_manager.get_theme()
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme['dialog_background']};
            }}
            QWidget {{
                color: {theme['foreground']};
            }}
            QLineEdit {{
                background-color: {theme['input_background']};
                color: {theme['foreground']};
                border: 1px solid {theme['input_border']};
                padding: 5px;
                border-radius: 3px;
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
            QPushButton#saveBtn {{
                background-color: {theme['primary_button']};
                color: white;
            }}
            QPushButton#saveBtn:hover {{
                background-color: {theme['primary_button_hover']};
            }}
            QPushButton#testBtn {{
                background-color: {theme['secondary_button'] if 'secondary_button' in theme else theme['button_background']};
                color: {theme['foreground']};
            }}
            QPushButton#testBtn:hover {{
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
        self.setWindowTitle("编辑模型" if self.model_data else "添加模型")
        self.setMinimumSize(450, 450)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("模型配置")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("模型名称")
        form_layout.addRow("名称:", self.name_input)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("API Key")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("API Key:", self.api_key_input)
        
        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText("https://api.example.com 或 http://localhost:11434")
        form_layout.addRow("接口地址:", self.endpoint_input)
        
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
        
        self.enabled_checkbox = QCheckBox("启用此模型")
        self.enabled_checkbox.setChecked(True)
        form_layout.addRow("", self.enabled_checkbox)
        
        layout.addLayout(form_layout)
        
        # 添加测试按钮
        test_btn_layout = QHBoxLayout()
        test_btn_layout.addStretch()
        self.test_button = QPushButton("测试连接")
        self.test_button.setObjectName("testBtn")
        self.test_button.clicked.connect(self._on_test_clicked)
        test_btn_layout.addWidget(self.test_button)
        layout.addLayout(test_btn_layout)
        
        layout.addStretch()
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        button_layout.addSpacing(10)
        
        save_btn = QPushButton("保存")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _on_test_clicked(self):
        """异步测试连接"""
        config = self.get_model_data()
        base_url = config.get("endpoint", "")
        if not base_url:
            QMessageBox.warning(self, "错误", "请先填写接口地址！")
            return
        
        # 禁用测试按钮防止重复点击
        self.test_button.setEnabled(False)
        self.test_button.setText("测试中...")
        
        # 检测是否是 Ollama（检查 endpoint 或名称）
        service_name = config.get("name", "").lower()
        is_ollama = "ollama" in service_name or "localhost" in base_url or "127.0.0.1" in base_url
        
        if is_ollama:
            # 使用 Ollama 专门的测试
            self.custom_test_worker = OllamaAsyncWorker(base_url, operation="test")
            self.custom_test_worker.test_success.connect(self._on_custom_test_success)
            self.custom_test_worker.test_failed.connect(self._on_custom_test_failed)
            self.custom_test_worker.finished.connect(self._on_custom_test_finished)
            self.custom_test_worker.start()
        else:
            # 通用的异步测试
            self.generic_test_worker = GenericTestWorker(base_url)
            self.generic_test_worker.test_success.connect(self._on_generic_test_success)
            self.generic_test_worker.test_failed.connect(self._on_generic_test_failed)
            self.generic_test_worker.finished.connect(self._on_custom_test_finished)
            self.generic_test_worker.start()
    
    def _on_custom_test_success(self, models_count):
        """自定义模型测试成功（Ollama）"""
        QMessageBox.information(self, "测试成功", f"连接成功！发现 {models_count} 个模型。")
    
    def _on_custom_test_failed(self, error_msg):
        """自定义模型测试失败"""
        QMessageBox.warning(self, "测试失败", f"连接失败！错误信息: {error_msg}")
    
    def _on_generic_test_success(self, status_code):
        """通用测试成功"""
        QMessageBox.information(self, "测试成功", f"连接成功！服务器状态码: {status_code}")
    
    def _on_generic_test_failed(self, error_msg):
        """通用测试失败"""
        QMessageBox.warning(self, "测试失败", f"连接失败！错误信息: {error_msg}")
    
    def _on_custom_test_finished(self):
        """测试完成，恢复按钮状态"""
        self.test_button.setEnabled(True)
        self.test_button.setText("测试连接")
    
    def load_model_data(self, model_data):
        self.name_input.setText(model_data.get('name', ''))
        self.api_key_input.setText(model_data.get('api_key', ''))
        self.endpoint_input.setText(model_data.get('endpoint', ''))
        self.model_input.setText(model_data.get('model', ''))
        self.timeout_spinbox.setValue(model_data.get('timeout', 30))
        self.proxy_input.setText(model_data.get('proxy', ''))
        self.enabled_checkbox.setChecked(model_data.get('enabled', False))
    
    def get_model_data(self):
        return {
            'name': self.name_input.text().strip(),
            'api_key': self.api_key_input.text().strip(),
            'endpoint': self.endpoint_input.text().strip(),
            'model': self.model_input.text().strip(),
            'timeout': self.timeout_spinbox.value(),
            'proxy': self.proxy_input.text().strip(),
            'enabled': self.enabled_checkbox.isChecked()
        }


class ModelManagerWidget(QWidget):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.theme_manager = None
        self.custom_models = []
        self.init_ui()
        self.load_models()
    
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
            QListWidget {{
                background-color: {theme['input_background']};
                border: 1px solid {theme['input_border']};
                border-radius: 5px;
                color: {theme['foreground']};
            }}
            QListWidget::item {{
                padding: 8px;
            }}
            QListWidget::item:selected {{
                background-color: {theme['list_item_selected']};
                color: white;
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
            QCheckBox {{
                color: {theme['foreground']};
            }}
            QLabel {{
                color: {theme['foreground']};
            }}
        """)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        header_layout = QHBoxLayout()
        header_label = QLabel("自定义模型管理")
        header_font = QFont()
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        self.model_list = QListWidget()
        self.model_list.itemChanged.connect(self.on_model_item_changed)
        self.model_list.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.model_list)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self.add_model)
        button_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self.edit_model)
        self.edit_btn.setEnabled(False)
        button_layout.addWidget(self.edit_btn)
        
        self.test_btn = QPushButton("测试")
        self.test_btn.clicked.connect(self.test_model)
        self.test_btn.setEnabled(False)
        button_layout.addWidget(self.test_btn)
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self.delete_model)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
    
    def load_models(self):
        self.custom_models = self.settings_manager.get_custom_models()
        self.refresh_model_list()
    
    def refresh_model_list(self):
        self.model_list.clear()
        for model in self.custom_models:
            item = QListWidgetItem(model.get('name', '未命名'))
            item.setData(Qt.UserRole, model)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if model.get('enabled', False) else Qt.Unchecked)
            self.model_list.addItem(item)
    
    def on_model_item_changed(self, item):
        model = item.data(Qt.UserRole)
        if model:
            model['enabled'] = (item.checkState() == Qt.Checked)
            index = None
            for i, m in enumerate(self.custom_models):
                if m.get('name') == model.get('name'):
                    index = i
                    break
            if index is not None:
                self.custom_models[index] = model
    
    def on_selection_changed(self):
        has_selection = len(self.model_list.selectedItems()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.test_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def test_model(self):
        """异步测试选中的模型连接"""
        selected_items = self.model_list.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        model = item.data(Qt.UserRole)
        if not model:
            return
        
        base_url = model.get("endpoint", "")
        if not base_url:
            QMessageBox.warning(self, "错误", "该模型没有配置接口地址！")
            return
        
        # 禁用测试按钮防止重复点击
        self.test_btn.setEnabled(False)
        self.test_btn.setText("测试中...")
        
        # 检测是否是 Ollama
        service_name = model.get("name", "").lower()
        is_ollama = "ollama" in service_name or "localhost" in base_url or "127.0.0.1" in base_url
        
        # 保存模型名称用于结果显示
        self.current_test_model_name = model.get('name', '未命名')
        
        if is_ollama:
            # 使用 Ollama 专门的测试
            self.manager_test_worker = OllamaAsyncWorker(base_url, operation="test")
            self.manager_test_worker.test_success.connect(self._on_manager_test_success)
            self.manager_test_worker.test_failed.connect(self._on_manager_test_failed)
            self.manager_test_worker.finished.connect(self._on_manager_test_finished)
            self.manager_test_worker.start()
        else:
            # 通用的异步测试
            self.manager_generic_worker = GenericTestWorker(base_url)
            self.manager_generic_worker.test_success.connect(self._on_manager_generic_test_success)
            self.manager_generic_worker.test_failed.connect(self._on_manager_test_failed)
            self.manager_generic_worker.finished.connect(self._on_manager_test_finished)
            self.manager_generic_worker.start()
    
    def _on_manager_test_success(self, models_count):
        """模型列表测试成功"""
        QMessageBox.information(self, "测试成功", f"模型 '{self.current_test_model_name}' 连接成功！发现 {models_count} 个模型。")
    
    def _on_manager_generic_test_success(self, status_code):
        """通用测试成功"""
        QMessageBox.information(self, "测试成功", f"模型 '{self.current_test_model_name}' 连接成功！服务器状态码: {status_code}")
    
    def _on_manager_test_failed(self, error_msg):
        """测试失败"""
        QMessageBox.warning(self, "测试失败", f"模型 '{self.current_test_model_name}' 连接失败！错误信息: {error_msg}")
    
    def _on_manager_test_finished(self):
        """测试完成，恢复按钮状态"""
        self.test_btn.setEnabled(True)
        self.test_btn.setText("测试")
    
    def add_model(self):
        dialog = ModelEditDialog(parent=self)
        if self.theme_manager:
            dialog.set_theme_manager(self.theme_manager)
        if dialog.exec_() == QDialog.Accepted:
            model_data = dialog.get_model_data()
            if model_data.get('name'):
                self.custom_models.append(model_data)
                self.refresh_model_list()
    
    def edit_model(self):
        selected_items = self.model_list.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        model = item.data(Qt.UserRole)
        if not model:
            return
        
        dialog = ModelEditDialog(model_data=model, parent=self)
        if self.theme_manager:
            dialog.set_theme_manager(self.theme_manager)
        if dialog.exec_() == QDialog.Accepted:
            updated_model = dialog.get_model_data()
            # 找到并更新原模型
            for i, m in enumerate(self.custom_models):
                if m.get('name') == model.get('name'):
                    self.custom_models[i] = updated_model
                    break
            self.refresh_model_list()
    
    def delete_model(self):
        selected_items = self.model_list.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        model = item.data(Qt.UserRole)
        if not model:
            return
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除模型 '{model.get('name')}' 吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.custom_models = [m for m in self.custom_models if m.get('name') != model.get('name')]
            self.refresh_model_list()
    
    def get_models(self):
        return self.custom_models


class GeneralSettingsPanel(QWidget):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.theme_manager = None
        self.init_ui()
        self.load_settings()
    
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
                background-color: {theme['dialog_background']};
                color: {theme['foreground']};
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
        layout.setSpacing(20)
        
        self.header_label = QLabel("通用设置")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        self.header_label.setFont(header_font)
        layout.addWidget(self.header_label)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("浅色主题", "light")
        self.theme_combo.addItem("深色主题", "dark")
        form_layout.addRow("主题:", self.theme_combo)
        
        self.auto_save_checkbox = QCheckBox("自动保存")
        form_layout.addRow("", self.auto_save_checkbox)
        
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setValue(5)
        self.auto_save_interval.setSuffix(" 分钟")
        form_layout.addRow("自动保存间隔:", self.auto_save_interval)
        
        self.reading_font_size_spin = QSpinBox()
        self.reading_font_size_spin.setRange(8, 24)
        self.reading_font_size_spin.setValue(12)
        self.reading_font_size_spin.setSuffix(" pt")
        form_layout.addRow("阅读字号:", self.reading_font_size_spin)
        
        layout.addLayout(form_layout)
        layout.addStretch()
    
    def load_settings(self):
        theme = self.settings_manager.get('theme', 'light')
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        font_size = self.settings_manager.get_reading_font_size()
        self.reading_font_size_spin.setValue(font_size)
    
    def save_settings(self):
        self.settings_manager.set('theme', self.theme_combo.currentData())
        self.settings_manager.set_reading_font_size(self.reading_font_size_spin.value())


class PromptSettingsPanel(QWidget):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.theme_manager = None
        self.init_ui()
        self.load_settings()
    
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
                background-color: {theme['dialog_background']};
                color: {theme['foreground']};
            }}
            QTextEdit {{
                background-color: {theme['input_background']};
                color: {theme['foreground']};
                border: 1px solid {theme['input_border']};
                padding: 5px;
                border-radius: 3px;
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
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(20)
        
        self.header_label = QLabel("提示词配置")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        self.header_label.setFont(header_font)
        container_layout.addWidget(self.header_label)
        
        container_layout.addWidget(QLabel("请配置各业务模式的提示词模板："))
        
        self.translation_group = QGroupBox("翻译模式")
        translation_layout = QVBoxLayout(self.translation_group)
        translation_layout.setSpacing(10)
        self.translation_input = QTextEdit()
        self.translation_input.setPlaceholderText("请输入翻译模式的提示词...")
        self.translation_input.setMaximumHeight(100)
        translation_layout.addWidget(self.translation_input)
        container_layout.addWidget(self.translation_group)
        
        self.analysis_group = QGroupBox("解析模式")
        analysis_layout = QVBoxLayout(self.analysis_group)
        analysis_layout.setSpacing(10)
        self.analysis_input = QTextEdit()
        self.analysis_input.setPlaceholderText("请输入解析模式的提示词...")
        self.analysis_input.setMaximumHeight(100)
        analysis_layout.addWidget(self.analysis_input)
        container_layout.addWidget(self.analysis_group)
        
        self.scenery_group = QGroupBox("造景模式")
        scenery_layout = QVBoxLayout(self.scenery_group)
        scenery_layout.setSpacing(10)
        self.scenery_input = QTextEdit()
        self.scenery_input.setPlaceholderText("请输入造景模式的提示词...")
        self.scenery_input.setMaximumHeight(100)
        scenery_layout.addWidget(self.scenery_input)
        container_layout.addWidget(self.scenery_group)
        
        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
    
    def load_settings(self):
        prompt_templates = self.settings_manager.get_prompt_templates()
        self.translation_input.setPlainText(prompt_templates.get('translation', ''))
        self.analysis_input.setPlainText(prompt_templates.get('analysis', ''))
        self.scenery_input.setPlainText(prompt_templates.get('scenery', ''))
    
    def save_settings(self):
        prompt_templates = {
            'translation': self.translation_input.toPlainText().strip(),
            'analysis': self.analysis_input.toPlainText().strip(),
            'scenery': self.scenery_input.toPlainText().strip()
        }
        self.settings_manager.set_prompt_templates(prompt_templates)


class SettingsDialog(QDialog):
    def __init__(self, settings_manager, theme_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.theme_manager = theme_manager
        self.panels = {}
        self.init_ui()
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
            self.apply_theme(self.theme_manager.get_current_theme_name())
    
    def apply_theme(self, theme_name=None):
        if not self.theme_manager:
            return
        theme = self.theme_manager.get_theme()
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme['dialog_background']};
            }}
        """)
        
        self.sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['sidebar_background']};
                border-right: 1px solid {theme['sidebar_border']};
            }}
        """)
        
        self.sidebar_header.setStyleSheet(f"""
            padding: 15px 10px;
            font-size: 14px;
            font-weight: bold;
            background-color: {theme['sidebar_header']};
            border-bottom: 1px solid {theme['sidebar_border']};
            color: {theme['foreground']};
        """)
        
        self.category_list.setStyleSheet(f"""
            QListWidget {{
                border: none;
                outline: none;
                background-color: transparent;
            }}
            QListWidget::item {{
                padding: 12px 15px;
                border: none;
                color: {theme['foreground']};
            }}
            QListWidget::item:selected {{
                background-color: {theme['list_item_selected']};
                color: white;
            }}
            QListWidget::item:hover:!selected {{
                background-color: {theme['list_item_hover']};
            }}
        """)
        
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['primary_button']};
                color: white;
                padding: 6px 20px;
                border-radius: 3px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {theme['primary_button_hover']};
            }}
        """)
        
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['button_background']};
                color: {theme['foreground']};
                padding: 6px 20px;
                border-radius: 3px;
                border: 1px solid {theme['input_border']};
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover']};
            }}
        """)
    
    def init_ui(self):
        self.setWindowTitle("设置")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Horizontal)
        
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.setStyleSheet("background-color: #f3f3f3; border-right: 1px solid #ddd;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        self.sidebar_header = QLabel("  设置")
        self.sidebar_header.setStyleSheet("""
            padding: 15px 10px;
            font-size: 14px;
            font-weight: bold;
            background-color: #e8e8e8;
            border-bottom: 1px solid #ddd;
        """)
        sidebar_layout.addWidget(self.sidebar_header)
        
        self.category_list = QListWidget()
        self.category_list.setStyleSheet("""
            QListWidget {
                border: none;
                outline: none;
                background-color: transparent;
            }
            QListWidget::item {
                padding: 12px 15px;
                border: none;
            }
            QListWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background-color: #e0e0e0;
            }
        """)
        self.category_list.currentRowChanged.connect(self.on_category_changed)
        sidebar_layout.addWidget(self.category_list)
        
        self.content_stack = QStackedWidget()
        
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.content_stack)
        splitter.setSizes([220, 780])
        
        main_layout.addWidget(splitter, 1)
        
        button_container = QWidget()
        button_container.setStyleSheet("background-color: transparent;")
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(15, 10, 15, 15)
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFixedSize(90, 32)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        button_layout.addSpacing(10)
        
        self.save_button = QPushButton("保存")
        self.save_button.setFixedSize(90, 32)
        self.save_button.clicked.connect(self.save_and_close)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #007acc;
                color: white;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        button_layout.addWidget(self.save_button)
        
        main_layout.addWidget(button_container)
        
        self.setup_categories()
    
    def setup_categories(self):
        categories = [
            ("通用", GeneralSettingsPanel),
            ("翻译服务", TranslationSettingsPanel),
            ("提示词配置", PromptSettingsPanel)
        ]
        
        # 添加背诵模式设置面板（如果可用）
        if RecitationSettingsPanel is not None:
            categories.insert(1, ("背诵模式", RecitationSettingsPanel))
        
        for name, panel_class in categories:
            item = QListWidgetItem(name)
            self.category_list.addItem(item)
            
            panel = panel_class(self.settings_manager)
            if hasattr(panel, 'set_theme_manager') and self.theme_manager:
                panel.set_theme_manager(self.theme_manager)
            self.panels[name] = panel
            self.content_stack.addWidget(panel)
        
        if self.category_list.count() > 0:
            self.category_list.setCurrentRow(0)
    
    def on_category_changed(self, row):
        self.content_stack.setCurrentIndex(row)
    
    def save_and_close(self):
        for panel in self.panels.values():
            panel.save_settings()
        self.settings_manager.save()
        QMessageBox.information(self, "保存成功", "设置已保存！")
        self.accept()
