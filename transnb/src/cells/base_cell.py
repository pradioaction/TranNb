from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QToolButton, QSizePolicy
from PyQt5.QtCore import pyqtSignal as Signal, Qt
from utils.size_calculator import SizeCalculator

class BaseCell(QWidget):
    selected = Signal(object)
    translate_requested = Signal(object)
    delete_requested = Signal(object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
    
    def __init__(self):
        super().__init__()
        self.is_selected = True
        self.theme = None
        self.min_height = 150
        self.max_height = 3000
        self.translation_service = None
        self.settings_manager = None
        self.gutter_widget = None
        self.init_ui()
        
    def set_translation_service(self, translation_service):
        self.translation_service = translation_service
        
    def set_settings_manager(self, settings_manager):
        self.settings_manager = settings_manager
        
    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
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
        self.translate_requested.emit(self)
        
    def on_delete_clicked(self):
        self.delete_requested.emit(self)
        
    def on_move_up_clicked(self):
        self.move_up_requested.emit(self)
        
    def on_move_down_clicked(self):
        self.move_down_requested.emit(self)
        
    def set_selected(self, selected):
        '''设置单元格是否选中'''
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
        self.theme = theme
        self.content_area.setStyleSheet(f"background-color: {theme['background']};")
        # 确保 gutter 区域保持透明，不被背景色包含
        if self.gutter_widget:
            self.gutter_widget.setStyleSheet("background-color: transparent;")
        self.set_selected(self.is_selected)
            
    def mousePressEvent(self, event):
        # 传递Shift键状态给CellManager
        # 最最简单直接的方法！
        from PyQt5.QtWidgets import QApplication
        # 使用应用程序级别的键盘状态检测
        shift_pressed = bool(QApplication.queryKeyboardModifiers() & Qt.ShiftModifier)
        print(f"[DEBUG BaseCell] shift_pressed: {shift_pressed}")
        self.selected.emit((self, shift_pressed))
        super().mousePressEvent(event)
        
    def adjust_height(self):
        # 基础实现，子类可以覆盖
        self.setMinimumHeight(self.min_height)
        self.setMaximumHeight(self.max_height)
        
    def set_gutter_visible(self, visible):
        """控制左侧按钮区域的显示/隐藏"""
        if self.gutter_widget:
            self.gutter_widget.setVisible(visible)
