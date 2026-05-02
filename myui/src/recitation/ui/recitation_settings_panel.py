from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QFormLayout, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import json
import os


class RecitationSettingsPanel(QWidget):
    """背诵模式设置面板"""
    
    def __init__(self, settings_manager=None, parent=None):
        super().__init__(parent)
        self._settings_manager = settings_manager
        self._theme_manager = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("背诵模式设置")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 每日学习设置
        daily_group = QGroupBox("每日学习设置")
        daily_layout = QFormLayout(daily_group)
        
        self._daily_new_spin = QSpinBox()
        self._daily_new_spin.setRange(1, 200)
        self._daily_new_spin.setValue(20)
        self._daily_new_spin.setSuffix(" 个")
        daily_layout.addRow("每日新学单词:", self._daily_new_spin)
        
        self._daily_review_spin = QSpinBox()
        self._daily_review_spin.setRange(1, 200)
        self._daily_review_spin.setValue(50)
        self._daily_review_spin.setSuffix(" 个")
        daily_layout.addRow("每日复习单词:", self._daily_review_spin)
        
        layout.addWidget(daily_group)
        
        # 说明
        note_label = QLabel(
            "提示：\n"
            "- 新学单词是从未学习过的单词\n"
            "- 复习单词是根据艾宾浩斯遗忘曲线计算的需要复习的单词\n"
            "- 建议根据个人时间和能力合理设置每日学习量"
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: gray; padding: 10px;")
        layout.addWidget(note_label)
        
        layout.addStretch()
        
        self.load_settings()
    
    def set_theme_manager(self, theme_manager):
        """设置主题管理器"""
        self._theme_manager = theme_manager
        if self._theme_manager:
            self._theme_manager.theme_changed.connect(self.apply_theme)
            self.apply_theme(self._theme_manager.get_current_theme_name())
    
    def apply_theme(self, theme_name=None):
        """应用主题"""
        if not self._theme_manager:
            return
        
        theme = self._theme_manager.get_theme()
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.get('dialog_background', 'transparent')};
                color: {theme.get('foreground', 'black')};
            }}
            QGroupBox {{
                background-color: {theme.get('group_box', 'transparent')};
                border: 1px solid {theme.get('input_border', '#ccc')};
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: {theme.get('foreground', 'black')};
            }}
            QSpinBox {{
                background-color: {theme.get('input_background', 'white')};
                color: {theme.get('foreground', 'black')};
                border: 1px solid {theme.get('input_border', '#ccc')};
                padding: 3px;
                border-radius: 3px;
            }}
            QLabel {{
                color: {theme.get('foreground', 'black')};
            }}
        """)
    
    def load_settings(self):
        """加载设置"""
        # 尝试从settings_manager加载
        if self._settings_manager:
            recitation_settings = self._settings_manager.get('recitation', {})
            if recitation_settings:
                daily_new = recitation_settings.get('daily_new_words', 20)
                daily_review = recitation_settings.get('daily_review_words', 50)
                self._daily_new_spin.setValue(daily_new)
                self._daily_review_spin.setValue(daily_review)
                return
        
        # 作为备选，尝试直接从studywordmode.json加载
        try:
            if self._settings_manager and hasattr(self._settings_manager, 'get_workspace_path'):
                workspace_path = self._settings_manager.get_workspace_path()
                if workspace_path:
                    settings_path = os.path.join(workspace_path, '.TransRead', 'studywordmode.json')
                    if os.path.exists(settings_path):
                        with open(settings_path, 'r', encoding='utf-8') as f:
                            settings_data = json.load(f)
                            daily_new = settings_data.get('daily_new_words', 20)
                            daily_review = settings_data.get('daily_review_words', 50)
                            self._daily_new_spin.setValue(daily_new)
                            self._daily_review_spin.setValue(daily_review)
        except Exception:
            pass
    
    def save_settings(self):
        """保存设置"""
        daily_new = self._daily_new_spin.value()
        daily_review = self._daily_review_spin.value()
        
        # 保存到settings_manager
        if self._settings_manager:
            recitation_settings = self._settings_manager.get('recitation', {})
            recitation_settings['daily_new_words'] = daily_new
            recitation_settings['daily_review_words'] = daily_review
            self._settings_manager.set('recitation', recitation_settings)
        
        # 同时也保存到studywordmode.json（与背诵模块兼容）
        try:
            if self._settings_manager and hasattr(self._settings_manager, 'get_workspace_path'):
                workspace_path = self._settings_manager.get_workspace_path()
                if workspace_path:
                    transread_dir = os.path.join(workspace_path, '.TransRead')
                    os.makedirs(transread_dir, exist_ok=True)
                    settings_path = os.path.join(transread_dir, 'studywordmode.json')
                    
                    settings_data = {}
                    if os.path.exists(settings_path):
                        try:
                            with open(settings_path, 'r', encoding='utf-8') as f:
                                settings_data = json.load(f)
                        except Exception:
                            pass
                    
                    settings_data['daily_new_words'] = daily_new
                    settings_data['daily_review_words'] = daily_review
                    
                    with open(settings_path, 'w', encoding='utf-8') as f:
                        json.dump(settings_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
