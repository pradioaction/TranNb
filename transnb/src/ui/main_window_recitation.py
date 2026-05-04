from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import Qt
from recitation import (
    PathManager as RecitationPathManager,
    DatabaseManager as RecitationDatabaseManager,
    RecitationDAL,
    BookService,
    StudyService,
    ArticleGenerator
)
from .main_window_workers import GenerateArticleWorker


class MainWindowRecitationMixin:
    def _init_recitation(self):
        self.recitation_path_manager = RecitationPathManager()
        self.recitation_db_manager = self._create_recitation_db_manager(self.recitation_path_manager)
        self.recitation_dal = self._create_recitation_dal(self.recitation_db_manager)
        self.recitation_book_service = self._create_book_service(self.recitation_dal, self.recitation_path_manager)
        self.recitation_study_service = self._create_study_service(self.recitation_dal, self.recitation_path_manager)

        self._current_new_words = []
        self._current_review_words = []
        self._current_book_id = None

    def _create_recitation_db_manager(self, path_manager):
        return RecitationDatabaseManager(path_manager)

    def _create_recitation_dal(self, db_manager):
        return RecitationDAL(db_manager)

    def _create_book_service(self, dal, path_manager):
        return BookService(dal, path_manager)

    def _create_study_service(self, dal, path_manager):
        return StudyService(dal, path_manager)

    def _refresh_book_counts(self):
        try:
            if self.recitation_dal:
                self.recitation_dal.refresh_all_book_counts()
                print("词书数量同步完成")
        except Exception as e:
            print(f"同步词书数量失败: {e}")

    def _open_recitation_mode(self):
        workspace = self.workspace_manager.get_workspace()
        if not workspace:
            self._select_workspace()
            workspace = self.workspace_manager.get_workspace()
            if not workspace:
                return

        self.recitation_path_manager.set_workspace(workspace)

        self.recitation_db_manager = self._create_recitation_db_manager(self.recitation_path_manager)
        success = self.recitation_db_manager.initialize()
        if not success:
            QMessageBox.warning(self, "错误", "初始化背诵模式数据库失败")
            return

        self.recitation_dal = self._create_recitation_dal(self.recitation_db_manager)
        self.recitation_book_service = self._create_book_service(self.recitation_dal, self.recitation_path_manager)
        self.recitation_study_service = self._create_study_service(self.recitation_dal, self.recitation_path_manager)

        self.recitation_main_page.set_dependencies(
            self.recitation_dal,
            self.recitation_path_manager,
            self.recitation_study_service,
            self.recitation_book_service
        )
        self.recitation_quiz_page.set_dependencies(
            self.recitation_dal,
            self.recitation_path_manager
        )

        self.recitation_main_page.load_data()

        self.stacked_widget.setCurrentIndex(self.PAGE_RECITATION_MAIN)
        self._update_menu_states()
        self.status_label.setText("背诵模式")

    def _on_recitation_back(self):
        if self.file_service.is_file_open():
            self._switch_to_editor_page()
        else:
            self._switch_to_welcome_page()

    def _on_generate_article_requested(self, new_words, review_words):
        self._current_new_words = new_words
        self._current_review_words = review_words

        current_book = self.recitation_main_page._current_book
        self._current_book_id = current_book.id if current_book else None

        all_words = new_words + review_words
        if not all_words:
            QMessageBox.warning(self, "提示", "没有可学习的单词")
            return

        word_texts = [w.word for w in all_words]

        self._progress_dialog = QProgressDialog("正在生成文章...", "取消", 0, 0, self)
        self._progress_dialog.setWindowModality(Qt.WindowModal)
        self._progress_dialog.setCancelButton(None)
        self._progress_dialog.show()

        self._generate_worker = GenerateArticleWorker(
            self.translation_service,
            word_texts
        )
        self._generate_worker.finished.connect(self._on_article_generated)
        self._generate_worker.progress.connect(self._on_article_progress)
        self._generate_worker.start()

    def _on_article_progress(self, message):
        if self._progress_dialog:
            self._progress_dialog.setLabelText(message)

    def _on_article_generated(self, success, article, error_msg):
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None

        if not success:
            QMessageBox.warning(self, "错误", f"生成文章失败: {error_msg}")
            return

        formatted_article = ArticleGenerator.format_article(
            article,
            self._current_new_words,
            self._current_review_words
        )

        title = ArticleGenerator.extract_title(article)

        workspace = self.workspace_manager.get_workspace()
        if not workspace:
            QMessageBox.warning(self, "错误", "请先选择工作区")
            return

        save_success, file_path_or_error = ArticleGenerator.save_article(
            workspace,
            formatted_article,
            title
        )

        if not save_success:
            QMessageBox.warning(self, "错误", f"保存文章失败: {file_path_or_error}")
            return

        self.file_service.open_file(file_path_or_error)

    def _on_start_quiz_requested(self, new_words, review_words):
        self._current_new_words = new_words
        self._current_review_words = review_words

        current_book = self.recitation_main_page._current_book
        self._current_book_id = current_book.id if current_book else None

        all_words = new_words + review_words
        if not all_words:
            QMessageBox.warning(self, "提示", "没有可检测的单词")
            return

        self.recitation_quiz_page.set_words(
            new_words,
            review_words,
            self._current_book_id
        )

        self.stacked_widget.setCurrentIndex(self.PAGE_RECITATION_QUIZ)

    def _on_quiz_finished(self, results):
        QMessageBox.information(self, "完成", "检测已完成！")
        self.stacked_widget.setCurrentIndex(self.PAGE_RECITATION_MAIN)
