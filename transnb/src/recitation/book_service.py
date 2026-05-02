import logging
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from .models import Book, Word
from .dal import RecitationDAL
from .book_importer import BookImporter
from .path_manager import PathManager

logger = logging.getLogger(__name__)


class BookService:
    """词书管理服务 - 提供词书管理的业务逻辑"""
    
    CONFIG_KEY_CURRENT_BOOK = "current_book_id"
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager):
        self.dal = dal
        self.path_manager = path_manager
        self.book_importer = BookImporter()
        self._config: Dict = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            config_path = self.path_manager.get_config_path()
            if config_path and config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}", exc_info=True)
            self._config = {}
    
    def _save_config(self):
        """保存配置文件"""
        try:
            config_path = self.path_manager.get_config_path()
            if config_path:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}", exc_info=True)
    
    def import_book(self, file_path: str) -> Optional[Book]:
        """
        导入词书
        
        Args:
            file_path: JSON文件路径
        
        Returns:
            导入的词书对象，失败返回None
        """
        book, words = self.book_importer.import_from_file(file_path)
        
        if not book or not words:
            return None
        
        saved_book = self.dal.add_book(book)
        if not saved_book:
            return None
        
        for word in words:
            word.book_id = saved_book.id
        
        count = self.dal.add_words_batch(words)
        logger.info(f"成功导入词书: {saved_book.name}, 单词数: {count}")
        
        return saved_book
    
    def get_all_books(self) -> List[Book]:
        """
        获取所有词书
        
        Returns:
            词书列表
        """
        return self.dal.get_all_books()
    
    def get_book_with_progress(self, book_id: int) -> Optional[Dict]:
        """
        获取词书及其进度信息
        
        Args:
            book_id: 词书ID
        
        Returns:
            包含词书和进度信息的字典，失败返回None
        """
        book = self.dal.get_book_by_id(book_id)
        if not book:
            return None
        
        progress = self.dal.get_book_progress(book_id)
        
        return {
            'book': book,
            'total': progress['total'],
            'studied': progress['studied'],
            'review_due': progress['review_due'],
            'progress': (progress['studied'] / progress['total'] * 100) if progress['total'] > 0 else 0
        }
    
    def get_all_books_with_progress(self) -> List[Dict]:
        """
        获取所有词书及其进度信息
        
        Returns:
            包含词书和进度信息的字典列表
        """
        books = self.get_all_books()
        result = []
        
        for book in books:
            progress = self.dal.get_book_progress(book.id)
            result.append({
                'book': book,
                'total': progress['total'],
                'studied': progress['studied'],
                'review_due': progress['review_due'],
                'progress': (progress['studied'] / progress['total'] * 100) if progress['total'] > 0 else 0
            })
        
        return result
    
    def select_book(self, book_id: int) -> bool:
        """
        选择当前学习的词书
        
        Args:
            book_id: 词书ID
        
        Returns:
            是否成功
        """
        book = self.dal.get_book_by_id(book_id)
        if not book:
            return False
        
        self._config[self.CONFIG_KEY_CURRENT_BOOK] = book_id
        self._save_config()
        logger.info(f"选择词书: {book.name}")
        return True
    
    def get_current_book(self) -> Optional[Book]:
        """
        获取当前选择的词书
        
        Returns:
            词书对象，未选择返回None
        """
        book_id = self._config.get(self.CONFIG_KEY_CURRENT_BOOK)
        if not book_id:
            return None
        
        return self.dal.get_book_by_id(book_id)
    
    def delete_book(self, book_id: int) -> bool:
        """
        删除词书
        
        Args:
            book_id: 词书ID
        
        Returns:
            是否成功
        """
        success = self.dal.delete_book(book_id)
        
        if success:
            current_id = self._config.get(self.CONFIG_KEY_CURRENT_BOOK)
            if current_id == book_id:
                del self._config[self.CONFIG_KEY_CURRENT_BOOK]
                self._save_config()
        
        return success
