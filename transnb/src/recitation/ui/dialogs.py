from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QComboBox, QMessageBox, QGroupBox,
    QListWidget, QListWidgetItem, QCheckBox, QFormLayout, QWidget
)
from PyQt5.QtCore import Qt
from typing import List, Optional
from ..models import Word, Book
from ..dal import RecitationDAL
from ..path_manager import PathManager
from ..utils import format_phonetic


class NewBookDialog(QDialog):
    """新建词书对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建词书")
        self.setMinimumWidth(400)
        self._book_name_edit = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        name_group = QGroupBox("词书信息")
        name_layout = QVBoxLayout(name_group)
        
        name_label = QLabel("词书名称：")
        self._book_name_edit = QLineEdit()
        self._book_name_edit.setPlaceholderText("请输入词书名称")
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(self._book_name_edit)
        
        layout.addWidget(name_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self._on_ok)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_ok(self):
        name = self._book_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入词书名称！")
            return
        self.accept()
    
    def get_book_name(self) -> str:
        return self._book_name_edit.text().strip()


class AddWordDialog(QDialog):
    """手动添加单词对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加单词")
        self.setMinimumWidth(500)
        self._word_edit = None
        self._phonetic_edit = None
        self._definition_edit = None
        self._example_edit = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 单词输入
        word_group = QGroupBox("单词信息")
        word_layout = QFormLayout(word_group)
        
        self._word_edit = QLineEdit()
        self._word_edit.setPlaceholderText("请输入单词")
        word_layout.addRow("单词：", self._word_edit)
        
        self._phonetic_edit = QLineEdit()
        self._phonetic_edit.setPlaceholderText("请输入音标（可选）")
        word_layout.addRow("音标：", self._phonetic_edit)
        
        self._definition_edit = QTextEdit()
        self._definition_edit.setMaximumHeight(100)
        self._definition_edit.setPlaceholderText("请输入单词释义")
        word_layout.addRow("释义：", self._definition_edit)
        
        self._example_edit = QTextEdit()
        self._example_edit.setMaximumHeight(80)
        self._example_edit.setPlaceholderText("请输入例句（可选）")
        word_layout.addRow("例句：", self._example_edit)
        
        layout.addWidget(word_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("添加")
        ok_btn.clicked.connect(self._on_ok)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_ok(self):
        word = self._word_edit.text().strip()
        definition = self._definition_edit.toPlainText().strip()
        
        if not word:
            QMessageBox.warning(self, "提示", "请输入单词！")
            return
        if not definition:
            QMessageBox.warning(self, "提示", "请输入单词释义！")
            return
        
        self.accept()
    
    def get_word_data(self) -> dict:
        return {
            'word': self._word_edit.text().strip(),
            'phonetic': self._phonetic_edit.text().strip(),
            'definition': self._definition_edit.toPlainText().strip(),
            'example': self._example_edit.toPlainText().strip()
        }


class AddToBookDialog(QDialog):
    """添加单词到指定词书对话框"""
    
    def __init__(self, word: Word, dal: RecitationDAL, parent=None):
        super().__init__(parent)
        self._word = word
        self._dal = dal
        self._books: List[Book] = []
        self._book_combo = None
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle("添加单词到词书")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        
        # 单词信息预览
        word_group = QGroupBox("要添加的单词")
        word_layout = QVBoxLayout(word_group)
        
        info_text = f"<b>{self._word.word}</b>"
        formatted_phonetic = format_phonetic(self._word.phonetic)
        if formatted_phonetic:
            info_text += f" {formatted_phonetic}"
        info_text += f"<br>{self._word.definition}"
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        word_layout.addWidget(info_label)
        
        layout.addWidget(word_group)
        
        # 词书选择
        book_group = QGroupBox("选择目标词书")
        book_layout = QVBoxLayout(book_group)
        
        self._book_combo = QComboBox()
        self._load_books()
        book_layout.addWidget(self._book_combo)
        
        layout.addWidget(book_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("添加")
        ok_btn.clicked.connect(self._on_ok)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_books(self):
        self._books = self._dal.get_all_books()
        self._book_combo.clear()
        for book in self._books:
            self._book_combo.addItem(f"{book.name} ({book.count}词)", book.id)
        
        if not self._books:
            self._book_combo.addItem("暂无词书，请先创建")
            self._book_combo.setEnabled(False)
    
    def get_selected_book_id(self) -> Optional[int]:
        if not self._books:
            return None
        return self._book_combo.currentData()
    
    def _on_ok(self):
        if not self._books:
            QMessageBox.warning(self, "提示", "暂无可用词书，请先创建词书！")
            return
        
        book_id = self.get_selected_book_id()
        if not book_id:
            return
        
        exists = self._dal.check_word_exists_in_book(book_id, self._word.word)
        if exists:
            QMessageBox.warning(self, "提示", "该单词已存在于目标词书中！")
            return
        
        self.accept()


class AddToBookBatchDialog(QDialog):
    """批量添加单词到指定词书对话框"""
    
    def __init__(self, words: List[Word], dal: RecitationDAL, parent=None):
        super().__init__(parent)
        self._words = words
        self._dal = dal
        self._books: List[Book] = []
        self._book_combo = None
        self._words_list = None
        self._selected_words: List[Word] = []  # 存储用户选择的单词
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle("添加单词到词书")
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)
        
        layout = QVBoxLayout(self)
        
        # 单词列表预览
        word_group = QGroupBox(f"错题单词 ({len(self._words)}个) - 请选择要添加的单词")
        word_layout = QVBoxLayout(word_group)
        
        # 全选/全不选按钮
        select_btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("全选")
        select_all_btn.clicked.connect(self._on_select_all)
        select_none_btn = QPushButton("全不选")
        select_none_btn.clicked.connect(self._on_select_none)
        select_btn_layout.addWidget(select_all_btn)
        select_btn_layout.addWidget(select_none_btn)
        select_btn_layout.addStretch()
        word_layout.addLayout(select_btn_layout)
        
        self._words_list = QListWidget()
        self._load_words()
        word_layout.addWidget(self._words_list)
        
        layout.addWidget(word_group)
        
        # 词书选择
        book_group = QGroupBox("选择目标词书")
        book_layout = QVBoxLayout(book_group)
        
        self._book_combo = QComboBox()
        self._load_books()
        book_layout.addWidget(self._book_combo)
        
        layout.addWidget(book_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("添加选中")
        ok_btn.clicked.connect(self._on_ok)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def _load_words(self):
        self._words_list.clear()
        for word in self._words:
            text = word.word
            formatted_phonetic = format_phonetic(word.phonetic)
            if formatted_phonetic:
                text += f" {formatted_phonetic}"
            if word.definition:
                text += f" - {word.definition[:40]}"
                if len(word.definition) > 40:
                    text += "..."
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, word)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)  # 允许复选
            item.setCheckState(Qt.Checked)  # 默认选中
            self._words_list.addItem(item)
    
    def _load_books(self):
        self._books = self._dal.get_all_books()
        self._book_combo.clear()
        for book in self._books:
            self._book_combo.addItem(f"{book.name} ({book.count}词)", book.id)
        
        if not self._books:
            self._book_combo.addItem("暂无词书，请先创建")
            self._book_combo.setEnabled(False)
    
    def get_selected_book_id(self) -> Optional[int]:
        if not self._books:
            return None
        return self._book_combo.currentData()
    
    def get_selected_words(self) -> List[Word]:
        """获取用户选中的单词列表"""
        selected = []
        for i in range(self._words_list.count()):
            item = self._words_list.item(i)
            if item.checkState() == Qt.Checked:
                word = item.data(Qt.UserRole)
                selected.append(word)
        return selected
    
    def _on_select_all(self):
        """全选"""
        for i in range(self._words_list.count()):
            item = self._words_list.item(i)
            item.setCheckState(Qt.Checked)
    
    def _on_select_none(self):
        """全不选"""
        for i in range(self._words_list.count()):
            item = self._words_list.item(i)
            item.setCheckState(Qt.Unchecked)
    
    def _on_ok(self):
        if not self._books:
            QMessageBox.warning(self, "提示", "暂无可用词书，请先创建词书！")
            return
        
        # 检查是否有选中的单词
        selected_words = self.get_selected_words()
        if not selected_words:
            QMessageBox.warning(self, "提示", "请至少选择一个单词！")
            return
        
        book_id = self.get_selected_book_id()
        if not book_id:
            return
        
        self.accept()


