import uuid
from typing import Optional, List, Any


class CellNode:
    """单元格节点类，用于管理单元格的层级关系
    
    这个类用于表示单元格之间的父子关系，并提供了
    管理这种关系的方法。
    """
    
    def __init__(self, cell: Optional[Any] = None):
        """初始化单元格节点
        
        Args:
            cell: 实际的单元格对象，可以为 None（用于根节点）
        """
        self.cell = cell
        self.parent: Optional[CellNode] = None
        self.children: List[CellNode] = []
        self.is_collapsed: bool = False
        # 唯一标识符，用于持久化
        self.cell_id: str = str(uuid.uuid4())
        # 缩进级别（0 表示顶级，1 表示一级从属）
        self.indent_level: int = 0
    
    def add_child(self, child: 'CellNode') -> None:
        """添加一个子节点
        
        Args:
            child: 要添加的子节点
        """
        child.parent = self
        child.indent_level = 1  # 只支持一层从属关系
        self.children.append(child)
    
    def remove_child(self, child: 'CellNode') -> bool:
        """移除一个子节点
        
        Args:
            child: 要移除的子节点
            
        Returns:
            成功返回 True，否则返回 False
        """
        if child in self.children:
            child.parent = None
            child.indent_level = 0
            self.children.remove(child)
            return True
        return False
    
    def remove_from_parent(self) -> None:
        """将自己从父节点中移除"""
        if self.parent:
            self.parent.remove_child(self)
    
    def get_all_descendants(self) -> List['CellNode']:
        """获取所有后代节点
        
        Returns:
            所有后代节点的列表
        """
        descendants: List[CellNode] = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
    
    def __repr__(self) -> str:
        return f"CellNode(id={self.cell_id}, indent={self.indent_level})"
