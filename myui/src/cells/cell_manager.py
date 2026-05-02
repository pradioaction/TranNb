
import json
import os
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from PyQt5.QtCore import pyqtSignal as Signal, QObject
from cells.markdown_cell import MarkdownCell
from translation.translation_service import TranslationService

class CellManager(QObject):
    content_changed = Signal()  # 内容变化信号
    
    def __init__(self, layout: QVBoxLayout, translation_service=None):
        super().__init__()
        self.layout = layout
        self.cells = []
        self.selected_index = -1
        self.translation_service = translation_service
        self.settings_manager = None
        
    def set_settings_manager(self, settings_manager):
        self.settings_manager = settings_manager
        self.translation_service.set_settings_manager(settings_manager)
        for cell in self.cells:
            cell.set_settings_manager(settings_manager)
        if self.settings_manager:
            self.settings_manager.reading_font_size_changed.connect(self.on_reading_font_size_changed)
        
    def on_reading_font_size_changed(self, font_size):
        print(f"[Font change] New font size: {font_size}")
        for cell in self.cells:
            cell.adjust_height()
    
    def _on_cell_content_changed(self):
        """单元格内容变化时触发"""
        self.content_changed.emit()
        
    def add_cell(self, cell):
        self.cells.append(cell)
        self.layout.addWidget(cell)
        cell.selected.connect(self.on_cell_selected)
        cell.translate_requested.connect(self.on_cell_translate_requested)
        cell.delete_requested.connect(self.on_cell_delete_requested)
        cell.move_up_requested.connect(self.on_cell_move_up)
        cell.move_down_requested.connect(self.on_cell_move_down)
        cell.set_translation_service(self.translation_service)
        if self.settings_manager:
            cell.set_settings_manager(self.settings_manager)
        # 监听内容变化
        if hasattr(cell, 'input_editor'):
            cell.input_editor.content_changed.connect(self._on_cell_content_changed)
        if hasattr(cell, 'output_editor'):
            cell.output_editor.content_changed.connect(self._on_cell_content_changed)
        
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
        
    def on_cell_translate_requested(self, cell):
        index = self.cells.index(cell)
        self.translate_cell(index)
        
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
            
    def translate_cell(self, index):
        if 0 <= index < len(self.cells):
            self.cells[index].translate()
            
    def translate_selected_cell(self):
        if self.selected_index >= 0:
            self.translate_cell(self.selected_index)
            
    def translate_all_cells(self):
        for i, cell in enumerate(self.cells):
            cell.translate()
            
    def insert_cell_above(self):
        if self.selected_index < 0:
            self.selected_index = 0
        
        new_cell = MarkdownCell()
        self.cells.insert(self.selected_index, new_cell)
        self.layout.insertWidget(self.selected_index, new_cell)
        self._connect_cell_signals(new_cell)
        new_cell.set_translation_service(self.translation_service)
        if self.settings_manager:
            new_cell.set_settings_manager(self.settings_manager)
        
    def insert_cell_below(self):
        if self.selected_index < 0:
            insert_index = len(self.cells)
        else:
            insert_index = self.selected_index + 1
        
        new_cell = MarkdownCell()
        self.cells.insert(insert_index, new_cell)
        self.layout.insertWidget(insert_index, new_cell)
        self._connect_cell_signals(new_cell)
        new_cell.set_translation_service(self.translation_service)
        if self.settings_manager:
            new_cell.set_settings_manager(self.settings_manager)
        
        self.selected_index = insert_index
        
    def _connect_cell_signals(self, cell):
        cell.selected.connect(self.on_cell_selected)
        cell.translate_requested.connect(self.on_cell_translate_requested)
        cell.delete_requested.connect(self.on_cell_delete_requested)
        cell.move_up_requested.connect(self.on_cell_move_up)
        cell.move_down_requested.connect(self.on_cell_move_down)
        
    def delete_selected_cell(self):
        if self.selected_index >= 0:
            self.remove_cell(self.selected_index)
            
    def adjust_all_cell_heights(self):
        for cell in self.cells:
            cell.adjust_height()
                
    def save_to_file(self, file_path):
        cells_data = []
        for cell in self.cells:
            cells_data.append({
                'type': 'markdown',
                'content': cell.get_content(),
                'output': cell.get_output()
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
            cell = MarkdownCell()
            cell.set_content(cell_data.get('content', ''))
            cell.set_output(cell_data.get('output', ''))
            self.add_cell(cell)
            
    def load_from_text_content(self, content: str):
        """从文本内容加载单元格
        
        Args:
            content: 文本内容，按段落分割
        """
        self.clear_all_cells()
        
        # 按换行符分割，兼容 \n 和 \r\n
        lines = content.replace('\r\n', '\n').split('\n')
        
        # 过滤空行和纯空白段落
        paragraphs = [line.strip() for line in lines if line.strip()]
        
        # 为每个有效段落创建 MarkdownCell
        for paragraph in paragraphs:
            cell = MarkdownCell()
            cell.set_content(paragraph)
            self.add_cell(cell)
