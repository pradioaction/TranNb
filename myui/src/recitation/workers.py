import logging
from typing import List, Optional, Callable, Any, Tuple
from PyQt5.QtCore import QThread, pyqtSignal as Signal
from .models import Book, Word, UserStudy
from .dal import RecitationDAL
from .book_importer import BookImporter
from .book_service import BookService
from .download_service import DownloadService
from .path_manager import PathManager
from .study_service import StudyService

logger = logging.getLogger(__name__)


class BaseWorker(QThread):
    """基础工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL):
        super().__init__()
        self.dal = dal


class InitializeDBWorker(QThread):
    """数据库初始化工作线程"""
    
    started = Signal()
    finished = Signal(bool)
    error = Signal(str)
    
    def __init__(self, path_manager: PathManager):
        super().__init__()
        self.path_manager = path_manager
    
    def run(self):
        from .database import DatabaseManager
        try:
            self.started.emit()
            db_manager = DatabaseManager(self.path_manager)
            success = db_manager.initialize()
            self.finished.emit(success)
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}", exc_info=True)
            self.error.emit(str(e))


class AddBookWorker(BaseWorker):
    """添加词书工作线程"""
    
    def __init__(self, dal: RecitationDAL, book: Book):
        super().__init__(dal)
        self.book = book
    
    def run(self):
        try:
            self.started.emit()
            result = self.dal.add_book(self.book)
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"添加词书失败: {e}", exc_info=True)
            self.error.emit(str(e))


class GetAllBooksWorker(BaseWorker):
    """获取所有词书工作线程"""
    
    def run(self):
        try:
            self.started.emit()
            books = self.dal.get_all_books()
            self.finished.emit(books)
        except Exception as e:
            logger.error(f"获取词书列表失败: {e}", exc_info=True)
            self.error.emit(str(e))


class DeleteBookWorker(BaseWorker):
    """删除词书工作线程"""
    
    def __init__(self, dal: RecitationDAL, book_id: int):
        super().__init__(dal)
        self.book_id = book_id
    
    def run(self):
        try:
            self.started.emit()
            success = self.dal.delete_book(self.book_id)
            self.finished.emit(success)
        except Exception as e:
            logger.error(f"删除词书失败: {e}", exc_info=True)
            self.error.emit(str(e))


class ExportBookWorker(QThread):
    """导出词书工作线程"""
    
    started = Signal()
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager, book_id: int, output_path: str):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
        self.book_id = book_id
        self.output_path = output_path
    
    def run(self):
        from pathlib import Path
        import json
        try:
            self.started.emit()
            
            # 获取词书信息
            book = self.dal.get_book_by_id(self.book_id)
            if not book:
                self.finished.emit({'success': False, 'error': '词书不存在'})
                return
            
            # 获取所有单词
            words = self.dal.get_words_by_book_id(self.book_id)
            
            # 构建导出数据
            export_data = []
            for word in words:
                # 优先使用保存的原始数据
                if word.raw_data:
                    try:
                        word_data = json.loads(word.raw_data)
                        export_data.append(word_data)
                        continue
                    except:
                        pass
                
                # 如果没有原始数据，构建简单格式
                word_data = {
                    'word': word.word,
                    'phonetic': word.phonetic,
                    'definition': word.definition,
                    'example': word.example
                }
                export_data.append(word_data)
            
            # 保存到文件
            output_file = Path(self.output_path)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"词书导出成功: {output_file}, 单词数: {len(export_data)}")
            self.finished.emit({
                'success': True,
                'file_path': str(output_file),
                'word_count': len(export_data)
            })
            
        except Exception as e:
            logger.error(f"导出词书失败: {e}", exc_info=True)
            self.error.emit(str(e))
            self.finished.emit({
                'success': False,
                'error': str(e)
            })


class VacuumDatabaseWorker(QThread):
    """压缩数据库工作线程"""
    
    started = Signal()
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
    
    def run(self):
        from pathlib import Path
        try:
            self.started.emit()
            
            db_path = self.path_manager.get_db_path()
            old_size = 0
            if db_path and Path(db_path).exists():
                old_size = Path(db_path).stat().st_size
            
            # 执行VACUUM
            from .database import DatabaseManager
            db_manager = DatabaseManager(self.path_manager)
            success = db_manager.vacuum()
            
            new_size = 0
            if db_path and Path(db_path).exists():
                new_size = Path(db_path).stat().st_size
            
            self.finished.emit({
                'success': success,
                'old_size': old_size,
                'new_size': new_size
            })
            
        except Exception as e:
            logger.error(f"压缩数据库失败: {e}", exc_info=True)
            self.error.emit(str(e))
            self.finished.emit({
                'success': False,
                'error': str(e)
            })


class ImportWordsWorker(BaseWorker):
    """批量导入单词工作线程"""
    
    progress = Signal(int)
    
    def __init__(self, dal: RecitationDAL, book_id: int, words: List[Word]):
        super().__init__(dal)
        self.book_id = book_id
        self.words = words
    
    def run(self):
        try:
            self.started.emit()
            
            for word in self.words:
                word.book_id = self.book_id
            
            count = self.dal.add_words_batch(self.words)
            self.finished.emit(count)
        except Exception as e:
            logger.error(f"导入单词失败: {e}", exc_info=True)
            self.error.emit(str(e))


class GetWordsWorker(BaseWorker):
    """获取单词列表工作线程"""
    
    def __init__(self, dal: RecitationDAL, book_id: int):
        super().__init__(dal)
        self.book_id = book_id
    
    def run(self):
        try:
            self.started.emit()
            words = self.dal.get_words_by_book_id(self.book_id)
            self.finished.emit(words)
        except Exception as e:
            logger.error(f"获取单词列表失败: {e}", exc_info=True)
            self.error.emit(str(e))


class GetUnstudiedWordsWorker(BaseWorker):
    """获取未学习单词工作线程"""
    
    def __init__(self, dal: RecitationDAL, book_id: int, limit: Optional[int] = None):
        super().__init__(dal)
        self.book_id = book_id
        self.limit = limit
    
    def run(self):
        try:
            self.started.emit()
            words = self.dal.get_unstudied_words(self.book_id, self.limit)
            self.finished.emit(words)
        except Exception as e:
            logger.error(f"获取未学习单词失败: {e}", exc_info=True)
            self.error.emit(str(e))


class GetReviewWordsWorker(BaseWorker):
    """获取复习单词工作线程"""
    
    def __init__(self, dal: RecitationDAL, book_id: int, limit: Optional[int] = None):
        super().__init__(dal)
        self.book_id = book_id
        self.limit = limit
    
    def run(self):
        try:
            self.started.emit()
            words = self.dal.get_words_for_review(self.book_id, self.limit)
            self.finished.emit(words)
        except Exception as e:
            logger.error(f"获取复习单词失败: {e}", exc_info=True)
            self.error.emit(str(e))


class UpdateUserStudyWorker(BaseWorker):
    """更新学习记录工作线程"""
    
    def __init__(self, dal: RecitationDAL, user_study: UserStudy):
        super().__init__(dal)
        self.user_study = user_study
    
    def run(self):
        try:
            self.started.emit()
            success = self.dal.update_user_study(self.user_study)
            self.finished.emit(success)
        except Exception as e:
            logger.error(f"更新学习记录失败: {e}", exc_info=True)
            self.error.emit(str(e))


class AddUserStudyWorker(BaseWorker):
    """添加学习记录工作线程"""
    
    def __init__(self, dal: RecitationDAL, user_study: UserStudy):
        super().__init__(dal)
        self.user_study = user_study
    
    def run(self):
        try:
            self.started.emit()
            result = self.dal.add_user_study(self.user_study)
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"添加学习记录失败: {e}", exc_info=True)
            self.error.emit(str(e))


class GetBookProgressWorker(BaseWorker):
    """获取词书进度工作线程"""
    
    def __init__(self, dal: RecitationDAL, book_id: int):
        super().__init__(dal)
        self.book_id = book_id
    
    def run(self):
        try:
            self.started.emit()
            progress = self.dal.get_book_progress(self.book_id)
            self.finished.emit(progress)
        except Exception as e:
            logger.error(f"获取词书进度失败: {e}", exc_info=True)
            self.error.emit(str(e))


class ImportBookWorker(QThread):
    """词书导入工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(int)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager, file_path: str):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
        self.file_path = file_path
    
    def run(self):
        try:
            self.started.emit()
            book_service = BookService(self.dal, self.path_manager)
            book = book_service.import_book(self.file_path)
            self.finished.emit(book)
        except Exception as e:
            logger.error(f"导入词书失败: {e}", exc_info=True)
            self.error.emit(str(e))


