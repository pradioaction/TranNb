
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QToolButton, 
                             QHBoxLayout, QSplitter, QLabel, QMessageBox, QSizePolicy)
from PyQt5.QtCore import pyqtSignal as Signal, Qt, QSize
from cells.base_cell import BaseCell
from translation.translation_worker import TranslationWorker
from utils.size_calculator import SizeCalculator
import markdown

class MarkdownEditor(QWidget):
    content_changed = Signal()
    needs_height_update = Signal()
    
    def __init__(self):
        super().__init__()
        self.is_reading_mode = False
        self.settings_manager = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        mode_bar = QWidget()
        mode_layout = QHBoxLayout(mode_bar)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        
        self.edit_button = QToolButton()
        self.edit_button.setText("Edit")
        self.edit_button.clicked.connect(self.switch_to_edit_mode)
        mode_layout.addWidget(self.edit_button)
        
        self.reading_button = QToolButton()
        self.reading_button.setText("Read")
        self.reading_button.clicked.connect(self.switch_to_reading_mode)
        mode_layout.addWidget(self.reading_button)
        
        mode_layout.addStretch(1)
        layout.addWidget(mode_bar)
        
        self.editor = QTextEdit()
        self.editor.setStyleSheet("font-family: Consolas, sans-serif; font-size: 10pt; border: 1px solid #ccc;")
        self.editor.setLineWrapMode(QTextEdit.WidgetWidth)
        self.editor.setAcceptRichText(False)
        self.editor.textChanged.connect(self._on_text_changed)
        self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.reading = QTextEdit()
        self.reading.setReadOnly(True)
        self.reading.setStyleSheet("border: 1px solid #ccc; padding: 10px;")
        self.reading.setLineWrapMode(QTextEdit.WidgetWidth)
        self.reading.hide()
        self.reading.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reading.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reading.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout.addWidget(self.editor)
        layout.addWidget(self.reading)
        
    def set_settings_manager(self, settings_manager):
        self.settings_manager = settings_manager
        if self.settings_manager:
            self.settings_manager.reading_font_size_changed.connect(self.on_reading_font_size_changed)
        self.update_reading_font()
        
    def on_reading_font_size_changed(self, font_size):
        self.update_reading_font()
        self.needs_height_update.emit()
        
    def update_reading_font(self):
        if self.settings_manager:
            font_size = self.settings_manager.get_reading_font_size()
            self.reading.setStyleSheet(f"border: 1px solid #ccc; padding: 10px; font-size: {font_size}pt;")
        else:
            self.reading.setStyleSheet("border: 1px solid #ccc; padding: 10px;")
        
    def _on_text_changed(self):
        self.update_reading()
        self.content_changed.emit()
        self.needs_height_update.emit()
        
    def set_content(self, content):
        self.editor.setPlainText(content)
        self.update_reading()
        
    def get_content(self):
        return self.editor.toPlainText()
    
    def update_reading(self):
        md_text = self.editor.toPlainText()
        html = markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'nl2br'])
        self.reading.setHtml(html)
        
    def switch_to_edit_mode(self):
        self.is_reading_mode = False
        self.editor.show()
        self.reading.hide()
        self.content_changed.emit()
        self.needs_height_update.emit()
        
    def switch_to_reading_mode(self):
        self.is_reading_mode = True
        self.editor.hide()
        self.reading.show()
        self.content_changed.emit()
        self.needs_height_update.emit()
        
    def apply_theme(self, theme):
        self.editor.setStyleSheet(f"font-family: Consolas, sans-serif; font-size: 10pt; border: 1px solid {theme['output_border']}; background-color: {theme['editor_background']}; color: {theme['editor_foreground']};")
        if self.settings_manager:
            font_size = self.settings_manager.get_reading_font_size()
            self.reading.setStyleSheet(f"border: 1px solid {theme['output_border']}; padding: 10px; background-color: {theme['markdown_background']}; color: {theme['foreground']}; font-size: {font_size}pt;")
        else:
            self.reading.setStyleSheet(f"border: 1px solid {theme['output_border']}; padding: 10px; background-color: {theme['markdown_background']}; color: {theme['foreground']};")

