from PyQt5.QtWidgets import QFileDialog, QMessageBox, QInputDialog, QApplication, QDialog
import os
from components.text_editor_dialog import TextEditorDialog


class MainWindowFileOpsMixin:
    def new_file(self):
        if not self.workspace_manager.get_workspace():
            self._select_workspace()
            if not self.workspace_manager.get_workspace():
                return

        filename, ok = QInputDialog.getText(self, "新建文件", "请输入文件名:")
        if ok and filename:
            self.file_service.create_new_file(filename)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "翻译笔记本 (*.transnb)")
        if file_path:
            self.file_service.open_file(file_path)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择工作区", "")
        if folder_path:
            self.workspace_manager.set_workspace(folder_path)

    def import_text(self):
        if not self.workspace_manager.get_workspace():
            self._select_workspace()
            if not self.workspace_manager.get_workspace():
                return

        filename, ok = QInputDialog.getText(self, "新建文件", "请输入文件名:")
        if not ok or not filename:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要导入的文本文件", "",
            "文本文件 (*.txt *.md *.html *.htm);;所有文件 (*.*)")
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            QMessageBox.warning(self, "错误", "文件不存在")
            return
        except UnicodeDecodeError:
            QMessageBox.warning(self, "错误", "文件编码错误，请确保是 UTF-8 编码")
            return
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取文件失败: {str(e)}")
            return

        self.file_service.create_file_with_content(filename, content)

    def import_from_clipboard(self):
        if not self.workspace_manager.get_workspace():
            self._select_workspace()
            if not self.workspace_manager.get_workspace():
                return

        clipboard = QApplication.clipboard()
        clipboard_text = clipboard.text()

        if not clipboard_text:
            QMessageBox.warning(self, "提示", "粘贴板中没有文本内容")
            return

        dialog = TextEditorDialog(self)
        dialog.set_text(clipboard_text)

        if dialog.exec_() == QDialog.Accepted:
            edited_text = dialog.edited_text
            if not edited_text:
                return

            filename, ok = QInputDialog.getText(self, "新建文件", "请输入文件名:")
            if not ok or not filename:
                return

            self.file_service.create_file_with_content(filename, edited_text)

    def save_file(self):
        self.file_service.save_file()

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "另存为", "", "翻译笔记本 (*.transnb)")
        if file_path:
            self.file_service.save_file_as(file_path)

    def on_file_double_clicked(self, index):
        file_path = self.file_model.filePath(index)

        if self.file_model.isDir(index):
            return

        if file_path.endswith('.transnb'):
            self.file_service.open_file(file_path)

    def _set_file_browser_path(self, path):
        self.file_model.setRootPath(path)
        self.file_tree.setRootIndex(self.file_model.index(path))

    def restore_workspace(self):
        old_path = self.settings_manager.get_file_browser_path()

        workspace_loaded = self.workspace_manager.load_workspace()

        if not workspace_loaded and old_path and os.path.exists(old_path):
            self.workspace_manager.set_workspace(old_path)
            workspace_loaded = True

        if workspace_loaded:
            workspace = self.workspace_manager.get_workspace()
            self._set_file_browser_path(workspace)

            if workspace:
                self.recitation_path_manager.set_workspace(workspace)
                self.recitation_db_manager = self._create_recitation_db_manager(self.recitation_path_manager)
                self.recitation_db_manager.initialize()
                self.recitation_dal = self._create_recitation_dal(self.recitation_db_manager)
                self.recitation_book_service = self._create_book_service(self.recitation_dal, self.recitation_path_manager)
                self.recitation_study_service = self._create_study_service(self.recitation_dal, self.recitation_path_manager)
                self._refresh_book_counts()
                if hasattr(self, 'cell_manager') and self.cell_manager:
                    self.cell_manager.recitation_dal = self.recitation_dal
                    if self.cell_manager.add_word_dialog:
                        self.cell_manager.add_word_dialog.close()
                        self.cell_manager.add_word_dialog = None

            saved_file = self.settings_manager.get_current_file()
            if saved_file and os.path.exists(saved_file):
                try:
                    self.cell_manager.load_from_file(saved_file)
                    self.file_service._current_file = saved_file
                    self.file_service._open_files[saved_file] = False
                    self.file_service._modified = False
                    self._switch_to_editor_page()
                    self._update_window_title()
                except Exception as e:
                    print(f"Failed to restore file: {e}")
                    self._switch_to_welcome_page()
            else:
                self._switch_to_welcome_page()
        else:
            self._switch_to_welcome_page()

    def _check_unsaved_changes(self):
        if not self.file_service.is_file_open():
            return True

        if not self.file_service.is_modified():
            return True

        reply = QMessageBox.question(
            self, "保存提示", "当前文档有未保存的更改，是否保存？",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )
        if reply == QMessageBox.Save:
            self.file_service.save_file()
            return True
        elif reply == QMessageBox.Discard:
            return True
        else:
            return False

    def _select_workspace(self):
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择工作区目录", "")
        if folder_path:
            self.workspace_manager.set_workspace(folder_path)

    def _on_create_new_file_requested(self):
        self.new_file()

    def _on_file_opened(self, file_path):
        self.cell_manager.clear_all_cells()
        try:
            self.cell_manager.load_from_file(file_path)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载文件失败: {str(e)}")
            self._switch_to_welcome_page()
            return
        self._switch_to_editor_page()
        self.setWindowTitle(f"翻译笔记本 - {file_path}")
        self.settings_manager.set_current_file(file_path)
        self.status_label.setText(f"已打开: {os.path.basename(file_path)}")

    def _on_file_saved(self, file_path):
        self._update_window_title()
        self.status_label.setText(f"已保存: {os.path.basename(file_path)}")

    def _on_file_closed(self):
        self.cell_manager.clear_all_cells()
        self._switch_to_welcome_page()
        self.setWindowTitle("翻译笔记本")
        self.settings_manager.set_current_file("")
        self.status_label.setText("就绪")

    def _on_file_modified(self, is_modified):
        self._update_window_title()

    def _on_file_error(self, error_msg):
        QMessageBox.warning(self, "错误", error_msg)

    def _on_workspace_changed(self, new_path):
        if self.file_service.is_file_open():
            self.file_service.close_file()

        self._switch_to_welcome_page()

        if new_path:
            self._set_file_browser_path(new_path)

        if new_path:
            self.recitation_path_manager.set_workspace(new_path)
            self.recitation_db_manager = self._create_recitation_db_manager(self.recitation_path_manager)
            self.recitation_db_manager.initialize()
            self.recitation_dal = self._create_recitation_dal(self.recitation_db_manager)
            self.recitation_book_service = self._create_book_service(self.recitation_dal, self.recitation_path_manager)
            self.recitation_study_service = self._create_study_service(self.recitation_dal, self.recitation_path_manager)
            self._refresh_book_counts()
            if hasattr(self, 'recitation_main_page') and self.recitation_main_page:
                self.recitation_main_page.set_dependencies(
                    self.recitation_dal,
                    self.recitation_path_manager,
                    self.recitation_study_service,
                    self.recitation_book_service
                )
            if hasattr(self, 'recitation_quiz_page') and self.recitation_quiz_page:
                self.recitation_quiz_page.set_dependencies(
                    self.recitation_dal,
                    self.recitation_path_manager
                )
            if hasattr(self, 'cell_manager') and self.cell_manager:
                self.cell_manager.recitation_dal = self.recitation_dal
                if self.cell_manager.add_word_dialog:
                    self.cell_manager.add_word_dialog.close()
                    self.cell_manager.add_word_dialog = None

        self._update_window_title()

    def _on_files_changed(self):
        pass

    def _update_window_title(self):
        current_file = self.file_service.get_current_file()
        workspace = self.workspace_manager.get_workspace()

        if current_file:
            if self.file_service.is_modified():
                self.setWindowTitle(f"翻译笔记本 - {current_file} *")
            else:
                self.setWindowTitle(f"翻译笔记本 - {current_file}")
        elif workspace:
            self.setWindowTitle(f"翻译笔记本 - {workspace}")
        else:
            self.setWindowTitle("翻译笔记本")

    def _on_cell_content_changed(self):
        if self.file_service.is_file_open() and not self.file_service.is_modified():
            self.file_service.set_modified(True)
