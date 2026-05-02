from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal as Signal, QEvent
from PyQt5.QtGui import QFont, QCursor


class ClickableLabel(QLabel):
    """可点击的标签类"""
    
    clicked = Signal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class WelcomePage(QWidget):
    """欢迎页面组件"""
    
    # 信号定义
    create_new_file_requested = Signal()
    import_text_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = None
        self._welcome_text = "欢迎使用翻译笔记本"
        self._hint_text = "点击开始创建文本"
        self._link_text = "新建文件"
        self._import_text = "导入文本"
        self.init_ui()
    
    def set_theme_manager(self, theme_manager):
        """设置主题管理器"""
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
            self.apply_theme(self.theme_manager.get_current_theme_name())
    
    def apply_theme(self, theme_name=None):
        """应用主题"""
        if not self.theme_manager:
            return
        theme = self.theme_manager.get_theme()
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
            }}
        """)
        
        # 应用链接样式
        self._update_link_style()
    
    def _update_link_style(self):
        """更新链接样式"""
        if self.theme_manager:
            theme = self.theme_manager.get_theme()
            link_color = theme.get('primary_button', '#1a73e8')
            hover_color = theme.get('primary_button_hover', '#1557b0')
            
            style = f"""
                ClickableLabel {{
                    color: {link_color};
                    text-decoration: underline;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                    background-color: transparent;
                }}
                ClickableLabel:hover {{
                    color: {hover_color};
                    background-color: rgba(0,0,0,0.05);
                }}
            """
            self.link_label.setStyleSheet(style)
            self.import_label.setStyleSheet(style)
        else:
            # 默认样式
            style = """
                ClickableLabel {
                    color: #1a73e8;
                    text-decoration: underline;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 8px 16px;
                    border-radius: 4px;
                    background-color: transparent;
                }
                ClickableLabel:hover {
                    color: #1557b0;
                    background-color: rgba(0,0,0,0.05);
                }
            """
            self.link_label.setStyleSheet(style)
            self.import_label.setStyleSheet(style)
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # 设置透明背景
        self.setStyleSheet("QWidget { background-color: transparent; }")
        
        # 添加弹性空间
        layout.addStretch()
        
        # 欢迎标题
        self.title_label = QLabel(self._welcome_text)
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.title_label)
        
        # 引导提示
        self.hint_label = QLabel(self._hint_text)
        hint_font = QFont()
        hint_font.setPointSize(14)
        self.hint_label.setFont(hint_font)
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setStyleSheet("color: #888; background-color: transparent;")
        layout.addWidget(self.hint_label)
        
        # 添加间距
        layout.addSpacing(40)
        
        # 新建文件链接（可点击的文本）
        self.link_label = ClickableLabel(self._link_text)
        self.link_label.setAlignment(Qt.AlignCenter)
        self.link_label.clicked.connect(self.create_new_file_requested)
        
        # 导入文本链接（可点击的文本）
        self.import_label = ClickableLabel(self._import_text)
        self.import_label.setAlignment(Qt.AlignCenter)
        self.import_label.clicked.connect(self.import_text_requested)
        
        self._update_link_style()
        
        # 链接居中
        link_layout = QVBoxLayout()
        link_layout.addStretch()
        link_layout.addWidget(self.link_label, 0, Qt.AlignCenter)
        link_layout.addSpacing(10)
        link_layout.addWidget(self.import_label, 0, Qt.AlignCenter)
        link_layout.addStretch()
        
        # 链接容器
        link_container = QWidget()
        link_container.setLayout(link_layout)
        layout.addWidget(link_container)
        
        # 添加弹性空间
        layout.addStretch()
    
    def set_welcome_text(self, text):
        """设置欢迎文案"""
        self._welcome_text = text
        self.title_label.setText(text)
    
    def set_hint_text(self, text):
        """设置引导提示"""
        self._hint_text = text
        self.hint_label.setText(text)
    
    def set_button_text(self, text):
        """设置链接文字（保持方法名兼容）"""
        self._link_text = text
        self.link_label.setText(text)
