from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QToolButton
from PyQt5.QtCore import pyqtSignal as Signal, Qt
from utils.size_calculator import SizeCalculator

class BaseCell(QWidget):
    selected = Signal(object)
    run_requested = Signal(object)
    delete_requested = Signal(object)
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
    height_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self.is_selected = False
        self.theme = None
        self.min_height = 100
        self.max_height = 2000
        self.init_ui()
        
    def init_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.gutter_layout = QVBoxLayout()
        self.gutter_layout.setContentsMargins(5, 0, 5, 0)
        self.gutter_layout.setSpacing(2)
        
        self.run_button = QToolButton()
        self.run_button.setText("▶")
        self.run_button.setFixedSize(24, 24)
        self.run_button.clicked.connect(self.on_run_clicked)
        self.gutter_layout.addWidget(self.run_button)
        
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
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        
        self.main_layout.addLayout(self.gutter_layout)
        self.main_layout.addWidget(self.content_area, 1)
        
        self.set_selected(False)
        
    def on_run_clicked(self):
        self.run_requested.emit(self)
        
    def on_delete_clicked(self):
        self.delete_requested.emit(self)
        
    def on_move_up_clicked(self):
        self.move_up_requested.emit(self)
        
    def on_move_down_clicked(self):
        self.move_down_requested.emit(self)
        
    def set_selected(self, selected):
        self.is_selected = selected
        if self.theme:
            if selected:
                self.setStyleSheet(f"background-color: {self.theme['cell_selected']}; border-left: 3px solid {self.theme['cell_border']};")
            else:
                self.setStyleSheet(f"background-color: {self.theme['background']}; border-left: 3px solid transparent;")
        else:
            if selected:
                self.setStyleSheet("background-color: #e8f4fd; border-left: 3px solid #1a73e8;")
            else:
                self.setStyleSheet("background-color: white; border-left: 3px solid transparent;")
            
    def apply_theme(self, theme):
        self.theme = theme
        self.content_area.setStyleSheet(f"background-color: {theme['background']};")
        self.set_selected(self.is_selected)
            
    def mousePressEvent(self, event):
        self.selected.emit(self)
        super().mousePressEvent(event)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_height()
        
    def adjust_height(self):
        pass
        
    def set_min_height(self, height):
        self.min_height = height
        
    def set_max_height(self, height):
        self.max_height = height