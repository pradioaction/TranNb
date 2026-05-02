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
from utils.message_box_theme import show_information, show_warning
from translation.providers.api_key_resolve import ark_api_key_configured, openai_api_key_configured
import httpx
import os
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


class EnvVarNameDialog(QDialog):
    """登记单个环境变量「名称」与可选说明。"""

    def __init__(self, title, initial_name="", initial_desc="", theme_manager=None, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setWindowTitle(title)
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setText(initial_name)
        self.name_edit.setPlaceholderText("例如 ARK_API_KEY")
        self.desc_edit = QLineEdit()
        self.desc_edit.setText(initial_desc)
        self.desc_edit.setPlaceholderText("可选，便于识别用途")
        form.addRow("变量名:", self.name_edit)
        form.addRow("说明:", self.desc_edit)
        layout.addLayout(form)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("saveBtn")
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)
        if self.theme_manager:
            self._apply_theme()

    def _apply_theme(self):
        theme = self.theme_manager.get_theme()
        self.setStyleSheet(f"""
            QDialog {{ background-color: {theme['dialog_background']}; }}
            QLabel {{ color: {theme['foreground']}; }}
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
            QPushButton#saveBtn {{
                background-color: {theme['primary_button']};
                color: white;
            }}
        """)

    def values(self):
        return self.name_edit.text().strip(), self.desc_edit.text().strip()