class DownloadBookWorker(QThread):
    """词书下载工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(int, int)
    
    def __init__(self, save_dir: str, url: str = None, filename: str = None):
        super().__init__()
        self.save_dir = save_dir
        self.url = url
        self.filename = filename
    
    def run(self):
        try:
            self.started.emit()
            download_service = DownloadService()
            
            if self.url:
                result = download_service.download_book(
                    self.url,
                    self.save_dir,
                    self.filename or "book.json",
                    lambda r, t: self.progress.emit(r, t)
                )
            else:
                result = download_service.download_default_book(
                    self.save_dir,
                    lambda r, t: self.progress.emit(r, t)
                )
            
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"下载词书失败: {e}", exc_info=True)
            self.error.emit(str(e))


class GetAllBooksWithProgressWorker(QThread):
    """获取所有词书及其进度工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
    
    def run(self):
        try:
            self.started.emit()
            book_service = BookService(self.dal, self.path_manager)
            books_with_progress = book_service.get_all_books_with_progress()
            self.finished.emit(books_with_progress)
        except Exception as e:
            logger.error(f"获取词书列表失败: {e}", exc_info=True)
            self.error.emit(str(e))


class SelectBookWorker(QThread):
    """选择词书工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager, book_id: int):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
        self.book_id = book_id
    
    def run(self):
        try:
            self.started.emit()
            book_service = BookService(self.dal, self.path_manager)
            success = book_service.select_book(self.book_id)
            self.finished.emit(success)
        except Exception as e:
            logger.error(f"选择词书失败: {e}", exc_info=True)
            self.error.emit(str(e))


class GetCurrentBookWorker(QThread):
    """获取当前选择的词书工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
    
    def run(self):
        try:
            self.started.emit()
            book_service = BookService(self.dal, self.path_manager)
            book = book_service.get_current_book()
            self.finished.emit(book)
        except Exception as e:
            logger.error(f"获取当前词书失败: {e}", exc_info=True)
            self.error.emit(str(e))


