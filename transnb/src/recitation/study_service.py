import logging
import json
import random
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from pathlib import Path
from .models import Book, Word, UserStudy
from .dal import RecitationDAL
from .path_manager import PathManager
from .ebbinghaus import EbbinghausAlgorithm

logger = logging.getLogger(__name__)


class StudyService:
    """学习服务 - 管理学习记录、抽取单词、更新学习进度"""
    
    CONFIG_KEY_DAILY_NEW = "daily_new_words"
    CONFIG_KEY_DAILY_REVIEW = "daily_review_words"
    CONFIG_KEY_TODAY_WORDS = "today_words"  # 每日学习的单词
    CONFIG_KEY_TODAY_DATE = "today_date"    # 今日日期
    
    DEFAULT_DAILY_NEW = 20
    DEFAULT_DAILY_REVIEW = 50
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager):
        self.dal = dal
        self.path_manager = path_manager
        self.ebbinghaus = EbbinghausAlgorithm()
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
    
    def get_daily_new_words(self) -> int:
        """
        获取每日新学单词数量
        
        Returns:
            每日新学单词数量
        """
        return self._config.get(self.CONFIG_KEY_DAILY_NEW, self.DEFAULT_DAILY_NEW)
    
    def set_daily_new_words(self, count: int):
        """
        设置每日新学单词数量
        
        Args:
            count: 每日新学单词数量
        """
        self._config[self.CONFIG_KEY_DAILY_NEW] = max(1, count)
        self._save_config()
    
    def get_daily_review_words(self) -> int:
        """
        获取每日复习单词数量
        
        Returns:
            每日复习单词数量
        """
        return self._config.get(self.CONFIG_KEY_DAILY_REVIEW, self.DEFAULT_DAILY_REVIEW)
    
    def set_daily_review_words(self, count: int):
        """
        设置每日复习单词数量
        
        Args:
            count: 每日复习单词数量
        """
        self._config[self.CONFIG_KEY_DAILY_REVIEW] = max(1, count)
        self._save_config()
    
    def get_study_words(self, book_id: int, count: Optional[int] = None) -> List[Word]:
        """
        获取新学习单词
        
        Args:
            book_id: 词书ID
            count: 单词数量，None则使用每日新学数量
        
        Returns:
            单词列表
        """
        if count is None:
            count = self.get_daily_new_words()
        
        unstudied_words = self.dal.get_unstudied_words(book_id)
        
        if len(unstudied_words) <= count:
            return unstudied_words
        
        random.shuffle(unstudied_words)
        return unstudied_words[:count]
    
    def get_review_words(self, book_id: int, count: Optional[int] = None) -> List[Word]:
        """
        获取复习单词
        
        Args:
            book_id: 词书ID
            count: 单词数量，None则使用每日复习数量
        
        Returns:
            单词列表（按权重从高到低排序）
        """
        if count is None:
            count = self.get_daily_review_words()
        
        return self.dal.get_words_for_review(book_id, count)
    
    def _get_today_key(self, book_id: int) -> str:
        """获取今日单词存储的键名"""
        return f"{self.CONFIG_KEY_TODAY_WORDS}_{book_id}"
    
    def _is_same_day(self) -> bool:
        """检查是否是同一天"""
        today_str = datetime.now().strftime('%Y-%m-%d')
        saved_date = self._config.get(self.CONFIG_KEY_TODAY_DATE, '')
        return today_str == saved_date
    
    def get_today_words(self, book_id: int, force_refresh: bool = False) -> Tuple[List[Word], List[Word]]:
        """
        获取今日学习和复习单词
        
        Args:
            book_id: 词书ID
            force_refresh: 是否强制刷新
        
        Returns:
            (new_words, review_words) 单词列表元组
        """
        # 检查是否需要刷新：强制刷新 或 不是同一天 或 没有记录
        today_key = self._get_today_key(book_id)
        
        if not force_refresh and self._is_same_day() and today_key in self._config:
            # 使用保存的记录
            saved_data = self._config[today_key]
            new_word_ids = saved_data.get('new_words', [])
            review_word_ids = saved_data.get('review_words', [])
            
            # 从数据库加载单词
            new_words = [self.dal.get_word_by_id(wid) for wid in new_word_ids if self.dal.get_word_by_id(wid)]
            review_words = [self.dal.get_word_by_id(wid) for wid in review_word_ids if self.dal.get_word_by_id(wid)]
            
            # 如果单词还在，返回它们
            if new_words or review_words:
                return new_words, review_words
        
        # 需要刷新：获取新单词并保存
        new_words = self.get_study_words(book_id)
        review_words = self.get_review_words(book_id)
        
        # 保存今日记录
        today_str = datetime.now().strftime('%Y-%m-%d')
        self._config[self.CONFIG_KEY_TODAY_DATE] = today_str
        self._config[today_key] = {
            'new_words': [w.id for w in new_words],
            'review_words': [w.id for w in review_words]
        }
        self._save_config()
        
        return new_words, review_words
    
    def refresh_today_words(self, book_id: int) -> Tuple[List[Word], List[Word]]:
        """
        强制刷新今日单词（跳过本轮）
        
        Args:
            book_id: 词书ID
        
        Returns:
            (new_words, review_words) 新的单词列表元组
        """
        return self.get_today_words(book_id, force_refresh=True)
    
    def start_study_word(self, book_id: int, word_id: int) -> Optional[UserStudy]:
        """
        开始学习一个单词
        
        Args:
            book_id: 词书ID
            word_id: 单词ID
        
        Returns:
            学习记录对象，失败返回None
        """
        existing = self.dal.get_user_study_by_word_id(book_id, word_id)
        if existing:
            return existing
        
        stage, weight, last_review, next_review = self.ebbinghaus.calculate_initial_state()
        
        user_study = UserStudy(
            book_id=book_id,
            word_id=word_id,
            stage=stage,
            weight=weight,
            last_review=last_review,
            next_review=next_review
        )
        
        return self.dal.add_user_study(user_study)
    
    def review_word(self, book_id: int, word_id: int, is_correct: bool) -> Optional[UserStudy]:
        """
        复习一个单词
        
        Args:
            book_id: 词书ID
            word_id: 单词ID
            is_correct: 复习是否正确
        
        Returns:
            更新后的学习记录对象，失败返回None
        """
        user_study = self.dal.get_user_study_by_word_id(book_id, word_id)
        if not user_study:
            return None
        
        new_stage, new_weight, new_last_review, new_next_review = self.ebbinghaus.calculate_review_result(
            user_study.stage,
            user_study.weight,
            user_study.last_review or datetime.now(),
            is_correct
        )
        
        user_study.stage = new_stage
        user_study.weight = new_weight
        user_study.last_review = new_last_review
        user_study.next_review = new_next_review
        
        success = self.dal.update_user_study(user_study)
        if success:
            return user_study
        return None
    
    def update_all_weights(self, book_id: int) -> int:
        """
        更新词书所有单词的权重
        
        Args:
            book_id: 词书ID
        
        Returns:
            更新的单词数量
        """
        studies = self.dal.get_user_studies_by_book_id(book_id)
        updated_count = 0
        
        for study in studies:
            if study.last_review and study.next_review:
                new_weight = self.ebbinghaus.update_weight_current(
                    study.stage,
                    study.last_review,
                    study.next_review
                )
                study.weight = new_weight
                if self.dal.update_user_study(study):
                    updated_count += 1
        
        return updated_count
    
    def review_batch_words(self, book_id: int, word_results: List[Tuple[int, bool]]) -> List[Optional[UserStudy]]:
        """
        批量复习单词
        
        Args:
            book_id: 词书ID
            word_results: (word_id, is_correct) 元组列表
        
        Returns:
            学习记录对象列表
        """
        results = []
        for word_id, is_correct in word_results:
            result = self.review_word(book_id, word_id, is_correct)
            results.append(result)
        return results
    
    def start_study_batch_words(self, book_id: int, word_ids: List[int]) -> List[Optional[UserStudy]]:
        """
        批量开始学习单词
        
        Args:
            book_id: 词书ID
            word_ids: 单词ID列表
        
        Returns:
            学习记录对象列表
        """
        results = []
        for word_id in word_ids:
            result = self.start_study_word(book_id, word_id)
            results.append(result)
        return results
