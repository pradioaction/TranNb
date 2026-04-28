import json
import os
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from cells.code_cell import CodeCell
from cells.markdown_cell import MarkdownCell

class CellManager:
    def __init__(self, layout: QVBoxLayout, kernel_manager):
        self.layout = layout
        self.kernel_manager = kernel_manager
        self.cells = []
        self.selected_index = -1
        
    def add_cell(self, cell):
        self.cells.append(cell)
        self.layout.addWidget(cell)
        cell.selected.connect(self.on_cell_selected)
        cell.run_requested.connect(self.on_cell_run_requested)
        cell.delete_requested.connect(self.on_cell_delete_requested)
        cell.move_up_requested.connect(self.on_cell_move_up)
        cell.move_down_requested.connect(self.on_cell_move_down)
        
    def remove_cell(self, index):
        if 0 <= index < len(self.cells):
            cell = self.cells[index]
            self.layout.removeWidget(cell)
            cell.deleteLater()
            del self.cells[index]
            if self.selected_index == index:
                self.selected_index = -1
            elif self.selected_index > index:
                self.selected_index -= 1
                
    def clear_all_cells(self):
        for cell in self.cells:
            self.layout.removeWidget(cell)
            cell.deleteLater()
        self.cells.clear()
        self.selected_index = -1
        
    def select_cell(self, index):
        if 0 <= index < len(self.cells):
            if self.selected_index >= 0:
                self.cells[self.selected_index].set_selected(False)
            self.selected_index = index
            self.cells[index].set_selected(True)
            
    def on_cell_selected(self, cell):
        index = self.cells.index(cell)
        self.select_cell(index)
        
    def on_cell_run_requested(self, cell):
        index = self.cells.index(cell)
        self.run_cell(index)
        
    def on_cell_delete_requested(self, cell):
        index = self.cells.index(cell)
        self.remove_cell(index)
        
    def on_cell_move_up(self, cell):
        index = self.cells.index(cell)
        if index > 0:
            self.move_cell(index, index - 1)
            
    def on_cell_move_down(self, cell):
        index = self.cells.index(cell)
        if index < len(self.cells) - 1:
            self.move_cell(index, index + 1)
            
    def move_cell(self, from_index, to_index):
        cell = self.cells[from_index]
        self.layout.removeWidget(cell)
        self.cells.pop(from_index)
        self.cells.insert(to_index, cell)
        self.layout.insertWidget(to_index, cell)
        
        if self.selected_index == from_index:
            self.selected_index = to_index
            
    def run_cell(self, index):
        if 0 <= index < len(self.cells):
            cell = self.cells[index]
            if isinstance(cell, CodeCell):
                cell.run()
                
    def run_selected_cell(self):
        if self.selected_index >= 0:
            self.run_cell(self.selected_index)
            
    def run_all_cells(self):
        for i, cell in enumerate(self.cells):
            if isinstance(cell, CodeCell):
                cell.run()
                
    def insert_cell_above(self, cell_type='code'):
        if self.selected_index < 0:
            self.selected_index = 0
            
        if cell_type == 'code':
            new_cell = CodeCell(self.kernel_manager)
        else:
            new_cell = MarkdownCell()
            
        self.cells.insert(self.selected_index, new_cell)
        self.layout.insertWidget(self.selected_index, new_cell)
        new_cell.selected.connect(self.on_cell_selected)
        new_cell.run_requested.connect(self.on_cell_run_requested)
        new_cell.delete_requested.connect(self.on_cell_delete_requested)
        new_cell.move_up_requested.connect(self.on_cell_move_up)
        new_cell.move_down_requested.connect(self.on_cell_move_down)
        
    def insert_cell_below(self, cell_type='code'):
        if self.selected_index < 0:
            insert_index = len(self.cells)
        else:
            insert_index = self.selected_index + 1
            
        if cell_type == 'code':
            new_cell = CodeCell(self.kernel_manager)
        else:
            new_cell = MarkdownCell()
            
        self.cells.insert(insert_index, new_cell)
        self.layout.insertWidget(insert_index, new_cell)
        new_cell.selected.connect(self.on_cell_selected)
        new_cell.run_requested.connect(self.on_cell_run_requested)
        new_cell.delete_requested.connect(self.on_cell_delete_requested)
        new_cell.move_up_requested.connect(self.on_cell_move_up)
        new_cell.move_down_requested.connect(self.on_cell_move_down)
        
        self.selected_index = insert_index
        
    def delete_selected_cell(self):
        if self.selected_index >= 0:
            self.remove_cell(self.selected_index)
            
    def adjust_all_cell_heights(self):
        for cell in self.cells:
            cell.adjust_height()
            
    def format_selected_cell(self):
        if self.selected_index >= 0:
            cell = self.cells[self.selected_index]
            if isinstance(cell, CodeCell):
                cell.format_code()
            
    def convert_selected_to_markdown(self):
        if self.selected_index >= 0:
            cell = self.cells[self.selected_index]
            if isinstance(cell, CodeCell):
                content = cell.get_code()
                self.remove_cell(self.selected_index)
                new_cell = MarkdownCell()
                new_cell.set_content(content)
                self.cells.insert(self.selected_index, new_cell)
                self.layout.insertWidget(self.selected_index, new_cell)
                new_cell.selected.connect(self.on_cell_selected)
                new_cell.run_requested.connect(self.on_cell_run_requested)
                new_cell.delete_requested.connect(self.on_cell_delete_requested)
                new_cell.move_up_requested.connect(self.on_cell_move_up)
                new_cell.move_down_requested.connect(self.on_cell_move_down)
                
    def convert_selected_to_code(self):
        if self.selected_index >= 0:
            cell = self.cells[self.selected_index]
            if isinstance(cell, MarkdownCell):
                content = cell.get_content()
                self.remove_cell(self.selected_index)
                new_cell = CodeCell(self.kernel_manager)
                new_cell.set_code(content)
                self.cells.insert(self.selected_index, new_cell)
                self.layout.insertWidget(self.selected_index, new_cell)
                new_cell.selected.connect(self.on_cell_selected)
                new_cell.run_requested.connect(self.on_cell_run_requested)
                new_cell.delete_requested.connect(self.on_cell_delete_requested)
                new_cell.move_up_requested.connect(self.on_cell_move_up)
                new_cell.move_down_requested.connect(self.on_cell_move_down)
                
    def save_to_file(self, file_path):
        cells_data = []
        for cell in self.cells:
            if isinstance(cell, CodeCell):
                cells_data.append({
                    'type': 'code',
                    'content': cell.get_code(),
                    'output': cell.get_output()
                })
            elif isinstance(cell, MarkdownCell):
                cells_data.append({
                    'type': 'markdown',
                    'content': cell.get_content()
                })
        
        data = {
            'version': '1.0',
            'cells': cells_data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
    def load_from_file(self, file_path):
        self.clear_all_cells()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for cell_data in data.get('cells', []):
            cell_type = cell_data.get('type', 'code')
            content = cell_data.get('content', '')
            
            if cell_type == 'code':
                cell = CodeCell(self.kernel_manager)
                cell.set_code(content)
                output = cell_data.get('output', '')
                cell.set_output(output)
            else:
                cell = MarkdownCell()
                cell.set_content(content)
                
            self.add_cell(cell)