class GetDailySettingsWorker(QThread):
    """获取每日学习设置工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
    
    def run(self):
        try:
            self.started.emit()
            study_service = StudyService(self.dal, self.path_manager)
            daily_new = study_service.get_daily_new_words()
            daily_review = study_service.get_daily_review_words()
            self.finished.emit({'daily_new': daily_new, 'daily_review': daily_review})
        except Exception as e:
            logger.error(f"获取每日设置失败: {e}", exc_info=True)
            self.error.emit(str(e))


class SetDailySettingsWorker(QThread):
    """设置每日学习设置工作线程"""
    
    started = Signal()
    finished = Signal(bool)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager, daily_new: int, daily_review: int):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
        self.daily_new = daily_new
        self.daily_review = daily_review
    
    def run(self):
        try:
            self.started.emit()
            study_service = StudyService(self.dal, self.path_manager)
            study_service.set_daily_new_words(self.daily_new)
            study_service.set_daily_review_words(self.daily_review)
            self.finished.emit(True)
        except Exception as e:
            logger.error(f"设置每日设置失败: {e}", exc_info=True)
            self.error.emit(str(e))


class GetTodayWordsWorker(QThread):
    """获取今日学习和复习单词工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager, book_id: int, force_refresh: bool = False):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
        self.book_id = book_id
        self.force_refresh = force_refresh
    
    def run(self):
        try:
            self.started.emit()
            study_service = StudyService(self.dal, self.path_manager)
            new_words, review_words = study_service.get_today_words(self.book_id, force_refresh=self.force_refresh)
            self.finished.emit({'new_words': new_words, 'review_words': review_words})
        except Exception as e:
            logger.error(f"获取今日单词失败: {e}", exc_info=True)
            self.error.emit(str(e))


