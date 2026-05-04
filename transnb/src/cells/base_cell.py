from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolButton, QSizePolicy
from PyQt5.QtCore import pyqtSignal as Signal, Qt
from utils.size_calculator import SizeCalculator
from .cell_config import CellConfig


class BaseCell(QWidget):
    """单元格基类 - 定义所有单元格的通用接口
    
    子类应该实现以下方法：
    - get_content() -> str
    - set_content(content: str)
    - get_output() -> str
    - set_output(content: str)
    - translate()
    """
    
    selected = Signal(object)
    translate_requested = Signal(object)
    delete_requested = Signal(object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
    
    def __init__(self):
        super().__init__()
        self.is_selected = True
        self.theme = None
        self.min_height = CellConfig.MIN_HEIGHT
        self.max_height = CellConfig.MAX_HEIGHT
        self.translation_service = None
        self.settings_manager = None
        self.gutter_widget = None
        
        # 层级关系相关属性
        self.cell_id: str = None
        self.parent_cell_id: str = None
        self.indent_level: int = 0
        self.is_dependent_collapsed: bool = False
        
        # 初始化UI
        self.init_ui()
    
    def get_content(self) -> str:
        """获取单元格内容 - 子类应该实现此方法"""
        raise NotImplementedError("子类必须实现 get_content() 方法")
    
    def set_content(self, content: str) -> None:
        """设置单元格内容 - 子类应该实现此方法"""
        raise NotImplementedError("子类必须实现 set_content() 方法")
    
    def get_output(self) -> str:
        """获取单元格输出内容 - 子类应该实现此方法"""
        raise NotImplementedError("子类必须实现 get_output() 方法")
    
    def set_output(self, content: str) -> None:
        """设置单元格输出内容 - 子类应该实现此方法"""
        raise NotImplementedError("子类必须实现 set_output() 方法")
    
    def translate(self) -> None:
        """执行翻译操作 - 子类应该实现此方法"""
        raise NotImplementedError("子类必须实现 translate() 方法")
    
    def set_translation_service(self, translation_service):
        """设置翻译服务"""
        self.translation_service = translation_service
    
    def set_settings_manager(self, settings_manager):
        """设置设置管理器"""
        self.settings_manager = settings_manager
    
    def init_ui(self):
        """初始化UI"""
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 缩进占位符（用于单元格从属时的整体缩进）
        self.indent_widget = QWidget()
        self.indent_widget.setFixedWidth(0)  # 默认没有缩进
        self.main_layout.addWidget(self.indent_widget)
        
        # 左侧按钮容器
        self.gutter_widget = QWidget()
        self.gutter_layout = QVBoxLayout(self.gutter_widget)
        self.gutter_layout.setContentsMargins(5, 0, 5, 0)
        self.gutter_layout.setSpacing(2)
        
        self.translate_button = QToolButton()
        self.translate_button.setText("🌐")
        self.translate_button.setFixedSize(24, 24)
        self.translate_button.clicked.connect(self.on_translate_clicked)
        self.gutter_layout.addWidget(self.translate_button)
        
        self.move_up_button = QToolButton()
        self.move_up_button.setText("↑")
        self.move_up_button.setFixedSize(24, 20)
        self.move_up_button.clicked.connect(self.on_move_up_clicked)
        self.gutter_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QToolButton()
        self.move_down_button.setText("↓")
        self.move_down_button.setFixedSize(24, 20)
        self.move_down_button.clicked.connect(self.on_move_down_clicked)
        self.gutter_layout.addWidget(self.move_down_button)
        
        self.delete_button = QToolButton()
        self.delete_button.setText("✕")
        self.delete_button.setFixedSize(24, 20)
        self.delete_button.clicked.connect(self.on_delete_clicked)
        self.gutter_layout.addWidget(self.delete_button)
        
        self.gutter_layout.addStretch(1)
        
        self.content_area = QWidget()
        # 设置大小策略，确保垂直方向可以扩展
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.content_area.setSizePolicy(size_policy)
        
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        
        self.main_layout.addWidget(self.gutter_widget)
        self.main_layout.addWidget(self.content_area, 1)
        
        self.set_selected(False)

        # 确保 widget 本身背景透明
        self.setStyleSheet("background-color: transparent;")
    
    def on_translate_clicked(self):
        """翻译按钮点击事件"""
        self.translate_requested.emit(self)
    
    def on_delete_clicked(self):
        """删除按钮点击事件"""
        self.delete_requested.emit(self)
    
    def on_move_up_clicked(self):
        """上移按钮点击事件"""
        self.move_up_requested.emit(self)
    
    def on_move_down_clicked(self):
        """下移按钮点击事件"""
        self.move_down_requested.emit(self)
    
    def set_selected(self, selected: bool):
        """设置单元格是否选中"""
        if self.is_selected == selected:
            return
        
        self.is_selected = selected
        # 只对 content_area 设置背景色，保持 gutter 区域透明（漂浮效果）
        if self.theme:
            if selected:
                self.content_area.setStyleSheet(f"background-color: {self.theme['cell_selected']};")
            else:
                self.content_area.setStyleSheet(f"background-color: {self.theme['background']};")
        else:
            if selected:
                self.content_area.setStyleSheet("background-color: #e8f4fd;")
            else:
                self.content_area.setStyleSheet("background-color: white;")
            
    def apply_theme(self, theme):
        """应用主题"""
        self.theme = theme
        self.content_area.setStyleSheet(f"background-color: {theme['background']};")
        # 确保 gutter 区域保持透明，不被背景色包含
        if self.gutter_widget:
            self.gutter_widget.setStyleSheet("background-color: transparent;")
        self.set_selected(self.is_selected)
            
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        # 传递Shift键状态给CellManager
        from PyQt5.QtWidgets import QApplication
        # 使用应用程序级别的键盘状态检测
        shift_pressed = bool(QApplication.queryKeyboardModifiers() & Qt.ShiftModifier)
        self.selected.emit((self, shift_pressed))
        super().mousePressEvent(event)
        
    def adjust_height(self):
        """调整单元格高度"""
        # 基础实现，子类可以覆盖
        self.setMinimumHeight(self.min_height)
        self.setMaximumHeight(self.max_height)
        
    def set_gutter_visible(self, visible: bool):
        """控制左侧按钮区域的显示/隐藏"""
        if self.gutter_widget:
            self.gutter_widget.setVisible(visible)
    
    def set_indent(self, level: int):
        """设置单元格的缩进级别
        
        Args:
            level: 缩进级别（0 表示顶级，1 表示一级从属）
        """
        self.indent_level = level
        # 计算缩进宽度：基础 20 + 级别 * 30
        indent_width = level * CellConfig.INDENT_LEVEL_STEP
        self.indent_widget.setFixedWidth(indent_width)
        # 内容区域保持原来的基础边距
        self.content_layout.setContentsMargins(5, 5, 5, 5)
    
    def set_dependent_collapsed(self, collapsed: bool):
        """设置单元格是否作为从属折叠
        
        Args:
            collapsed: 是否折叠
        """
        self.is_dependent_collapsed = collapsed
        self.setVisible(not collapsed)
    

