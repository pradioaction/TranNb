import logging
from typing import List, Optional
from datetime import datetime
from ..models import Book

logger = logging.getLogger(__name__)


class BookDAL:
    """词书数据访问层"""
    
    def __init__(self, db_manager):
        self._db_manager = db_manager
    
    def add_book(self, book: Book) -> Optional[Book]:
        """添加词书"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO book (name, path, count, create_time) VALUES (?, ?, ?, ?)',
                    (book.name, book.path, book.count, book.create_time or datetime.now())
                )
                book.id = cursor.lastrowid
                conn.commit()
                logger.info(f"添加词书成功: {book.name}")
                return book
        except Exception as e:
            logger.error(f"添加词书失败: {e}", exc_info=True)
            return None
    
    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        """根据ID获取词书"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM book WHERE id = ?', (book_id,))
                row = cursor.fetchone()
                return self._row_to_book(row) if row else None
        except Exception as e:
            logger.error(f"获取词书失败: {e}", exc_info=True)
            return None
    
    def get_all_books(self) -> List[Book]:
        """获取所有词书"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM book ORDER BY create_time DESC')
                rows = cursor.fetchall()
                return [self._row_to_book(row) for row in rows]
        except Exception as e:
            logger.error(f"获取词书列表失败: {e}", exc_info=True)
            return []
    
    def update_book(self, book: Book) -> bool:
        """更新词书"""
        if not book.id:
            return False
        
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE book SET name = ?, path = ?, count = ? WHERE id = ?',
                    (book.name, book.path, book.count, book.id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新词书失败: {e}", exc_info=True)
            return False
    
    def delete_book(self, book_id: int) -> bool:
        """删除词书"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM book WHERE id = ?', (book_id,))
                conn.commit()
                logger.info(f"删除词书成功: {book_id}")
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除词书失败: {e}", exc_info=True)
            return False
    
    def _row_to_book(self, row) -> Book:
        return Book(
            id=row['id'],
            name=row['name'],
            path=row['path'],
            count=row['count'],
            create_time=row['create_time']
        )
