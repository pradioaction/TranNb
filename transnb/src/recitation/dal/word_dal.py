import logging
from typing import List, Optional
from ..models import Word

logger = logging.getLogger(__name__)


class WordDAL:
    """单词数据访问层"""
    
    def __init__(self, db_manager):
        self._db_manager = db_manager
    
    def add_word(self, word: Word) -> Optional[Word]:
        """添加单词"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO word (book_id, word, phonetic, definition, example, raw_data) VALUES (?, ?, ?, ?, ?, ?)',
                    (word.book_id, word.word, word.phonetic, word.definition, word.example, word.raw_data)
                )
                word.id = cursor.lastrowid
                conn.commit()
                return word
        except Exception as e:
            logger.error(f"添加单词失败: {e}", exc_info=True)
            return None
    
    def add_words_batch(self, words: List[Word]) -> int:
        """批量添加单词"""
        if not words:
            return 0
        
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                word_tuples = [
                    (w.book_id, w.word, w.phonetic, w.definition, w.example, w.raw_data)
                    for w in words
                ]
                cursor.executemany(
                    'INSERT INTO word (book_id, word, phonetic, definition, example, raw_data) VALUES (?, ?, ?, ?, ?, ?)',
                    word_tuples
                )
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"批量添加单词失败: {e}", exc_info=True)
            return 0
    
    def get_word_by_id(self, word_id: int) -> Optional[Word]:
        """根据ID获取单词"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM word WHERE id = ?', (word_id,))
                row = cursor.fetchone()
                return self._row_to_word(row) if row else None
        except Exception as e:
            logger.error(f"获取单词失败: {e}", exc_info=True)
            return None
    
    def get_words_by_book_id(self, book_id: int) -> List[Word]:
        """获取词书的所有单词"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM word WHERE book_id = ?', (book_id,))
                rows = cursor.fetchall()
                return [self._row_to_word(row) for row in rows]
        except Exception as e:
            logger.error(f"获取词书单词失败: {e}", exc_info=True)
            return []
    
    def get_unstudied_words(self, book_id: int, limit: Optional[int] = None) -> List[Word]:
        """获取词书中未学习的单词"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT w.* FROM word w
                    LEFT JOIN user_study us ON w.id = us.word_id AND w.book_id = ?
                    WHERE w.book_id = ? AND us.id IS NULL
                '''
                params = [book_id, book_id]
                
                if limit:
                    query += ' ORDER BY w.id LIMIT ?'
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [self._row_to_word(row) for row in rows]
        except Exception as e:
            logger.error(f"获取未学习单词失败: {e}", exc_info=True)
            return []
    
    def get_words_for_review(self, book_id: int, limit: Optional[int] = None) -> List[Word]:
        """获取需要复习的单词"""
        try:
            from datetime import datetime
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                now = datetime.now()
                query = '''
                    SELECT w.* FROM word w
                    JOIN user_study us ON w.id = us.word_id
                    WHERE w.book_id = ? AND us.next_review <= ?
                    ORDER BY us.weight DESC
                '''
                params = [book_id, now]
                
                if limit:
                    query += ' LIMIT ?'
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [self._row_to_word(row) for row in rows]
        except Exception as e:
            logger.error(f"获取复习单词失败: {e}", exc_info=True)
            return []
    
    def update_word(self, word: Word) -> bool:
        """更新单词"""
        if not word.id:
            return False
        
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE word SET word = ?, phonetic = ?, definition = ?, example = ?, raw_data = ? WHERE id = ?',
                    (word.word, word.phonetic, word.definition, word.example, word.raw_data, word.id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"更新单词失败: {e}", exc_info=True)
            return False
    
    def delete_word(self, word_id: int) -> bool:
        """删除单词"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM word WHERE id = ?', (word_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除单词失败: {e}", exc_info=True)
            return False
    
    def check_word_exists_in_book(self, book_id: int, word_text: str) -> bool:
        """检查单词是否已存在于指定词书中"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM word WHERE book_id = ? AND word = ?', (book_id, word_text))
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            logger.error(f"检查单词是否存在失败: {e}", exc_info=True)
            return False
    
    def search_words(self, search_text: str, book_id: Optional[int] = None) -> List[Word]:
        """搜索单词"""
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                search_pattern = f'%{search_text}%'
                
                if book_id:
                    query = '''
                        SELECT * FROM word 
                        WHERE book_id = ? AND (word LIKE ? OR definition LIKE ?)
                        ORDER BY word
                    '''
                    cursor.execute(query, (book_id, search_pattern, search_pattern))
                else:
                    query = '''
                        SELECT * FROM word 
                        WHERE word LIKE ? OR definition LIKE ?
                        ORDER BY word
                    '''
                    cursor.execute(query, (search_pattern, search_pattern))
                
                rows = cursor.fetchall()
                return [self._row_to_word(row) for row in rows]
        except Exception as e:
            logger.error(f"搜索单词失败: {e}", exc_info=True)
            return []
    
    def _row_to_word(self, row) -> Word:
        raw_data = ''
        try:
            raw_data = row['raw_data']
        except (KeyError, IndexError):
            pass
        return Word(
            id=row['id'],
            book_id=row['book_id'],
            word=row['word'],
            phonetic=row['phonetic'],
            definition=row['definition'],
            example=row['example'],
            raw_data=raw_data
        )
