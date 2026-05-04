
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QToolButton, 
                             QHBoxLayout, QSplitter, QLabel, QMessageBox, QSizePolicy, QFrame, QMenu, QAction)
from PyQt5.QtCore import pyqtSignal as Signal, Qt, QSize, QTimer, QEvent
from cells.base_cell import BaseCell
from translation.translation_worker import TranslationWorker
from utils.size_calculator import SizeCalculator
from utils.message_box_theme import apply_message_box_theme
import markdown

class ClickableIndicatorLine(QFrame):
    double_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(3)
        self.setStyleSheet("background-color: transparent;")
        self.setMouseTracking(True)
        self.default_color = "transparent"
        self.hover_color = "#1a73e8"
        
    def set_colors(self, default, hover):
        self.default_color = default
        self.hover_color = hover
        self.setStyleSheet(f"background-color: {self.default_color};")
        
    def enterEvent(self, event):
        self.setStyleSheet(f"background-color: {self.hover_color};")
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.setStyleSheet(f"background-color: {self.default_color};")
        super().leaveEvent(event)
        
    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

class ClickableTextEdit(QTextEdit):
    double_clicked = Signal()
    collect_word = Signal(str)  # 新增信号：用于发送选中的单词
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)
        
    def contextMenuEvent(self, event):
        """右键菜单事件"""
        # 获取选中的文本
        selected_text = self.textCursor().selectedText().strip()
        
        # 创建右键菜单
        menu = QMenu(self)
        
        # 添加标准的编辑菜单项
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self.copy)
        copy_action.setEnabled(selected_text != "")
        menu.addAction(copy_action)
        
        paste_action = QAction("粘贴", self)
        paste_action.triggered.connect(self.paste)
        menu.addAction(paste_action)
        
        menu.addSeparator()
        
        # 添加收藏单词菜单项
        if selected_text:
            collect_action = QAction("收藏单词", self)
            collect_action.triggered.connect(lambda: self.collect_word.emit(selected_text))
            menu.addAction(collect_action)
        
        # 显示菜单
        menu.exec_(event.globalPos())

