from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtCore import Qt
import markdown

class SizeCalculator:
    @staticmethod
    def calculate_text_height(text, available_width, font=None):
        """
        精确计算文本高度
        """
        if not text:
            return 0
            
        if font is None:
            font = QFont("Consolas", 10)
            
        fm = QFontMetrics(font)
        
        # 预留边距空间
        actual_width = max(10, available_width - 40)
        
        lines = text.split('\n')
        total_height = 0
        line_spacing = fm.lineSpacing()
        
        for line in lines:
            if not line:
                total_height += line_spacing
                continue
            
            # 使用 boundingRect 计算
            rect = fm.boundingRect(0, 0, actual_width, 10000,
                                    Qt.TextWordWrap | Qt.TextExpandTabs,
                                    line)
            total_height += rect.height()
        
        return total_height + 30
    
    @staticmethod
    def calculate_precise_height(text_edit, available_width):
        """基于 QTextEdit 文档布局高度（available_width 应为视口可用宽度，避免估宽导致行数错误）"""
        if not text_edit:
            return 32

        document = text_edit.document()
        if not document:
            return 32

        margin = 2 * document.documentMargin()
        text_width = max(40, int(available_width - margin))
        document.setTextWidth(text_width)

        layout = document.documentLayout()
        if layout:
            doc_h = layout.documentSize().height()
        else:
            doc_h = document.size().height()

        frame_pad = 6
        return max(28, int(doc_h + margin + frame_pad))
    
    @staticmethod
    def calculate_markdown_height(text, available_width, font=None):
        """简化的 markdown 高度计算"""
        if not text:
            return 150
            
        if font is None:
            font = QFont("Consolas", 10)
            
        return SizeCalculator.calculate_text_height(text, available_width, font)
