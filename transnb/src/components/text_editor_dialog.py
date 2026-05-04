from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QInputDialog, QMessageBox
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt

class TextEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文本编辑器 - 从粘贴板导入")
        self.setMinimumSize(800, 600)
        self.edited_text = ""
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 提示标签
        info_label = QLabel("请编辑文本，然后点击\"确认导入\"继续。")
        layout.addWidget(info_label)
        
        # 文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在这里粘贴或编辑文本...")
        layout.addWidget(self.text_edit)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        # 清空按钮
        self.clear_button = QPushButton("清空")
        self.clear_button.clicked.connect(self.text_edit.clear)
        button_layout.addWidget(self.clear_button)
        
        button_layout.addStretch()
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # 确认按钮
        self.confirm_button = QPushButton("确认导入")
        self.confirm_button.setDefault(True)
        self.confirm_button.clicked.connect(self.on_confirm)
        button_layout.addWidget(self.confirm_button)
        
        layout.addLayout(button_layout)
    
    def set_text(self, text):
        """设置编辑器中的文本"""
        self.text_edit.setPlainText(text)
    
    def get_text(self):
        """获取编辑器中的文本"""
        return self.text_edit.toPlainText()
    
    def on_confirm(self):
        """确认导入"""
        text = self.get_text().strip()
        if not text:
            QMessageBox.warning(self, "提示", "文本内容不能为空")
            return
        
        self.edited_text = text
        self.accept()
