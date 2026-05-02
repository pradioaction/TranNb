import logging
from typing import List, Optional
from ..models import UserStudy

logger = logging.getLogger(__name__)


class UserStudyDAL:
    """学习记录数据访问层"""
    
    def __init__(self, db_manager):
        self._db_manager = db_manager
    
    def add_user_study(self, user_study: UserStudy) -> Optional[UserStudy]:
        """添加学习记录"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO user_study (book_id, word_id, stage, weight, last_review, next_review) VALUES (?, ?, ?, ?, ?, ?)',
                    (user_study.book_id, user_study.word_id, user_study.stage, user_study.weight, user_study.last_review, user_study.next_review)
                )
                user_study.id = cursor.lastrowid
                conn.commit()
                return user_study
        except Exception as e:
            logger.error(f"添加学习记录失败: {e}", exc_info=True)
            return None
    
    def get_user_study_by_word_id(self, book_id: int, word_id: int) -> Optional[UserStudy]:
        """根据单词ID获取学习记录"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM user_study WHERE book_id = ? AND word_id = ?', (book_id, word_id))
                row = cursor.fetchone()
                return self._row_to_user_study(row) if row else None
        except Exception as e:
            logger.error(f"获取学习记录失败: {e}", exc_info=True)
            return None
    
    def get_user_studies_by_book_id(self, book_id: int) -> List[UserStudy]:
        """获取词书的所有学习记录"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM user_study WHERE book_id = ?', (book_id,))
                rows = cursor.fetchall()
                return [self._row_to_user_study(row) for row in rows]
        except Exception as e:
            logger.error(f"获取学习记录列表失败: {e}", exc_info=True)
            return []
    
    def update_user_study(self, user_study: UserStudy) -> bool:
        """更新学习记录"""
        if not user_study.id:
            return False
        
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE user_study SET stage = ?, weight = ?, last_review = ?, next_review = ? WHERE id = ?',
                    (user_study.stage, user_study.weight, user_study.last_review, user_study.next_review, user_study.id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新学习记录失败: {e}", exc_info=True)
            return False
    
    def delete_user_study(self, user_study_id: int) -> bool:
        """删除学习记录"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM user_study WHERE id = ?', (user_study_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除学习记录失败: {e}", exc_info=True)
            return False
    
    def _row_to_user_study(self, row) -> UserStudy:
        return UserStudy(
            id=row['id'],
            book_id=row['book_id'],
            word_id=row['word_id'],
            stage=row['stage'],
            weight=row['weight'],
            last_review=row['last_review'],
            next_review=row['next_review']
        )
