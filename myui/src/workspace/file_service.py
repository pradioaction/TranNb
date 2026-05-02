import os
import json
from pathlib import Path
from typing import Optional, Dict
from PyQt5.QtCore import QObject, pyqtSignal
from workspace.workspace_manager import WorkspaceManager
from utils.file_utils import FileUtils


class FileService(QObject):
    """文件服务层：管理文件的打开、保存、修改等操作"""
    
    file_opened = pyqtSignal(str)
    file_saved = pyqtSignal(str)
    file_modified = pyqtSignal(bool)  # 简化信号，只传递是否修改
    file_closed = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, workspace_manager: WorkspaceManager, cell_manager=None):
        super().__init__()
        self._workspace_manager = workspace_manager
        self._cell_manager = cell_manager
        self._current_file: Optional[str] = None
        self._open_files: Dict[str, bool] = {}
        self._modified: bool = False
    
    def set_cell_manager(self, cell_manager):
        """设置 CellManager 实例"""
        self._cell_manager = cell_manager
    
    def is_file_open(self, file_path: str = None) -> bool:
        """检查文件是否已打开，或检查是否有文件已打开"""
        if file_path is None:
            return self._current_file is not None
        normalized_path = str(FileUtils.normalize_path(file_path))
        return normalized_path in self._open_files
    
    def get_current_file(self) -> Optional[str]:
        """获取当前打开的文件"""
        return self._current_file
    
    def is_modified(self) -> bool:
        """检查当前文件是否有未保存的修改"""
        return self._modified
    
    def set_modified(self, modified: bool):
        """设置当前文件的修改状态"""
        if self._current_file:
            self._modified = modified
            self._open_files[self._current_file] = modified
            self.file_modified.emit(modified)
    
    def create_new_file(self, filename: str) -> Optional[str]:
        """
        在工作区创建新文件并打开
        
        Args:
            filename: 文件名
            
        Returns:
            新文件路径，失败返回 None
        """
        try:
            workspace = self._workspace_manager.get_workspace()
            if not workspace:
                self.error_occurred.emit("工作区未设置")
                return None
            
            normalized_filename = FileUtils.ensure_transnb_extension(filename)
            valid, error_msg = FileUtils.validate_filename(Path(normalized_filename).name, workspace)
            if not valid:
                self.error_occurred.emit(error_msg)
                return None
            
            file_path = str(Path(workspace) / normalized_filename)
            
            # 先关闭当前文件
            if self._current_file:
                self.close_file(emit_signal=False)
            
            # 创建空文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({'version': '1.0', 'cells': []}, f, indent=2)
            
            self._current_file = file_path
            self._open_files[file_path] = False
            self._modified = False
            self.file_opened.emit(file_path)
            return file_path
        except Exception as e:
            self.error_occurred.emit(f"创建文件失败: {str(e)}")
            return None
    
    def create_file_with_content(self, filename: str, content: str) -> Optional[str]:
        """
        在工作区创建新文件并加载文本内容
        
        Args:
            filename: 文件名
            content: 要加载的文本内容
            
        Returns:
            新文件路径，失败返回 None
        """
        try:
            workspace = self._workspace_manager.get_workspace()
            if not workspace:
                self.error_occurred.emit("工作区未设置")
                return None
            
            normalized_filename = FileUtils.ensure_transnb_extension(filename)
            valid, error_msg = FileUtils.validate_filename(Path(normalized_filename).name, workspace)
            if not valid:
                self.error_occurred.emit(error_msg)
                return None
            
            file_path = str(Path(workspace) / normalized_filename)
            
            # 先关闭当前文件
            if self._current_file:
                self.close_file(emit_signal=False)
            
            # 准备要保存的单元格数据
            lines = content.replace('\r\n', '\n').split('\n')
            paragraphs = [line.strip() for line in lines if line.strip()]
            cells_data = [{
                'type': 'markdown',
                'content': paragraph,
                'output': ''
            } for paragraph in paragraphs]
            
            # 创建包含完整内容的文件
            data = {
                'version': '1.0',
                'cells': cells_data
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self._current_file = file_path
            self._open_files[file_path] = False
            self._modified = False
            
            # 直接发出信号，让 on_file_opened 从文件加载内容
            self.file_opened.emit(file_path)
            
            # 标记为已修改（因为是新导入的内容）
            self.set_modified(True)
            return file_path
        except Exception as e:
            self.error_occurred.emit(f"创建文件失败: {str(e)}")
            return None
    
    def open_file(self, file_path: str, check_unsaved: bool = True) -> bool:
        """
        打开文件
        
        Args:
            file_path: 文件路径
            check_unsaved: 是否检查未保存的修改（由外部处理时设为 False）
            
        Returns:
            是否成功打开
        """
        try:
            normalized_path = str(FileUtils.normalize_path(file_path))
            
            # 检查是否是同一文件
            if self._current_file == normalized_path:
                return True
            
            # 如果是工作区外的文件，尝试设置该文件所在目录为新工作区
            file_dir = str(Path(normalized_path).parent)
            current_workspace = self._workspace_manager.get_workspace()
            
            if current_workspace and not FileUtils.is_path_in_workspace(normalized_path, current_workspace):
                # 切换到文件所在目录作为新工作区
                self._workspace_manager.set_workspace(file_dir)
            
            # 如果当前没有工作区，设置文件所在目录为工作区
            if not self._workspace_manager.get_workspace():
                self._workspace_manager.set_workspace(file_dir)
            
            if not Path(normalized_path).exists():
                self.error_occurred.emit("文件不存在")
                return False
            
            if not normalized_path.endswith(FileUtils.TRANSNB_EXTENSION):
                self.error_occurred.emit("仅支持 .transnb 格式文件")
                return False
            
            # 先关闭当前文件
            if self._current_file:
                self.close_file(emit_signal=False)
            
            self._current_file = normalized_path
            self._open_files[normalized_path] = False
            self._modified = False
            self.file_opened.emit(normalized_path)
            return True
        except Exception as e:
            self.error_occurred.emit(f"打开文件失败: {str(e)}")
            return False
    
    def save_file(self) -> bool:
        """
        保存当前文件
        
        Returns:
            是否成功保存
        """
        if not self._current_file:
            self.error_occurred.emit("没有打开的文件")
            return False
        
        return self._save_to_path(self._current_file)
    
    def save_file_as(self, new_file_path: str) -> bool:
        """
        另存为
        
        Args:
            new_file_path: 新文件路径
            
        Returns:
            是否成功保存
        """
        try:
            workspace = self._workspace_manager.get_workspace()
            if not workspace:
                self.error_occurred.emit("工作区未设置")
                return False
            
            if not FileUtils.is_path_in_workspace(new_file_path, workspace):
                self.error_occurred.emit("目标路径不在工作区内")
                return False
            
            normalized_path = str(FileUtils.normalize_path(new_file_path))
            normalized_path = FileUtils.ensure_transnb_extension(normalized_path)
            
            if self._save_to_path(normalized_path):
                if self._current_file:
                    self.close_file()
                
                self._current_file = normalized_path
                self._open_files[normalized_path] = False
                self._modified = False
                self.file_opened.emit(normalized_path)
                return True
            
            return False
        except Exception as e:
            self.error_occurred.emit(f"另存为失败: {str(e)}")
            return False
    
    def _save_to_path(self, file_path: str) -> bool:
        """
        保存到指定路径（内部方法）
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功保存
        """
        try:
            if not self._cell_manager:
                self.error_occurred.emit("CellManager 未设置")
                return False
            
            self._cell_manager.save_to_file(file_path)
            
            self._modified = False
            self._open_files[file_path] = False
            self.file_saved.emit(file_path)
            return True
        except Exception as e:
            self.error_occurred.emit(f"保存文件失败: {str(e)}")
            return False
    
    def rename_file(self, old_path: str, new_filename: str) -> bool:
        """
        重命名文件
        
        Args:
            old_path: 原文件路径
            new_filename: 新文件名
            
        Returns:
            是否成功重命名
        """
        try:
            workspace = self._workspace_manager.get_workspace()
            if not workspace:
                self.error_occurred.emit("工作区未设置")
                return False
            
            if not FileUtils.is_path_in_workspace(old_path, workspace):
                self.error_occurred.emit("原文件不在工作区内")
                return False
            
            old_normalized = str(FileUtils.normalize_path(old_path))
            
            if not Path(old_normalized).exists():
                self.error_occurred.emit("原文件不存在")
                return False
            
            new_filename = FileUtils.ensure_transnb_extension(new_filename)
            valid, error_msg = FileUtils.validate_filename(Path(new_filename).name, workspace)
            if not valid:
                self.error_occurred.emit(error_msg)
                return False
            
            new_normalized = str(Path(workspace) / Path(new_filename).name)
            
            if old_normalized == new_normalized:
                return True
            
            is_current = old_normalized == self._current_file
            
            Path(old_normalized).rename(new_normalized)
            
            if old_normalized in self._open_files:
                self._open_files[new_normalized] = self._open_files[old_normalized]
                del self._open_files[old_normalized]
            
            if is_current:
                self._current_file = new_normalized
                self.file_opened.emit(new_normalized)
            
            return True
        except Exception as e:
            self.error_occurred.emit(f"重命名文件失败: {str(e)}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功删除
        """
        try:
            workspace = self._workspace_manager.get_workspace()
            if not workspace:
                self.error_occurred.emit("工作区未设置")
                return False
            
            if not FileUtils.is_path_in_workspace(file_path, workspace):
                self.error_occurred.emit("文件不在工作区内")
                return False
            
            normalized_path = str(FileUtils.normalize_path(file_path))
            
            if not Path(normalized_path).exists():
                self.error_occurred.emit("文件不存在")
                return False
            
            if normalized_path == self._current_file:
                self.close_file()
            
            if normalized_path in self._open_files:
                del self._open_files[normalized_path]
            
            Path(normalized_path).unlink()
            return True
        except Exception as e:
            self.error_occurred.emit(f"删除文件失败: {str(e)}")
            return False
    
    def close_file(self, emit_signal: bool = True):
        """
        关闭当前文件
        
        Args:
            emit_signal: 是否发出 file_closed 信号
        """
        if self._current_file:
            old_file = self._current_file
            self._current_file = None
            self._modified = False
            if old_file in self._open_files:
                del self._open_files[old_file]
            if emit_signal:
                self.file_closed.emit()
