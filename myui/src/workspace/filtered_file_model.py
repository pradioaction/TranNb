from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtCore import QModelIndex


class FilteredFileModel(QFileSystemModel):
    """自定义文件系统模型，用于过滤显示 .transnb 后缀的文件和所有文件夹"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.allowed_extensions = {'.transnb'}
    
    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        重写过滤方法，决定哪些行应该被显示
        
        Args:
            source_row: 源模型中的行号
            source_parent: 源模型中的父索引
            
        Returns:
            bool: 如果应该显示该行则返回 True，否则返回 False
        """
        index = self.index(source_row, 0, source_parent)
        file_path = self.filePath(index)
        
        if self.isDir(index):
            return True
        
        if self.is_file_allowed(file_path):
            return True
        
        return False
    
    def is_file_allowed(self, file_path: str) -> bool:
        """
        检查文件是否允许显示
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 如果文件允许显示则返回 True
        """
        for ext in self.allowed_extensions:
            if file_path.lower().endswith(ext):
                return True
        return False
    
    def add_allowed_extension(self, extension: str):
        """
        添加允许显示的文件后缀
        
        Args:
            extension: 文件后缀，例如 '.txt'
        """
        if not extension.startswith('.'):
            extension = '.' + extension
        self.allowed_extensions.add(extension.lower())
    
    def remove_allowed_extension(self, extension: str):
        """
        移除允许显示的文件后缀
        
        Args:
            extension: 文件后缀，例如 '.txt'
        """
        if not extension.startswith('.'):
            extension = '.' + extension
        self.allowed_extensions.discard(extension.lower())
