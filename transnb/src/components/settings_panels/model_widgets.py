import re
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox,
    QSpinBox, QFormLayout, QComboBox, QListWidget,
    QListWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal as Signal
from PyQt5.QtGui import QFont
from utils.message_box_theme import show_information, show_warning
from translation.providers.api_key_resolve import ark_api_key_configured
from ..settings_workers import (
    OllamaAsyncWorker,
    GenericTestWorker,
    ArkTestWorker
)


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
        self.setMinimumSize(500, 650)
        
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

        self.api_key_env_combo.setStyleSheet("""
            QComboBox { background-color: white; color: black; }
            QComboBox QAbstractItemView { background-color: white; color: black; }
        """)

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


__all__ = ['ModelEditDialog', 'ModelManagerWidget']