class EnvVarsEditorWidget(QWidget):
    """在设置中维护 API 密钥对应的环境变量名称列表（不保存密钥本身）。"""

    entries_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = None
        self._entries = []
        self.init_ui()

    def set_theme_manager(self, theme_manager):
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
            self.apply_theme()

    def apply_theme(self, theme_name=None):
        if not self.theme_manager:
            return
        theme = self.theme_manager.get_theme()
        self.setStyleSheet(f"""
            QWidget {{ background-color: transparent; color: {theme['foreground']}; }}
            QListWidget {{
                background-color: {theme['input_background']};
                border: 1px solid {theme['input_border']};
                border-radius: 5px;
                color: {theme['foreground']};
            }}
            QListWidget::item {{ padding: 8px; }}
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
            QPushButton:hover {{ background-color: {theme['button_hover']}; }}
            QLabel {{ color: {theme['foreground']}; }}
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        hint = QLabel(
            "下列条目仅保存「变量名」。请在本机环境（系统变量或启动脚本）中配置真实密钥值；"
            "自定义 Ark 模型可从下拉中选此处登记的名称，也可手动输入未登记的变量名。"
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.list_w = QListWidget()
        layout.addWidget(self.list_w)
        row = QHBoxLayout()
        row.addStretch()
        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self._add_entry)
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._edit_entry)
        self.del_btn = QPushButton("删除")
        self.del_btn.clicked.connect(self._del_entry)
        row.addWidget(self.add_btn)
        row.addWidget(self.edit_btn)
        row.addWidget(self.del_btn)
        layout.addLayout(row)

    def set_entries(self, entries):
        self._entries = [dict(e) for e in (entries or [])]
        self._refresh_list()

    def get_entries(self):
        return [dict(e) for e in self._entries]

    def _refresh_list(self):
        self.list_w.clear()
        for e in self._entries:
            name = (e.get("name") or "").strip()
            desc = (e.get("description") or "").strip()
            label = name + (f" — {desc}" if desc else "")
            item = QListWidgetItem(label or "(未命名)")
            item.setData(Qt.UserRole, e)
            self.list_w.addItem(item)

    def _valid_var_name(self, name: str) -> bool:
        return bool(name and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name))

    def _add_entry(self):
        dlg = EnvVarNameDialog("添加环境变量名", theme_manager=self.theme_manager, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        name, desc = dlg.values()
        if not self._valid_var_name(name):
            show_warning(self, "错误", "变量名不能为空，且仅限字母、数字、下划线，不能以数字开头。", theme_manager=self.theme_manager)
            return
        if any((e.get("name") or "").strip() == name for e in self._entries):
            show_warning(self, "错误", "该变量名已存在。", theme_manager=self.theme_manager)
            return
        self._entries.append({"name": name, "description": desc})
        self._refresh_list()
        self.entries_changed.emit()

    def _edit_entry(self):
        row = self.list_w.currentRow()
        if row < 0 or row >= len(self._entries):
            return
        cur = self._entries[row]
        dlg = EnvVarNameDialog(
            "编辑环境变量名",
            initial_name=cur.get("name", ""),
            initial_desc=cur.get("description", ""),
            theme_manager=self.theme_manager,
            parent=self,
        )
        if dlg.exec_() != QDialog.Accepted:
            return
        name, desc = dlg.values()
        if not self._valid_var_name(name):
            show_warning(self, "错误", "变量名不能为空，且仅限字母、数字、下划线，不能以数字开头。", theme_manager=self.theme_manager)
            return
        for i, e in enumerate(self._entries):
            if i != row and (e.get("name") or "").strip() == name:
                show_warning(self, "错误", "该变量名已被其他条目使用。", theme_manager=self.theme_manager)
                return
        self._entries[row] = {"name": name, "description": desc}
        self._refresh_list()
        self.entries_changed.emit()

    def _del_entry(self):
        row = self.list_w.currentRow()
        if row < 0 or row >= len(self._entries):
            return
        name = (self._entries[row].get("name") or "").strip()
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除环境变量名「{name}」吗？（不影响系统环境，仅从本列表移除）",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        del self._entries[row]
        self._refresh_list()
        self.entries_changed.emit()


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


class ModelEditDialog(QDialog):
    def __init__(self, model_data=None, parent=None, settings_manager=None):
        super().__init__(parent)
        self.model_data = model_data or {}
        self.settings_manager = settings_manager
        self.theme_manager = None
        self.init_ui()
        if model_data:
            self.load_model_data(model_data)
        else:
            self._refresh_api_key_env_combo()
        self._update_backend_fields()
    
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
                selection-color: white;
                border: 1px solid {theme['input_border']};
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

        self.backend_combo = QComboBox()
        self.backend_combo.addItem("Ollama", "ollama")
        self.backend_combo.addItem("火山方舟 Ark", "ark")
        form_layout.addRow("后端:", self.backend_combo)
        self.backend_combo.currentIndexChanged.connect(lambda *_: self._update_backend_fields())

        self.ark_key_row = QWidget()
        ark_key_layout = QVBoxLayout(self.ark_key_row)
        ark_key_layout.setContentsMargins(0, 0, 0, 0)
        self.api_key_env_combo = QComboBox()
        self.api_key_env_combo.setEditable(True)
        self.api_key_env_combo.setToolTip("可从上方「环境变量名」列表选择，或直接输入系统已有的变量名")
        ark_key_layout.addWidget(self.api_key_env_combo)
        ark_hint = QLabel("密钥从系统环境变量读取；设置文件中只保存上述变量名。")
        ark_hint.setWordWrap(True)
        ark_key_layout.addWidget(ark_hint)
        form_layout.addRow("API 密钥环境变量:", self.ark_key_row)

        self.endpoint_input = QLineEdit()
        self.endpoint_input.setPlaceholderText(
            "Ollama: http://host:11434；Ark 可留空（默认北京）或填自定义 base_url"
        )
        form_layout.addRow("接口地址:", self.endpoint_input)
        
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Ollama 模型名；Ark 填推理接入点 ID")
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
        save_btn.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)

    def _refresh_api_key_env_combo(self):
        keep = ""
        if hasattr(self, "api_key_env_combo"):
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

    def _update_backend_fields(self):
        backend = (self.backend_combo.currentData() or "ollama").lower()
        self.ark_key_row.setVisible(backend == "ark")

    def _on_save_clicked(self):
        backend = (self.backend_combo.currentData() or "ollama").lower()
        if backend == "ark":
            env_name = self.api_key_env_combo.currentText().strip()
            if not env_name:
                show_warning(self, "错误", "请填写或选择 API 密钥对应的环境变量名。", theme_manager=self.theme_manager)
                return
            if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", env_name):
                show_warning(
                    self,
                    "错误",
                    "环境变量名格式无效（仅限字母、数字、下划线，且不能以数字开头）。",
                    theme_manager=self.theme_manager,
                )
                return
        self.accept()
    
    def _on_test_clicked(self):
        """异步测试连接"""
        config = self.get_model_data()
        backend = (config.get("backend") or "ollama").lower()
        base_url = config.get("endpoint", "")

        if backend == "ark":
            env_name = (config.get("api_key_env") or "").strip()
            if not env_name:
                show_warning(self, "错误", "请填写 API 密钥对应的环境变量名。", theme_manager=self.theme_manager)
                return
            if not ark_api_key_configured(config):
                show_warning(
                    self,
                    "错误",
                    f"未能从进程环境中读取到密钥，请确认已设置「{env_name}」且启动本程序时能继承该变量。",
                    theme_manager=self.theme_manager,
                )
                return
            if not (config.get("model") or "").strip():
                show_warning(self, "错误", "请填写方舟模型 / 推理接入点 ID", theme_manager=self.theme_manager)
                return
            self.test_button.setEnabled(False)
            self.test_button.setText("测试中...")
            self._ark_edit_test_worker = ArkTestWorker(config)
            self._ark_edit_test_worker.test_success.connect(self._on_ark_edit_test_success)
            self._ark_edit_test_worker.test_failed.connect(self._on_ark_edit_test_failed)
            self._ark_edit_test_worker.finished.connect(self._on_custom_test_finished)
            self._ark_edit_test_worker.start()
            return

        if not base_url:
            show_warning(self, "错误", "请先填写接口地址！", theme_manager=self.theme_manager)
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
        show_information(self, "测试成功", f"连接成功！发现 {models_count} 个模型。", theme_manager=self.theme_manager)
    
    def _on_custom_test_failed(self, error_msg):
        """自定义模型测试失败"""
        show_warning(self, "测试失败", f"连接失败！错误信息: {error_msg}", theme_manager=self.theme_manager)
    
    def _on_generic_test_success(self, status_code):
        """通用测试成功"""
        show_information(self, "测试成功", f"连接成功！服务器状态码: {status_code}", theme_manager=self.theme_manager)
    
    def _on_generic_test_failed(self, error_msg):
        """通用测试失败"""
        show_warning(self, "测试失败", f"连接失败！错误信息: {error_msg}", theme_manager=self.theme_manager)
    
    def _on_custom_test_finished(self):
        """测试完成，恢复按钮状态"""
        self.test_button.setEnabled(True)
        self.test_button.setText("测试连接")

    def _on_ark_edit_test_success(self):
        show_information(self, "测试成功", "方舟 Chat 调用成功。", theme_manager=self.theme_manager)

    def _on_ark_edit_test_failed(self, error_msg):
        show_warning(self, "测试失败", f"连接失败：{error_msg}", theme_manager=self.theme_manager)
    
    def load_model_data(self, model_data):
        self.name_input.setText(model_data.get('name', ''))
        backend = model_data.get("backend", "ollama")
        idx = self.backend_combo.findData(backend)
        self.backend_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._refresh_api_key_env_combo()
        env_name = (model_data.get("api_key_env") or "").strip()
        if not env_name and (model_data.get("api_key") or "").strip():
            env_name = "ARK_API_KEY"
        self.api_key_env_combo.setEditText(env_name)
        self.endpoint_input.setText(model_data.get('endpoint', ''))
        self.model_input.setText(model_data.get('model', ''))
        self.timeout_spinbox.setValue(model_data.get('timeout', 30))
        self.proxy_input.setText(model_data.get('proxy', ''))
        self.enabled_checkbox.setChecked(model_data.get('enabled', True))
    
    def get_model_data(self):
        backend = self.backend_combo.currentData() or 'ollama'
        env_name = self.api_key_env_combo.currentText().strip() if backend.lower() == "ark" else ""
        return {
            'name': self.name_input.text().strip(),
            'backend': backend,
            'api_key_env': env_name,
            'endpoint': self.endpoint_input.text().strip(),
            'model': self.model_input.text().strip(),
            'timeout': self.timeout_spinbox.value(),
            'proxy': self.proxy_input.text().strip(),
            'enabled': self.enabled_checkbox.isChecked()
        }


class ModelManagerWidget(QWidget):
    models_changed = Signal()
    
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
            item.setCheckState(Qt.Checked if model.get('enabled', True) else Qt.Unchecked)
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
                self.models_changed.emit()
    
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
        
        backend = (model.get("backend") or "ollama").lower()
        base_url = model.get("endpoint", "")

        if backend == "ark":
            env_name = (model.get("api_key_env") or "").strip()
            if not env_name:
                show_warning(self, "错误", "该模型未填写 API 密钥对应的环境变量名。", theme_manager=self.theme_manager)
                return
            if not ark_api_key_configured(model):
                show_warning(
                    self,
                    "错误",
                    f"未能从进程环境中读取到密钥，请确认已设置「{env_name}」。",
                    theme_manager=self.theme_manager,
                )
                return
            if not (model.get("model") or "").strip():
                show_warning(self, "错误", "请填写方舟模型 / 推理接入点 ID", theme_manager=self.theme_manager)
                return
            self.test_btn.setEnabled(False)
            self.test_btn.setText("测试中...")
            self.current_test_model_name = model.get('name', '未命名')
            self.manager_ark_worker = ArkTestWorker(model)
            self.manager_ark_worker.test_success.connect(self._on_manager_ark_test_success)
            self.manager_ark_worker.test_failed.connect(self._on_manager_test_failed)
            self.manager_ark_worker.finished.connect(self._on_manager_test_finished)
            self.manager_ark_worker.start()
            return

        if not base_url:
            show_warning(self, "错误", "该模型没有配置接口地址！", theme_manager=self.theme_manager)
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
    
    def _on_manager_ark_test_success(self):
        show_information(
            self,
            "测试成功",
            f"模型 '{self.current_test_model_name}' 方舟 Chat 调用成功。",
            theme_manager=self.theme_manager,
        )

    def _on_manager_test_success(self, models_count):
        """模型列表测试成功"""
        show_information(
            self,
            "测试成功",
            f"模型 '{self.current_test_model_name}' 连接成功！发现 {models_count} 个模型。",
            theme_manager=self.theme_manager,
        )
    
    def _on_manager_generic_test_success(self, status_code):
        """通用测试成功"""
        show_information(
            self,
            "测试成功",
            f"模型 '{self.current_test_model_name}' 连接成功！服务器状态码: {status_code}",
            theme_manager=self.theme_manager,
        )
    
    def _on_manager_test_failed(self, error_msg):
        """测试失败"""
        show_warning(
            self,
            "测试失败",
            f"模型 '{self.current_test_model_name}' 连接失败！错误信息: {error_msg}",
            theme_manager=self.theme_manager,
        )
    
    def _on_manager_test_finished(self):
        """测试完成，恢复按钮状态"""
        self.test_btn.setEnabled(True)
        self.test_btn.setText("测试")
    
    def add_model(self):
        dialog = ModelEditDialog(parent=self, settings_manager=self.settings_manager)
        if self.theme_manager:
            dialog.set_theme_manager(self.theme_manager)
        if dialog.exec_() == QDialog.Accepted:
            model_data = dialog.get_model_data()
            if model_data.get('name'):
                self.custom_models.append(model_data)
                self.refresh_model_list()
                self.models_changed.emit()
    
    def edit_model(self):
        selected_items = self.model_list.selectedItems()
        if not selected_items:
            return
        item = selected_items[0]
        model = item.data(Qt.UserRole)
        if not model:
            return
        
        dialog = ModelEditDialog(model_data=model, parent=self, settings_manager=self.settings_manager)
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
            self.models_changed.emit()
    
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
            self.models_changed.emit()
    
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
                selection-color: white;
                border: 1px solid {theme['input_border']};
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
    def __init__(self, settings_manager, theme_manager, translation_service=None, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.theme_manager = theme_manager
        self.translation_service = translation_service
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
        # 刷新翻译服务配置
        if self.translation_service:
            self.translation_service.reload_from_settings()
        QMessageBox.information(self, "保存成功", "设置已保存！")
        self.accept()