class AddWordToBookDialog(QWidget):
    """非模态对话框，用于编辑单词信息并添加到指定词书"""
    
    def __init__(self, dal, parent=None):
        super().__init__(parent)
        self._dal = dal
        self._word_edit = None
        self._phonetic_edit = None
        self._definition_edit = None
        self._example_edit = None
        self._book_combo = None
        self._info_label = None
        self._init_ui()
        
    def _init_ui(self):
        self.setWindowTitle("收藏")
        self.setMinimumWidth(550)
        
        layout = QVBoxLayout(self)
        
        # 信息提示标签
        self._info_label = QLabel()
        self._info_label.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self._info_label)
        
        # 单词信息
        word_group = QGroupBox("单词信息")
        word_layout = QFormLayout(word_group)
        
        self._word_edit = QLineEdit()
        self._word_edit.setPlaceholderText("请输入单词")
        word_layout.addRow("单词：", self._word_edit)
        
        self._phonetic_edit = QLineEdit()
        self._phonetic_edit.setPlaceholderText("请输入音标（可选）")
        word_layout.addRow("音标：", self._phonetic_edit)
        
        self._definition_edit = QTextEdit()
        self._definition_edit.setMaximumHeight(100)
        self._definition_edit.setPlaceholderText("请输入单词释义")
        word_layout.addRow("释义：", self._definition_edit)
        
        self._example_edit = QTextEdit()
        self._example_edit.setMaximumHeight(80)
        self._example_edit.setPlaceholderText("请输入例句（可选）")
        word_layout.addRow("例句：", self._example_edit)
        
        layout.addWidget(word_group)
        
        # 词书选择
        book_group = QGroupBox("选择词书")
        book_layout = QVBoxLayout(book_group)
        
        self._book_combo = QComboBox()
        self._load_books()
        book_layout.addWidget(self._book_combo)
        
        layout.addWidget(book_group)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("关闭")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("添加到词书")
        add_btn.clicked.connect(self._on_add)
        add_btn.setDefault(True)
        btn_layout.addWidget(add_btn)
        
        layout.addLayout(btn_layout)
        
    def _preprocess_word(self, raw_text):
        """预处理单词：去空格等"""
        if not raw_text:
            return ""
        # 去除首尾空格，合并中间多余空格
        return ' '.join(raw_text.strip().split())
        
    def _search_and_fill_word(self, processed_word):
        """搜索单词并回填信息"""
        self._info_label.setText("")
        
        if not processed_word:
            return
            
        # 搜索数据库
        found_word = self._dal.search_word_exact_lower(processed_word)
        
        if found_word:
            # 找到匹配，回填所有信息
            self._word_edit.setText(found_word.word)
            self._phonetic_edit.setText(found_word.phonetic or "")
            self._definition_edit.setPlainText(found_word.definition or "")
            self._example_edit.setPlainText(found_word.example or "")
            
            # 选中对应词书
            self._select_book_by_id(found_word.book_id)
            
            # 显示提示
            self._info_label.setText("✓ 已找到该单词的记录，信息已自动填充")
            self._info_label.setStyleSheet("color: #2e7d32; padding: 5px; font-weight: bold;")
        else:
            # 未找到，清空其他字段，仅保留单词
            self._phonetic_edit.clear()
            self._definition_edit.clear()
            self._example_edit.clear()
            self._book_combo.setCurrentIndex(0)
            self._info_label.setText("")
        
    def _select_book_by_id(self, book_id):
        """根据词书ID选中对应的下拉项"""
        for i in range(self._book_combo.count()):
            item_data = self._book_combo.itemData(i)
            if item_data == book_id:
                self._book_combo.setCurrentIndex(i)
                break
        
    def _load_books(self):
        """加载词书列表"""
        self._book_combo.clear()
        books = self._dal.get_all_books()
        for book in books:
            self._book_combo.addItem(f"{book.name} ({book.count}词)", book.id)
        
        if not books:
            self._book_combo.addItem("暂无词书，请先创建")
            self._book_combo.setEnabled(False)
        else:
            self._book_combo.setEnabled(True)
            
    def set_word(self, word_text):
        """设置要收藏的单词 - 包含完整预处理和搜索逻辑"""
        # 1. 预处理单词
        processed = self._preprocess_word(word_text)
        
        # 2. 先填入预处理后的单词
        self._word_edit.setText(processed)
        
        # 3. 重新加载词书列表（确保是最新的）
        self._load_books()
        
        # 4. 搜索并回填
        if processed:
            self._search_and_fill_word(processed)
        
    def set_phonetic(self, phonetic):
        """设置音标"""
        self._phonetic_edit.setText(phonetic)
        
    def set_definition(self, definition):
        """设置释义"""
        self._definition_edit.setPlainText(definition)
        
    def set_example(self, example):
        """设置例句"""
        self._example_edit.setPlainText(example)
        
    def showEvent(self, event):
        """对话框显示时重新加载词书"""
        self._load_books()
        super().showEvent(event)
        
    def _on_add(self):
        word = self._word_edit.text().strip()
        definition = self._definition_edit.toPlainText().strip()
        
        if not word:
            QMessageBox.warning(self, "提示", "请输入单词！")
            return
        if not definition:
            QMessageBox.warning(self, "提示", "请输入单词释义！")
            return
            
        book_id = self._book_combo.currentData()
        if not book_id:
            QMessageBox.warning(self, "提示", "请先创建并选择一个词书！")
            return
            
        # 检查单词是否已存在
        exists = self._dal.check_word_exists_in_book(book_id, word)
        if exists:
            QMessageBox.warning(self, "提示", "该单词已存在于目标词书中！")
            return
            
        # 添加单词
        from ..models import Word
        new_word = Word(
            word=word,
            phonetic=self._phonetic_edit.text().strip(),
            definition=definition,
            example=self._example_edit.toPlainText().strip()
        )
        new_word.book_id = book_id
        
        success = self._dal.add_word(new_word)
        if success:
            QMessageBox.information(self, "成功", "单词已添加到词书！")
            self._load_books()  # 刷新词书列表以更新单词计数
        else:
            QMessageBox.warning(self, "错误", "添加单词失败！")
