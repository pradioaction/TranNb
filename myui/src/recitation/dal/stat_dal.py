import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class StatDAL:
    """统计数据访问层"""
    
    def __init__(self, db_manager):
        self._db_manager = db_manager
    
    def get_book_progress(self, book_id: int) -> Dict:
        """获取词书学习进度统计"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM word WHERE book_id = ?', (book_id,))
                total = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM user_study WHERE book_id = ?', (book_id,))
                studied = cursor.fetchone()[0]
                
                now = datetime.now()
                cursor.execute('SELECT COUNT(*) FROM user_study WHERE book_id = ? AND next_review <= ?', (book_id, now))
                review_due = cursor.fetchone()[0]
                
                return {
                    'total': total,
                    'studied': studied,
                    'review_due': review_due
                }
        except Exception as e:
            logger.error(f"获取词书进度失败: {e}", exc_info=True)
            return {'total': 0, 'studied': 0, 'review_due': 0}
    
    def get_book_detailed_stats(self, book_id: int) -> Dict:
        """获取词书的详细统计信息"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT name, count FROM book WHERE id = ?', (book_id,))
                book_row = cursor.fetchone()
                name = book_row['name'] if book_row else '未知'
                word_count = book_row['count'] if book_row else 0
                
                cursor.execute('SELECT COUNT(*) FROM word WHERE book_id = ?', (book_id,))
                actual_word_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM user_study WHERE book_id = ?', (book_id,))
                study_count = cursor.fetchone()[0]
                
                return {
                    'name': name,
                    'word_count': actual_word_count,
                    'study_count': study_count
                }
        except Exception as e:
            logger.error(f"获取词书详细统计失败: {e}", exc_info=True)
            return {'name': '未知', 'word_count': 0, 'study_count': 0}
