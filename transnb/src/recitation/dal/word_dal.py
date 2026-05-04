import logging
from typing import List, Optional
from ..models import Word

logger = logging.getLogger(__name__)


class WordDAL:
    """单词数据访问层"""
    
    def __init__(self, db_manager):
        self._db_manager = db_manager
    
    def _update_book_count(self, book_id: int, delta: int):
        """更新词书的单词数量
        Args:
            book_id: 词书ID
            delta: 变更数量（+1或-1）
        """
        try:
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE book SET count = count + ? WHERE id = ?',
                    (delta, book_id)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"更新词书数量失败: {e}", exc_info=True)
    
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
                # 更新词书数量
                self._update_book_count(word.book_id, 1)
                return word
        except Exception as e:
            logger.error(f"添加单词失败: {e}", exc_info=True)
            return None
    
    def add_words_batch(self, words: List[Word]) -> int:
        """批量添加单词"""
        if not words:
            return 0
        
        try:
            # 按词书分组统计单词数量
            from collections import defaultdict
            book_word_counts = defaultdict(int)
            for word in words:
                book_word_counts[word.book_id] += 1
            
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
                count = cursor.rowcount
                conn.commit()
                
                # 更新每个词书的数量
                for book_id, added_count in book_word_counts.items():
                    self._update_book_count(book_id, added_count)
                
                return count
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
            import random
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT w.* FROM word w
                    LEFT JOIN user_study us ON w.id = us.word_id AND w.book_id = ?
                    WHERE w.book_id = ? AND us.id IS NULL
                '''
                params = [book_id, book_id]
                
                # 不使用数据库的 LIMIT，而是获取所有然后随机抽取，这样更公平
                cursor.execute(query, params)
                rows = cursor.fetchall()
                words = [self._row_to_word(row) for row in rows]
                
                if limit and len(words) > limit:
                    random.shuffle(words)
                    return words[:limit]
                
                return words
        except Exception as e:
            logger.error(f"获取未学习单词失败: {e}", exc_info=True)
            return []
    
    def get_words_for_review(self, book_id: int, limit: Optional[int] = None) -> List[Word]:
        """获取需要复习的单词"""
        try:
            import random
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
                
                # 获取所有待复习单词，然后随机抽取指定数量
                cursor.execute(query, params)
                rows = cursor.fetchall()
                words = [self._row_to_word(row) for row in rows]
                
                if limit and len(words) > limit:
                    random.shuffle(words)
                    return words[:limit]
                
                return words
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
        book_id = None
        try:
            # 先获取要删除的单词信息
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT book_id FROM word WHERE id = ?', (word_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                book_id = row['book_id']
            
            # 再删除单词
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM word WHERE id = ?', (word_id,))
                success = cursor.rowcount > 0
                conn.commit()
                
                return success
        except Exception as e:
            logger.error(f"删除单词失败: {e}", exc_info=True)
            return False
        finally:
            # 在外面更新词书数量
            if book_id:
                try:
                    self._update_book_count(book_id, -1)
                except Exception as e:
                    logger.error(f"更新词书数量失败: {e}", exc_info=True)
    
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
    
    def search_word_exact_lower(self, word_text: str, book_id: Optional[int] = None) -> Optional[Word]:
        """全小写精确搜索单词（在所有词书或指定词书中）"""
        try:
            # 先将输入转为小写
            search_word = word_text.lower()
            
            with self._db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                if book_id:
                    query = '''
                        SELECT * FROM word 
                        WHERE book_id = ? AND LOWER(word) = ?
                        LIMIT 1
                    '''
                    cursor.execute(query, (book_id, search_word))
                else:
                    query = '''
                        SELECT * FROM word 
                        WHERE LOWER(word) = ?
                        LIMIT 1
                    '''
                    cursor.execute(query, (search_word,))
                
                row = cursor.fetchone()
                return self._row_to_word(row) if row else None
        except Exception as e:
            logger.error(f"精确搜索单词失败: {e}", exc_info=True)
            return None
    
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
