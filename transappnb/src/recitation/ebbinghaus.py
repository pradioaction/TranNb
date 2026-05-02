import math
import logging
from datetime import datetime, timedelta
from typing import Tuple

logger = logging.getLogger(__name__)


class EbbinghausAlgorithm:
    """艾宾浩斯遗忘曲线算法 - 计算复习权重和下次复习时间"""
    
    STAGE_INTERVALS = [
        timedelta(minutes=5),
        timedelta(minutes=30),
        timedelta(hours=12),
        timedelta(days=1),
        timedelta(days=2),
        timedelta(days=4),
        timedelta(days=7),
        timedelta(days=15),
        timedelta(days=30),
    ]
    
    MAX_STAGE = len(STAGE_INTERVALS) - 1
    
    def __init__(self):
        pass
    
    def calculate_initial_state(self) -> Tuple[int, float, datetime, datetime]:
        """
        计算初始学习状态
        
        Returns:
            (stage, weight, last_review, next_review)
        """
        now = datetime.now()
        stage = 0
        weight = 1.0
        next_review = now + self.STAGE_INTERVALS[0]
        return stage, weight, now, next_review
    
    def calculate_review_result(self, stage: int, weight: float, last_review: datetime, is_correct: bool) -> Tuple[int, float, datetime, datetime]:
        """
        计算复习后的状态
        
        Args:
            stage: 当前阶段
            weight: 当前权重
            last_review: 上次复习时间
            is_correct: 复习是否正确
        
        Returns:
            (new_stage, new_weight, new_last_review, new_next_review)
        """
        now = datetime.now()
        new_last_review = now
        
        if is_correct:
            new_stage = min(stage + 1, self.MAX_STAGE)
            interval = self.STAGE_INTERVALS[new_stage]
            new_next_review = now + interval
            new_weight = self._calculate_weight(new_stage, now, new_next_review)
        else:
            new_stage = max(stage - 1, 0)
            interval = self.STAGE_INTERVALS[new_stage]
            new_next_review = now + interval
            new_weight = self._calculate_weight(new_stage, now, new_next_review)
        
        return new_stage, new_weight, new_last_review, new_next_review
    
    def _calculate_weight(self, stage: int, now: datetime, next_review: datetime) -> float:
        """
        计算复习权重
        
        使用指数衰减算法，权重随时间递减，接近下次复习时间时权重增加
        
        Args:
            stage: 当前阶段
            now: 当前时间
            next_review: 下次复习时间
        
        Returns:
            复习权重
        """
        time_until_review = (next_review - now).total_seconds()
        total_interval = self.STAGE_INTERVALS[stage].total_seconds()
        
        if total_interval <= 0:
            return 1.0
        
        progress = 1.0 - (time_until_review / total_interval)
        progress = max(0.0, min(1.0, progress))
        
        weight = 1.0 + (1.0 - stage / (self.MAX_STAGE + 1)) * math.exp(progress * 3)
        
        return weight
    
    def update_weight_current(self, stage: int, last_review: datetime, next_review: datetime) -> float:
        """
        更新当前时间点的权重
        
        Args:
            stage: 当前阶段
            last_review: 上次复习时间
            next_review: 下次复习时间
        
        Returns:
            当前权重
        """
        now = datetime.now()
        return self._calculate_weight(stage, now, next_review)
