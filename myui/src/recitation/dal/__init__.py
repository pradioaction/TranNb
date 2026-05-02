# 导出各个子 DAL 类
from .book_dal import BookDAL
from .word_dal import WordDAL
from .user_study_dal import UserStudyDAL
from .stat_dal import StatDAL

__all__ = [
    'BookDAL',
    'WordDAL',
    'UserStudyDAL',
    'StatDAL'
]

# 保持向后兼容：让 from recitation.dal import RecitationDAL 能工作
# 但不在这里导入 RecitationDAL，避免循环导入
def __getattr__(name):
    if name == 'RecitationDAL':
        from ..recitation_dal import RecitationDAL
        return RecitationDAL
    raise AttributeError(f"module {__name__} has no attribute {name}")

