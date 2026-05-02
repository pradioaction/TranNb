import os
import stat
from pathlib import Path
from typing import Optional, Tuple


class FileUtils:
    """文件工具类"""
    
    WINDOWS_ILLEGAL_CHARS = '\\/:*?"<>|'
    TRANSNB_EXTENSION = '.transnb'
    
    @staticmethod
    def validate_filename(filename: str, directory: Optional[str] = None) -> Tuple[bool, str]:
        """
        校验文件名
        
        Args:
            filename: 待校验的文件名
            directory: 可选，同目录路径，用于检查文件是否已存在
            
        Returns:
            (是否有效, 错误信息)
        """
        if not filename or not filename.strip():
            return False, "文件名不能为空"
        
        filename = filename.strip()
        
        for char in FileUtils.WINDOWS_ILLEGAL_CHARS:
            if char in filename:
                return False, f"文件名不能包含非法字符: {char}"
        
        if directory:
            dir_path = Path(directory)
            file_path = dir_path / filename
            if file_path.exists():
                return False, "同名文件已存在"
        
        return True, ""
    
    @staticmethod
    def normalize_path(path: str) -> Path:
        """
        规范化路径
        
        Args:
            path: 原始路径
            
        Returns:
            规范化后的 Path 对象
        """
        return Path(path).resolve()
    
    @staticmethod
    def ensure_transnb_extension(file_path: str) -> str:
        """
        自动补全 .transnb 后缀
        
        Args:
            file_path: 文件路径
            
        Returns:
            补全后缀后的文件路径
        """
        path = Path(file_path)
        if path.suffix.lower() != FileUtils.TRANSNB_EXTENSION:
            return str(path.with_suffix(FileUtils.TRANSNB_EXTENSION))
        return str(path)
    
    @staticmethod
    def is_path_in_workspace(path: str, workspace_path: str) -> bool:
        """
        检查路径是否在工作区内
        
        Args:
            path: 待检查的路径
            workspace_path: 工作区路径
            
        Returns:
            是否在工作区内
        """
        try:
            target_path = FileUtils.normalize_path(path)
            workspace = FileUtils.normalize_path(workspace_path)
            return workspace in target_path.parents or target_path == workspace
        except Exception:
            return False
    
    @staticmethod
    def check_directory_permissions(dir_path: str) -> Tuple[bool, str]:
        """
        检查目录读写权限
        
        Args:
            dir_path: 目录路径
            
        Returns:
            (是否有权限, 错误信息)
        """
        path = Path(dir_path)
        if not path.exists():
            return False, "目录不存在"
        
        if not path.is_dir():
            return False, "不是一个目录"
        
        try:
            if not os.access(str(path), os.R_OK):
                return False, "目录没有读权限"
            if not os.access(str(path), os.W_OK):
                return False, "目录没有写权限"
        except Exception as e:
            return False, f"检查权限失败: {str(e)}"
        
        return True, ""
    
    @staticmethod
    def is_file_readonly(file_path: str) -> bool:
        """
        检查文件是否只读
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否只读
        """
        path = Path(file_path)
        if not path.exists():
            return False
        
        try:
            file_stat = path.stat()
            return not bool(file_stat.st_mode & stat.S_IWRITE)
        except Exception:
            return False
    
    @staticmethod
    def ensure_directory_exists(dir_path: str) -> bool:
        """
        确保目录存在，不存在则创建
        
        Args:
            dir_path: 目录路径
            
        Returns:
            是否成功
        """
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_unique_filename(directory: str, base_name: str, extension: str = TRANSNB_EXTENSION) -> str:
        """
        获取唯一文件名
        
        Args:
            directory: 目录路径
            base_name: 基础文件名（不含后缀）
            extension: 文件后缀
            
        Returns:
            唯一的文件名
        """
        dir_path = Path(directory)
        counter = 1
        filename = f"{base_name}{extension}"
        
        while (dir_path / filename).exists():
            filename = f"{base_name}_{counter}{extension}"
            counter += 1
        
        return filename
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """
        获取文件后缀
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件后缀（包含点）
        """
        return Path(file_path).suffix
    
    @staticmethod
    def get_file_name_without_extension(file_path: str) -> str:
        """
        获取不含后缀的文件名
        
        Args:
            file_path: 文件路径
            
        Returns:
            不含后缀的文件名
        """
        return Path(file_path).stem
