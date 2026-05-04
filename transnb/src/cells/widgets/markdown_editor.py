from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy, QTextEdit
from PyQt5.QtCore import pyqtSignal as Signal, Qt
from typing import Optional
import markdown
from cells.widgets.clickable_text_edit import ClickableTextEdit
from cells.cell_config import CellConfig


class MarkdownEditor(QWidget):
    """Markdown编辑器组件，支持编辑和阅读两种模式"""
    content_changed = Signal()
    needs_height_update = Signal()
    collect_word = Signal(str)
    edit_mode_entered = Signal()  # 进入编辑模式时发出
    
    def __init__(self):
        super().__init__()
        self.is_reading_mode: bool = False
        self.settings_manager: Optional[object] = None
        self.init_ui()
        
    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.editor = ClickableTextEdit()
        self.editor.setStyleSheet("font-family: Consolas, sans-serif; font-size: 10pt; border: 1px solid #ccc;")
        self.editor.setLineWrapMode(QTextEdit.WidgetWidth)
        self.editor.setAcceptRichText(False)
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.editor.double_clicked.connect(self.toggle_mode)
        self.editor.collect_word.connect(self.collect_word.emit)
        
        self.reading = ClickableTextEdit()
        self.reading.setReadOnly(True)
        self.reading.setStyleSheet("border: 1px solid #ccc; padding: 10px;")
        self.reading.setLineWrapMode(QTextEdit.WidgetWidth)
        self.reading.hide()
        self.reading.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reading.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reading.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.reading.double_clicked.connect(self.toggle_mode)
        self.reading.collect_word.connect(self.collect_word.emit)
        
        layout.addWidget(self.editor)
        layout.addWidget(self.reading)
        
    def set_settings_manager(self, settings_manager: object) -> None:
        self.settings_manager = settings_manager
        if self.settings_manager:
            self.settings_manager.reading_font_size_changed.connect(self.on_reading_font_size_changed)
        self.update_reading_font()
        
    def on_reading_font_size_changed(self, font_size: int) -> None:
        self.update_reading_font()
        self.needs_height_update.emit()
        
    def update_reading_font(self) -> None:
        if self.settings_manager:
            font_size = self.settings_manager.get_reading_font_size()
            self.reading.setStyleSheet(f"border: 1px solid #ccc; padding: 10px; font-size: {font_size}pt;")
        else:
            self.reading.setStyleSheet("border: 1px solid #ccc; padding: 10px;")
        
    def _on_text_changed(self) -> None:
        self.update_reading()
        self.content_changed.emit()
        self.needs_height_update.emit()
        
    def set_content(self, content: str) -> None:
        self.editor.setPlainText(content)
        self.update_reading()
        
    def get_content(self) -> str:
        return self.editor.toPlainText()
    
    def update_reading(self) -> None:
        md_text = self.editor.toPlainText()
        html = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'nl2br'])
        self.reading.setHtml(html)

    def sync_body_min_height(self, content_height: int) -> None:
        h = max(CellConfig.MIN_EDITOR_HEIGHT, int(content_height))
        self.editor.setMinimumHeight(h)
        self.reading.setMinimumHeight(h)
        
    def toggle_mode(self) -> None:
        if self.is_reading_mode:
            self.switch_to_edit_mode()
        else:
            self.switch_to_reading_mode()
        
    def switch_to_edit_mode(self) -> None:
        self.is_reading_mode = False
        self.editor.show()
        self.reading.hide()
        self.content_changed.emit()
        self.needs_height_update.emit()
        self.edit_mode_entered.emit()  # 发出进入编辑模式的信号
        
    def switch_to_reading_mode(self) -> None:
        self.is_reading_mode = True
        self.editor.hide()
        self.reading.show()
        self.content_changed.emit()
        self.needs_height_update.emit()
        
    def apply_theme(self, theme: dict) -> None:
        self.editor.setStyleSheet(f"font-family: Consolas, sans-serif; font-size: 10pt; border: 1px solid {theme['output_border']}; background-color: {theme['editor_background']}; color: {theme['editor_foreground']};")
        if self.settings_manager:
            font_size = self.settings_manager.get_reading_font_size()
            self.reading.setStyleSheet(f"border: 1px solid {theme['output_border']}; padding: 10px; background-color: {theme['markdown_background']}; color: {theme['foreground']}; font-size: {font_size}pt;")
        else:
            self.reading.setStyleSheet(f"border: 1px solid {theme['output_border']}; padding: 10px; background-color: {theme['markdown_background']}; color: {theme['foreground']};")
    
    def get_cursor_position(self) -> Optional[int]:
        """获取编辑模式下的光标位置（如果是阅读模式则返回 None）"""
        if self.is_reading_mode:
            return None
        return self.editor.get_cursor_position()
    
    def get_text_before_cursor(self) -> Optional[str]:
        """获取编辑模式下光标前的文本（如果是阅读模式则返回 None）"""
        if self.is_reading_mode:
            return None
        return self.editor.get_text_before_cursor()
    
    def get_text_after_cursor(self) -> Optional[str]:
        """获取编辑模式下光标后的文本（如果是阅读模式则返回 None）"""
        if self.is_reading_mode:
            return None
        return self.editor.get_text_after_cursor()
