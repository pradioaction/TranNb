from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QToolBar, QStatusBar, QScrollArea,
    QAction, QFileDialog, QMessageBox, QLabel,
    QSplitter, QFrame, QTreeView, QStackedWidget, QInputDialog, QProgressDialog
)
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QDir, QSize, QThread, pyqtSignal as Signal
import os
import asyncio
from cells.cell_manager import CellManager
from cells.markdown_cell import MarkdownCell
from utils.theme_manager import ThemeManager
from settingmanager.settings_manager import SettingsManager
from components.settings_dialog import SettingsDialog
from components.welcome_page import WelcomePage
from translation.translation_service import TranslationService
from workspace.workspace_manager import WorkspaceManager
from workspace.filtered_file_model import FilteredFileModel
from workspace.file_service import FileService
from utils import file_utils
from recitation import (
    PathManager as RecitationPathManager,
    DatabaseManager as RecitationDatabaseManager,
    RecitationDAL,
    BookService,
    StudyService,
    ArticleGenerator,
    RecitationMainPage,
    QuizPage
)

class GenerateArticleWorker(QThread):
    finished = Signal(bool, str, str)  # 成功, 文章内容, 错误信息
    progress = Signal(str)
    
    def __init__(self, translation_service, words, prompt_template=None):
        super().__init__()
        self.translation_service = translation_service
        self.words = words
        self.prompt_template = prompt_template
    
    def run(self):
        try:
            self.progress.emit("正在生成文章...")
            
            # 运行异步函数
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                article = loop.run_until_complete(
                    self.translation_service.generate_scene_text(
                        self.words,
                        self.prompt_template
                    )
                )
                loop.close()
                self.finished.emit(True, article, "")
            except Exception as e:
                loop.close()
                self.finished.emit(False, "", str(e))
        
        except Exception as e:
            self.finished.emit(False, "", str(e))


