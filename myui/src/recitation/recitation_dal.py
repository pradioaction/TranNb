import logging
from typing import List, Optional
from .database import DatabaseManager
from .models import Book, Word, UserStudy
from .dal.book_dal import BookDAL
from .dal.word_dal import WordDAL
from .dal.user_study_dal import UserStudyDAL
from .dal.stat_dal import StatDAL

logger = logging.getLogger(__name__)


class RecitationDAL:
    """背诵模式数据访问层 - 组合各个子 DAL 模块"""
    
    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager
        self.book_dal = BookDAL(db_manager)
        self.word_dal = WordDAL(db_manager)
        self.user_study_dal = UserStudyDAL(db_manager)
        self.stat_dal = StatDAL(db_manager)
    
    # ==================== 词书相关 ====================
    def add_book(self, book: Book) -> Optional[Book]:
        return self.book_dal.add_book(book)
    
    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        return self.book_dal.get_book_by_id(book_id)
    
    def get_all_books(self) -> List[Book]:
        return self.book_dal.get_all_books()
    
    def update_book(self, book: Book) -> bool:
        return self.book_dal.update_book(book)
    
    def delete_book(self, book_id: int) -> bool:
        return self.book_dal.delete_book(book_id)
    
    # ==================== 单词相关 ====================
    def add_word(self, word: Word) -> Optional[Word]:
        return self.word_dal.add_word(word)
    
    def add_words_batch(self, words: List[Word]) -> int:
        return self.word_dal.add_words_batch(words)
    
    def get_word_by_id(self, word_id: int) -> Optional[Word]:
        return self.word_dal.get_word_by_id(word_id)
    
    def get_words_by_book_id(self, book_id: int) -> List[Word]:
        return self.word_dal.get_words_by_book_id(book_id)
    
    def get_unstudied_words(self, book_id: int, limit: Optional[int] = None) -> List[Word]:
        return self.word_dal.get_unstudied_words(book_id, limit)
    
    def get_words_for_review(self, book_id: int, limit: Optional[int] = None) -> List[Word]:
        return self.word_dal.get_words_for_review(book_id, limit)
    
    def update_word(self, word: Word) -> bool:
        return self.word_dal.update_word(word)
    
    def delete_word(self, word_id: int) -> bool:
        return self.word_dal.delete_word(word_id)
    
    def check_word_exists_in_book(self, book_id: int, word_text: str) -> bool:
        return self.word_dal.check_word_exists_in_book(book_id, word_text)
    
    def search_words(self, search_text: str, book_id: Optional[int] = None) -> List[Word]:
        return self.word_dal.search_words(search_text, book_id)
    
    # ==================== 学习记录相关 ====================
    def add_user_study(self, user_study: UserStudy) -> Optional[UserStudy]:
        return self.user_study_dal.add_user_study(user_study)
    
    def get_user_study_by_word_id(self, book_id: int, word_id: int) -> Optional[UserStudy]:
        return self.user_study_dal.get_user_study_by_word_id(book_id, word_id)
    
    def get_user_studies_by_book_id(self, book_id: int) -> List[UserStudy]:
        return self.user_study_dal.get_user_studies_by_book_id(book_id)
    
    def update_user_study(self, user_study: UserStudy) -> bool:
        return self.user_study_dal.update_user_study(user_study)
    
    def delete_user_study(self, user_study_id: int) -> bool:
        return self.user_study_dal.delete_user_study(user_study_id)
    
    # ==================== 统计相关 ====================
    def get_book_progress(self, book_id: int) -> dict:
        return self.stat_dal.get_book_progress(book_id)
    
    def get_book_detailed_stats(self, book_id: int) -> dict:
        return self.stat_dal.get_book_detailed_stats(book_id)
