import json
import os
from typing import List, Optional, Any, Dict
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal as Signal, QObject, Qt
from cells.cell_factory import CellFactory
from cells.cell_node import CellNode
from translation.translation_service import TranslationService
from recitation.ui.dialogs import AddWordToBookDialog


class CellManager(QObject):
    content_changed = Signal()
    
    def __init__(self, layout: QVBoxLayout, translation_service: Optional[TranslationService] = None, recitation_dal: Optional[Any] = None):
        super().__init__()
        self.layout = layout
        self.cells: List[Any] = []
        self.selected_index: int = -1
        self.selected_indices: List[int] = []
        self.translation_service = translation_service
        self.settings_manager: Optional[Any] = None
        self.recitation_dal = recitation_dal
        self.add_word_dialog: Optional[AddWordToBookDialog] = None
        
        # 新数据结构 - 用于层级管理
        self.cell_nodes: Dict[str, CellNode] = {}
        self.root_node = CellNode(None)  # 虚拟根节点
        self.display_order: List[str] = []  # 显示顺序的 cell_id 列表
    
    def set_settings_manager(self, settings_manager: Any) -> None:
        self.settings_manager = settings_manager
        if self.translation_service:
            self.translation_service.set_settings_manager(settings_manager)
        for cell in self.cells:
            cell.set_settings_manager(settings_manager)
        if self.settings_manager:
            self.settings_manager.reading_font_size_changed.connect(self.on_reading_font_size_changed)
    
    def on_reading_font_size_changed(self, font_size: int) -> None:
        for cell in self.cells:
            cell.adjust_height()
    
    def _on_cell_content_changed(self) -> None:
        self.content_changed.emit()
    
    def add_cell(self, cell: Any) -> None:
        self.cells.append(cell)
        self.layout.addWidget(cell)
        self._setup_cell(cell)
    
    def remove_cell(self, index: int) -> None:
        if 0 <= index < len(self.cells):
            cell = self.cells[index]
            self.layout.removeWidget(cell)
            cell.deleteLater()
            del self.cells[index]
            if self.selected_index == index:
                self.selected_index = -1
            elif self.selected_index > index:
                self.selected_index -= 1
    
    def clear_all_cells(self) -> None:
        for cell in self.cells:
            self.layout.removeWidget(cell)
            cell.deleteLater()
        self.cells.clear()
        self.selected_index = -1
    
    def select_cell(self, index: int) -> None:
        if 0 <= index < len(self.cells):
            for i in list(self.selected_indices):
                if 0 <= i < len(self.cells):
                    self.cells[i].set_selected(False)
            
            self.selected_indices.clear()
            self.selected_index = index
            self.selected_indices.append(index)
            self.cells[index].set_selected(True)
    
    def select_cell_range(self, from_index: int, to_index: int) -> None:
        if 0 <= from_index < len(self.cells) and 0 <= to_index < len(self.cells):
            for i in list(self.selected_indices):
                if 0 <= i < len(self.cells):
                    self.cells[i].set_selected(False)
            
            self.selected_indices.clear()
            start = min(from_index, to_index)
            end = max(from_index, to_index)
            for i in range(start, end + 1):
                self.selected_indices.append(i)
                self.cells[i].set_selected(True)
            
            self.selected_index = from_index
    
    def toggle_cell_selection(self, index: int) -> None:
        '''
        切换指定索引的单元格的选中状态
        '''
        if 0 <= index < len(self.cells):
            if index in self.selected_indices:
                self.selected_indices.remove(index)
                self.cells[index].set_selected(False)
            else:
                self.selected_indices.append(index)
                self.cells[index].set_selected(True)
            
            if not self.selected_indices:
                self.selected_index = -1
            else:
                self.selected_index = index if index in self.selected_indices else self.selected_indices[-1]
    
    def get_selected_cells(self) -> List[Any]:
        return [self.cells[i] for i in self.selected_indices if 0 <= i < len(self.cells)]
    
    def on_cell_selected(self, data: Any) -> None:
        if isinstance(data, tuple) and len(data) == 2:
            cell, shift_pressed = data
        else:
            cell = data
            shift_pressed = False
        
        index = self.cells.index(cell)
        
        if shift_pressed and self.selected_index >= 0:
            self.select_cell_range(self.selected_index, index)
        else:
            self.select_cell(index)
    
    def on_cell_translate_requested(self, cell: Any) -> None:
        index = self.cells.index(cell)
        self.translate_cell(index)
    
    def on_cell_delete_requested(self, cell: Any) -> None:
        index = self.cells.index(cell)
        self.remove_cell(index)
    
    def on_cell_move_up(self, cell: Any) -> None:
        index = self.cells.index(cell)
        if index > 0:
            self.move_cell(index, index - 1)
    
    def on_cell_move_down(self, cell: Any) -> None:
        index = self.cells.index(cell)
        if index < len(self.cells) - 1:
            self.move_cell(index, index + 1)
    
    def on_collect_word(self, word_text: str) -> None:
        if not self.recitation_dal:
            QMessageBox.warning(None, "提示", "请先选择工作区后再使用收藏功能！")
            return
        
        if not self.add_word_dialog:
            self.add_word_dialog = AddWordToBookDialog(self.recitation_dal)
            self.add_word_dialog.setWindowFlags(self.add_word_dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        
        self.add_word_dialog.set_word(word_text)
        self.add_word_dialog.show()
        self.add_word_dialog.raise_()
        self.add_word_dialog.activateWindow()
    
    def move_cell(self, from_index: int, to_index: int) -> None:
        cell = self.cells[from_index]
        self.layout.removeWidget(cell)
        self.cells.pop(from_index)
        self.cells.insert(to_index, cell)
        self.layout.insertWidget(to_index, cell)
        
        if self.selected_index == from_index:
            self.selected_index = to_index
    
    def translate_cell(self, index: int) -> None:
        if 0 <= index < len(self.cells):
            self.cells[index].translate()
    
    def translate_selected_cell(self) -> None:
        for cell in self.get_selected_cells():
            cell.translate()
    
    def translate_all_cells(self) -> None:
        for cell in self.cells:
            cell.translate()
    
    def _setup_cell(self, cell: Any) -> None:
        cell.set_translation_service(self.translation_service)
        if self.settings_manager:
            cell.set_settings_manager(self.settings_manager)
    
    def _create_and_insert_cell(self, index: int) -> Any:
        cell = CellFactory.create_cell('markdown', cell_manager=self)
        self.cells.insert(index, cell)
        self.layout.insertWidget(index, cell)
        self._setup_cell(cell)
        return cell
    
    def insert_cell_above(self) -> None:
        if self.selected_index < 0:
            self.selected_index = 0
        
        self._create_and_insert_cell(self.selected_index)
    
    def insert_cell_below(self) -> None:
        if self.selected_index < 0:
            insert_index = len(self.cells)
        else:
            insert_index = self.selected_index + 1
        
        self._create_and_insert_cell(insert_index)
        self.selected_index = insert_index
    
    def delete_selected_cell(self) -> None:
        if self.selected_index >= 0:
            self.remove_cell(self.selected_index)
    
    def copy_cell(self, index: int = None) -> Any:
        """复制指定索引的单元格，插入到其下方
        
        Args:
            index: 要复制的单元格索引，如果为 None 则使用当前选中的单元格
            
        Returns:
            新创建的单元格，如果失败则返回 None
        """
        if index is None:
            index = self.selected_index
            
        if 0 <= index < len(self.cells):
            original_cell = self.cells[index]
            
            # 创建新单元格
            new_cell = CellFactory.create_cell('markdown', cell_manager=self)
            
            # 复制内容
            new_cell.set_content(original_cell.get_content())
            new_cell.set_output(original_cell.get_output())
            
            # 复制层级关系
            if hasattr(original_cell, 'indent_level'):
                new_cell.set_indent(original_cell.indent_level)
            if hasattr(original_cell, 'parent_cell_id'):
                new_cell.parent_cell_id = original_cell.parent_cell_id
            
            # 插入到原单元格下方
            insert_index = index + 1
            self.cells.insert(insert_index, new_cell)
            self.layout.insertWidget(insert_index, new_cell)
            self._setup_cell(new_cell)
            
            # 选中新单元格
            self.select_cell(insert_index)
            
            # 更新树形结构
            self._update_tree_structure()
            
            return new_cell
        return None
    
    def split_cell_at_cursor(self, index: Optional[int] = None) -> Optional[object]:
        """在当前选中的单元格中，在光标位置处拆分单元格
        
        Args:
            index: 要拆分的单元格索引
        
        Returns:
            如果成功拆分则返回新单元格，否则返回 None
        """
        if index is None:
            index = self.selected_index
            
        # 如果索引无效，尝试找出第一个可编辑的单元格或使用第一个单元格
        if index < 0 or index >= len(self.cells):
            for i, cell in enumerate(self.cells):
                if hasattr(cell, 'is_reading_mode') and hasattr(cell, 'get_text_before_cursor'):
                    if not cell.is_reading_mode():
                        index = i
                        break
            if (index < 0 or index >= len(self.cells)) and len(self.cells) > 0:
                index = 0
            else:
                return None
        
        cell = self.cells[index]
        
        # 检查单元格是否支持拆分
        if not hasattr(cell, 'get_text_before_cursor') or not hasattr(cell, 'get_text_after_cursor'):
            return None
        
        # 检查是否处于阅读模式
        if hasattr(cell, 'is_reading_mode') and cell.is_reading_mode():
            return None
        
        # 获取光标位置和分割文本
        text_before = cell.get_text_before_cursor()
        text_after = cell.get_text_after_cursor()
        
        if text_before is None or text_after is None:
            return None
        
        # 更新原单元格内容
        cell.set_content(text_before)
        
        # 创建新单元格并插入
        new_cell = CellFactory.create_cell('markdown', cell_manager=self)
        new_cell.set_content(text_after)
        
        # 继承层级关系
        if hasattr(cell, 'indent_level'):
            new_cell.set_indent(cell.indent_level)
        if hasattr(cell, 'parent_cell_id'):
            new_cell.parent_cell_id = cell.parent_cell_id
        
        # 插入到原单元格下面
        insert_index = index + 1
        self.cells.insert(insert_index, new_cell)
        self.layout.insertWidget(insert_index, new_cell)
        self._setup_cell(new_cell)
        
        # 选中新单元格
        self.select_cell(insert_index)
        
        return new_cell
    
    def make_cell_dependent(self, child_index: Optional[int] = None, parent_index: Optional[int] = None) -> bool:
        """将一个单元格设置为另一个单元格的从属
        
        Args:
            child_index: 要设置为从属的单元格索引
            parent_index: 父单元格索引，如果为 None 则使用选中单元格
            
        Returns:
            如果成功设置从属关系则返回 True
        """
        if parent_index is None and child_index is None:
            if self.selected_indices and len(self.selected_indices) >= 2:
                # 如果有多个选中的单元格，取第一个作为父，第二个作为子
                parent_index = self.selected_indices[0]
                child_index = self.selected_indices[1]
        
        # 验证索引有效
        if (child_index is None or 
            parent_index is None or
            child_index < 0 or child_index >= len(self.cells) or 
            parent_index < 0 or parent_index >= len(self.cells) or 
            child_index == parent_index):
            return False
        
        child_cell = self.cells[child_index]
        parent_cell = self.cells[parent_index]
        
        # 获取父单元格的 ID
        parent_id = self._get_cell_id(parent_cell)
        if parent_id is None:
            return False
        
        # 设置层级关系
        if hasattr(child_cell, 'parent_cell_id'):
            child_cell.parent_cell_id = parent_id
        if hasattr(child_cell, 'set_indent'):
            child_cell.set_indent(1)
        
        # 更新树形结构
        self._update_tree_structure()
        
        return True
    
    def set_selected_cell_dependent(self) -> bool:
        """切换当前选中单元格的从属关系
        
        - 如果没有从属 → 设置为从属
        - 如果已经从属 → 取消从属，同时处理子节点
        
        Returns:
            如果成功返回 True
        """
        if self.selected_index is None or self.selected_index < 0:
            return False
        
        cell_index = self.selected_index
        cell = self.cells[cell_index]
        
        # 检查是否已经从属
        if hasattr(cell, 'parent_cell_id') and cell.parent_cell_id is not None:
            # 已经从属 → 取消从属
            return self.remove_cell_dependency(cell_index)
        else:
            # 没有从属 → 设置从属
            if cell_index <= 0:
                return False
            
            child_index = cell_index
            prev_index = child_index - 1
            
            # 检查上一个单元格是否是从属节点
            prev_cell = self.cells[prev_index]
            
            if hasattr(prev_cell, 'parent_cell_id') and prev_cell.parent_cell_id is not None:
                # 上一个是从属节点，找到它的父节点在 cells 中的索引
                parent_id = prev_cell.parent_cell_id
                parent_index = None
                for idx, cell_obj in enumerate(self.cells):
                    cell_id = self._get_cell_id(cell_obj)
                    if cell_id == parent_id:
                        parent_index = idx
                        break
                
                if parent_index is not None:
                    return self.make_cell_dependent(child_index, parent_index)
            
            # 否则（上一个是正常节点），正常从属
            return self.make_cell_dependent(child_index, prev_index)
    
    def remove_cell_dependency(self, index: Optional[int] = None) -> bool:
        """移除单元格的从属关系，同时处理子节点
        
        2.1 如果自己有子节点 → 子节点从属于自己
        2.2 如果自己有父节点 → 把子节点移交给自己的父节点
        
        Args:
            index: 单元格索引，默认为选中单元格
            
        Returns:
            成功移除返回 True
        """
        if index is None:
            index = self.selected_index
        
        if index < 0 or index >= len(self.cells):
            return False
        
        cell = self.cells[index]
        
        # 先保存自己的父节点ID
        old_parent_id = cell.parent_cell_id if hasattr(cell, 'parent_cell_id') else None
        
        # 先更新树形结构确保最新
        self._update_tree_structure()
        
        # 获取自己的 cell_id
        cell_id = self._get_cell_id(cell)
        
        # 处理子节点
        if cell_id and cell_id in self.cell_nodes:
            node = self.cell_nodes[cell_id]
            # 遍历所有子节点
            for child_node in node.children:
                if child_node.cell:
                    child_cell = child_node.cell
                    if old_parent_id is not None:
                        # 2.2 自己有父节点 → 子节点移交给自己的父节点
                        child_cell.parent_cell_id = old_parent_id
                    # 2.1 自己没有父节点 → 子节点保持从属（自己现在是顶级了）
        
        # 然后移除自己的从属关系
        if hasattr(cell, 'parent_cell_id'):
            cell.parent_cell_id = None
        if hasattr(cell, 'set_indent'):
            cell.set_indent(0)
        if hasattr(cell, 'set_dependent_collapsed'):
            cell.set_dependent_collapsed(False)
        
        # 再次更新树形结构
        self._update_tree_structure()
        
        return True
    

    
    def on_cell_collapse_changed(self, cell: Any, collapsed: bool) -> None:
        """单元格折叠状态变化时，同步从属单元格的折叠状态
        
        Args:
            cell: 状态变化的单元格
            collapsed: 新的折叠状态
        """
        # 找到单元格对应的 cell_id
        cell_id = self._get_cell_id(cell)
        if cell_id is None or cell_id not in self.cell_nodes:
            return
        
        # 找到 cell_node，遍历其 children
        parent_node = self.cell_nodes[cell_id]
        for child_node in parent_node.children:
            if child_node.cell and hasattr(child_node.cell, 'set_dependent_collapsed'):
                child_node.cell.set_dependent_collapsed(collapsed)
    
    # 层级关系管理的辅助方法
    def _get_cell_id(self, cell: Any) -> Optional[str]:
        """获取单元格的唯一 ID（通过查找 cell_nodes）
        
        Args:
            cell: 单元格对象
            
        Returns:
            单元格的 ID，如果未找到则返回 None
        """
        for cell_id, node in self.cell_nodes.items():
            if node.cell == cell:
                return cell_id
        return None
    
    def _update_tree_structure(self) -> None:
        """更新树形结构（用于维护数据一致性）
        
        这个方法会根据当前 cells 的状态和它们的层级关系
        来重建 cell_nodes 和 root_node。
        """
        # 重建 cell_nodes
        self.cell_nodes.clear()
        self.root_node = CellNode(None)
        self.display_order.clear()
        
        # 第一步：先把所有 cell 加入 cell_nodes！
        for cell in self.cells:
            node = CellNode(cell)
            # 优先使用 cell 已有的 cell_id，不要重新生成
            if hasattr(cell, 'cell_id') and cell.cell_id:
                node.cell_id = cell.cell_id
            else:
                # 只有在没有时才生成新的，并保存到 cell 上
                if hasattr(cell, 'cell_id'):
                    cell.cell_id = node.cell_id
            self.cell_nodes[node.cell_id] = node
        
        # 第二步：再建立父子关系！
        for cell in self.cells:
            cell_id = cell.cell_id if hasattr(cell, 'cell_id') else None
            if cell_id not in self.cell_nodes:
                continue
            node = self.cell_nodes[cell_id]
            
            if hasattr(cell, 'parent_cell_id') and cell.parent_cell_id is not None:
                # 是从属 cell，找父节点
                parent_id = cell.parent_cell_id
                if parent_id in self.cell_nodes:
                    parent_node = self.cell_nodes[parent_id]
                    parent_node.add_child(node)
                    # 从属节点显示在父节点后面
                    if parent_id in self.display_order:
                        idx = self.display_order.index(parent_id)
                        self.display_order.insert(idx + 1, cell_id)
                    else:
                        self.display_order.append(cell_id)
                else:
                    self.root_node.add_child(node)
                    self.display_order.append(cell_id)
            else:
                # 顶级 cell，添加到 root
                self.root_node.add_child(node)
                self.display_order.append(cell_id)
    
    def adjust_all_cell_heights(self) -> None:
        for cell in self.cells:
            cell.adjust_height()
    
    def save_to_file(self, file_path: str) -> None:
        # 确保树形结构是最新的
        self._update_tree_structure()
        
        cells_data = []
        for idx, cell in enumerate(self.cells):
            cell_data = {
                'type': 'markdown',
                'content': cell.get_content(),
                'output': cell.get_output()
            }
            
            # 添加层级相关的信息
            if hasattr(cell, 'parent_cell_id'):
                cell_data['parent_id'] = cell.parent_cell_id
            if hasattr(cell, 'indent_level'):
                cell_data['indent_level'] = cell.indent_level
            if hasattr(cell, 'is_collapsed'):
                cell_data['is_collapsed'] = cell.is_collapsed
            
            # 添加单元格唯一 ID
            cell_id = self._get_cell_id(cell)
            cell_data['id'] = cell_id if cell_id else f"cell_{idx}"
            
            cells_data.append(cell_data)
        
        data = {
            'version': '2.0',
            'cells': cells_data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, file_path: str) -> None:
        self.clear_all_cells()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        version = data.get('version', '1.0')
        
        # 先读取所有单元格数据，暂存它们
        cells_temp = []
        
        for cell_data in data.get('cells', []):
            cell = CellFactory.create_cell('markdown', cell_manager=self)
            cell.set_content(cell_data.get('content', ''))
            cell.set_output(cell_data.get('output', ''))
            
            # 存储其他信息，稍后恢复
            cell._temp_id = cell_data.get('id', None)
            cell._temp_parent_id = cell_data.get('parent_id', None)
            cell._temp_indent_level = cell_data.get('indent_level', 0)
            cell._temp_is_collapsed = cell_data.get('is_collapsed', False)
            
            cells_temp.append(cell)
        
        # 第一次循环：添加所有单元格到界面
        for cell in cells_temp:
            self.add_cell(cell)
        
        # 第二次循环：恢复层级关系
        id_to_cell = {}
        for cell in self.cells:
            if hasattr(cell, '_temp_id') and cell._temp_id:
                id_to_cell[cell._temp_id] = cell
        
        for cell in self.cells:
            if hasattr(cell, '_temp_id') and cell._temp_id and hasattr(cell, 'cell_id'):
                cell.cell_id = cell._temp_id
            if hasattr(cell, '_temp_parent_id'):
                cell.parent_cell_id = cell._temp_parent_id
            if hasattr(cell, '_temp_indent_level'):
                cell.set_indent(cell._temp_indent_level)
            if hasattr(cell, '_temp_is_collapsed') and hasattr(cell, 'is_cell_collapsed'):
                cell.is_cell_collapsed = cell._temp_is_collapsed
        
        # 更新树形结构
        self._update_tree_structure()
    
    def load_from_text_content(self, content: str) -> None:
        self.clear_all_cells()
        
        lines = content.replace('\r\n', '\n').split('\n')
        paragraphs = [line.strip() for line in lines if line.strip()]
        
        for paragraph in paragraphs:
            cell = CellFactory.create_cell('markdown', cell_manager=self)
            cell.set_content(paragraph)
            self.add_cell(cell)
    
    def toggle_input_collapse_all(self) -> None:
        for cell in self.cells:
            cell.toggle_input_collapse()
    
    def toggle_output_collapse_all(self) -> None:
        for cell in self.cells:
            cell.toggle_output_collapse()
    
    def toggle_input_collapse_selected(self) -> None:
        for cell in self.get_selected_cells():
            cell.toggle_input_collapse()
    
    def toggle_output_collapse_selected(self) -> None:
        for cell in self.get_selected_cells():
            cell.toggle_output_collapse()
    
    def toggle_cell_collapse_all(self) -> None:
        """折叠/展开全部单元格"""
        for cell in self.cells:
            if hasattr(cell, 'toggle_cell_collapse'):
                cell.toggle_cell_collapse()
    
    def toggle_cell_collapse_selected(self) -> None:
        """折叠/展开选中的单元格"""
        for cell in self.get_selected_cells():
            if hasattr(cell, 'toggle_cell_collapse'):
                cell.toggle_cell_collapse()
    
    def merge_selected_cells(self) -> bool:
        """合并选中的单元格
        
        1. 合并到第一个选中的单元格
        2. 其他单元格的内容追加进来，中间加空行
        3. 处理从属关系变化
        4. 删除其他单元格
        
        Returns:
            成功返回 True
        """
        if not self.selected_indices or len(self.selected_indices) < 2:
            return False
        
        # 按顺序排序，确保第一个是最早的
        sorted_indices = sorted(self.selected_indices)
        target_index = sorted_indices[0]
        source_indices = sorted_indices[1:]
        
        # 如果目标索引无效，直接返回
        if target_index < 0 or target_index >= len(self.cells):
            return False
        
        target_cell = self.cells[target_index]
        
        # 先更新树形结构，确保能正确处理从属关系
        self._update_tree_structure()
        
        # 1. 先处理从属关系变化
        # 收集所有被删除的单元格的信息
        deleted_info = []
        for idx in source_indices:
            if idx < 0 or idx >= len(self.cells):
                continue
            
            cell = self.cells[idx]
            old_parent_id = cell.parent_cell_id if hasattr(cell, 'parent_cell_id') else None
            cell_id = self._get_cell_id(cell)
            deleted_info.append((cell, old_parent_id, cell_id))
        
        # 处理每个被删单元格的子节点
        for cell, old_parent_id, cell_id in deleted_info:
            if cell_id and cell_id in self.cell_nodes:
                node = self.cell_nodes[cell_id]
                for child_node in node.children:
                    if child_node.cell:
                        child_cell = child_node.cell
                        if old_parent_id is not None:
                            # 被删单元格有父 → 子移交给父
                            child_cell.parent_cell_id = old_parent_id
                        else:
                            # 被删单元格没父 → 子取消从属
                            child_cell.parent_cell_id = None
                            child_cell.set_indent(0)
                            child_cell.set_dependent_collapsed(False)
        
        # 2. 合并内容
        for idx in source_indices:
            if idx < 0 or idx >= len(self.cells):
                continue
            
            cell = self.cells[idx]
            
            # 追加原文
            content = cell.get_content()
            if content.strip():
                target_cell.set_content(target_cell.get_content() + '\n\n' + content)
            
            # 追加翻译
            output = cell.get_output()
            if output.strip():
                target_cell.set_output(target_cell.get_output() + '\n\n' + output)
        
        # 3. 删除其他单元格（从后往前删）
        for idx in reversed(source_indices):
            if idx < 0 or idx >= len(self.cells):
                continue
            self.remove_cell(idx)
        
        # 选中目标单元格
        self.select_cell(target_index)
        
        # 更新树形结构
        self._update_tree_structure()
        
        return True