class MainWindow(QMainWindow):
    # 页面索引常量
    PAGE_WELCOME = 0
    PAGE_EDITOR = 1
    PAGE_RECITATION_MAIN = 2
    PAGE_RECITATION_QUIZ = 3
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("翻译笔记本")
        self.setGeometry(100, 100, 1200, 800)
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logob.png')
        self.setWindowIcon(QIcon(icon_path))
        self._active_workers = []
        
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_changed.connect(self.apply_theme)
        
        self.settings_manager = SettingsManager()
        
        # 初始化翻译服务
        self.translation_service = TranslationService()
        self.translation_service.set_settings_manager(self.settings_manager)
        
        # 初始化工作区管理器
        self.workspace_manager = WorkspaceManager(self.settings_manager)
        self.workspace_manager.workspace_changed.connect(self._on_workspace_changed)
        self.workspace_manager.files_changed.connect(self._on_files_changed)
        
        # 初始化文件服务
        self.file_service = FileService(self.workspace_manager)
        self.file_service.file_opened.connect(self._on_file_opened)
        self.file_service.file_saved.connect(self._on_file_saved)
        self.file_service.file_closed.connect(self._on_file_closed)
        self.file_service.file_modified.connect(self._on_file_modified)
        self.file_service.error_occurred.connect(self._on_file_error)
        
        # 初始化背诵模式相关
        self._init_recitation()
        
        self.init_ui()
        self.init_menus()
        self.init_toolbar()
        self.init_statusbar()
        
        self._update_menu_states()
        self.restore_workspace()
    
    def closeEvent(self, event):
        """窗口关闭事件，清理所有线程"""
        # 清理背诵模式的线程
        if hasattr(self, 'recitation_main_page'):
            self.recitation_main_page._cleanup_workers()
        
        # 清理所有活动线程
        for worker in self._active_workers:
            if worker and worker.isRunning():
                worker.quit()
                worker.wait(1000)
        
        event.accept()
    
    def _init_recitation(self):
        """初始化背诵模式相关"""
        self.recitation_path_manager = RecitationPathManager()
        self.recitation_db_manager = RecitationDatabaseManager(self.recitation_path_manager)
        self.recitation_dal = RecitationDAL(self.recitation_db_manager)
        self.recitation_book_service = BookService(self.recitation_dal, self.recitation_path_manager)
        self.recitation_study_service = StudyService(self.recitation_dal, self.recitation_path_manager)
        
        # 当前学习的单词
        self._current_new_words = []
        self._current_review_words = []
        self._current_book_id = None
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 左侧文件浏览器面板
        self.left_panel = QFrame()
        self.left_panel.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        left_label = QLabel("文件浏览器")
        left_label.setAlignment(Qt.AlignCenter)
        left_label.setStyleSheet("padding: 10px; font-weight: bold;")
        left_layout.addWidget(left_label)
        
        # 使用过滤后的文件模型
        self.file_model = FilteredFileModel()
        self.file_tree = QTreeView()
        self.file_tree.setModel(self.file_model)
        self.file_tree.hideColumn(1)
        self.file_tree.hideColumn(2)
        self.file_tree.hideColumn(3)
        self.file_tree.doubleClicked.connect(self.on_file_double_clicked)
        left_layout.addWidget(self.file_tree)
        
        # 设置默认根路径（用户主目录）
        import os
        default_path = os.path.expanduser("~")
        self.file_model.setRootPath(default_path)
        self.file_tree.setRootIndex(self.file_model.index(default_path))
        
        # 右侧内容区域（使用QStackedWidget）
        self.right_panel = QFrame()
        self.right_panel.setFrameShape(QFrame.StyledPanel)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # 创建 QStackedWidget
        self.stacked_widget = QStackedWidget()
        
        # 页面 0: 欢迎页
        self.welcome_page = WelcomePage()
        self.welcome_page.set_theme_manager(self.theme_manager)
        self.welcome_page.create_new_file_requested.connect(self._on_create_new_file_requested)
        self.welcome_page.import_text_requested.connect(self.import_text)
        self.stacked_widget.addWidget(self.welcome_page)
        
        # 页面 1: 编辑器页面
        self.editor_container = QWidget()
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.cells_container = QWidget()
        self.cells_layout = QVBoxLayout(self.cells_container)
        self.cells_layout.setContentsMargins(10, 10, 10, 10)
        self.cells_layout.setSpacing(5)
        self.cells_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.cells_container)
        editor_layout.addWidget(self.scroll_area)
        
        self.stacked_widget.addWidget(self.editor_container)
        
        # 页面 2: 背诵模式主页面
        self.recitation_main_page = RecitationMainPage()
        self.recitation_main_page.set_dependencies(
            self.recitation_dal,
            self.recitation_path_manager,
            self.recitation_study_service,
            self.recitation_book_service
        )
        self.recitation_main_page.generate_article_requested.connect(
            self._on_generate_article_requested
        )
        self.recitation_main_page.start_quiz_requested.connect(
            self._on_start_quiz_requested
        )
        self.recitation_main_page.back_requested.connect(self._on_recitation_back)
        self.recitation_main_page.settings_requested.connect(self.open_settings)
        self.stacked_widget.addWidget(self.recitation_main_page)
        
        # 页面 3: 检测页面
        self.recitation_quiz_page = QuizPage()
        self.recitation_quiz_page.set_dependencies(
            self.recitation_dal,
            self.recitation_path_manager
        )
        self.recitation_quiz_page.finished.connect(self._on_quiz_finished)
        self.recitation_quiz_page.back_requested.connect(self._on_recitation_back)
        self.stacked_widget.addWidget(self.recitation_quiz_page)
        
        right_layout.addWidget(self.stacked_widget)
        
        # 组装分割器
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        
        self.splitter.setSizes([250, 750])
        self.splitter.setCollapsible(0, True)
        self.splitter.setCollapsible(1, False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        
        self.left_panel.setMinimumWidth(200)
        self.left_panel.setMaximumWidth(500)
        
        self.main_layout.addWidget(self.splitter)
        
        # 初始化 CellManager
        self.cell_manager = CellManager(self.cells_layout, self.translation_service)
        self.cell_manager.set_settings_manager(self.settings_manager)
        self.cell_manager.content_changed.connect(self._on_cell_content_changed)
        self.file_service.set_cell_manager(self.cell_manager)
        
    def init_menus(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu("文件")
        self.new_action = QAction("新建", self)
        self.new_action.setShortcut(QKeySequence("Ctrl+N"))
        self.new_action.triggered.connect(self.new_file)
        file_menu.addAction(self.new_action)
        
        self.open_action = QAction("打开", self)
        self.open_action.setShortcut(QKeySequence("Ctrl+O"))
        self.open_action.triggered.connect(self.open_file)
        file_menu.addAction(self.open_action)
        
        self.open_folder_action = QAction("打开文件夹", self)
        self.open_folder_action.setShortcut(QKeySequence("Ctrl+K"))
        self.open_folder_action.triggered.connect(self.open_folder)
        file_menu.addAction(self.open_folder_action)
        
        self.import_text_action = QAction("导入文本", self)
        self.import_text_action.setShortcut(QKeySequence("Ctrl+I"))
        self.import_text_action.triggered.connect(self.import_text)
        file_menu.addAction(self.import_text_action)
        
        self.save_action = QAction("保存", self)
        self.save_action.setShortcut(QKeySequence("Ctrl+S"))
        self.save_action.triggered.connect(self.save_file)
        file_menu.addAction(self.save_action)
        
        self.save_as_action = QAction("另存为", self)
        self.save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(self.save_as_action)
        
        edit_menu = menubar.addMenu("编辑")
        self.undo_action = QAction("撤销", self)
        self.undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        edit_menu.addAction(self.undo_action)
        
        self.redo_action = QAction("重做", self)
        self.redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        edit_menu.addAction(self.redo_action)
        
        edit_menu.addSeparator()
        
        self.translate_action = QAction("翻译当前", self)
        self.translate_action.setShortcut(QKeySequence("Ctrl+Enter"))
        self.translate_action.triggered.connect(self.translate_current_cell)
        edit_menu.addAction(self.translate_action)
        
        self.translate_all_action = QAction("翻译全部", self)
        self.translate_all_action.triggered.connect(self.translate_all_cells)
        edit_menu.addAction(self.translate_all_action)
        
        edit_menu.addSeparator()
        
        self.insert_above_action = QAction("上方插入", self)
        self.insert_above_action.setShortcut(QKeySequence("Ctrl+A"))
        self.insert_above_action.triggered.connect(self.insert_cell_above)
        edit_menu.addAction(self.insert_above_action)
        
        self.insert_below_action = QAction("下方插入", self)
        self.insert_below_action.setShortcut(QKeySequence("Ctrl+B"))
        self.insert_below_action.triggered.connect(self.insert_cell_below)
        edit_menu.addAction(self.insert_below_action)
        
        self.delete_action = QAction("删除", self)
        self.delete_action.setShortcut(QKeySequence("Delete"))
        self.delete_action.triggered.connect(self.delete_selected_cell)
        edit_menu.addAction(self.delete_action)
        
        view_menu = menubar.addMenu("查看")
        self.light_theme_action = QAction("浅色主题", self, checkable=True)
        self.light_theme_action.setChecked(True)
        self.light_theme_action.triggered.connect(lambda: self.set_theme('light'))
        view_menu.addAction(self.light_theme_action)
        
        self.dark_theme_action = QAction("深色主题", self, checkable=True)
        self.dark_theme_action.triggered.connect(lambda: self.set_theme('dark'))
        view_menu.addAction(self.dark_theme_action)
        
        # 背诵模式菜单
        recitation_menu = menubar.addMenu("背诵模式")
        self.recitation_action = QAction("打开背诵模式", self)
        self.recitation_action.setShortcut(QKeySequence("Ctrl+Shift+B"))
        self.recitation_action.triggered.connect(self._open_recitation_mode)
        recitation_menu.addAction(self.recitation_action)
        
        settings_menu = menubar.addMenu("设置")
        self.settings_action = QAction("打开设置", self)
        self.settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(self.settings_action)
        
        help_menu = menubar.addMenu("帮助")
        self.about_action = QAction("关于", self)
        self.about_action.triggered.connect(self.show_about)
        help_menu.addAction(self.about_action)
        
    def set_theme(self, theme_name):
        self.light_theme_action.setChecked(theme_name == 'light')
        self.dark_theme_action.setChecked(theme_name == 'dark')
        self.theme_manager.set_theme(theme_name)
        
    def apply_theme(self, theme_name):
        theme = self.theme_manager.get_theme()
        self.cells_container.setStyleSheet(f"background-color: {theme['scroll_area']};")
        self.scroll_area.setStyleSheet(f"background-color: {theme['scroll_area']};")
        self.left_panel.setStyleSheet(f"background-color: {theme['scroll_area']};")
        self.right_panel.setStyleSheet(f"background-color: {theme['scroll_area']};")
        
        for cell in self.cell_manager.cells:
            cell.apply_theme(theme)
        
    def init_toolbar(self):
        toolbar = QToolBar("工具栏")
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.translate_action)
        toolbar.addSeparator()
        
        self.insert_markdown_action = QAction("插入单元格", self)
        self.insert_markdown_action.triggered.connect(lambda: self.insert_cell_below())
        toolbar.addAction(self.insert_markdown_action)
        
        toolbar.addSeparator()
        toolbar.addAction(self.delete_action)
        toolbar.addSeparator()
        toolbar.addAction(self.save_action)
        
    def init_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("padding: 0 10px;")
        self.status_bar.addWidget(self.status_label)
        
    def translate_current_cell(self):
        self.cell_manager.translate_selected_cell()
        # 标记为已修改
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)
        
    def translate_all_cells(self):
        self.cell_manager.translate_all_cells()
        # 标记为已修改
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)
        
    def insert_cell_above(self):
        self.cell_manager.insert_cell_above()
        # 标记为已修改
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)
        
    def insert_cell_below(self):
        self.cell_manager.insert_cell_below()
        # 标记为已修改
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)
        
    def delete_selected_cell(self):
        self.cell_manager.delete_selected_cell()
        # 标记为已修改
        if self.file_service.is_file_open():
            self.file_service.set_modified(True)
        
    def new_file(self):
        """新建文件"""
        # 检查是否有未保存的更改
        if not self._check_unsaved_changes():
            return
            
        # 检查是否配置了工作区
        if not self.workspace_manager.get_workspace():
            self._select_workspace()
            if not self.workspace_manager.get_workspace():
                return
        
        # 弹出对话框输入文件名
        filename, ok = QInputDialog.getText(self, "新建文件", "请输入文件名:")
        if ok and filename:
            self.file_service.create_new_file(filename)
    
    def open_file(self):
        """打开文件"""
        # 检查未保存更改
        if not self._check_unsaved_changes():
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "翻译笔记本 (*.transnb)")
        if file_path:
            self.file_service.open_file(file_path)
    
    def open_folder(self):
        """打开文件夹作为工作区"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择工作区", "")
        if folder_path:
            self.workspace_manager.set_workspace(folder_path)
    
    def import_text(self):
        """导入文本文件"""
        # 检查是否有未保存的更改
        if not self._check_unsaved_changes():
            return
            
        # 检查是否配置了工作区
        if not self.workspace_manager.get_workspace():
            self._select_workspace()
            if not self.workspace_manager.get_workspace():
                return
        
        # 弹出对话框输入文件名
        filename, ok = QInputDialog.getText(self, "新建文件", "请输入文件名:")
        if not ok or not filename:
            return
        
        # 选择要导入的文本文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要导入的文本文件", "", 
            "文本文件 (*.txt *.md *.html *.htm);;所有文件 (*.*)")
        if not file_path:
            return
        
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            QMessageBox.warning(self, "错误", "文件不存在")
            return
        except UnicodeDecodeError:
            QMessageBox.warning(self, "错误", "文件编码错误，请确保是 UTF-8 编码")
            return
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取文件失败: {str(e)}")
            return
        
        # 调用 file_service.create_file_with_content 创建文件并导入内容
        self.file_service.create_file_with_content(filename, content)

    def _set_file_browser_path(self, path):
        """设置文件浏览器路径"""
        self.file_model.setRootPath(path)
        self.file_tree.setRootIndex(self.file_model.index(path))

    def restore_workspace(self):
        """恢复工作区状态"""
        # 先尝试从旧的设置恢复（向后兼容）
        old_path = self.settings_manager.get_file_browser_path()
        
        # 再加载工作区
        workspace_loaded = self.workspace_manager.load_workspace()
        
        # 如果有旧路径但没有工作区，用旧路径
        if not workspace_loaded and old_path and os.path.exists(old_path):
            self.workspace_manager.set_workspace(old_path)
            workspace_loaded = True
        
        if workspace_loaded:
            workspace = self.workspace_manager.get_workspace()
            self._set_file_browser_path(workspace)
            
            # 初始化背诵模式的工作区路径
            if workspace:
                self.recitation_path_manager.set_workspace(workspace)
                # 重新初始化数据库连接
                self.recitation_db_manager = RecitationDatabaseManager(self.recitation_path_manager)
                self.recitation_dal = RecitationDAL(self.recitation_db_manager)
                self.recitation_book_service = BookService(self.recitation_dal, self.recitation_path_manager)
                self.recitation_study_service = StudyService(self.recitation_dal, self.recitation_path_manager)
            
            # 尝试恢复上次打开的文件
            saved_file = self.settings_manager.get_current_file()
            if saved_file and os.path.exists(saved_file):
                try:
                    # 直接恢复，不用 FileService 的完整流程
                    self.cell_manager.load_from_file(saved_file)
                    self.file_service._current_file = saved_file
                    self.file_service._open_files[saved_file] = False
                    self.file_service._modified = False
                    self._switch_to_editor_page()
                    self._update_window_title()
                except Exception as e:
                    print(f"Failed to restore file: {e}")
                    self._switch_to_welcome_page()
            else:
                self._switch_to_welcome_page()
        else:
            # 没有工作区，显示欢迎页，不自动弹对话框
            self._switch_to_welcome_page()

    def save_workspace(self):
        """保存工作区状态"""
        # 由 WorkspaceManager 和 FileService 处理

    def on_file_double_clicked(self, index):
        """文件树双击事件"""
        file_path = self.file_model.filePath(index)
        
        # 如果是目录，不处理
        if self.file_model.isDir(index):
            return
            
        # 检查是否是 .transnb 文件
        if file_path.endswith('.transnb'):
            # 检查未保存更改
            if not self._check_unsaved_changes():
                return
                
            # 打开文件
            self.file_service.open_file(file_path)
            
    def save_file(self):
        """保存文件"""
        self.file_service.save_file()
            
    def save_file_as(self):
        """另存为"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "另存为", "", "翻译笔记本 (*.transnb)")
        if file_path:
            self.file_service.save_file_as(file_path)
            
    def closeEvent(self, event):
        """关闭事件"""
        if not self._check_unsaved_changes():
            event.ignore()
            return
        
        # 保存状态
        self.settings_manager.set_current_file(self.file_service.get_current_file() or "")
        event.accept()
        
    def showEvent(self, event):
        """首次显示时初始化"""
        super().showEvent(event)
        if not hasattr(self, '_has_shown'):
            self._has_shown = True
        
    def open_settings(self):
        dialog = SettingsDialog(self.settings_manager, self.theme_manager, self.translation_service, self)
        dialog.exec_()
        
    def show_about(self):
        QMessageBox.about(self, "关于", "翻译笔记本\n\n一个用于翻译的笔记本应用")
    
    # ========== 新增的槽函数和辅助方法 ==========
    
    def _switch_to_welcome_page(self):
        """切换到欢迎页"""
        self.stacked_widget.setCurrentIndex(self.PAGE_WELCOME)
        self._update_menu_states()
    
    def _switch_to_editor_page(self):
        """切换到编辑器页"""
        self.stacked_widget.setCurrentIndex(self.PAGE_EDITOR)
        self._update_menu_states()
    
    def _update_menu_states(self):
        """更新菜单项状态"""
        is_editor_page = self.stacked_widget.currentIndex() == self.PAGE_EDITOR
        is_file_open = self.file_service.is_file_open()
        
        # 文件菜单
        self.save_action.setEnabled(is_file_open)
        self.save_as_action.setEnabled(is_editor_page)
        self.import_text_action.setEnabled(True)
        
        # 编辑菜单（除了翻译相关）
        self.undo_action.setEnabled(is_editor_page)
        self.redo_action.setEnabled(is_editor_page)
        self.translate_action.setEnabled(is_editor_page)
        self.translate_all_action.setEnabled(is_editor_page)
        self.insert_above_action.setEnabled(is_editor_page)
        self.insert_below_action.setEnabled(is_editor_page)
        self.delete_action.setEnabled(is_editor_page)
    
    def _check_unsaved_changes(self):
        """检查是否有未保存的更改，返回是否继续"""
        if not self.file_service.is_file_open():
            return True
            
        if not self.file_service.is_modified():
            return True
            
        reply = QMessageBox.question(
            self, "保存提示", "当前文档有未保存的更改，是否保存？",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )
        if reply == QMessageBox.Save:
            self.file_service.save_file()
            return True
        elif reply == QMessageBox.Discard:
            return True
        else:
            return False
    
    def _select_workspace(self):
        """引导用户选择工作区"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择工作区目录", "")
        if folder_path:
            self.workspace_manager.set_workspace(folder_path)
    
    def _on_create_new_file_requested(self):
        """欢迎页点击新建文件"""
        self.new_file()
    
    def _on_file_opened(self, file_path):
        """文件已打开"""
        self.cell_manager.clear_all_cells()
        try:
            self.cell_manager.load_from_file(file_path)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载文件失败: {str(e)}")
            self._switch_to_welcome_page()
            return
        self._switch_to_editor_page()
        self.setWindowTitle(f"翻译笔记本 - {file_path}")
        self.settings_manager.set_current_file(file_path)
        self.status_label.setText(f"已打开: {os.path.basename(file_path)}")
    
    def _on_file_saved(self, file_path):
        """文件已保存"""
        self._update_window_title()
        self.status_label.setText(f"已保存: {os.path.basename(file_path)}")
    
    def _on_file_closed(self):
        """文件已关闭"""
        self.cell_manager.clear_all_cells()
        self._switch_to_welcome_page()
        self.setWindowTitle("翻译笔记本")
        self.settings_manager.set_current_file("")
        self.status_label.setText("就绪")
    
    def _on_file_modified(self, is_modified):
        """文件修改状态变更"""
        self._update_window_title()
    
    def _on_file_error(self, error_msg):
        """文件操作错误"""
        QMessageBox.warning(self, "错误", error_msg)
    
    def _on_workspace_changed(self, new_path):
        """工作区路径变化"""
        # 检查未保存更改
        if not self._check_unsaved_changes():
            return
            
        # 关闭当前文件
        if self.file_service.is_file_open():
            self.file_service.close_file()
            
        # 切换到欢迎页
        self._switch_to_welcome_page()
        
        # 更新文件浏览器路径
        if new_path:
            self._set_file_browser_path(new_path)
            
        # 更新背诵模式的工作区路径
        if new_path:
            self.recitation_path_manager.set_workspace(new_path)
            # 重新初始化数据库连接
            self.recitation_db_manager = RecitationDatabaseManager(self.recitation_path_manager)
            self.recitation_dal = RecitationDAL(self.recitation_db_manager)
            self.recitation_book_service = BookService(self.recitation_dal, self.recitation_path_manager)
            self.recitation_study_service = StudyService(self.recitation_dal, self.recitation_path_manager)
            # 更新UI中的服务引用
            if hasattr(self, 'recitation_main_page') and self.recitation_main_page:
                self.recitation_main_page.set_dependencies(
                    self.recitation_dal,
                    self.recitation_path_manager,
                    self.recitation_study_service,
                    self.recitation_book_service
                )
            if hasattr(self, 'recitation_quiz_page') and self.recitation_quiz_page:
                self.recitation_quiz_page.set_dependencies(
                    self.recitation_dal,
                    self.recitation_path_manager
                )
            
        # 更新窗口标题
        self._update_window_title()
    
    def _on_files_changed(self):
        """工作区文件列表变化"""
        # 文件树会自动更新
        pass
    
    def _update_window_title(self):
        """更新窗口标题"""
        current_file = self.file_service.get_current_file()
        workspace = self.workspace_manager.get_workspace()
        
        if current_file:
            if self.file_service.is_modified():
                self.setWindowTitle(f"翻译笔记本 - {current_file} *")
            else:
                self.setWindowTitle(f"翻译笔记本 - {current_file}")
        elif workspace:
            self.setWindowTitle(f"翻译笔记本 - {workspace}")
        else:
            self.setWindowTitle("翻译笔记本")
    
    def _on_cell_content_changed(self):
        """单元格内容变化时标记文件为已修改"""
        if self.file_service.is_file_open() and not self.file_service.is_modified():
            self.file_service.set_modified(True)
    
    # ========== 背诵模式相关的槽函数 ==========
    
    def _open_recitation_mode(self):
        """打开背诵模式"""
        # 检查是否有未保存的更改
        if not self._check_unsaved_changes():
            return
        
        # 检查是否配置了工作区
        workspace = self.workspace_manager.get_workspace()
        if not workspace:
            self._select_workspace()
            workspace = self.workspace_manager.get_workspace()
            if not workspace:
                return
        
        # 设置背诵模式的工作区路径
        self.recitation_path_manager.set_workspace(workspace)
        
        # 重新初始化数据库连接
        self.recitation_db_manager = RecitationDatabaseManager(self.recitation_path_manager)
        # 先真正初始化数据库
        success = self.recitation_db_manager.initialize()
        if not success:
            QMessageBox.warning(self, "错误", "初始化背诵模式数据库失败")
            return
        
        self.recitation_dal = RecitationDAL(self.recitation_db_manager)
        self.recitation_book_service = BookService(self.recitation_dal, self.recitation_path_manager)
        self.recitation_study_service = StudyService(self.recitation_dal, self.recitation_path_manager)
        
        # 更新背诵模式页面的依赖
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
        
        # 初始化背诵模式主页面（不再初始化数据库，直接加载数据）
        self.recitation_main_page.load_data()
        
        # 切换到背诵模式主页面
        self.stacked_widget.setCurrentIndex(self.PAGE_RECITATION_MAIN)
        self._update_menu_states()
        self.status_label.setText("背诵模式")
    
    def _on_recitation_back(self):
        """从背诵模式返回"""
        # 返回到欢迎页或编辑器页（根据之前的状态）
        if self.file_service.is_file_open():
            self._switch_to_editor_page()
        else:
            self._switch_to_welcome_page()
    
    def _on_generate_article_requested(self, new_words, review_words):
        """生成文章请求"""
        self._current_new_words = new_words
        self._current_review_words = review_words
        
        # 获取当前词书ID
        current_book = self.recitation_main_page._current_book
        self._current_book_id = current_book.id if current_book else None
        
        # 检查是否有单词
        all_words = new_words + review_words
        if not all_words:
            QMessageBox.warning(self, "提示", "没有可学习的单词")
            return
        
        # 收集单词文本
        word_texts = [w.word for w in all_words]
        
        # 显示进度对话框
        self._progress_dialog = QProgressDialog("正在生成文章...", "取消", 0, 0, self)
        self._progress_dialog.setWindowModality(Qt.WindowModal)
        self._progress_dialog.setCancelButton(None)
        self._progress_dialog.show()
        
        # 启动生成文章的工作线程
        self._generate_worker = GenerateArticleWorker(
            self.translation_service,
            word_texts
        )
        self._generate_worker.finished.connect(self._on_article_generated)
        self._generate_worker.progress.connect(self._on_article_progress)
        self._generate_worker.start()
    
    def _on_article_progress(self, message):
        """文章生成进度更新"""
        if self._progress_dialog:
            self._progress_dialog.setLabelText(message)
    
    def _on_article_generated(self, success, article, error_msg):
        """文章生成完成"""
        if self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None
        
        if not success:
            QMessageBox.warning(self, "错误", f"生成文章失败: {error_msg}")
            return
        
        # 格式化文章（新单词下划线，复习单词加粗）
        formatted_article = ArticleGenerator.format_article(
            article,
            self._current_new_words,
            self._current_review_words
        )
        
        # 提取标题
        title = ArticleGenerator.extract_title(article)
        
        # 检查是否有工作区
        workspace = self.workspace_manager.get_workspace()
        if not workspace:
            QMessageBox.warning(self, "错误", "请先选择工作区")
            return
        
        # 保存文章
        save_success, file_path_or_error = ArticleGenerator.save_article(
            workspace,
            formatted_article,
            title
        )
        
        if not save_success:
            QMessageBox.warning(self, "错误", f"保存文章失败: {file_path_or_error}")
            return
        
        # 打开文章
        self.file_service.open_file(file_path_or_error)
    
    def _on_start_quiz_requested(self, new_words, review_words):
        """开始检测请求"""
        self._current_new_words = new_words
        self._current_review_words = review_words
        
        # 获取当前词书ID
        current_book = self.recitation_main_page._current_book
        self._current_book_id = current_book.id if current_book else None
        
        # 检查是否有单词
        all_words = new_words + review_words
        if not all_words:
            QMessageBox.warning(self, "提示", "没有可检测的单词")
            return
        
        # 设置检测页面的单词
        self.recitation_quiz_page.set_words(
            new_words,
            review_words,
            self._current_book_id
        )
        
        # 切换到检测页面
        self.stacked_widget.setCurrentIndex(self.PAGE_RECITATION_QUIZ)
    
    def _on_quiz_finished(self, results):
        """检测完成"""
        # 这里可以添加检测完成后的处理逻辑
        QMessageBox.information(self, "完成", "检测已完成！")
        # 返回到背诵模式主页面
        self.stacked_widget.setCurrentIndex(self.PAGE_RECITATION_MAIN)
