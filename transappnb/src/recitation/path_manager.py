import os
import stat
from pathlib import Path
from typing import Optional


class PathManager:
    """背诵模式路径管理器 - 负责工作区隔离的路径管理"""
    
    DATA_DIR_NAME = ".TransRead"
    DB_FILENAME = "words.db"
    CONFIG_FILENAME = "studywordmode.json"
    
    def __init__(self, workspace_path: Optional[str] = None):
        self._workspace_path: Optional[Path] = None
        if workspace_path:
            self.set_workspace(workspace_path)
    
    def set_workspace(self, workspace_path: str):
        """
        设置工作区路径
        
        Args:
            workspace_path: 工作区路径
        """
        self._workspace_path = Path(workspace_path).resolve()
    
    def get_workspace(self) -> Optional[str]:
        """
        获取当前工作区路径
        
        Returns:
            工作区路径，若未设置则返回None
        """
        return str(self._workspace_path) if self._workspace_path else None
    
    def get_data_dir(self) -> Optional[Path]:
        """
        获取背诵模式数据目录路径
        
        Returns:
            数据目录Path对象，若工作区未设置则返回None
        """
        if not self._workspace_path:
            return None
        return self._workspace_path / self.DATA_DIR_NAME
    
    def get_db_path(self) -> Optional[Path]:
        """
        获取数据库文件路径
        
        Returns:
            数据库文件Path对象，若工作区未设置则返回None
        """
        data_dir = self.get_data_dir()
        if not data_dir:
            return None
        return data_dir / self.DB_FILENAME
    
    def get_config_path(self) -> Optional[Path]:
        """
        获取配置文件路径
        
        Returns:
            配置文件Path对象，若工作区未设置则返回None
        """
        data_dir = self.get_data_dir()
        if not data_dir:
            return None
        return data_dir / self.CONFIG_FILENAME
    
    def ensure_data_dir(self) -> bool:
        """
        确保数据目录存在，不存在则创建并设为隐藏（Windows）
        
        Returns:
            是否成功
        """
        data_dir = self.get_data_dir()
        if not data_dir:
            return False
        
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            
            if os.name == 'nt':
                os.chmod(str(data_dir), os.stat(str(data_dir)).st_mode | stat.FILE_ATTRIBUTE_HIDDEN)
            
            return True
        except Exception as e:
            print(f"创建数据目录失败: {e}")
            return False
    
    def is_valid(self) -> bool:
        """
        检查路径管理器是否有效（是否已设置工作区）
        
        Returns:
            是否有效
        """
        return self._workspace_path is not None
