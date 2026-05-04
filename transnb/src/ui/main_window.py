from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, Qt
import os
import logging

logger = logging.getLogger(__name__)

from utils.theme_manager import ThemeManager
from settingmanager.settings_manager import SettingsManager
from components.settings_dialog import SettingsDialog
from components.text_editor_dialog import TextEditorDialog
from translation.translation_service import TranslationService
from workspace.workspace_manager import WorkspaceManager
from workspace.file_service import FileService
from recitation import RecitationMainPage, QuizPage

from .main_window_menus import MainWindowMenusMixin
from .main_window_ui import MainWindowUIMixin
from .main_window_file_ops import MainWindowFileOpsMixin
from .main_window_recitation import MainWindowRecitationMixin
from .main_window_actions import MainWindowActionsMixin


class MainWindow(
    QMainWindow,
    MainWindowMenusMixin,
    MainWindowUIMixin,
    MainWindowFileOpsMixin,
    MainWindowRecitationMixin,
    MainWindowActionsMixin
):
    PAGE_WELCOME = 0
    PAGE_EDITOR = 1
    PAGE_RECITATION_MAIN = 2
    PAGE_RECITATION_QUIZ = 3

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TransNb")
        self.setGeometry(100, 100, 1200, 800)

        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logob.png')
        self.setWindowIcon(QIcon(icon_path))
        self._active_workers = []

        self.theme_manager = ThemeManager()
        self.theme_manager.theme_changed.connect(self.apply_theme)

        self.settings_manager = SettingsManager()

        self.translation_service = TranslationService()
        self.translation_service.set_settings_manager(self.settings_manager)

        self.workspace_manager = WorkspaceManager(self.settings_manager)
        self.workspace_manager.workspace_changed.connect(self._on_workspace_changed)
        self.workspace_manager.files_changed.connect(self._on_files_changed)

        self.file_service = FileService(self.workspace_manager)
        self.file_service.file_opened.connect(self._on_file_opened)
        self.file_service.file_saved.connect(self._on_file_saved)
        self.file_service.file_closed.connect(self._on_file_closed)
        self.file_service.file_modified.connect(self._on_file_modified)
        self.file_service.error_occurred.connect(self._on_file_error)

        self.recitation_main_page = RecitationMainPage()
        self.recitation_quiz_page = QuizPage()

        self._init_recitation()

        self.recitation_main_page.set_dependencies(
            self.recitation_dal,
            self.recitation_path_manager,
            self.recitation_study_service,
            self.recitation_book_service
        )
        self.recitation_main_page.generate_article_requested.connect(
            self._on_generate_article_requested
        )
        self.recitation_main_page.start_quiz_requested.connect(
            self._on_start_quiz_requested
        )
        self.recitation_main_page.back_requested.connect(self._on_recitation_back)
        self.recitation_main_page.settings_requested.connect(self.open_settings)

        self.recitation_quiz_page.set_dependencies(
            self.recitation_dal,
            self.recitation_path_manager
        )
        self.recitation_quiz_page.finished.connect(self._on_quiz_finished)
        self.recitation_quiz_page.back_requested.connect(self._on_recitation_back)

        self.init_ui()
        self.init_menus()
        self.init_toolbar()
        self.init_statusbar()

        self._update_menu_states()
        self.restore_workspace()

    def closeEvent(self, event):
        if hasattr(self, 'recitation_main_page'):
            self.recitation_main_page._cleanup_workers()

        for worker in self._active_workers:
            if worker and worker.isRunning():
                worker.quit()
                worker.wait(1000)

        if not self._check_unsaved_changes():
            event.ignore()
            return

        self.settings_manager.set_current_file(self.file_service.get_current_file() or "")
        event.accept()

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_has_shown'):
            self._has_shown = True

    def open_settings(self):
        dialog = SettingsDialog(self.settings_manager, self.theme_manager, self.translation_service, self)
        dialog.exec_()

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()

        if self.stacked_widget.currentIndex() == self.PAGE_EDITOR:
            if not modifiers and key == Qt.Key_Up:
                if self.cell_manager.selected_index > 0:
                    new_index = self.cell_manager.selected_index - 1
                    self.cell_manager.select_cell(new_index)

            if not modifiers and key == Qt.Key_Down:
                if self.cell_manager.selected_index < len(self.cell_manager.cells) - 1:
                    new_index = self.cell_manager.selected_index + 1
                    self.cell_manager.select_cell(new_index)

            if modifiers & Qt.ShiftModifier and key == Qt.Key_Up:
                if self.cell_manager.selected_index > 0:
                    new_index = self.cell_manager.selected_index - 1
                    if self.cell_manager.selected_indices:
                        from_index = self.cell_manager.selected_index
                        self.cell_manager.select_cell_range(from_index, new_index)
                    else:
                        self.cell_manager.select_cell_range(new_index, self.cell_manager.selected_index)

            if modifiers & Qt.ShiftModifier and key == Qt.Key_Down:
                if self.cell_manager.selected_index < len(self.cell_manager.cells) - 1:
                    new_index = self.cell_manager.selected_index + 1
                    if self.cell_manager.selected_indices:
                        from_index = self.cell_manager.selected_index
                        self.cell_manager.select_cell_range(from_index, new_index)
                    else:
                        self.cell_manager.select_cell_range(self.cell_manager.selected_index, new_index)

            if modifiers & Qt.ControlModifier and key == Qt.Key_Q:
                self.toggle_input_collapse_selected()
                return

            if modifiers & Qt.ControlModifier and key == Qt.Key_W:
                self.toggle_output_collapse_selected()
                return

            if (modifiers & Qt.ControlModifier and modifiers & Qt.ShiftModifier
                    and key == Qt.Key_Q):
                self.toggle_input_collapse_all()
                return

            if (modifiers & Qt.ControlModifier and modifiers & Qt.ShiftModifier
                    and key == Qt.Key_W):
                self.toggle_output_collapse_all()
                return

            if modifiers & Qt.ControlModifier and (key == Qt.Key_Return or key == Qt.Key_Enter):
                self.translate_current_cell()
                return

            if (modifiers & Qt.ControlModifier and modifiers & Qt.ShiftModifier
                    and (key == Qt.Key_Return or key == Qt.Key_Enter)):
                self.translate_all_cells()
                return

        event.ignore()
        super().keyPressEvent(event)
