from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QToolButton, QHBoxLayout
from PyQt5.QtCore import pyqtSignal as Signal, Qt
from cells.base_cell import BaseCell
from utils.size_calculator import SizeCalculator
import markdown

class MarkdownCell(BaseCell):
    def __init__(self):
        super().__init__()
        self.is_preview_mode = False
        self.init_markdown_editor()
        
    def init_markdown_editor(self):
        self.editor_container = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_container)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_layout.setSpacing(0)
        
        self.mode_bar = QWidget()
        self.mode_layout = QHBoxLayout(self.mode_bar)
        self.mode_layout.setContentsMargins(0, 0, 0, 0)
        
        self.edit_button = QToolButton()
        self.edit_button.setText("编辑")
        self.edit_button.clicked.connect(self.switch_to_edit_mode)
        self.mode_layout.addWidget(self.edit_button)
        
        self.preview_button = QToolButton()
        self.preview_button.setText("预览")
        self.preview_button.clicked.connect(self.switch_to_preview_mode)
        self.mode_layout.addWidget(self.preview_button)
        
        self.mode_layout.addStretch(1)
        
        self.editor_layout.addWidget(self.mode_bar)
        
        self.editor = QTextEdit()
        self.editor.setStyleSheet("font-family: Consolas; font-size: 10pt; border: 1px solid #ccc;")
        self.editor.setLineWrapMode(QTextEdit.WidgetWidth)
        self.editor.textChanged.connect(self.on_text_changed)
        
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setStyleSheet("border: 1px solid #ccc; padding: 10px;")
        self.preview.setLineWrapMode(QTextEdit.WidgetWidth)
        self.preview.hide()
        
        self.editor_layout.addWidget(self.editor)
        self.editor_layout.addWidget(self.preview)
        
        self.content_layout.addWidget(self.editor_container)
        
    def set_content(self, content):
        self.editor.setPlainText(content)
        self.update_preview()
        self.adjust_height()
        
    def get_content(self):
        return self.editor.toPlainText()
    
    def on_text_changed(self):
        self.update_preview()
        self.adjust_height()
        
    def update_preview(self):
        md_text = self.editor.toPlainText()
        html = markdown.markdown(md_text, extensions=['tables', 'fenced_code'])
        self.preview.setHtml(html)
        
    def switch_to_edit_mode(self):
        self.is_preview_mode = False
        self.editor.show()
        self.preview.hide()
        self.adjust_height()
        
    def switch_to_preview_mode(self):
        self.is_preview_mode = True
        self.editor.hide()
        self.preview.show()
        self.adjust_height()
        
    def run(self):
        self.switch_to_preview_mode()
        
    def apply_theme(self, theme):
        super().apply_theme(theme)
        self.editor.setStyleSheet(f"font-family: Consolas; font-size: 10pt; border: 1px solid {theme['output_border']}; background-color: {theme['editor_background']}; color: {theme['editor_foreground']};")
        self.preview.setStyleSheet(f"border: 1px solid {theme['output_border']}; padding: 10px; background-color: {theme['markdown_background']}; color: {theme['foreground']};")
        
    def adjust_height(self):
        content_width = self.content_area.width()
        if content_width <= 0:
            return
            
        if self.is_preview_mode:
            height = self.calculate_preview_height(content_width)
        else:
            height = self.calculate_editor_height(content_width)
            
        height = max(height, self.min_height)
        height = min(height, self.max_height)
        
        self.setMinimumHeight(int(height))
        self.setMaximumHeight(int(height))
        
        self.height_changed.emit()
        
    def calculate_editor_height(self, width):
        text = self.editor.toPlainText()
        font = self.editor.font()
        return SizeCalculator.calculate_text_height(text, width - 20, font) + 40
    
    def calculate_preview_height(self, width):
        text = self.editor.toPlainText()
        return SizeCalculator.calculate_markdown_height(text, width) + 40