import os
from pathlib import Path
from typing import List, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QFileSystemWatcher
from settingmanager.settings_manager import SettingsManager
from utils.file_utils import FileUtils


class WorkspaceManager(QObject):
    """工作区管理器"""
    
    workspace_changed = pyqtSignal(str)
    files_changed = pyqtSignal()
    
    def __init__(self, settings_manager: SettingsManager):
        super().__init__()
        self._settings_manager = settings_manager
        self._current_path: Optional[Path] = None
        self._file_watcher = QFileSystemWatcher()
        self._connect_watcher_signals()
        # 不在构造时自动加载，等外部明确调用
        # self._load_current_workspace()
    
    def _connect_watcher_signals(self):
        """连接文件系统监听器信号"""
        self._file_watcher.directoryChanged.connect(self._on_directory_changed)
        self._file_watcher.fileChanged.connect(self._on_file_changed)
    
    def load_workspace(self):
        """加载当前工作区（外部调用）"""
        path = self._settings_manager.get_workspace_path()
        if path:
            return self.set_workspace(path, save=False)
        return False
    
    def _load_current_workspace(self):
        """加载当前工作区（内部使用）"""
        path = self._settings_manager.get_workspace_path()
        if path:
            self.set_workspace(path, save=False)
    
    def set_workspace(self, path: str, save: bool = True) -> bool:
        """
        设置工作区路径
        
        Args:
            path: 工作区路径
            save: 是否保存到配置
            
        Returns:
            是否设置成功
        """
        try:
            normalized_path = FileUtils.normalize_path(path)
            
            valid, error_msg = self.validate_workspace_path(str(normalized_path))
            if not valid:
                print(f"无效的工作区路径: {error_msg}")
                return False
            
            self._clear_watcher()
            self._current_path = normalized_path
            
            if save:
                self._settings_manager.set_workspace_path(str(self._current_path))
            
            self._setup_watcher()
            self.workspace_changed.emit(str(self._current_path))
            self.files_changed.emit()
            
            return True
        except Exception as e:
            print(f"设置工作区失败: {e}")
            return False
    
    def get_workspace(self) -> Optional[str]:
        """
        获取当前工作区路径
        
        Returns:
            工作区路径，若未设置则返回 None
        """
        return str(self._current_path) if self._current_path else None
    
    def validate_workspace_path(self, path: str) -> tuple[bool, str]:
        """
        验证工作区路径
        
        Args:
            path: 待验证的路径
            
        Returns:
            (是否有效, 错误信息)
        """
        path_obj = Path(path)
        
        if not path_obj.exists():
            return False, "路径不存在"
        
        if not path_obj.is_dir():
            return False, "不是一个目录"
        
        has_perm, perm_msg = FileUtils.check_directory_permissions(path)
        if not has_perm:
            return False, perm_msg
        
        return True, ""
    
    def _clear_watcher(self):
        """清除文件系统监听器"""
        if self._file_watcher.directories():
            self._file_watcher.removePaths(self._file_watcher.directories())
        if self._file_watcher.files():
            self._file_watcher.removePaths(self._file_watcher.files())
    
    def _setup_watcher(self):
        """设置文件系统监听器"""
        if self._current_path and self._current_path.exists():
            self._file_watcher.addPath(str(self._current_path))
    
    def _on_directory_changed(self, path: str):
        """目录变化回调"""
        if self._current_path and Path(path) == self._current_path:
            self.files_changed.emit()
    
    def _on_file_changed(self, path: str):
        """文件变化回调"""
        self.files_changed.emit()
    
    def get_transnb_files(self, recursive: bool = False) -> List[str]:
        """
        获取工作区下所有 .transnb 文件
        
        Args:
            recursive: 是否递归获取
            
        Returns:
            .transnb 文件路径列表
        """
        if not self._current_path or not self._current_path.exists():
            return []
        
        files = []
        pattern = f"**/*{FileUtils.TRANSNB_EXTENSION}" if recursive else f"*{FileUtils.TRANSNB_EXTENSION}"
        
        try:
            for file_path in self._current_path.glob(pattern):
                if file_path.is_file():
                    files.append(str(file_path))
        except Exception as e:
            print(f"获取文件列表失败: {e}")
        
        return sorted(files)
