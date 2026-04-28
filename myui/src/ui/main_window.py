from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QToolBar, QStatusBar, QScrollArea,
    QAction, QFileDialog, QMessageBox, QLabel
)
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QTimer
from cells.cell_manager import CellManager
from kernel.kernel_manager import KernelManager
from cells.code_cell import CodeCell
from cells.markdown_cell import MarkdownCell
from utils.theme_manager import ThemeManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Jupyter Editor")
        self.setGeometry(100, 100, 1200, 800)
        
        self.current_file = None
        self.unsaved_changes = False
        
        self.kernel_manager = KernelManager()
        self.kernel_manager.start_kernel()
        
        self.theme_manager = ThemeManager()
        self.theme_manager.theme_changed.connect(self.apply_theme)
        
        self.init_ui()
        self.init_menus()
        self.init_toolbar()
        self.init_statusbar()
        
        self.add_initial_cells()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        
        self.cells_container = QWidget()
        self.cells_layout = QVBoxLayout(self.cells_container)
        self.cells_layout.setContentsMargins(10, 10, 10, 10)
        self.cells_layout.setSpacing(5)
        self.cells_layout.setAlignment(Qt.AlignTop)
        
        self.scroll_area.setWidget(self.cells_container)
        self.main_layout.addWidget(self.scroll_area)
        
        self.cell_manager = CellManager(self.cells_layout, self.kernel_manager)
        
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
        
        run_menu = menubar.addMenu("运行")
        self.run_action = QAction("运行当前", self)
        self.run_action.setShortcut(QKeySequence("Ctrl+Enter"))
        self.run_action.triggered.connect(self.run_current_cell)
        run_menu.addAction(self.run_action)
        
        self.run_all_action = QAction("运行全部", self)
        self.run_all_action.triggered.connect(self.run_all_cells)
        run_menu.addAction(self.run_all_action)
        
        self.stop_action = QAction("停止", self)
        self.stop_action.triggered.connect(self.stop_kernel)
        run_menu.addAction(self.stop_action)
        
        cell_menu = menubar.addMenu("单元格")
        self.insert_above_action = QAction("上方插入", self)
        self.insert_above_action.setShortcut(QKeySequence("Ctrl+A"))
        self.insert_above_action.triggered.connect(self.insert_cell_above)
        cell_menu.addAction(self.insert_above_action)
        
        self.insert_below_action = QAction("下方插入", self)
        self.insert_below_action.setShortcut(QKeySequence("Ctrl+B"))
        self.insert_below_action.triggered.connect(self.insert_cell_below)
        cell_menu.addAction(self.insert_below_action)
        
        self.delete_action = QAction("删除", self)
        self.delete_action.setShortcut(QKeySequence("Delete"))
        self.delete_action.triggered.connect(self.delete_selected_cell)
        cell_menu.addAction(self.delete_action)
        
        self.to_markdown_action = QAction("转为 Markdown", self)
        self.to_markdown_action.setShortcut(QKeySequence("Esc,M"))
        self.to_markdown_action.triggered.connect(self.convert_to_markdown)
        cell_menu.addAction(self.to_markdown_action)
        
        self.to_code_action = QAction("转为代码", self)
        self.to_code_action.setShortcut(QKeySequence("Esc,Y"))
        self.to_code_action.triggered.connect(self.convert_to_code)
        cell_menu.addAction(self.to_code_action)
        
        view_menu = menubar.addMenu("视图")
        self.light_theme_action = QAction("浅色主题", self, checkable=True)
        self.light_theme_action.setChecked(True)
        self.light_theme_action.triggered.connect(lambda: self.set_theme('light'))
        view_menu.addAction(self.light_theme_action)
        
        self.dark_theme_action = QAction("深色主题", self, checkable=True)
        self.dark_theme_action.triggered.connect(lambda: self.set_theme('dark'))
        view_menu.addAction(self.dark_theme_action)
        
    def set_theme(self, theme_name):
        self.light_theme_action.setChecked(theme_name == 'light')
        self.dark_theme_action.setChecked(theme_name == 'dark')
        self.theme_manager.set_theme(theme_name)
        
    def apply_theme(self, theme_name):
        theme = self.theme_manager.get_theme()
        self.cells_container.setStyleSheet(f"background-color: {theme['scroll_area']};")
        self.scroll_area.setStyleSheet(f"background-color: {theme['scroll_area']};")
        
        for cell in self.cell_manager.cells:
            cell.apply_theme(theme)
        
    def init_toolbar(self):
        toolbar = QToolBar("工具栏")
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.run_action)
        toolbar.addAction(self.stop_action)
        toolbar.addSeparator()
        
        self.insert_code_action = QAction("插入代码单元格", self)
        self.insert_code_action.triggered.connect(lambda: self.insert_cell_below(cell_type='code'))
        toolbar.addAction(self.insert_code_action)
        
        self.insert_markdown_action = QAction("插入 Markdown 单元格", self)
        self.insert_markdown_action.triggered.connect(lambda: self.insert_cell_below(cell_type='markdown'))
        toolbar.addAction(self.insert_markdown_action)
        
        toolbar.addSeparator()
        toolbar.addAction(self.delete_action)
        toolbar.addSeparator()
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        
        self.format_action = QAction("格式化代码", self)
        self.format_action.triggered.connect(self.format_selected_cell)
        toolbar.addAction(self.format_action)
        
    def format_selected_cell(self):
        self.cell_manager.format_selected_cell()
        
    def init_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.kernel_status_label = QLabel()
        self.kernel_status_label.setStyleSheet("padding: 0 10px;")
        self.status_bar.addWidget(self.kernel_status_label)
        self.update_kernel_status()
        
        self.kernel_manager.status_changed.connect(self.update_kernel_status)
        
    def update_kernel_status(self):
        status = self.kernel_manager.get_status()
        if status == 'idle':
            self.kernel_status_label.setText("内核状态: 空闲")
            self.kernel_status_label.setStyleSheet("color: green; padding: 0 10px;")
        elif status == 'busy':
            self.kernel_status_label.setText("内核状态: 运行中")
            self.kernel_status_label.setStyleSheet("color: orange; padding: 0 10px;")
        else:
            self.kernel_status_label.setText(f"内核状态: {status}")
            self.kernel_status_label.setStyleSheet("color: red; padding: 0 10px;")
        
    def add_initial_cells(self):
        code_cell = CodeCell(self.kernel_manager)
        code_cell.set_code('print("Hello, PyQt Jupyter!")')
        self.cell_manager.add_cell(code_cell)
        
        markdown_cell = MarkdownCell()
        markdown_cell.set_content("# Welcome to PyQt Jupyter Editor\n\nThis is a Markdown cell. You can write **bold**, *italic*, and create lists:\n\n- Item 1\n- Item 2\n- Item 3")
        self.cell_manager.add_cell(markdown_cell)
        
        code_cell2 = CodeCell(self.kernel_manager)
        code_cell2.set_code('import numpy as np\nimport matplotlib.pyplot as plt\n\nx = np.linspace(0, 10, 100)\ny = np.sin(x)\n\nplt.plot(x, y)\nplt.title("Sine Wave")\nplt.show()')
        self.cell_manager.add_cell(code_cell2)
        
    def run_current_cell(self):
        self.cell_manager.run_selected_cell()
        
    def run_all_cells(self):
        self.cell_manager.run_all_cells()
        
    def stop_kernel(self):
        self.kernel_manager.stop_kernel()
        self.kernel_manager.start_kernel()
        
    def insert_cell_above(self, cell_type='code'):
        self.cell_manager.insert_cell_above(cell_type)
        
    def insert_cell_below(self, cell_type='code'):
        self.cell_manager.insert_cell_below(cell_type)
        
    def delete_selected_cell(self):
        self.cell_manager.delete_selected_cell()
        
    def convert_to_markdown(self):
        self.cell_manager.convert_selected_to_markdown()
        
    def convert_to_code(self):
        self.cell_manager.convert_selected_to_code()
        
    def new_file(self):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, "保存提示", "当前文档有未保存的更改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return
        
        self.cell_manager.clear_all_cells()
        self.add_initial_cells()
        self.current_file = None
        self.unsaved_changes = False
        self.setWindowTitle("PyQt Jupyter Editor")
        self.adjust_all_cell_heights()
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "PyQt Notebook (*.pyqtnb);;Jupyter Notebook (*.ipynb)"
        )
        if file_path:
            self.cell_manager.load_from_file(file_path)
            self.current_file = file_path
            self.unsaved_changes = False
            self.setWindowTitle(f"PyQt Jupyter Editor - {file_path}")
            self.adjust_all_cell_heights()
            
    def save_file(self):
        if self.current_file:
            self.cell_manager.save_to_file(self.current_file)
            self.unsaved_changes = False
        else:
            self.save_file_as()
            
    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "另存为", "", "PyQt Notebook (*.pyqtnb)"
        )
        if file_path:
            if not file_path.endswith('.pyqtnb'):
                file_path += '.pyqtnb'
            self.cell_manager.save_to_file(file_path)
            self.current_file = file_path
            self.unsaved_changes = False
            self.setWindowTitle(f"PyQt Jupyter Editor - {file_path}")
            
    def closeEvent(self, event):
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, "保存提示", "当前文档有未保存的更改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Save:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        self.kernel_manager.stop_kernel()
        event.accept()
        
    def showEvent(self, event):
        super().showEvent(event)
        self.adjust_all_cell_heights()
        
    def adjust_all_cell_heights(self):
        QTimer.singleShot(100, self._adjust_all_cell_heights_delayed)
        
    def _adjust_all_cell_heights_delayed(self):
        self.cell_manager.adjust_all_cell_heights()