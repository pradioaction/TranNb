from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget,
    QListWidgetItem, QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal as Signal
import re
from utils.message_box_theme import show_information, show_warning


class UrlValidator:
    @staticmethod
    def is_valid(url):
        if not url:
            return True
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S*)?$', re.IGNORECASE)
        return bool(url_pattern.match(url))


class EnvVarNameDialog(QDialog):
    """登记单个环境变量「名称」与可选说明。"""

    def __init__(self, title, initial_name="", initial_desc="", theme_manager=None, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setWindowTitle(title)
        self.setMinimumWidth(380)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setText(initial_name)
        self.name_edit.setPlaceholderText("例如 ARK_API_KEY")
        self.desc_edit = QLineEdit()
        self.desc_edit.setText(initial_desc)
        self.desc_edit.setPlaceholderText("可选，便于识别用途")
        form.addRow("变量名:", self.name_edit)
        form.addRow("说明:", self.desc_edit)
        layout.addLayout(form)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("saveBtn")
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)
        if self.theme_manager:
            self._apply_theme()

    def _apply_theme(self):
        theme = self.theme_manager.get_theme()
        self.setStyleSheet(f"""
            QDialog {{ background-color: {theme['dialog_background']}; }}
            QLabel {{ color: {theme['foreground']}; }}
            QLineEdit {{
                background-color: {theme['input_background']};
                color: {theme['foreground']};
                border: 1px solid {theme['input_border']};
                padding: 5px;
                border-radius: 3px;
            }}
            QPushButton {{
                background-color: {theme['button_background']};
                color: {theme['foreground']};
                border: 1px solid {theme['input_border']};
                padding: 6px 15px;
                border-radius: 3px;
            }}
            QPushButton#saveBtn {{
                background-color: {theme['primary_button']};
                color: white;
            }}
        """)

    def values(self):
        return self.name_edit.text().strip(), self.desc_edit.text().strip()


class EnvVarsEditorWidget(QWidget):
    """在设置中维护 API 密钥对应的环境变量名称列表（不保存密钥本身）。"""

    entries_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_manager = None
        self._entries = []
        self.init_ui()

    def set_theme_manager(self, theme_manager):
        self.theme_manager = theme_manager
        if self.theme_manager:
            self.theme_manager.theme_changed.connect(self.apply_theme)
            self.apply_theme()

    def apply_theme(self, theme_name=None):
        if not self.theme_manager:
            return
        theme = self.theme_manager.get_theme()
        self.setStyleSheet(f"""
            QWidget {{ background-color: transparent; color: {theme['foreground']}; }}
            QListWidget {{
                background-color: {theme['input_background']};
                border: 1px solid {theme['input_border']};
                border-radius: 5px;
                color: {theme['foreground']};
            }}
            QListWidget::item {{ padding: 8px; }}
            QListWidget::item:selected {{
                background-color: {theme['list_item_selected']};
                color: white;
            }}
            QPushButton {{
                background-color: {theme['button_background']};
                color: {theme['foreground']};
                border: 1px solid {theme['input_border']};
                padding: 6px 15px;
                border-radius: 3px;
            }}
            QPushButton:hover {{ background-color: {theme['button_hover']}; }}
            QLabel {{ color: {theme['foreground']}; }}
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        hint = QLabel(
            "下列条目仅保存「变量名」。请在本机环境（系统变量或启动脚本）中配置真实密钥值；"
            "自定义 Ark 模型可从下拉中选此处登记的名称，也可手动输入未登记的变量名。"
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.list_w = QListWidget()
        layout.addWidget(self.list_w)
        row = QHBoxLayout()
        row.addStretch()
        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self._add_entry)
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._edit_entry)
        self.del_btn = QPushButton("删除")
        self.del_btn.clicked.connect(self._del_entry)
        row.addWidget(self.add_btn)
        row.addWidget(self.edit_btn)
        row.addWidget(self.del_btn)
        layout.addLayout(row)

    def set_entries(self, entries):
        self._entries = [dict(e) for e in (entries or [])]
        self._refresh_list()

    def get_entries(self):
        return [dict(e) for e in self._entries]

    def _refresh_list(self):
        self.list_w.clear()
        for e in self._entries:
            name = (e.get("name") or "").strip()
            desc = (e.get("description") or "").strip()
            label = name + (f" — {desc}" if desc else "")
            item = QListWidgetItem(label or "(未命名)")
            item.setData(Qt.UserRole, e)
            self.list_w.addItem(item)

    def _valid_var_name(self, name: str) -> bool:
        return bool(name and re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name))

    def _add_entry(self):
        dlg = EnvVarNameDialog("添加环境变量名", theme_manager=self.theme_manager, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return
        name, desc = dlg.values()
        if not self._valid_var_name(name):
            show_warning(self, "错误", "变量名不能为空，且仅限字母、数字、下划线，不能以数字开头。", theme_manager=self.theme_manager)
            return
        if any((e.get("name") or "").strip() == name for e in self._entries):
            show_warning(self, "错误", "该变量名已存在。", theme_manager=self.theme_manager)
            return
        self._entries.append({"name": name, "description": desc})
        self._refresh_list()
        self.entries_changed.emit()

    def _edit_entry(self):
        row = self.list_w.currentRow()
        if row < 0 or row >= len(self._entries):
            return
        cur = self._entries[row]
        dlg = EnvVarNameDialog(
            "编辑环境变量名",
            initial_name=cur.get("name", ""),
            initial_desc=cur.get("description", ""),
            theme_manager=self.theme_manager,
            parent=self,
        )
        if dlg.exec_() != QDialog.Accepted:
            return
        name, desc = dlg.values()
        if not self._valid_var_name(name):
            show_warning(self, "错误", "变量名不能为空，且仅限字母、数字、下划线，不能以数字开头。", theme_manager=self.theme_manager)
            return
        for i, e in enumerate(self._entries):
            if i != row and (e.get("name") or "").strip() == name:
                show_warning(self, "错误", "该变量名已被其他条目使用。", theme_manager=self.theme_manager)
                return
        self._entries[row] = {"name": name, "description": desc}
        self._refresh_list()
        self.entries_changed.emit()

    def _del_entry(self):
        row = self.list_w.currentRow()
        if row < 0 or row >= len(self._entries):
            return
        name = (self._entries[row].get("name") or "").strip()
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除环境变量名「{name}」吗？（不影响系统环境，仅从本列表移除）",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        del self._entries[row]
        self._refresh_list()
        self.entries_changed.emit()


__all__ = ['UrlValidator', 'EnvVarNameDialog', 'EnvVarsEditorWidget']
