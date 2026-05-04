from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QToolButton, 
                             QHBoxLayout, QSplitter, QLabel, QMessageBox, QSizePolicy)
from PyQt5.QtCore import pyqtSignal as Signal, Qt, QSize, QTimer, QEvent
from cells.base_cell import BaseCell
from cells.cell_config import CellConfig
from cells.cell_height_calculator import CellHeightCalculator
from cells.widgets import (
    ClickableIndicatorLine,
    MarkdownEditor
)
from translation.translation_worker import TranslationWorker
from utils.message_box_theme import apply_message_box_theme
from typing import Optional


class MarkdownCell(BaseCell):
    """Markdown单元格，支持原文和翻译两个Markdown编辑器"""
    collect_word = Signal(str)
    cell_collapse_changed = Signal(object, bool)
    
    def __init__(self):
        super().__init__()
        self.height_update_timer = QTimer()
        self.height_update_timer.setSingleShot(True)
        self.height_update_timer.timeout.connect(self._update_height_now)
        self.is_input_collapsed: bool = False
        self.is_output_collapsed: bool = False
        self.is_cell_collapsed: bool = False
        
    def set_settings_manager(self, settings_manager: object) -> None:
        super().set_settings_manager(settings_manager)
        self.input_editor.set_settings_manager(settings_manager)
        self.output_editor.set_settings_manager(settings_manager)
        
    def init_ui(self) -> None:
        super().init_ui()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        main_content_layout = QHBoxLayout()
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(3)
        
        self.cell_indicator = ClickableIndicatorLine()
        self.cell_indicator.set_colors("#1a73e8", "#4285f4")
        self.cell_indicator.double_clicked.connect(self.toggle_cell_collapse)
        main_content_layout.addWidget(self.cell_indicator)
        
        main_content = QWidget()
        main_content_inner_layout = QVBoxLayout(main_content)
        main_content_inner_layout.setContentsMargins(0, 0, 0, 0)
        main_content_inner_layout.setSpacing(0)
        
        self.cell_ellipsis_label = QLabel("...")
        self.cell_ellipsis_label.setStyleSheet("font-size: 16pt; color: #666; padding: 5px;")
        self.cell_ellipsis_label.hide()
        main_content_inner_layout.addWidget(self.cell_ellipsis_label)
        
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)
        
        input_container = QWidget()
        input_container_layout = QHBoxLayout(input_container)
        input_container_layout.setContentsMargins(0, 0, 0, 0)
        input_container_layout.setSpacing(3)
        
        self.input_indicator = ClickableIndicatorLine()
        self.input_indicator.set_colors("#34a853", "#5cb85c")
        self.input_indicator.double_clicked.connect(self.toggle_input_collapse)
        input_container_layout.addWidget(self.input_indicator)
        
        self.input_section = QWidget()
        input_layout = QVBoxLayout(self.input_section)
        input_layout.setContentsMargins(0, 0, 0, 5)
        input_layout.setSpacing(3)
        
        self.input_label = QWidget()
        label_layout = QHBoxLayout(self.input_label)
        label_layout.setContentsMargins(0, 0, 0, 0)
        self.input_label_text = QLabel("Source")
        self.input_label_text.setStyleSheet("font-weight: bold; font-size: 11pt;")
        label_layout.addWidget(self.input_label_text)
        label_layout.addStretch(1)
        input_layout.addWidget(self.input_label)
        
        self.input_editor = MarkdownEditor()
        self.input_editor.switch_to_reading_mode()
        self.input_editor.needs_height_update.connect(self._on_needs_height_update)
        self.input_editor.collect_word.connect(self.collect_word.emit)
        # 当切换到编辑模式时，确保单元格被选中
        self.input_editor.edit_mode_entered.connect(self._on_edit_mode_entered)
        input_layout.addWidget(self.input_editor)
        
        self.input_ellipsis_label = QLabel("...")
        self.input_ellipsis_label.setStyleSheet("font-size: 14pt; color: #666; padding: 5px;")
        self.input_ellipsis_label.hide()
        input_layout.addWidget(self.input_ellipsis_label)
        
        input_container_layout.addWidget(self.input_section, 1)
        
        output_container = QWidget()
        output_container_layout = QHBoxLayout(output_container)
        output_container_layout.setContentsMargins(0, 0, 0, 0)
        output_container_layout.setSpacing(3)
        
        self.output_indicator = ClickableIndicatorLine()
        self.output_indicator.set_colors("#ea4335", "#f06292")
        self.output_indicator.double_clicked.connect(self.toggle_output_collapse)
        output_container_layout.addWidget(self.output_indicator)
        
        self.output_section = QWidget()
        output_layout = QVBoxLayout(self.output_section)
        output_layout.setContentsMargins(0, 5, 0, 0)
        output_layout.setSpacing(3)
        
        self.output_label = QWidget()
        label_layout2 = QHBoxLayout(self.output_label)
        label_layout2.setContentsMargins(0, 0, 0, 0)
        self.output_label_text = QLabel("Translation")
        self.output_label_text.setStyleSheet("font-weight: bold; font-size: 11pt;")
        label_layout2.addWidget(self.output_label_text)
        label_layout2.addStretch(1)
        output_layout.addWidget(self.output_label)
        
        self.output_editor = MarkdownEditor()
        self.output_editor.switch_to_reading_mode()
        self.output_editor.needs_height_update.connect(self._on_needs_height_update)
        self.output_editor.collect_word.connect(self.collect_word.emit)
        output_layout.addWidget(self.output_editor)
        
        self.output_ellipsis_label = QLabel("...")
        self.output_ellipsis_label.setStyleSheet("font-size: 14pt; color: #666; padding: 5px;")
        self.output_ellipsis_label.hide()
        output_layout.addWidget(self.output_ellipsis_label)
        
        output_container_layout.addWidget(self.output_section, 1)
        
        self.splitter.addWidget(input_container)
        self.splitter.addWidget(output_container)
        
        main_content_inner_layout.addWidget(self.splitter)
        main_content_layout.addWidget(main_content, 1)
        
        self.content_layout.addLayout(main_content_layout)
        
    def toggle_cell_collapse(self) -> None:
        self.is_cell_collapsed = not self.is_cell_collapsed
        if self.is_cell_collapsed:
            self.splitter.hide()
            self.cell_ellipsis_label.show()
            self.cell_indicator.set_colors("#666", "#888")
            self.set_gutter_visible(False)
        else:
            self.splitter.show()
            self.cell_ellipsis_label.hide()
            self.cell_indicator.set_colors("#1a73e8", "#4285f4")
            self.set_gutter_visible(True)
        self.cell_collapse_changed.emit(self, self.is_cell_collapsed)
        QTimer.singleShot(CellConfig.TOGGLE_DELAY_MS, self._update_height_now)
            
    def toggle_input_collapse(self) -> None:
        self.is_input_collapsed = not self.is_input_collapsed
        if self.is_input_collapsed:
            self.input_editor.hide()
            self.input_ellipsis_label.show()
            self.input_label.hide()
            self.input_indicator.set_colors("#666", "#888")
        else:
            self.input_editor.show()
            self.input_ellipsis_label.hide()
            self.input_label.show()
            self.input_indicator.set_colors("#34a853", "#5cb85c")
        QTimer.singleShot(CellConfig.TOGGLE_DELAY_MS, self._update_height_now)
            
    def toggle_output_collapse(self) -> None:
        self.is_output_collapsed = not self.is_output_collapsed
        if self.is_output_collapsed:
            self.output_editor.hide()
            self.output_ellipsis_label.show()
            self.output_label.hide()
            self.output_indicator.set_colors("#666", "#888")
        else:
            self.output_editor.show()
            self.output_ellipsis_label.hide()
            self.output_label.show()
            self.output_indicator.set_colors("#ea4335", "#f06292")
        QTimer.singleShot(CellConfig.TOGGLE_DELAY_MS, self._update_height_now)
        
    def _on_needs_height_update(self) -> None:
        self.height_update_timer.start(CellConfig.HEIGHT_UPDATE_DEBOUNCE_MS)
    
    def _update_height_now(self) -> None:
        try:
            total_height, input_doc_h, output_doc_h, splitter_sizes = CellHeightCalculator.calculate_height_for_cell(
                cell_widget=self,
                content_area=self.content_area,
                content_layout=self.content_layout,
                input_editor=self.input_editor,
                output_editor=self.output_editor,
                is_cell_collapsed=self.is_cell_collapsed,
                is_input_collapsed=self.is_input_collapsed,
                is_output_collapsed=self.is_output_collapsed,
                min_height=self.min_height,
                max_height=self.max_height
            )
            
            self.input_editor.sync_body_min_height(input_doc_h)
            self.output_editor.sync_body_min_height(output_doc_h)
            self.setFixedHeight(total_height)
            self.splitter.setSizes(list(splitter_sizes))
            
            if self.parentWidget():
                self.parentWidget().updateGeometry()
        except Exception:
            pass
        
    def set_content(self, content: str) -> None:
        self.input_editor.set_content(content)
        QTimer.singleShot(CellConfig.HEIGHT_UPDATE_IMMEDIATE_MS, self._update_height_now)
        
    def get_content(self) -> str:
        return self.input_editor.get_content()
        
    def set_output(self, content: str) -> None:
        self.output_editor.set_content(content)
        QTimer.singleShot(CellConfig.HEIGHT_UPDATE_IMMEDIATE_MS, self._update_height_now)
        
    def get_output(self) -> str:
        return self.output_editor.get_content()
        
    def translate(self) -> None:
        content = self.get_content()
        
        if not self.translation_service:
            translated = f"(Translation result)\n{content}"
            self.set_output(translated)
            return
        
        self.translate_button.setEnabled(False)
        
        prompt_template = ""
        if self.settings_manager:
            prompt_template = self.settings_manager.get_prompt_template("analysis")
        
        api_timeout = self.translation_service.get_translation_timeout_seconds()
        worker_timeout = max(api_timeout + 45, 90)
        
        self.translation_worker = TranslationWorker(
            translation_service=self.translation_service,
            text=content,
            prompt_template=prompt_template,
            timeout=worker_timeout,
        )
        
        self.translation_worker.started.connect(self.on_translation_started)
        self.translation_worker.finished.connect(self.on_translation_finished)
        self.translation_worker.error.connect(self.on_translation_error)
        
        self.translation_worker.start()
    
    def on_translation_started(self) -> None:
        self.set_output("Translating...")
    
    def on_translation_finished(self, result: object) -> None:
        self.set_output(str(result))
        self.translate_button.setEnabled(True)
    
    def on_translation_error(self, error_msg: str) -> None:
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("翻译错误")
        msg.setText(error_msg)
        msg.setStandardButtons(QMessageBox.Ok)
        apply_message_box_theme(msg, theme_dict=getattr(self, "theme", None))
        msg.exec_()
        content = self.get_content()
        self.set_output(f"(Translation failed)\n{content}")
        self.translate_button.setEnabled(True)
        
    def apply_theme(self, theme: dict) -> None:
        super().apply_theme(theme)
        self.input_editor.apply_theme(theme)
        self.output_editor.apply_theme(theme)
    
    def _on_edit_mode_entered(self):
        """当进入编辑模式时，确保单元格被选中"""
        print("[DEBUG] _on_edit_mode_entered")
        if not self.is_selected:
            # 如果单元格没有被选中，发出选中信号
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import Qt
            shift_pressed = bool(QApplication.queryKeyboardModifiers() & Qt.ShiftModifier)
            print(f"[DEBUG] 单元格未选中，发出选中信号 shift_pressed={shift_pressed}")
            self.selected.emit((self, shift_pressed))
        
    def sizeHint(self) -> QSize:
        try:
            total_height, _, _, _ = CellHeightCalculator.calculate_height_for_cell(
                cell_widget=self,
                content_area=self.content_area,
                content_layout=self.content_layout,
                input_editor=self.input_editor,
                output_editor=self.output_editor,
                is_cell_collapsed=self.is_cell_collapsed,
                is_input_collapsed=self.is_input_collapsed,
                is_output_collapsed=self.is_output_collapsed,
                min_height=self.min_height,
                max_height=self.max_height
            )
            ww = self.width() if self.width() > 100 else 400
            return QSize(ww, total_height)
        except Exception:
            ww = self.width() if self.width() > 100 else 400
            return QSize(ww, self.min_height)

    def minimumSizeHint(self) -> QSize:
        ww = self.width() if self.width() > 100 else 200
        return QSize(max(200, ww), self.min_height)
        
    def resizeEvent(self, event: QEvent) -> None:
        super().resizeEvent(event)
        self._on_needs_height_update()

    def adjust_height(self) -> None:
        self._update_height_now()
        self.updateGeometry()
    
    def get_text_before_cursor(self) -> Optional[str]:
        """获取光标前的文本内容（如果是阅读模式返回 None）"""
        result = self.input_editor.get_text_before_cursor()
        print(f"[DEBUG] MarkdownCell.get_text_before_cursor() -> {repr(result)}")
        return result
    
    def get_text_after_cursor(self) -> Optional[str]:
        """获取光标后的文本内容（如果是阅读模式返回 None）"""
        result = self.input_editor.get_text_after_cursor()
        print(f"[DEBUG] MarkdownCell.get_text_after_cursor() -> {repr(result)}")
        return result
    
    def is_reading_mode(self) -> bool:
        """检查是否处于阅读模式"""
        result = self.input_editor.is_reading_mode
        print(f"[DEBUG] MarkdownCell.is_reading_mode() -> {result}")
        return result
    
    def switch_to_edit_mode(self) -> None:
        """切换到编辑模式"""
        print("[DEBUG] MarkdownCell.switch_to_edit_mode()")
        self.input_editor.switch_to_edit_mode()
