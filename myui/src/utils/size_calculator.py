from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtCore import Qt

class SizeCalculator:
    @staticmethod
    def calculate_text_height(text, width, font=None):
        if not text:
            return 0
            
        if font is None:
            font = QFont("Consolas", 10)
            
        fm = QFontMetrics(font)
        
        lines = text.split('\n')
        total_height = 0
        
        for line in lines:
            if not line:
                total_height += fm.height()
                continue
            
            text_width = fm.width(line)
            if text_width <= width:
                total_height += fm.height()
            else:
                num_lines = (text_width + width - 1) // width
                total_height += num_lines * fm.height()
        
        return total_height + 20
    
    @staticmethod
    def calculate_editor_height(editor, available_width):
        if hasattr(editor, 'text'):
            text = editor.toPlainText()
            font = editor.font()
            return SizeCalculator.calculate_text_height(text, available_width - 40, font)
        return 100
    
    @staticmethod
    def calculate_markdown_height(markdown_text, width):
        import markdown
        html = markdown.markdown(markdown_text, extensions=['tables', 'fenced_code'])
        
        from PyQt5.QtWidgets import QTextEdit
        temp_edit = QTextEdit()
        temp_edit.setHtml(html)
        temp_edit.setFixedWidth(width - 40)
        temp_edit.document().setTextWidth(width - 40)
        
        height = temp_edit.document().size().height()
        return max(height + 20, 100)