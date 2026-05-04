from PyQt5.QtWidgets import (
    QMenuBar, QToolBar, QStatusBar, QAction, QMessageBox, QLabel, QDialog, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtCore import Qt
from cells.cell_config import CellConfig


class MainWindowMenusMixin:
    def init_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")
        self.new_action = QAction("新建", self)
        self.new_action.setShortcut(QKeySequence("Ctrl+N"))
        self.new_action.triggered.connect(self.new_file)
        file_menu.addAction(self.new_action)

        self.open_action = QAction("打开", self)
        self.open_action.setShortcut(QKeySequence("Ctrl+O"))
        self.open_action.triggered.connect(self.open_file)
        file_menu.addAction(self.open_action)

        self.open_folder_action = QAction("打开文件夹", self)
        self.open_folder_action.setShortcut(QKeySequence("Ctrl+K"))
        self.open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(self.open_folder_action)

        self.import_text_action = QAction("导入文本", self)
        self.import_text_action.setShortcut(QKeySequence("Ctrl+I"))
        self.import_text_action.triggered.connect(self.import_text)
        file_menu.addAction(self.import_text_action)

        self.import_from_clipboard_action = QAction("从粘贴板导入", self)
        self.import_from_clipboard_action.setShortcut(QKeySequence("Ctrl+Shift+V"))
        self.import_from_clipboard_action.triggered.connect(self.import_from_clipboard)
        file_menu.addAction(self.import_from_clipboard_action)

        self.save_action = QAction("保存", self)
        self.save_action.setShortcut(QKeySequence("Ctrl+S"))
        self.save_action.triggered.connect(self.save_file)
        file_menu.addAction(self.save_action)

        self.save_as_action = QAction("另存为", self)
        self.save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(self.save_as_action)

        edit_menu = menubar.addMenu("编辑")
        self.undo_action = QAction("撤销", self)
        self.undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("重做", self)
        self.redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        edit_menu.addAction(self.redo_action)

        edit_menu.addSeparator()

        self.translate_action = QAction("翻译选中", self)
        self.translate_action.setShortcut(QKeySequence("Ctrl+Enter"))
        self.translate_action.triggered.connect(self.translate_current_cell)
        edit_menu.addAction(self.translate_action)

        self.translate_all_action = QAction("翻译全部", self)
        self.translate_all_action.setShortcut(QKeySequence("Ctrl+Shift+Enter"))
        self.translate_all_action.triggered.connect(self.translate_all_cells)
        edit_menu.addAction(self.translate_all_action)

        edit_menu.addSeparator()

        self.insert_above_action = QAction("上方插入", self)
        self.insert_above_action.setShortcut(QKeySequence("Ctrl+A"))
        self.insert_above_action.triggered.connect(self.insert_cell_above)
        edit_menu.addAction(self.insert_above_action)

        self.insert_below_action = QAction("下方插入", self)
        self.insert_below_action.setShortcut(QKeySequence("Ctrl+B"))
        self.insert_below_action.triggered.connect(self.insert_cell_below)
        edit_menu.addAction(self.insert_below_action)

        self.delete_action = QAction("删除", self)
        self.delete_action.setShortcut(QKeySequence("Delete"))
        self.delete_action.triggered.connect(self.delete_selected_cell)
        edit_menu.addAction(self.delete_action)

        self.copy_cell_action = QAction("复制单元格", self)
        self.copy_cell_action.setShortcut(QKeySequence(CellConfig.SHORTCUT_COPY_CELL))
        self.copy_cell_action.triggered.connect(self.copy_selected_cell)
        edit_menu.addAction(self.copy_cell_action)

        self.split_cell_action = QAction("拆分单元格", self)
        self.split_cell_action.setShortcut(QKeySequence(CellConfig.SHORTCUT_SPLIT_CELL))
        self.split_cell_action.triggered.connect(self.split_selected_cell)
        edit_menu.addAction(self.split_cell_action)

        hierarchy_menu = edit_menu.addMenu("层级关系")

        self.set_dependent_action = QAction("设为上一个的从属", self)
        self.set_dependent_action.setShortcut(QKeySequence(CellConfig.SHORTCUT_SET_DEPENDENT))
        self.set_dependent_action.triggered.connect(self.set_selected_cell_dependent)
        hierarchy_menu.addAction(self.set_dependent_action)

        hierarchy_menu.addSeparator()

        self.make_dependent_action = QAction("设为从属", self)
        self.make_dependent_action.triggered.connect(self.make_cell_dependent)
        hierarchy_menu.addAction(self.make_dependent_action)

        self.remove_dependency_action = QAction("取消从属", self)
        self.remove_dependency_action.triggered.connect(self.remove_cell_dependency)
        hierarchy_menu.addAction(self.remove_dependency_action)

        edit_menu.addSeparator()

        self.merge_cells_action = QAction("合并选中单元格", self)
        self.merge_cells_action.setShortcut(QKeySequence(CellConfig.SHORTCUT_MERGE_CELLS))
        self.merge_cells_action.triggered.connect(self.merge_selected_cells)
        edit_menu.addAction(self.merge_cells_action)

        edit_menu.addSeparator()

        collapse_menu = edit_menu.addMenu("折叠/展开")

        self.toggle_cell_collapse_selected_action = QAction("选中折叠/展开单元格", self)
        self.toggle_cell_collapse_selected_action.setShortcut(QKeySequence(CellConfig.SHORTCUT_TOGGLE_CELL_SELECTED))
        self.toggle_cell_collapse_selected_action.triggered.connect(self.toggle_cell_collapse_selected)
        collapse_menu.addAction(self.toggle_cell_collapse_selected_action)

        self.toggle_cell_collapse_all_action = QAction("全部折叠/展开单元格", self)
        self.toggle_cell_collapse_all_action.setShortcut(QKeySequence(CellConfig.SHORTCUT_TOGGLE_CELL_ALL))
        self.toggle_cell_collapse_all_action.triggered.connect(self.toggle_cell_collapse_all)
        collapse_menu.addAction(self.toggle_cell_collapse_all_action)

        collapse_menu.addSeparator()

        self.toggle_input_collapse_selected_action = QAction("选中折叠/展开原文", self)
        self.toggle_input_collapse_selected_action.setShortcut(QKeySequence("Ctrl+Q"))
        self.toggle_input_collapse_selected_action.triggered.connect(self.toggle_input_collapse_selected)
        collapse_menu.addAction(self.toggle_input_collapse_selected_action)

        self.toggle_input_collapse_all_action = QAction("全部折叠/展开原文", self)
        self.toggle_input_collapse_all_action.setShortcut(QKeySequence("Ctrl+Shift+Q"))
        self.toggle_input_collapse_all_action.triggered.connect(self.toggle_input_collapse_all)
        collapse_menu.addAction(self.toggle_input_collapse_all_action)

        collapse_menu.addSeparator()

        self.toggle_output_collapse_selected_action = QAction("选中折叠/展开结果", self)
        self.toggle_output_collapse_selected_action.setShortcut(QKeySequence("Ctrl+W"))
        self.toggle_output_collapse_selected_action.triggered.connect(self.toggle_output_collapse_selected)
        collapse_menu.addAction(self.toggle_output_collapse_selected_action)

        self.toggle_output_collapse_all_action = QAction("全部折叠/展开结果", self)
        self.toggle_output_collapse_all_action.setShortcut(QKeySequence("Ctrl+Shift+W"))
        self.toggle_output_collapse_all_action.triggered.connect(self.toggle_output_collapse_all)
        collapse_menu.addAction(self.toggle_output_collapse_all_action)

        view_menu = menubar.addMenu("查看")
        self.light_theme_action = QAction("浅色主题", self, checkable=True)
        self.light_theme_action.setChecked(True)
        self.light_theme_action.triggered.connect(lambda: self.set_theme('light'))
        view_menu.addAction(self.light_theme_action)

        self.dark_theme_action = QAction("深色主题", self, checkable=True)
        self.dark_theme_action.triggered.connect(lambda: self.set_theme('dark'))
        view_menu.addAction(self.dark_theme_action)

        recitation_menu = menubar.addMenu("背诵模式")
        self.recitation_action = QAction("打开背诵模式", self)
        self.recitation_action.setShortcut(QKeySequence("Ctrl+Shift+B"))
        self.recitation_action.triggered.connect(self._open_recitation_mode)
        recitation_menu.addAction(self.recitation_action)

        settings_menu = menubar.addMenu("设置")
        self.settings_action = QAction("打开设置", self)
        self.settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(self.settings_action)

        help_menu = menubar.addMenu("帮助")
        self.about_action = QAction("关于", self)
        self.about_action.triggered.connect(self.show_about)
        help_menu.addAction(self.about_action)

        help_menu.addSeparator()

        self.shortcuts_action = QAction("快捷键列表", self)
        self.shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(self.shortcuts_action)

    def init_toolbar(self):
        toolbar = QToolBar("工具栏")
        self.addToolBar(toolbar)

        toolbar.addAction(self.new_action)
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)

        toolbar.addSeparator()

        toolbar.addAction(self.translate_action)
        toolbar.addAction(self.translate_all_action)

        toolbar.addSeparator()

        self.insert_markdown_action = QAction("插入单元格", self)
        self.insert_markdown_action.triggered.connect(lambda: self.insert_cell_below())
        toolbar.addAction(self.insert_markdown_action)

        toolbar.addAction(self.delete_action)
        toolbar.addAction(self.copy_cell_action)
        toolbar.addAction(self.split_cell_action)
        toolbar.addAction(self.merge_cells_action)

        toolbar.addSeparator()

        toolbar.addAction(self.toggle_input_collapse_all_action)
        toolbar.addAction(self.toggle_output_collapse_all_action)

    def init_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("padding: 0 10px;")
        self.status_bar.addWidget(self.status_label)

    def _update_menu_states(self):
        is_editor_page = self.stacked_widget.currentIndex() == self.PAGE_EDITOR
        is_file_open = self.file_service.is_file_open()

        self.save_action.setEnabled(is_file_open)
        self.save_as_action.setEnabled(is_editor_page)
        self.import_text_action.setEnabled(True)
        self.import_from_clipboard_action.setEnabled(True)

        self.undo_action.setEnabled(is_editor_page)
        self.redo_action.setEnabled(is_editor_page)
        self.translate_action.setEnabled(is_editor_page)
        self.translate_all_action.setEnabled(is_editor_page)
        self.insert_above_action.setEnabled(is_editor_page)
        self.insert_below_action.setEnabled(is_editor_page)
        self.delete_action.setEnabled(is_editor_page)

        self.toggle_input_collapse_all_action.setEnabled(is_editor_page)
        self.toggle_output_collapse_all_action.setEnabled(is_editor_page)
        self.toggle_input_collapse_selected_action.setEnabled(is_editor_page)
        self.toggle_output_collapse_selected_action.setEnabled(is_editor_page)

    def show_shortcuts(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("快捷键列表")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout(dialog)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["快捷键", "功能"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        shortcuts_data = [
            ("Ctrl+N", "新建文件"),
            ("Ctrl+O", "打开文件"),
            ("Ctrl+K", "打开文件夹（工作区）"),
            ("Ctrl+I", "导入文本"),
            ("Ctrl+Shift+V", "从粘贴板导入"),
            ("Ctrl+S", "保存文件"),
            ("Ctrl+Enter", "翻译选中单元格"),
            ("Ctrl+Shift+Enter", "翻译全部单元格"),
            ("Ctrl+A", "上方插入单元格"),
            ("Ctrl+B", "下方插入单元格"),
            ("Delete", "删除选中单元格"),
            ("Ctrl+D", "复制单元格"),
            ("Ctrl+-", "拆分单元格"),
            ("Ctrl+Shift+B", "打开背诵模式"),
            ("Ctrl+Z", "撤销（预留）"),
            ("Ctrl+Y", "重做（预留）"),
            ("Ctrl+Shift+Q", "全部折叠/展开原文"),
            ("Ctrl+Shift+W", "全部折叠/展开结果"),
            ("Ctrl+Q", "选中折叠/展开原文"),
            ("Ctrl+W", "选中折叠/展开结果"),
            ("Shift+↑", "向上多选单元格"),
            ("Shift+↓", "向下多选单元格"),
            ("Shift+点击", "按住Shift点击鼠标多选单元格"),
            ("↑", "选择上一个单元格"),
            ("↓", "选择下一个单元格")
        ]

        table.setRowCount(len(shortcuts_data))

        for row, (shortcut, description) in enumerate(shortcuts_data):
            shortcut_item = QTableWidgetItem(shortcut)
            shortcut_item.setFlags(shortcut_item.flags() & ~Qt.ItemIsEditable)
            shortcut_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 0, shortcut_item)

            desc_item = QTableWidgetItem(description)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 1, desc_item)

        layout.addWidget(table)
        dialog.exec_()

    def show_about(self):
        QMessageBox.about(self, "关于", "翻译笔记本\n\n一个用于翻译的笔记本应用")
