from PyQt5.QtCore import QObject
from typing import Any


class CellSignalManager(QObject):
    """单元格信号管理器，负责统一管理单元格信号连接
    
    该类将信号连接逻辑从 CellManager 中分离出来，
    负责处理所有与单元格信号相关的操作。
    """
    
    def __init__(self, cell_manager: Any):
        """构造函数
        
        Args:
            cell_manager: CellManager 实例，提供信号处理方法
        """
        super().__init__()
        self.cell_manager = cell_manager
    
    def connect_cell_signals(self, cell: Any) -> None:
        """连接单元格的所有信号
        
        Args:
            cell: 需要连接信号的单元格实例
        """
        cell.selected.connect(self.cell_manager.on_cell_selected)
        cell.translate_requested.connect(self.cell_manager.on_cell_translate_requested)
        cell.delete_requested.connect(self.cell_manager.on_cell_delete_requested)
        cell.move_up_requested.connect(self.cell_manager.on_cell_move_up)
        cell.move_down_requested.connect(self.cell_manager.on_cell_move_down)
        
        if hasattr(cell, 'input_editor'):
            cell.input_editor.content_changed.connect(self.cell_manager._on_cell_content_changed)
        
        if hasattr(cell, 'output_editor'):
            cell.output_editor.content_changed.connect(self.cell_manager._on_cell_content_changed)
        
        if hasattr(cell, 'collect_word'):
            cell.collect_word.connect(self.cell_manager.on_collect_word)
        
        if hasattr(cell, 'cell_collapse_changed'):
            cell.cell_collapse_changed.connect(self.cell_manager.on_cell_collapse_changed)