class MarkdownEditor(QWidget):
    content_changed = Signal()
    needs_height_update = Signal()
    collect_word = Signal(str)  # 新增信号：用于传递选中的单词
    
    def __init__(self):
        super().__init__()
        self.is_reading_mode = False
        self.settings_manager = None
        self.init_ui()
        
    def init_ui(self):
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
        self.editor.collect_word.connect(self.collect_word.emit)  # 转发信号
        
        self.reading = ClickableTextEdit()
        self.reading.setReadOnly(True)
        self.reading.setStyleSheet("border: 1px solid #ccc; padding: 10px;")
        self.reading.setLineWrapMode(QTextEdit.WidgetWidth)
        self.reading.hide()
        self.reading.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reading.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.reading.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.reading.double_clicked.connect(self.toggle_mode)
        self.reading.collect_word.connect(self.collect_word.emit)  # 转发信号
        
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

    def sync_body_min_height(self, content_height: int):
        """统一源/阅读两个文本框的最小高度，避免切换模式或 HTML 与纯文本高度不一致时裁切或留白。"""
        h = max(24, int(content_height))
        self.editor.setMinimumHeight(h)
        self.reading.setMinimumHeight(h)
        
    def toggle_mode(self):
        if self.is_reading_mode:
            self.switch_to_edit_mode()
        else:
            self.switch_to_reading_mode()
        
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
    collect_word = Signal(str)  # 新增信号：用于传递选中的单词
    
    def __init__(self):
        super().__init__()
        # 防抖定时器
        self.height_update_timer = QTimer()
        self.height_update_timer.setSingleShot(True)
        self.height_update_timer.timeout.connect(self._update_height_now)
        # 折叠状态
        self.is_input_collapsed = False
        self.is_output_collapsed = False
        self.is_cell_collapsed = False
        
    def set_settings_manager(self, settings_manager):
        super().set_settings_manager(settings_manager)
        self.input_editor.set_settings_manager(settings_manager)
        self.output_editor.set_settings_manager(settings_manager)
        
    def init_ui(self):
        super().init_ui()
        
        # 设置可以扩展但有合理范围的尺寸策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 主布局 - 添加三条指示线
        main_content_layout = QHBoxLayout()
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(3)
        
        # 单元格指示线
        self.cell_indicator = ClickableIndicatorLine()
        self.cell_indicator.set_colors("#1a73e8", "#4285f4")
        self.cell_indicator.double_clicked.connect(self.toggle_cell_collapse)
        main_content_layout.addWidget(self.cell_indicator)
        
        # 主内容区容器
        main_content = QWidget()
        main_content_inner_layout = QVBoxLayout(main_content)
        main_content_inner_layout.setContentsMargins(0, 0, 0, 0)
        main_content_inner_layout.setSpacing(0)
        
        # 单元格折叠时的省略号标签
        self.cell_ellipsis_label = QLabel("...")
        self.cell_ellipsis_label.setStyleSheet("font-size: 16pt; color: #666; padding: 5px;")
        self.cell_ellipsis_label.hide()
        main_content_inner_layout.addWidget(self.cell_ellipsis_label)
        
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)
        
        # 原文区域 - 包含指示线和内容
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
        self.input_editor.collect_word.connect(self.collect_word.emit)  # 连接收藏单词信号
        input_layout.addWidget(self.input_editor)
        
        # 原文折叠时的省略号标签
        self.input_ellipsis_label = QLabel("...")
        self.input_ellipsis_label.setStyleSheet("font-size: 14pt; color: #666; padding: 5px;")
        self.input_ellipsis_label.hide()
        input_layout.addWidget(self.input_ellipsis_label)
        
        input_container_layout.addWidget(self.input_section, 1)
        
        # 翻译区域 - 包含指示线和内容
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
        self.output_editor.collect_word.connect(self.collect_word.emit)  # 连接收藏单词信号
        output_layout.addWidget(self.output_editor)
        
        # 翻译折叠时的省略号标签
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
        
    def toggle_cell_collapse(self):
        self.is_cell_collapsed = not self.is_cell_collapsed
        if self.is_cell_collapsed:
            self.splitter.hide()
            self.cell_ellipsis_label.show()
            self.cell_indicator.set_colors("#666", "#888")
            self.set_gutter_visible(False)
            QTimer.singleShot(100, self._update_height_now)
        else:
            self.splitter.show()
            self.cell_ellipsis_label.hide()
            self.cell_indicator.set_colors("#1a73e8", "#4285f4")
            self.set_gutter_visible(True)
            QTimer.singleShot(100, self._update_height_now)
            
    def toggle_input_collapse(self):
        self.is_input_collapsed = not self.is_input_collapsed
        if self.is_input_collapsed:
            self.input_editor.hide()
            self.input_ellipsis_label.show()
            self.input_label.hide()
            self.input_indicator.set_colors("#666", "#888")
            QTimer.singleShot(100, self._update_height_now)
        else:
            self.input_editor.show()
            self.input_ellipsis_label.hide()
            self.input_label.show()
            self.input_indicator.set_colors("#34a853", "#5cb85c")
            QTimer.singleShot(100, self._update_height_now)
            
    def toggle_output_collapse(self):
        self.is_output_collapsed = not self.is_output_collapsed
        if self.is_output_collapsed:
            self.output_editor.hide()
            self.output_ellipsis_label.show()
            self.output_label.hide()
            self.output_indicator.set_colors("#666", "#888")
            QTimer.singleShot(100, self._update_height_now)
        else:
            self.output_editor.show()
            self.output_ellipsis_label.hide()
            self.output_label.show()
            self.output_indicator.set_colors("#ea4335", "#f06292")
            QTimer.singleShot(100, self._update_height_now)
        
    def _on_needs_height_update(self):
        # 防抖：300ms 后再真正计算高度，避免频繁更新
        self.height_update_timer.start(300)
    
    def _viewport_width_for(self, editor_widget):
        """用于文档折行的宽度：优先视口，避免用整格宽度导致低估行数、内容被裁切。"""
        for te in (editor_widget.reading, editor_widget.editor):
            vw = te.viewport().width()
            if vw > 50:
                return vw
        ca = self.content_area.width()
        if ca > 50:
            return max(50, ca - 16)
        cw = self.width()
        if cw > 80:
            return max(50, cw - 50)
        return 400

    def _update_height_now(self):
        """按文档真实高度 + 固定装饰区域计算单元格总高，并同步分割条，避免短内容大块留白或长内容被裁切。"""
        try:
            # 如果整个单元格折叠了
            if self.is_cell_collapsed:
                total_height = 40
                self.setFixedHeight(total_height)
                if self.parentWidget():
                    self.parentWidget().updateGeometry()
                return
                
            w_in = self._viewport_width_for(self.input_editor)
            w_out = self._viewport_width_for(self.output_editor)

            # 取纯文本与 HTML 布局的较大者，保证 Edit/Read 切换后都够高
            input_doc_h = max(
                SizeCalculator.calculate_precise_height(self.input_editor.reading, w_in),
                SizeCalculator.calculate_precise_height(self.input_editor.editor, w_in),
            )
            output_doc_h = max(
                SizeCalculator.calculate_precise_height(self.output_editor.reading, w_out),
                SizeCalculator.calculate_precise_height(self.output_editor.editor, w_out),
            )
            self.input_editor.sync_body_min_height(input_doc_h)
            self.output_editor.sync_body_min_height(output_doc_h)

            # 每段：区段标签 + MarkdownEditor（无顶栏，只有布局间距）+ 区段内边距
            editor_chrome = 5
            label_h = 22
            section_extra = 10
            splitter_handle = 6
            cm = self.content_layout.contentsMargins()
            content_margin_v = cm.top() + cm.bottom()

            # 计算每个区域的高度，考虑折叠状态
            if self.is_input_collapsed:
                input_section_h = label_h + 20  # 标签 + 省略号
            else:
                input_section_h = label_h + editor_chrome + input_doc_h + section_extra
                
            if self.is_output_collapsed:
                output_section_h = label_h + 20
            else:
                output_section_h = label_h + editor_chrome + output_doc_h + section_extra
                
            total_height = int(
                input_section_h + output_section_h + splitter_handle + content_margin_v
            )

            total_height = max(self.min_height, min(total_height, self.max_height))

            self.setFixedHeight(total_height)
            self.splitter.setSizes([max(42, input_section_h), max(42, output_section_h)])

            if self.parentWidget():
                self.parentWidget().updateGeometry()
        except Exception as e:
            print(f"[Height Update] Error: {e}")
        
    def set_content(self, content):
        self.input_editor.set_content(content)
        # 设置内容后立即更新高度（不防抖）
        QTimer.singleShot(50, self._update_height_now)
        
    def get_content(self):
        return self.input_editor.get_content()
        
    def set_output(self, content):
        self.output_editor.set_content(content)
        # 设置内容后立即更新高度（不防抖）
        QTimer.singleShot(50, self._update_height_now)
        
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

        api_timeout = self.translation_service.get_translation_timeout_seconds()
        # asyncio.wait_for 需略大于 SDK/HTTP 超时，避免线程池仍在跑时已误判超时
        worker_timeout = max(api_timeout + 45, 90)
        print(f"[Translation] 超时：模型配置 {api_timeout}s，线程上限 {worker_timeout}s")

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
        # 深色主题下原生 QMessageBox 常出现正文与背景同色（看似全黑），显式指定标签颜色
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
        
    def apply_theme(self, theme):
        super().apply_theme(theme)
        self.input_editor.apply_theme(theme)
        self.output_editor.apply_theme(theme)
        
    def sizeHint(self):
        try:
            # 如果整个单元格折叠了
            if self.is_cell_collapsed:
                ww = self.width() if self.width() > 100 else 400
                return QSize(ww, 40)
                
            w_in = self._viewport_width_for(self.input_editor)
            w_out = self._viewport_width_for(self.output_editor)
            input_doc_h = max(
                SizeCalculator.calculate_precise_height(self.input_editor.reading, w_in),
                SizeCalculator.calculate_precise_height(self.input_editor.editor, w_in),
            )
            output_doc_h = max(
                SizeCalculator.calculate_precise_height(self.output_editor.reading, w_out),
                SizeCalculator.calculate_precise_height(self.output_editor.editor, w_out),
            )
            editor_chrome = 5
            label_h = 22
            section_extra = 10
            splitter_handle = 6
            cm = self.content_layout.contentsMargins()
            content_margin_v = cm.top() + cm.bottom()
            
            # 计算每个区域的高度，考虑折叠状态
            if self.is_input_collapsed:
                input_section_h = label_h + 20
            else:
                input_section_h = label_h + editor_chrome + input_doc_h + section_extra
                
            if self.is_output_collapsed:
                output_section_h = label_h + 20
            else:
                output_section_h = label_h + editor_chrome + output_doc_h + section_extra
                
            total_height = int(
                input_section_h + output_section_h + splitter_handle + content_margin_v
            )
            total_height = max(self.min_height, min(total_height, self.max_height))
            ww = self.width() if self.width() > 100 else 400
            return QSize(ww, total_height)
        except Exception:
            ww = self.width() if self.width() > 100 else 400
            return QSize(ww, self.min_height)

    def minimumSizeHint(self):
        ww = self.width() if self.width() > 100 else 200
        return QSize(max(200, ww), self.min_height)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._on_needs_height_update()

    def adjust_height(self):
        self._update_height_now()
        self.updateGeometry()
