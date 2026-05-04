from PyQt5.QtWidgets import QTextEdit, QMenu, QAction, QWidget
from PyQt5.QtCore import pyqtSignal as Signal, QEvent
from PyQt5.QtGui import QTextCursor
from typing import Optional


class ClickableTextEdit(QTextEdit):
    """可点击的文本编辑框组件，支持双击和右键菜单"""
    double_clicked = Signal()
    collect_word = Signal(str)
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
    def mouseDoubleClickEvent(self, event: QEvent) -> None:
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)
        
    def contextMenuEvent(self, event: QEvent) -> None:
        selected_text = self.textCursor().selectedText().strip()
        menu = QMenu(self)
        
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self.copy)
        copy_action.setEnabled(selected_text != "")
        menu.addAction(copy_action)
        
        paste_action = QAction("粘贴", self)
        paste_action.triggered.connect(self.paste)
        menu.addAction(paste_action)
        
        menu.addSeparator()
        
        if selected_text:
            collect_action = QAction("收藏单词", self)
            collect_action.triggered.connect(lambda: self.collect_word.emit(selected_text))
            menu.addAction(collect_action)
        
        menu.exec_(event.globalPos())
        
    def get_cursor_position(self) -> int:
        """获取当前光标在文本中的位置"""
        return self.textCursor().position()
    
    def get_text_before_cursor(self) -> str:
        """获取光标前面的文本内容"""
        full_text = self.toPlainText()
        pos = self.textCursor().position()
        return full_text[:pos]
    
    def get_text_after_cursor(self) -> str:
        """获取光标后面的文本内容"""
        full_text = self.toPlainText()
        pos = self.textCursor().position()
        return full_text[pos:]
