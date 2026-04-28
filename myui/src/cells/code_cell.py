from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QSplitter, QLabel, QCompleter
from PyQt5.QtGui import QColor, QFont, QPixmap, QFontMetrics, QStandardItemModel
from PyQt5.QtCore import Qt, pyqtSignal as Signal, QStringListModel
from cells.base_cell import BaseCell
from utils.size_calculator import SizeCalculator
import sys
import keyword
import inspect

try:
    from PyQt5.Qsci import QsciScintilla, QsciLexerPython, QsciAPIs
    HAS_QSCINTILLA = True
except ImportError:
    HAS_QSCINTILLA = False

try:
    import black
    HAS_BLACK = True
except ImportError:
    HAS_BLACK = False

try:
    import autopep8
    HAS_AUTOPep8 = True
except ImportError:
    HAS_AUTOPep8 = False

class CodeCell(BaseCell):
    output_ready = Signal(str)
    
    def __init__(self, kernel_manager):
        super().__init__()
        self.kernel_manager = kernel_manager
        self.output_content = ""
        self.init_code_editor()
        
    def init_code_editor(self):
        self.editor_container = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_container)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.editor_layout.setSpacing(0)
        
        if HAS_QSCINTILLA:
            self.editor = QsciScintilla()
            self.editor.setLexer(QsciLexerPython())
            self.editor.setUtf8(True)
            self.editor.setAutoIndent(True)
            self.editor.setIndentationWidth(4)
            self.editor.setTabWidth(4)
            self.editor.setBackspaceUnindents(True)
            self.editor.setIndentationGuides(True)
            self.editor.setMarginsBackgroundColor(QColor("#f0f0f0"))
            self.editor.setMarginLineNumbers(1, True)
            self.editor.setMarginWidth(1, 40)
            self.editor.setBraceMatching(QsciScintilla.SloppyBraceMatch)
            self.editor.setWrapMode(QsciScintilla.WrapWord)
            self.editor.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            font = QFont("Consolas", 10)
            self.editor.setFont(font)
            self.editor.setMarginsFont(font)
            
            lexer = self.editor.lexer()
            lexer.setDefaultFont(font)
            lexer.setFont(font)
            
            self.editor.setStyleSheet("border: 1px solid #ccc;")
            
            self.init_autocomplete()
        else:
            self.editor = QTextEdit()
            self.editor.setStyleSheet("font-family: Consolas; font-size: 10pt; border: 1px solid #ccc;")
            self.editor.setLineWrapMode(QTextEdit.WidgetWidth)
            fm = QFontMetrics(QFont())
            self.editor.setTabStopWidth(4 * fm.width(' '))
            
            self.init_simple_autocomplete()
        
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor_layout.addWidget(self.editor)
        
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("background-color: #fafafa; border: 1px solid #eee; font-family: Consolas; font-size: 10pt;")
        self.output_area.setLineWrapMode(QTextEdit.WidgetWidth)
        self.output_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.output_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.editor_layout.addWidget(self.output_area)
        
        self.content_layout.addWidget(self.editor_container)
        
        self.kernel_manager.output_received.connect(self.on_output_received)
        self.kernel_manager.error_received.connect(self.on_error_received)
        self.kernel_manager.image_received.connect(self.on_image_received)
        
    def init_autocomplete(self):
        if not HAS_QSCINTILLA:
            return
            
        self.apis = QsciAPIs(self.editor.lexer())
        
        python_keywords = keyword.kwlist
        for kw in python_keywords:
            self.apis.add(kw)
            
        builtins = dir(__builtins__)
        for name in builtins:
            if not name.startswith('_'):
                self.apis.add(name)
                
        self.apis.prepare()
        self.editor.setAutoCompletionSource(QsciScintilla.AcsAPIs)
        self.editor.setAutoCompletionThreshold(2)
        self.editor.setAutoCompletionCaseSensitivity(False)
        self.editor.setAutoCompletionReplaceWord(True)
        
    def init_simple_autocomplete(self):
        pass
        
    def apply_theme(self, theme):
        super().apply_theme(theme)
        if HAS_QSCINTILLA:
            self.editor.setMarginsBackgroundColor(QColor(theme['gutter']))
            self.editor.setStyleSheet(f"border: 1px solid {theme['output_border']};")
        else:
            self.editor.setStyleSheet(f"font-family: Consolas; font-size: 10pt; border: 1px solid {theme['output_border']}; background-color: {theme['editor_background']}; color: {theme['editor_foreground']};")
        
        self.output_area.setStyleSheet(f"background-color: {theme['output_background']}; border: 1px solid {theme['output_border']}; font-family: Consolas; font-size: 10pt; color: {theme['foreground']};")
        
    def set_code(self, code):
        if hasattr(self.editor, 'setText'):
            self.editor.setText(code)
            self.adjust_height()
            
    def get_code(self):
        if hasattr(self.editor, 'text'):
            return self.editor.toPlainText()
        return ""
    
    def set_output(self, output):
        self.output_content = output
        self.output_area.setPlainText(output)
        self.adjust_height()
        
    def get_output(self):
        return self.output_content
    
    def run(self):
        code = self.get_code()
        if code.strip():
            self.output_area.clear()
            self.output_content = ""
            self.kernel_manager.execute_code(code)
            
    def on_text_changed(self):
        self.adjust_height()
        
    def adjust_height(self):
        content_width = self.content_area.width()
        if content_width <= 0:
            return
            
        editor_height = self.calculate_editor_height(content_width)
        output_height = self.calculate_output_height(content_width)
        
        total_height = editor_height + output_height + 20
        
        total_height = max(total_height, self.min_height)
        total_height = min(total_height, self.max_height)
        
        self.setMinimumHeight(int(total_height))
        self.setMaximumHeight(int(total_height))
        
        self.height_changed.emit()
        
    def calculate_editor_height(self, width):
        if not HAS_QSCINTILLA:
            text = self.editor.toPlainText()
            font = self.editor.font()
            return SizeCalculator.calculate_text_height(text, width - 20, font)
        
        lines = self.editor.lines()
        font = self.editor.font()
        fm = QFontMetrics(font)
        line_height = fm.height()
        
        return max(lines * line_height + 20, 60)
    
    def calculate_output_height(self, width):
        text = self.output_area.toPlainText()
        if not text:
            return 50
            
        font = self.output_area.font()
        return SizeCalculator.calculate_text_height(text, width - 20, font) + 10
        
    def format_code(self):
        code = self.get_code()
        if not code.strip():
            return
            
        try:
            if HAS_BLACK:
                formatted_code = black.format_str(code, mode=black.Mode())
            elif HAS_AUTOPep8:
                formatted_code = autopep8.fix_code(code)
            else:
                return
                
            self.set_code(formatted_code)
        except Exception as e:
            pass
            
    def update_completions(self, variables):
        if HAS_QSCINTILLA:
            self.apis.clear()
            
            python_keywords = keyword.kwlist
            for kw in python_keywords:
                self.apis.add(kw)
                
            builtins = dir(__builtins__)
            for name in builtins:
                if not name.startswith('_'):
                    self.apis.add(name)
                    
            for var_name in variables:
                self.apis.add(var_name)
                
            self.apis.prepare()
            
    def on_output_received(self, output):
        self.output_content += output
        self.output_area.setPlainText(self.output_content)
        self.output_area.setStyleSheet("background-color: #fafafa; border: 1px solid #eee; font-family: Consolas; font-size: 10pt; color: black;")
        self.adjust_height()
        
    def on_error_received(self, error):
        self.output_content += f"\nError:\n{error}"
        self.output_area.setPlainText(self.output_content)
        self.output_area.setStyleSheet("background-color: #ffebee; border: 1px solid #ef9a9a; font-family: Consolas; font-size: 10pt; color: #c62828;")
        self.adjust_height()
        
    def on_image_received(self, image_path):
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            label = QLabel()
            label.setPixmap(pixmap.scaledToWidth(min(600, self.content_area.width() - 20), Qt.SmoothTransformation))
            label.setStyleSheet("background-color: white;")
            
            layout = QVBoxLayout()
            layout.addWidget(label)
            
            widget = QWidget()
            widget.setLayout(layout)
            
            self.editor_layout.replaceWidget(self.output_area, widget)
            self.output_area.deleteLater()
            self.output_area = widget
            self.adjust_height()