from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame, QTreeView, QStackedWidget, QLabel
)
from PyQt5.QtCore import Qt
import os
from components.welcome_page import WelcomePage
from workspace.filtered_file_model import FilteredFileModel
from cells.cell_manager import CellManager


class MainWindowUIMixin:
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)

        self.left_panel = QFrame()
        self.left_panel.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        left_label = QLabel("文件浏览器")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("padding: 10px; font-weight: bold;")
        left_layout.addWidget(left_label)

        self.file_model = FilteredFileModel()
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.hideColumn(1)
        self.file_tree.hideColumn(2)
        self.file_tree.hideColumn(3)
        self.file_tree.doubleClicked.connect(self.on_file_double_clicked)
        left_layout.addWidget(self.file_tree)

        default_path = os.path.expanduser("~")
        self.file_model.setRootPath(default_path)
        self.file_tree.setRootIndex(self.file_model.index(default_path))

        self.right_panel = QFrame()
        self.right_panel.setFrameShape(QFrame.StyledPanel)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()

        self.welcome_page = WelcomePage()
        self.welcome_page.set_theme_manager(self.theme_manager)
        self.welcome_page.create_new_file_requested.connect(self._on_create_new_file_requested)
        self.welcome_page.import_text_requested.connect(self.import_text)
        self.stacked_widget.addWidget(self.welcome_page)

        self.editor_container = QWidget()
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)

        from PyQt5.QtWidgets import QScrollArea
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.cells_container = QWidget()
        self.cells_layout = QVBoxLayout(self.cells_container)
        self.cells_layout.setContentsMargins(10, 10, 10, 10)
        self.cells_layout.setSpacing(5)
        self.cells_layout.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.cells_container)
        editor_layout.addWidget(self.scroll_area)

        self.stacked_widget.addWidget(self.editor_container)

        self.stacked_widget.addWidget(self.recitation_main_page)
        self.stacked_widget.addWidget(self.recitation_quiz_page)

        right_layout.addWidget(self.stacked_widget)

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)

        self.splitter.setSizes([250, 750])
        self.splitter.setCollapsible(0, True)
        self.splitter.setCollapsible(1, False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        self.left_panel.setMinimumWidth(200)
        self.left_panel.setMaximumWidth(500)

        self.main_layout.addWidget(self.splitter)

        self.cell_manager = CellManager(self.cells_layout, self.translation_service, self.recitation_dal)
        self.cell_manager.set_settings_manager(self.settings_manager)
        self.cell_manager.content_changed.connect(self._on_cell_content_changed)
        self.file_service.set_cell_manager(self.cell_manager)

    def _switch_to_welcome_page(self):
        self.stacked_widget.setCurrentIndex(self.PAGE_WELCOME)
        self._update_menu_states()

    def _switch_to_editor_page(self):
        self.stacked_widget.setCurrentIndex(self.PAGE_EDITOR)
        self._update_menu_states()

    def set_theme(self, theme_name):
        self.light_theme_action.setChecked(theme_name == 'light')
        self.dark_theme_action.setChecked(theme_name == 'dark')
        self.theme_manager.set_theme(theme_name)

    def apply_theme(self, theme_name):
        theme = self.theme_manager.get_theme()
        self.cells_container.setStyleSheet(f"background-color: {theme['scroll_area']};")
        self.scroll_area.setStyleSheet(f"background-color: {theme['scroll_area']};")
        self.left_panel.setStyleSheet(f"background-color: {theme['scroll_area']};")
        self.right_panel.setStyleSheet(f"background-color: {theme['scroll_area']};")

        for cell in self.cell_manager.cells:
            cell.apply_theme(theme)