class MarkdownCell(BaseCell):
    def __init__(self):
        super().__init__()
        
    def set_settings_manager(self, settings_manager):
        super().set_settings_manager(settings_manager)
        self.input_editor.set_settings_manager(settings_manager)
        self.output_editor.set_settings_manager(settings_manager)
        
    def init_ui(self):
        super().init_ui()
        
        # 设置可以扩展但有合理范围的尺寸策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)
        
        self.input_section = QWidget()
        input_layout = QVBoxLayout(self.input_section)
        input_layout.setContentsMargins(0, 0, 0, 5)
        input_layout.setSpacing(3)
        
        input_label = QWidget()
        label_layout = QHBoxLayout(input_label)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("Source")
        label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        label_layout.addWidget(label)
        label_layout.addStretch(1)
        input_layout.addWidget(input_label)
        
        self.input_editor = MarkdownEditor()
        self.input_editor.switch_to_reading_mode()
        self.input_editor.needs_height_update.connect(self._on_needs_height_update)
        input_layout.addWidget(self.input_editor)
        
        self.output_section = QWidget()
        output_layout = QVBoxLayout(self.output_section)
        output_layout.setContentsMargins(0, 5, 0, 0)
        output_layout.setSpacing(3)
        
        output_label = QWidget()
        label_layout2 = QHBoxLayout(output_label)
        label_layout2.setContentsMargins(0, 0, 0, 0)
        label2 = QLabel("Translation")
        label2.setStyleSheet("font-weight: bold; font-size: 11pt;")
        label_layout2.addWidget(label2)
        label_layout2.addStretch(1)
        output_layout.addWidget(output_label)
        
        self.output_editor = MarkdownEditor()
        self.output_editor.switch_to_reading_mode()
        self.output_editor.needs_height_update.connect(self._on_needs_height_update)
        output_layout.addWidget(self.output_editor)
        
        self.splitter.addWidget(self.input_section)
        self.splitter.addWidget(self.output_section)
        # 设置默认的分割比例
        self.splitter.setSizes([300, 300])
        
        self.content_layout.addWidget(self.splitter)
        
    def _on_needs_height_update(self):
        self.updateGeometry()
        
    def set_content(self, content):
        self.input_editor.set_content(content)
        
    def get_content(self):
        return self.input_editor.get_content()
        
    def set_output(self, content):
        self.output_editor.set_content(content)
        
    def get_output(self):
        return self.output_editor.get_content()
        
    def translate(self):
        print("[Translation] Starting translation...")
        content = self.get_content()
        if len(content) > 100:
            print(f"[Translation] Source content: {content[:100]}...")
        else:
            print(f"[Translation] Source content: {content}")
        
        if not self.translation_service:
            print("[Translation] Translation service not initialized, using default")
            translated = f"(Translation result)\n{content}"
            self.set_output(translated)
            return
        
        self.translate_button.setEnabled(False)
        
        prompt_template = ""
        if self.settings_manager:
            prompt_template = self.settings_manager.get_prompt_template("analysis")
        
        print(f"[Translation] Prompt template: {prompt_template}")
        
        self.translation_worker = TranslationWorker(
            translation_service=self.translation_service,
            text=content,
            prompt_template=prompt_template,
            timeout=30
        )
        
        self.translation_worker.started.connect(self.on_translation_started)
        self.translation_worker.finished.connect(self.on_translation_finished)
        self.translation_worker.error.connect(self.on_translation_error)
        
        self.translation_worker.start()
    
    def on_translation_started(self):
        print("[Translation] Task started...")
        self.set_output("Translating...")
    
    def on_translation_finished(self, result):
        print("[Translation] Finished!")
        result_str = str(result)
        if len(result_str) > 100:
            print(f"[Translation] Result: {result_str[:100]}...")
        else:
            print(f"[Translation] Result: {result_str}")
        self.set_output(result)
        self.translate_button.setEnabled(True)
    
    def on_translation_error(self, error_msg):
        print(f"[Translation] Error: {error_msg}")
        QMessageBox.warning(
            self,
            "Translation Error",
            error_msg,
            QMessageBox.Ok
        )
        content = self.get_content()
        self.set_output(f"(Translation failed)\n{content}")
        self.translate_button.setEnabled(True)
        
    def apply_theme(self, theme):
        super().apply_theme(theme)
        self.input_editor.apply_theme(theme)
        self.output_editor.apply_theme(theme)
        
    def sizeHint(self):
        # 计算合理的高度，确保内容完整显示
        try:
            available_width = self.width() if self.width() > 100 else 800
            
            input_widget = self.input_editor.reading if self.input_editor.is_reading_mode else self.input_editor.editor
            output_widget = self.output_editor.reading if self.output_editor.is_reading_mode else self.output_editor.editor
            
            input_height = SizeCalculator.calculate_precise_height(input_widget, available_width)
            output_height = SizeCalculator.calculate_precise_height(output_widget, available_width)
            
            total_height = int(input_height + output_height + 150)
            total_height = max(self.min_height, min(total_height, self.max_height))
            
            # print(f"[sizeHint] Total: {total_height} (in: {input_height}, out: {output_height})")
            return QSize(self.width() if self.width() > 100 else 800, total_height)
        except Exception as e:
            # print(f"[sizeHint] Error: {e}")
            return QSize(self.width() if self.width() > 100 else 800, 600)
    
    def minimumSizeHint(self):
        return QSize(200, 400)
        
    def adjust_height(self):
        # print(f"[Height adjust] Current cell height: {self.height()}")
        self.updateGeometry()
