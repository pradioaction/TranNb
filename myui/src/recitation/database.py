import sqlite3
import logging
from typing import Optional, ContextManager
from contextlib import contextmanager
from pathlib import Path
from .path_manager import PathManager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器 - 负责数据库连接和表结构创建"""
    
    def __init__(self, path_manager: PathManager):
        self._path_manager = path_manager
        self._db_path: Optional[Path] = None
    
    def initialize(self) -> bool:
        """
        初始化数据库 - 创建数据目录和数据库表
        
        Returns:
            是否成功初始化
        """
        if not self._path_manager.is_valid():
            logger.error("路径管理器未设置工作区")
            return False
        
        if not self._path_manager.ensure_data_dir():
            logger.error("无法创建数据目录")
            return False
        
        self._db_path = self._path_manager.get_db_path()
        if not self._db_path:
            logger.error("无法获取数据库路径")
            return False
        
        try:
            self._create_tables()
            logger.info(f"数据库初始化成功: {self._db_path}")
            return True
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}", exc_info=True)
            return False
    
    def _create_tables(self):
        """创建数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS book (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    count INTEGER DEFAULT 0,
                    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS word (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    word TEXT NOT NULL,
                    phonetic TEXT DEFAULT '',
                    definition TEXT DEFAULT '',
                    example TEXT DEFAULT '',
                    raw_data TEXT DEFAULT '',
                    FOREIGN KEY (book_id) REFERENCES book (id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_study (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    word_id INTEGER NOT NULL,
                    stage INTEGER DEFAULT 0,
                    weight REAL DEFAULT 0.0,
                    last_review TIMESTAMP,
                    next_review TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES book (id) ON DELETE CASCADE,
                    FOREIGN KEY (word_id) REFERENCES word (id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_word_book_id ON word (book_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_study_book_id ON user_study (book_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_study_word_id ON user_study (word_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_study_next_review ON user_study (next_review)')
            
            conn.commit()
    
    @contextmanager
    def get_connection(self) -> ContextManager[sqlite3.Connection]:
        """
        获取数据库连接的上下文管理器
        
        Yields:
            sqlite3.Connection 对象
        """
        if not self._db_path:
            raise RuntimeError("数据库未初始化，请先调用 initialize()")
        
        conn = sqlite3.connect(
            str(self._db_path),
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')  # 关键：启用外键约束
        
        try:
            yield conn
        finally:
            conn.close()
    
    def vacuum(self) -> bool:
        """
        压缩数据库，清理未使用的空间
        
        Returns:
            是否成功
        """
        try:
            # 确保已初始化
            if not self.is_initialized():
                if not self.initialize():
                    logger.error("数据库初始化失败，无法压缩")
                    return False
            
            with self.get_connection() as conn:
                conn.execute('VACUUM')
                conn.commit()
                logger.info(f"数据库压缩成功: {self._db_path}")
                return True
        except Exception as e:
            logger.error(f"数据库压缩失败: {e}", exc_info=True)
            return False
    
    def is_initialized(self) -> bool:
        """
        检查数据库是否已初始化
        
        Returns:
            是否已初始化
        """
        return self._db_path is not None and self._db_path.exists()
