from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QSplitter, QMessageBox,
    QFileDialog, QGroupBox, QSpinBox, QFormLayout, QStackedWidget,
    QTextEdit, QDialog, QDialogButtonBox, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from typing import List, Optional, Tuple, Dict
from ..models import Book, Word
from ..utils import format_phonetic
from ..workers import (
    InitializeDBWorker, GetAllBooksWithProgressWorker, SelectBookWorker,
    GetCurrentBookWorker, GetTodayWordsWorker, RefreshTodayWordsWorker,
    ImportBookWorker, DeleteBookWorker, GetDailySettingsWorker,
    SetDailySettingsWorker, StartStudyBatchWordsWorker, ExportBookWorker,
    VacuumDatabaseWorker
)
from ..dal import RecitationDAL
from ..path_manager import PathManager
from ..workers import GetBookAllWordsWorker
from .dialogs import (
    NewBookDialog, AddWordDialog, AddToBookDialog
)


class BookViewDialog(QDialog):
    """词书查看对话框"""
    
    def __init__(self, book: Book, dal: RecitationDAL, path_manager: PathManager, parent=None):
        super().__init__(parent)
        self._book = book
        self._dal = dal
        self._path_manager = path_manager
        self._words: List[Word] = []
        self._filtered_words: List[Word] = []
        self._worker = None
        self._words_list = None
        self._search_edit = None
        self.setWindowTitle(f"词书详情: {book.name}")
        self.setMinimumSize(800, 600)
        self._init_ui()
        self._load_words()
    
    def closeEvent(self, event):
        """关闭对话框时清理线程"""
        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(1000)
        event.accept()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(f"{self._book.name} ({self._book.count} 个单词)")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 工具栏 - 搜索和添加
        toolbar_layout = QHBoxLayout()
        
        search_label = QLabel("搜索：")
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("输入单词或释义搜索...")
        self._search_edit.textChanged.connect(self._on_search)
        
        add_btn = QPushButton("添加单词")
        add_btn.clicked.connect(self._on_add_word)
        
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(self._search_edit)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(add_btn)
        
        layout.addLayout(toolbar_layout)
        
        # 单词列表
        self._words_list = QListWidget()
        self._words_list.itemDoubleClicked.connect(self._on_word_double_clicked)
        layout.addWidget(self._words_list)
        
        # 按钮
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(self.accept)
        layout.addWidget(btn_box)
    
    def _load_words(self):
        self._worker = GetBookAllWordsWorker(self._dal, self._path_manager, self._book.id)
        self._worker.finished.connect(self._on_words_loaded)
        self._worker.start()
    
    def _on_words_loaded(self, words: List[Word]):
        self._words = words
        self._filtered_words = words.copy()
        self._refresh_words_list()
    
    def _refresh_words_list(self):
        self._words_list.clear()
        for i, word in enumerate(self._filtered_words, 1):
            item_text = f"{i}. {word.word}"
            formatted_phonetic = format_phonetic(word.phonetic)
            if formatted_phonetic:
                item_text += f" {formatted_phonetic}"
            if word.definition:
                def_text = word.definition[:30]
                if len(word.definition) > 30:
                    def_text += "..."
                item_text += f" - {def_text}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, word)
            self._words_list.addItem(item)
    
    def _on_search(self):
        search_text = self._search_edit.text().strip().lower()
        if not search_text:
            self._filtered_words = self._words.copy()
        else:
            self._filtered_words = [
                word for word in self._words 
                if search_text in word.word.lower() 
                or search_text in word.definition.lower()
            ]
        self._refresh_words_list()
    
    def _on_add_word(self):
        dialog = AddWordDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_word_data()
            
            exists = self._dal.check_word_exists_in_book(self._book.id, data['word'])
            if exists:
                QMessageBox.warning(self, "提示", "该单词已存在于词书中！")
                return
            
            word = Word(
                book_id=self._book.id,
                word=data['word'],
                phonetic=data['phonetic'],
                definition=data['definition'],
                example=data['example'],
                raw_data=''
            )
            
            result = self._dal.add_word(word)
            if result:
                self._book.count += 1
                self._dal.update_book(self._book)
                QMessageBox.information(self, "成功", "单词添加成功！")
                self._load_words()
            else:
                QMessageBox.warning(self, "失败", "单词添加失败！")
    
    def _on_word_double_clicked(self, item: QListWidgetItem):
        word = item.data(Qt.UserRole)
        if word:
            dialog = WordDetailDialog(word, self._dal, self)
            dialog.exec_()


