from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QLabel, QComboBox, QCheckBox,
    QSpinBox, QGroupBox, QScrollArea,
    QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


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


__all__ = ['GeneralSettingsPanel', 'PromptSettingsPanel']
