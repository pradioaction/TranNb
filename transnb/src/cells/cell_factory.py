
from typing import Dict, Type, Any
from cells.base_cell import BaseCell
from cells.cell_signal_manager import CellSignalManager


class CellFactory:
    """单元格工厂类，用于创建不同类型的单元格实例
    
    使用工厂模式，支持注册和创建多种类型的单元格，
    便于未来扩展新的单元格类型（如 code、image 等）
    """
    
    # 类变量，用于存储单元格类型和对应的构造函数
    _cell_types: Dict[str, Type[BaseCell]] = {}
    _initialized = False
    
    @classmethod
    def _initialize(cls) -> None:
        """延迟初始化，避免循环依赖"""
        if cls._initialized:
            return
        # 延迟导入并注册
        from cells.markdown_cell import MarkdownCell
        cls._cell_types['markdown'] = MarkdownCell
        cls._initialized = True
    
    @classmethod
    def register_cell_type(cls, cell_type: str, cell_class: Type[BaseCell]) -> None:
        """注册新的单元格类型
        
        Args:
            cell_type: 单元格类型名称（如 "markdown"、"code"）
            cell_class: 单元格类（必须继承自 BaseCell）
        """
        cls._initialize()  # 确保已初始化
        cls._cell_types[cell_type] = cell_class
    
    @classmethod
    def create_cell(cls, cell_type: str, cell_manager: Any = None, **kwargs: Any) -> BaseCell:
        """创建指定类型的单元格实例
        
        Args:
            cell_type: 单元格类型名称
            cell_manager: 单元格管理器实例，用于连接信号
            **kwargs: 传递给单元格构造函数的参数
            
        Returns:
            创建的单元格实例
            
        Raises:
            ValueError: 当指定的单元格类型未注册时抛出
        """
        cls._initialize()  # 确保已初始化
        cell_class = cls._cell_types.get(cell_type)
        if cell_class is None:
            raise ValueError(f"未注册的单元格类型: {cell_type}，可用类型: {list(cls._cell_types.keys())}")
        cell = cell_class(**kwargs)
        
        # 让信号管理器负责连接信号
        if cell_manager is not None:
            signal_manager = CellSignalManager(cell_manager)
            signal_manager.connect_cell_signals(cell)
        
        return cell
    
    @classmethod
    def get_registered_types(cls) -> list:
        """获取所有已注册的单元格类型
        
        Returns:
            已注册的单元格类型名称列表
        """
        cls._initialize()  # 确保已初始化
        return list(cls._cell_types.keys())

