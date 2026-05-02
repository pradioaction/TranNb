"""统一 QMessageBox 样式，避免深色主题下正文与背景同色（看似全黑）。"""
from typing import Any, Dict, Optional

from PyQt5.QtWidgets import QMessageBox


def apply_message_box_theme(
    msg: QMessageBox,
    *,
    theme_manager=None,
    theme_dict: Optional[Dict[str, Any]] = None,
) -> None:
    theme = theme_dict
    if theme is None and theme_manager is not None:
        theme = theme_manager.get_theme()
    if theme:
        bg = theme.get("dialog_background", "#ffffff")
        fg = theme.get("foreground", "#000000")
    else:
        bg = "#f0f0f0"
        fg = "#202020"
    msg.setStyleSheet(
        f"QMessageBox {{ background-color: {bg}; }}"
        f"QMessageBox QLabel {{ color: {fg}; background-color: transparent; }}"
        f"QPushButton {{ min-width: 72px; padding: 4px 12px; }}"
    )


def show_warning(parent, title: str, text: str, *, theme_manager=None, theme_dict=None) -> None:
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    apply_message_box_theme(msg, theme_manager=theme_manager, theme_dict=theme_dict)
    msg.exec_()


def show_information(parent, title: str, text: str, *, theme_manager=None, theme_dict=None) -> None:
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setStandardButtons(QMessageBox.Ok)
    apply_message_box_theme(msg, theme_manager=theme_manager, theme_dict=theme_dict)
    msg.exec_()
