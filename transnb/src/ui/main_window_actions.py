from PyQt5.QtCore import Qt


class MainWindowActionsMixin:
    def translate_current_cell(self):
        self.cell_manager.translate_selected_cell()
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)

    def translate_all_cells(self):
        self.cell_manager.translate_all_cells()
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)

    def insert_cell_above(self):
        self.cell_manager.insert_cell_above()
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)

    def insert_cell_below(self):
        self.cell_manager.insert_cell_below()
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)

    def delete_selected_cell(self):
        self.cell_manager.delete_selected_cell()
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)

    def copy_selected_cell(self):
        self.cell_manager.copy_cell()
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)

    def split_selected_cell(self):
        self.cell_manager.split_cell_at_cursor()
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)

    def set_selected_cell_dependent(self):
        self.cell_manager.set_selected_cell_dependent()
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)

    def make_cell_dependent(self):
        self.cell_manager.make_cell_dependent(None, None)
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)

    def remove_cell_dependency(self):
        self.cell_manager.remove_cell_dependency()
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)

    def merge_selected_cells(self):
        success = self.cell_manager.merge_selected_cells()
        if success:
            if self.file_service.is_file_open():
                self.file_service.set_modified(True)

    def toggle_input_collapse_all(self):
        self.cell_manager.toggle_input_collapse_all()

    def toggle_output_collapse_all(self):
        self.cell_manager.toggle_output_collapse_all()

    def toggle_input_collapse_selected(self):
        self.cell_manager.toggle_input_collapse_selected()

    def toggle_output_collapse_selected(self):
        self.cell_manager.toggle_output_collapse_selected()

    def toggle_cell_collapse_all(self):
        self.cell_manager.toggle_cell_collapse_all()

    def toggle_cell_collapse_selected(self):
        self.cell_manager.toggle_cell_collapse_selected()


