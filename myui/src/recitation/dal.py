import logging
from typing import List, Optional
from datetime import datetime
from .database import DatabaseManager
from .models import Book, Word, UserStudy

logger = logging.getLogger(__name__)


class RecitationDAL:
    """背诵模式数据访问层 - 提供完整的CRUD操作"""
    
    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager
    
    def add_book(self, book: Book) -> Optional[Book]:
        """
        添加词书
        
        Args:
            book: 词书对象
        
        Returns:
            插入后的词书对象（包含生成的id），失败返回None
        """
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
        """
        根据ID获取词书
        
        Args:
            book_id: 词书ID
        
        Returns:
            词书对象，不存在返回None
        """
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
        """
        获取所有词书
        
        Returns:
            词书列表
        """
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
        """
        更新词书
        
        Args:
            book: 词书对象
        
        Returns:
            是否成功
        """
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
        """
        删除词书（级联删除相关单词和学习记录）
        
        Args:
            book_id: 词书ID
        
        Returns:
            是否成功
        """
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
    
    def add_word(self, word: Word) -> Optional[Word]:
        """
        添加单词
        
        Args:
            word: 单词对象
        
        Returns:
            插入后的单词对象（包含生成的id），失败返回None
        """
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
        """
        批量添加单词
        
        Args:
            words: 单词列表
        
        Returns:
            成功添加的数量
        """
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
        """
        根据ID获取单词
        
        Args:
            word_id: 单词ID
        
        Returns:
            单词对象，不存在返回None
        """
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
        """
        获取词书的所有单词
        
        Args:
            book_id: 词书ID
        
        Returns:
            单词列表
        """
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
        """
        获取词书中未学习的单词
        
        Args:
            book_id: 词书ID
            limit: 返回数量限制
        
        Returns:
            单词列表
        """
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
        """
        获取需要复习的单词（按权重排序）
        
        Args:
            book_id: 词书ID
            limit: 返回数量限制
        
        Returns:
            单词列表
        """
        try:
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
        """
        更新单词
        
        Args:
            word: 单词对象
        
        Returns:
            是否成功
        """
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
        """
        删除单词
        
        Args:
            word_id: 单词ID
        
        Returns:
            是否成功
        """
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM word WHERE id = ?', (word_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除单词失败: {e}", exc_info=True)
            return False
    
    def add_user_study(self, user_study: UserStudy) -> Optional[UserStudy]:
        """
        添加学习记录
        
        Args:
            user_study: 学习记录对象
        
        Returns:
            插入后的学习记录对象（包含生成的id），失败返回None
        """
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
        """
        根据单词ID获取学习记录
        
        Args:
            book_id: 词书ID
            word_id: 单词ID
        
        Returns:
            学习记录对象，不存在返回None
        """
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
        """
        获取词书的所有学习记录
        
        Args:
            book_id: 词书ID
        
        Returns:
            学习记录列表
        """
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
        """
        更新学习记录
        
        Args:
            user_study: 学习记录对象
        
        Returns:
            是否成功
        """
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
        """
        删除学习记录
        
        Args:
            user_study_id: 学习记录ID
        
        Returns:
            是否成功
        """
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM user_study WHERE id = ?', (user_study_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"删除学习记录失败: {e}", exc_info=True)
            return False
    
    def get_book_progress(self, book_id: int) -> dict:
        """
        获取词书学习进度统计
        
        Args:
            book_id: 词书ID
        
        Returns:
            统计字典: {total, studied, review_due}
        """
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
    
    def get_book_detailed_stats(self, book_id: int) -> dict:
        """
        获取词书的详细统计信息（用于删除确认）
        
        Args:
            book_id: 词书ID
        
        Returns:
            详细统计字典
        """
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
    
    def _row_to_book(self, row) -> Book:
        return Book(
            id=row['id'],
            name=row['name'],
            path=row['path'],
            count=row['count'],
            create_time=row['create_time']
        )
    
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
    
    def check_word_exists_in_book(self, book_id: int, word_text: str) -> bool:
        """
        检查单词是否已存在于指定词书中
        
        Args:
            book_id: 词书ID
            word_text: 单词文本
        
        Returns:
            单词是否存在
        """
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
        """
        搜索单词（支持模糊搜索单词和释义）
        
        Args:
            search_text: 搜索文本
            book_id: 可选，限定搜索的词书ID
        
        Returns:
            匹配的单词列表
        """
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
