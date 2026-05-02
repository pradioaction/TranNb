"""
设置对话框模块
保持向后兼容性，所有功能已拆分到子模块中
"""
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget,
    QLabel, QPushButton, QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt
from .settings_workers import (
    OllamaAsyncWorker,
    GenericTestWorker,
    ArkTestWorker,
    OpenAITestWorker
)
from .settings_panels import (
    UrlValidator,
    EnvVarNameDialog,
    EnvVarsEditorWidget,
    TranslationConfigWidget,
    TranslationSettingsPanel,
    ModelEditDialog,
    ModelManagerWidget,
    GeneralSettingsPanel,
    PromptSettingsPanel
)

# 导入背诵模式设置面板
try:
    from recitation.ui import RecitationSettingsPanel
except ImportError:
    RecitationSettingsPanel = None


class SettingsDialog(QDialog):
    """
    设置对话框
    主界面，管理各个设置面板的显示和切换
    """
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


# 保持向后兼容性，导出所有类
__all__ = [
    'SettingsDialog',
    'OllamaAsyncWorker',
    'GenericTestWorker',
    'ArkTestWorker',
    'OpenAITestWorker',
    'UrlValidator',
    'EnvVarNameDialog',
    'EnvVarsEditorWidget',
    'TranslationConfigWidget',
    'TranslationSettingsPanel',
    'ModelEditDialog',
    'ModelManagerWidget',
    'GeneralSettingsPanel',
    'PromptSettingsPanel'
]