class RefreshTodayWordsWorker(QThread):
    """刷新今日学习和复习单词工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager, book_id: int):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
        self.book_id = book_id
    
    def run(self):
        try:
            self.started.emit()
            study_service = StudyService(self.dal, self.path_manager)
            new_words, review_words = study_service.refresh_today_words(self.book_id)
            self.finished.emit({'new_words': new_words, 'review_words': review_words})
        except Exception as e:
            logger.error(f"刷新今日单词失败: {e}", exc_info=True)
            self.error.emit(str(e))


class StartStudyWordWorker(QThread):
    """开始学习单词工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager, book_id: int, word_id: int):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
        self.book_id = book_id
        self.word_id = word_id
    
    def run(self):
        try:
            self.started.emit()
            study_service = StudyService(self.dal, self.path_manager)
            result = study_service.start_study_word(self.book_id, self.word_id)
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"开始学习单词失败: {e}", exc_info=True)
            self.error.emit(str(e))


class ReviewWordWorker(QThread):
    """复习单词工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager, book_id: int, word_id: int, is_correct: bool):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
        self.book_id = book_id
        self.word_id = word_id
        self.is_correct = is_correct
    
    def run(self):
        try:
            self.started.emit()
            study_service = StudyService(self.dal, self.path_manager)
            result = study_service.review_word(self.book_id, self.word_id, self.is_correct)
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"复习单词失败: {e}", exc_info=True)
            self.error.emit(str(e))


class StartStudyBatchWordsWorker(QThread):
    """批量开始学习单词工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager, book_id: int, word_ids: List[int]):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
        self.book_id = book_id
        self.word_ids = word_ids
    
    def run(self):
        try:
            self.started.emit()
            study_service = StudyService(self.dal, self.path_manager)
            results = study_service.start_study_batch_words(self.book_id, self.word_ids)
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"批量开始学习单词失败: {e}", exc_info=True)
            self.error.emit(str(e))


class ReviewBatchWordsWorker(QThread):
    """批量复习单词工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager, book_id: int, word_results: List[Tuple[int, bool]]):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
        self.book_id = book_id
        self.word_results = word_results
    
    def run(self):
        try:
            self.started.emit()
            study_service = StudyService(self.dal, self.path_manager)
            results = study_service.review_batch_words(self.book_id, self.word_results)
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"批量复习单词失败: {e}", exc_info=True)
            self.error.emit(str(e))


class UpdateAllWeightsWorker(QThread):
    """更新所有单词权重工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager, book_id: int):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
        self.book_id = book_id
    
    def run(self):
        try:
            self.started.emit()
            study_service = StudyService(self.dal, self.path_manager)
            count = study_service.update_all_weights(self.book_id)
            self.finished.emit(count)
        except Exception as e:
            logger.error(f"更新所有权重失败: {e}", exc_info=True)
            self.error.emit(str(e))


class GetBookAllWordsWorker(QThread):
    """获取词书所有单词工作线程"""
    
    started = Signal()
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, dal: RecitationDAL, path_manager: PathManager, book_id: int):
        super().__init__()
        self.dal = dal
        self.path_manager = path_manager
        self.book_id = book_id
    
    def run(self):
        try:
            self.started.emit()
            words = self.dal.get_words_by_book_id(self.book_id)
            self.finished.emit(words)
        except Exception as e:
            logger.error(f"获取词书单词失败: {e}", exc_info=True)
            self.error.emit(str(e))
