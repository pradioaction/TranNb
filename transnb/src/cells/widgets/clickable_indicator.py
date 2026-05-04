from PyQt5.QtWidgets import QFrame, QWidget
from PyQt5.QtCore import pyqtSignal as Signal, QEvent
from typing import Optional


class ClickableIndicatorLine(QFrame):
    """可点击的指示线组件，用于折叠/展开"""
    double_clicked = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedWidth(4)
        self.setStyleSheet("background-color: transparent;")
        self.setMouseTracking(True)
        self.default_color = "transparent"
        self.hover_color = "#1a73e8"
        
    def set_colors(self, default: str, hover: str) -> None:
        self.default_color = default
        self.hover_color = hover
        self.setStyleSheet(f"background-color: {self.default_color};")
        
    def enterEvent(self, event: QEvent) -> None:
        self.setStyleSheet(f"background-color: {self.hover_color};")
        super().enterEvent(event)
        
    def leaveEvent(self, event: QEvent) -> None:
        self.setStyleSheet(f"background-color: {self.default_color};")
        super().leaveEvent(event)
        
    def mouseDoubleClickEvent(self, event: QEvent) -> None:
        self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)