class WordDetailDialog(QDialog):
    """单词详情对话框"""
    
    def __init__(self, word: Word, dal: RecitationDAL, parent=None):
        super().__init__(parent)
        self._word = word
        self._dal = dal
        self.setWindowTitle(f"单词详情: {word.word}")
        self.setMinimumSize(500, 400)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 单词
        word_label = QLabel(self._word.word)
        word_font = QFont()
        word_font.setPointSize(24)
        word_font.setBold(True)
        word_label.setFont(word_font)
        layout.addWidget(word_label)
        
        # 音标
        formatted_phonetic = format_phonetic(self._word.phonetic)
        if formatted_phonetic:
            phonetic_label = QLabel(f"音标: {formatted_phonetic}")
            phonetic_label.setStyleSheet("color: #666; font-size: 14px;")
            layout.addWidget(phonetic_label)
        
        # 释义
        if self._word.definition:
            def_group = QGroupBox("释义")
            def_layout = QVBoxLayout(def_group)
            def_text = QTextEdit()
            def_text.setPlainText(self._word.definition)
            def_text.setReadOnly(True)
            def_layout.addWidget(def_text)
            layout.addWidget(def_group)
        
        # 例句
        if self._word.example:
            ex_group = QGroupBox("例句")
            ex_layout = QVBoxLayout(ex_group)
            ex_text = QTextEdit()
            ex_text.setPlainText(self._word.example)
            ex_text.setReadOnly(True)
            ex_layout.addWidget(ex_text)
            layout.addWidget(ex_group)
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        add_to_book_btn = QPushButton("添加到词书")
        add_to_book_btn.clicked.connect(self._on_add_to_book)
        btn_layout.addWidget(add_to_book_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_add_to_book(self):
        dialog = AddToBookDialog(self._word, self._dal, self)
        if dialog.exec_() == QDialog.Accepted:
            book_id = dialog.get_selected_book_id()
            if not book_id:
                return
            
            new_word = Word(
                book_id=book_id,
                word=self._word.word,
                phonetic=self._word.phonetic,
                definition=self._word.definition,
                example=self._word.example,
                raw_data=self._word.raw_data
            )
            
            result = self._dal.add_word(new_word)
            if result:
                book = self._dal.get_book_by_id(book_id)
                if book:
                    book.count += 1
                    self._dal.update_book(book)
                QMessageBox.information(self, "成功", "单词添加成功！")
            else:
                QMessageBox.warning(self, "失败", "单词添加失败！")


class RecitationMainPage(QWidget):
    """背诵模式主页面"""
    
    generate_article_requested = pyqtSignal(list, list)  # new_words, review_words
    start_quiz_requested = pyqtSignal(list, list)  # new_words, review_words
    back_requested = pyqtSignal()
    settings_requested = pyqtSignal()  # 请求打开设置对话框
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_book: Optional[Book] = None
        self._today_new_words: List[Word] = []
        self._today_review_words: List[Word] = []
        self._workers = {}  # 用于存储所有工作线程
        self._dal: Optional[RecitationDAL] = None
        self._path_manager: Optional[PathManager] = None
        self._init_ui()
    
    def __del__(self):
        """清理线程"""
        self._cleanup_workers()
    
    def hideEvent(self, event):
        """页面隐藏时调用，清理线程"""
        self._cleanup_workers()
        super().hideEvent(event)
    
    def _cleanup_workers(self):
        """清理所有工作线程"""
        # 清理 self._workers 字典中的线程
        for worker in self._workers.values():
            if worker and worker.isRunning():
                worker.quit()
                worker.wait(1000)  # 等待最多1秒
        self._workers.clear()
        
        # 还需要清理 self._worker 单个线程引用（如果存在）
        if hasattr(self, '_worker') and self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait(1000)
            self._worker = None
    
    def _start_worker(self, worker, worker_id=None):
        """启动一个工作线程并正确管理它"""
        # 先清理已存在的同名线程
        if worker_id and worker_id in self._workers:
            old_worker = self._workers[worker_id]
            if old_worker and old_worker.isRunning():
                old_worker.quit()
                old_worker.wait(1000)
        
        # 存储并启动新线程
        if worker_id:
            self._workers[worker_id] = worker
        else:
            # 如果没有ID，也需要确保之前的线程被清理
            if hasattr(self, '_worker') and self._worker and self._worker.isRunning():
                self._worker.quit()
                self._worker.wait(1000)
            self._worker = worker
        
        worker.start()
    
    def set_dependencies(self, dal: RecitationDAL, path_manager: PathManager, *args, **kwargs):
        """设置依赖项"""
        self._dal = dal
        self._path_manager = path_manager
    
    def showEvent(self, event):
        """页面显示时调用"""
        super().showEvent(event)
        # 每次显示页面时更新数据库大小
        if self._dal and self._path_manager:
            self._update_db_size_label()
    
    def _update_db_size_label(self):
        """更新数据库大小显示"""
        if hasattr(self, '_db_size_label'):
            db_path = self._path_manager.get_db_path()
            if db_path and db_path.exists():
                size_bytes = db_path.stat().st_size
                if size_bytes < 1024:
                    size_text = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_text = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_text = f"{size_bytes / (1024 * 1024):.1f} MB"
                self._db_size_label.setText(f"数据库: {size_text}")
            else:
                self._db_size_label.setText("数据库: --")
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 顶部 - 标题和返回按钮
        top_widget = QWidget()
        top_widget.setMaximumHeight(40)
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)
        
        back_btn = QPushButton("← 返回")
        back_btn.clicked.connect(self.back_requested.emit)
        back_btn.setMaximumHeight(30)
        top_layout.addWidget(back_btn)
        
        title_label = QLabel("📚 背诵模式")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        top_layout.addWidget(title_label)
        
        top_layout.addStretch()
        
        self._db_size_label = QLabel("数据库: --")
        self._db_size_label.setStyleSheet("color: #666;")
        self._db_size_label.setFont(QFont("Arial", 9))
        top_layout.addWidget(self._db_size_label)
        
        layout.addWidget(top_widget)
        
        # 使用分割器划分左右两个区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：词书管理
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 词书列表标题
        book_title = QLabel("词书列表")
        book_title.setFont(QFont("Arial", 10, QFont.Bold))
        left_layout.addWidget(book_title)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        self._import_btn = QPushButton("导入词书")
        self._import_btn.clicked.connect(self._on_import_book)
        btn_layout.addWidget(self._import_btn)
        
        self._new_book_btn = QPushButton("新建词书")
        self._new_book_btn.clicked.connect(self._on_new_book)
        btn_layout.addWidget(self._new_book_btn)
        
        self._export_btn = QPushButton("导出词书")
        self._export_btn.clicked.connect(self._on_export_book)
        self._export_btn.setEnabled(False)
        btn_layout.addWidget(self._export_btn)
        
        self._view_btn = QPushButton("查看词书")
        self._view_btn.clicked.connect(self._on_view_book)
        self._view_btn.setEnabled(False)
        btn_layout.addWidget(self._view_btn)
        
        self._delete_btn = QPushButton("删除")
        self._delete_btn.clicked.connect(self._on_delete_book)
        self._delete_btn.setEnabled(False)
        btn_layout.addWidget(self._delete_btn)
        
        left_layout.addLayout(btn_layout)
        
        # 词书列表
        self._book_list = QListWidget()
        self._book_list.itemClicked.connect(self._on_book_selected)
        left_layout.addWidget(self._book_list)
        
        splitter.addWidget(left_widget)
        
        # 右侧：今日学习
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        right_title = QLabel("今日学习")
        right_title.setFont(QFont("Arial", 10, QFont.Bold))
        right_layout.addWidget(right_title)
        
        self._current_book_label = QLabel("请先选择词书")
        right_layout.addWidget(self._current_book_label)
        
        # 新单词部分
        new_group = QGroupBox("新学单词")
        new_layout = QVBoxLayout(new_group)
        
        new_header_layout = QHBoxLayout()
        self._new_count_label = QLabel("0个")
        new_header_layout.addWidget(self._new_count_label)
        
        self._new_select_all_btn = QPushButton("全选")
        self._new_select_all_btn.clicked.connect(lambda: self._select_all_words(self._new_list, True))
        new_header_layout.addWidget(self._new_select_all_btn)
        
        self._new_deselect_all_btn = QPushButton("取消全选")
        self._new_deselect_all_btn.clicked.connect(lambda: self._select_all_words(self._new_list, False))
        new_header_layout.addWidget(self._new_deselect_all_btn)
        
        new_header_layout.addStretch()
        new_layout.addLayout(new_header_layout)
        
        self._new_list = QListWidget()
        self._new_list.setSelectionMode(QListWidget.MultiSelection)
        new_layout.addWidget(self._new_list)
        
        right_layout.addWidget(new_group, 1)  # 给新学单词列表更大的权重
        
        # 复习单词部分
        review_group = QGroupBox("复习单词")
        review_layout = QVBoxLayout(review_group)
        
        review_header_layout = QHBoxLayout()
        self._review_count_label = QLabel("0个")
        review_header_layout.addWidget(self._review_count_label)
        
        self._review_select_all_btn = QPushButton("全选")
        self._review_select_all_btn.clicked.connect(lambda: self._select_all_words(self._review_list, True))
        review_header_layout.addWidget(self._review_select_all_btn)
        
        self._review_deselect_all_btn = QPushButton("取消全选")
        self._review_deselect_all_btn.clicked.connect(lambda: self._select_all_words(self._review_list, False))
        review_header_layout.addWidget(self._review_deselect_all_btn)
        
        review_header_layout.addStretch()
        review_layout.addLayout(review_header_layout)
        
        self._review_list = QListWidget()
        self._review_list.setSelectionMode(QListWidget.MultiSelection)
        review_layout.addWidget(self._review_list)
        
        right_layout.addWidget(review_group, 1)  # 给复习单词列表更大的权重
        
        # 底部操作按钮
        action_layout = QHBoxLayout()
        
        self._generate_btn = QPushButton("📖 生成文章学习")
        self._generate_btn.clicked.connect(self._on_generate_article)
        self._generate_btn.setEnabled(False)
        action_layout.addWidget(self._generate_btn)
        
        self._quiz_btn = QPushButton("📝 直接检测")
        self._quiz_btn.clicked.connect(self._on_start_quiz)
        self._quiz_btn.setEnabled(False)
        action_layout.addWidget(self._quiz_btn)
        
        self._skip_btn = QPushButton("🔄 跳过本轮")
        self._skip_btn.clicked.connect(self._on_skip)
        self._skip_btn.setEnabled(False)
        action_layout.addWidget(self._skip_btn)
        
        action_layout.addStretch()
        
        self._settings_btn = QPushButton("设置")
        self._settings_btn.clicked.connect(self.settings_requested.emit)
        action_layout.addWidget(self._settings_btn)
        
        self._vacuum_btn = QPushButton("压缩数据库")
        self._vacuum_btn.clicked.connect(self._on_vacuum)
        action_layout.addWidget(self._vacuum_btn)
        
        right_layout.addLayout(action_layout)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器初始比例
        splitter.setSizes([300, 500])
        
        layout.addWidget(splitter)
    
    def load_data(self):
        """直接加载数据，不重新初始化数据库"""
        self._workers.clear()  # 先清理
        self._update_db_size_label()
        self._load_books()
        self._load_current_book()
        self._load_daily_settings()
    
    def initialize(self, dal: RecitationDAL, path_manager: PathManager):
        """初始化页面"""
        self._dal = dal
        self._path_manager = path_manager
        self._load_books()
        self._load_daily_settings()
    
    def _load_books(self):
        """加载词书列表"""
        worker = GetAllBooksWithProgressWorker(self._dal, self._path_manager)
        worker.finished.connect(self._on_books_loaded)
        self._start_worker(worker, 'load_books')
    
    def _on_books_loaded(self, books_data):
        """词书加载完成"""
        self._book_list.clear()
        
        # 处理不同的数据结构
        books = []
        if isinstance(books_data, dict):
            books = books_data.get('books', [])
        elif isinstance(books_data, list):
            books = books_data
        
        for item_data in books:
            # 检查是直接的Book对象还是带进度信息的字典
            book = None
            if hasattr(item_data, 'name'):
                # 直接是Book对象
                book = item_data
            elif isinstance(item_data, dict) and 'book' in item_data:
                # 是带进度信息的字典
                book = item_data['book']
            
            if book and hasattr(book, 'name'):
                item = QListWidgetItem(f"{book.name} ({book.count}词)")
                item.setData(Qt.UserRole, book)
                self._book_list.addItem(item)
    
    def _on_book_selected(self, item):
        """选择词书"""
        book = item.data(Qt.UserRole)
        if book:
            self._current_book = book
            self._update_book_selection()
            self._load_today_words()
    
    def _update_book_selection(self):
        """更新词书选择后的UI状态"""
        if self._current_book:
            self._current_book_label.setText(f"当前词书: {self._current_book.name}")
            self._export_btn.setEnabled(True)
            self._view_btn.setEnabled(True)
            self._delete_btn.setEnabled(True)
            self._generate_btn.setEnabled(True)
            self._quiz_btn.setEnabled(True)
            self._skip_btn.setEnabled(True)
        else:
            self._current_book_label.setText("请先选择词书")
            self._export_btn.setEnabled(False)
            self._view_btn.setEnabled(False)
            self._delete_btn.setEnabled(False)
            self._generate_btn.setEnabled(False)
            self._quiz_btn.setEnabled(False)
            self._skip_btn.setEnabled(False)
    
    def _load_today_words(self):
        """加载今日学习单词"""
        if not self._current_book:
            return
        
        worker = GetTodayWordsWorker(self._dal, self._path_manager, self._current_book.id)
        worker.finished.connect(self._on_today_words_loaded)
        self._start_worker(worker, 'load_today_words')
    
    def _on_today_words_loaded(self, data):
        """今日单词加载完成"""
        self._today_new_words = data.get('new_words', [])
        self._today_review_words = data.get('review_words', [])
        
        self._new_list.clear()
        for word in self._today_new_words:
            item_text = word.word
            formatted_phonetic = format_phonetic(word.phonetic)
            if formatted_phonetic:
                item_text += f" {formatted_phonetic}"
            self._new_list.addItem(item_text)
        
        self._review_list.clear()
        for word in self._today_review_words:
            item_text = word.word
            formatted_phonetic = format_phonetic(word.phonetic)
            if formatted_phonetic:
                item_text += f" {formatted_phonetic}"
            self._review_list.addItem(item_text)
        
        # 默认全选所有单词
        self._select_all_words(self._new_list, True)
        self._select_all_words(self._review_list, True)
        
        self._new_count_label.setText(f"{len(self._today_new_words)}个")
        self._review_count_label.setText(f"{len(self._today_review_words)}个")
    
    def _select_all_words(self, list_widget, select):
        """全选或取消全选列表中的单词"""
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            item.setSelected(select)
    
    def _get_selected_words(self, all_words, list_widget):
        """获取选中的单词列表"""
        selected_indices = [i for i in range(list_widget.count()) if list_widget.item(i).isSelected()]
        return [all_words[i] for i in selected_indices if i < len(all_words)]
    
    def _load_current_book(self):
        """加载当前词书"""
        if self._current_book:
            self._load_today_words()
    
    def _load_daily_settings(self):
        """加载每日设置"""
        pass
    
    def _on_import_book(self):
        """导入词书"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择词书文件", "", "JSON文件 (*.json);;所有文件 (*)"
        )
        if file_path:
            worker = ImportBookWorker(self._dal, self._path_manager, file_path)
            worker.finished.connect(self._on_import_finished)
            self._start_worker(worker, 'import_book')
    
    def _on_import_finished(self, book: Optional[Book]):
        """导入完成"""
        if book:
            QMessageBox.information(self, "成功", f"词书 '{book.name}' 导入成功！")
            self._load_books()
            self._update_db_size_label()
        else:
            QMessageBox.warning(self, "失败", "词书导入失败！")
    
    def _on_new_book(self):
        """新建词书"""
        dialog = NewBookDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_book_name()
            
            book = Book(name=name, path='', count=0)
            result = self._dal.add_book(book)
            
            if result:
                QMessageBox.information(self, "成功", "词书创建成功！")
                self._load_books()
                self._update_db_size_label()
            else:
                QMessageBox.warning(self, "失败", "词书创建失败！")
    
    def _on_export_book(self):
        """导出词书"""
        if not self._current_book:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出词书", f"{self._current_book.name}.json", "JSON文件 (*.json)"
        )
        if file_path:
            worker = ExportBookWorker(self._dal, self._path_manager, self._current_book.id, file_path)
            worker.finished.connect(self._on_export_finished)
            self._start_worker(worker, 'export_book')
    
    def _on_export_finished(self, success: bool):
        """导出完成"""
        if success:
            QMessageBox.information(self, "成功", "词书导出成功！")
        else:
            QMessageBox.warning(self, "失败", "词书导出失败！")
    
    def _on_view_book(self):
        """查看词书详情"""
        if not self._current_book:
            return
        
        dialog = BookViewDialog(self._current_book, self._dal, self._path_manager, self)
        dialog.exec_()
    
    def _on_delete_book(self):
        """删除词书"""
        if not self._current_book:
            return
        
        stats = self._dal.get_book_detailed_stats(self._current_book.id)
        
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除词书 '{self._current_book.name}' 吗？\n\n"
            f"将同时删除:\n"
            f"- {stats['word_count']} 个单词\n"
            f"- {stats['study_count']} 条学习记录\n\n"
            f"此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            worker = DeleteBookWorker(self._dal, self._path_manager, self._current_book.id)
            worker.finished.connect(self._on_delete_finished)
            self._start_worker(worker, 'delete_book')
    
    def _on_delete_finished(self, success: bool):
        """删除完成"""
        if success:
            QMessageBox.information(self, "成功", "词书删除成功！")
            self._current_book = None
            self._update_book_selection()
            self._load_books()
            self._update_db_size_label()
            
            reply = QMessageBox.question(
                self,
                "压缩数据库",
                "删除词书后，是否立即压缩数据库以释放空间？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._on_vacuum()
        else:
            QMessageBox.warning(self, "失败", "词书删除失败！")
    
    def _on_vacuum(self):
        """压缩数据库"""
        worker = VacuumDatabaseWorker(self._dal, self._path_manager)
        worker.finished.connect(self._on_vacuum_finished)
        self._start_worker(worker, 'vacuum')
    
    def _on_vacuum_finished(self, success: bool):
        """压缩完成"""
        if success:
            QMessageBox.information(self, "成功", "数据库压缩成功！")
            self._update_db_size_label()
        else:
            QMessageBox.warning(self, "失败", "数据库压缩失败！")
    
    def _on_generate_article(self):
        """生成文章"""
        if not self._current_book:
            return
        
        selected_new = self._get_selected_words(self._today_new_words, self._new_list)
        selected_review = self._get_selected_words(self._today_review_words, self._review_list)
        
        if not selected_new and not selected_review:
            QMessageBox.warning(self, "提示", "请至少选择一个单词！")
            return
        
        self._start_study_batch(selected_new)
        self.generate_article_requested.emit(
            selected_new, selected_review
        )
    
    def _on_start_quiz(self):
        """开始检测"""
        if not self._current_book:
            return
        
        selected_new = self._get_selected_words(self._today_new_words, self._new_list)
        selected_review = self._get_selected_words(self._today_review_words, self._review_list)
        
        if not selected_new and not selected_review:
            QMessageBox.warning(self, "提示", "请至少选择一个单词！")
            return
        
        self._start_study_batch(selected_new)
        self.start_quiz_requested.emit(
            selected_new, selected_review
        )
    
    def _start_study_batch(self, selected_words):
        """批量开始学习记录"""
        if not self._current_book:
            return
        
        word_ids = [w.id for w in selected_words]
        if word_ids:
            worker = StartStudyBatchWordsWorker(
                self._dal, self._path_manager, self._current_book.id, word_ids
            )
            self._start_worker(worker, 'start_study_batch')
    
    def _on_skip(self):
        """跳过本轮"""
        reply = QMessageBox.question(
            self,
            "确认跳过",
            "确定要跳过本轮学习吗？\n这将重新抽取单词。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if not self._current_book:
                return
            
            worker = RefreshTodayWordsWorker(self._dal, self._path_manager, self._current_book.id)
            worker.finished.connect(self._on_today_words_loaded)
            self._start_worker(worker, 'refresh_today_words')
