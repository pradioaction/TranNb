from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QButtonGroup, QRadioButton, QStackedWidget, QProgressBar,
    QMessageBox, QGroupBox, QScrollArea, QFrame, QSplitter, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from typing import List, Dict, Tuple, Optional
import random
from ..models import Word
from ..utils import format_phonetic
from ..workers import ReviewBatchWordsWorker
from ..dal import RecitationDAL
from ..path_manager import PathManager
from .dialogs import AddToBookBatchDialog


class QuizQuestion:
    """题目数据类"""
    
    TYPE_WORD_TO_DEFINITION = 0  # 单词选释义
    TYPE_DEFINITION_TO_WORD = 1  # 释义选单词
    
    def __init__(self, word: Word, question_type: int, options: List[str]):
        self.word = word
        self.question_type = question_type
        self.options = options
        self.selected_answer: Optional[int] = None
        self.correct_answer: int = 0


class WordResult:
    """单词测试结果类"""
    
    def __init__(self, word: Word, is_new: bool):
        self.word = word
        self.is_new = is_new  # 是否是新学单词
        self.questions: List[QuizQuestion] = []  # 该单词的两道题目
        self.word_to_def_correct: Optional[bool] = None  # 单词选释义是否正确
        self.definition_to_word_correct: Optional[bool] = None  # 释义选单词是否正确
        self.overall_success: bool = False  # 是否记忆成功（两道题都对）


class QuizPage(QWidget):
    """检测页面"""
    
    finished = pyqtSignal(list)  # 结果列表
    back_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._new_words: List[Word] = []
        self._review_words: List[Word] = []
        self._all_words: List[Word] = []
        self._questions: List[QuizQuestion] = []  # 所有题目
        self._word_results: Dict[int, WordResult] = {}  # 单词ID -> 结果
        self._current_index: int = 0
        self._book_id: Optional[int] = None
        self._dal: Optional[RecitationDAL] = None
        self._path_manager: Optional[PathManager] = None
        self._workers = {}  # 存储工作线程
        self._init_ui()
    
    def hideEvent(self, event):
        """页面隐藏时清理线程"""
        self._cleanup_workers()
        super().hideEvent(event)
    
    def _cleanup_workers(self):
        """清理所有工作线程"""
        for worker in self._workers.values():
            if worker and hasattr(worker, 'isRunning') and worker.isRunning():
                worker.quit()
                worker.wait(1000)
        self._workers.clear()
    
    def _start_worker(self, worker, worker_id=None):
        """启动一个工作线程并正确管理"""
        # 先清理已存在的同名线程
        if worker_id and worker_id in self._workers:
            old_worker = self._workers[worker_id]
            if old_worker and hasattr(old_worker, 'isRunning') and old_worker.isRunning():
                old_worker.quit()
                old_worker.wait(1000)
        
        # 存储并启动新线程
        if worker_id:
            self._workers[worker_id] = worker
        worker.start()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 顶部 - 进度和控制
        top_layout = QHBoxLayout()
        
        self._back_btn = QPushButton("返回")
        self._back_btn.clicked.connect(self.back_requested.emit)
        top_layout.addWidget(self._back_btn)
        
        top_layout.addStretch()
        
        self._progress_label = QLabel("0 / 0")
        top_layout.addWidget(self._progress_label)
        
        layout.addLayout(top_layout)
        
        # 进度条
        self._progress_bar = QProgressBar()
        layout.addWidget(self._progress_bar)
        
        # 题目区域
        self._question_stack = QStackedWidget()
        layout.addWidget(self._question_stack, 1)
        
        # 创建各个页面
        self._question_widget = self._create_question_widget()
        self._result_widget = self._create_result_widget()
        self._question_stack.addWidget(self._question_widget)
        self._question_stack.addWidget(self._result_widget)
    
    def _create_question_widget(self) -> QWidget:
        """创建答题页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # 题目类型提示
        self._type_label = QLabel()
        type_font = QFont()
        type_font.setBold(True)
        self._type_label.setFont(type_font)
        self._type_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._type_label)
        
        # 题目内容
        self._question_content_label = QLabel()
        content_font = QFont()
        content_font.setPointSize(16)
        self._question_content_label.setFont(content_font)
        self._question_content_label.setWordWrap(True)
        self._question_content_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._question_content_label)
        
        # 选项区域
        options_group = QGroupBox("请选择答案")
        options_layout = QVBoxLayout(options_group)
        
        self._option_group = QButtonGroup()
        self._option_buttons: List[QRadioButton] = []
        
        for i in range(4):
            btn = QRadioButton()
            btn.clicked.connect(lambda checked, idx=i: self._on_option_selected(idx))
            options_layout.addWidget(btn)
            self._option_group.addButton(btn, i)
            self._option_buttons.append(btn)
        
        layout.addWidget(options_group)
        
        # 底部 - 导航按钮
        nav_layout = QHBoxLayout()
        
        self._prev_btn = QPushButton("上一题")
        self._prev_btn.clicked.connect(self._on_prev_question)
        self._prev_btn.setEnabled(False)
        nav_layout.addWidget(self._prev_btn)
        
        nav_layout.addStretch()
        
        self._next_btn = QPushButton("下一题")
        self._next_btn.clicked.connect(self._on_next_question)
        nav_layout.addWidget(self._next_btn)
        
        self._submit_btn = QPushButton("检查")
        self._submit_btn.clicked.connect(self._on_submit)
        self._submit_btn.hide()
        nav_layout.addWidget(self._submit_btn)
        
        layout.addLayout(nav_layout)
        
        return widget
    
    def _create_result_widget(self) -> QWidget:
        """创建结果页面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 顶部结果摘要
        summary_group = QGroupBox("检测结果")
        summary_layout = QVBoxLayout(summary_group)
        
        self._result_title = QLabel()
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        self._result_title.setFont(title_font)
        self._result_title.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self._result_title)
        
        self._score_label = QLabel()
        score_font = QFont()
        score_font.setPointSize(28)
        score_font.setBold(True)
        self._score_label.setFont(score_font)
        self._score_label.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self._score_label)
        
        self._result_summary = QLabel()
        self._result_summary.setWordWrap(True)
        self._result_summary.setAlignment(Qt.AlignCenter)
        summary_layout.addWidget(self._result_summary)
        
        layout.addWidget(summary_group)
        
        # 滚动区域显示详细结果
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self._details_container = QWidget()
        self._details_layout = QVBoxLayout(self._details_container)
        self._details_layout.setSpacing(10)
        self._details_layout.addStretch()
        
        scroll.setWidget(self._details_container)
        layout.addWidget(scroll, 1)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        self._add_failed_btn = QPushButton("添加错题到词书")
        self._add_failed_btn.clicked.connect(self._on_add_failed_to_book)
        self._add_failed_btn.setEnabled(False)
        btn_layout.addWidget(self._add_failed_btn)
        
        btn_layout.addStretch()
        
        # 返回按钮
        return_btn = QPushButton("返回背诵模式")
        return_btn.setMinimumHeight(50)
        return_btn.clicked.connect(self._on_back_to_main)
        btn_layout.addWidget(return_btn)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def set_dependencies(self, dal, path_manager):
        """设置依赖项"""
        self._dal = dal
        self._path_manager = path_manager
    
    def set_words(self, new_words: List[Word], review_words: List[Word], book_id: int):
        """设置要测验的单词"""
        self._new_words = new_words
        self._review_words = review_words
        self._all_words = new_words + review_words
        self._book_id = book_id
        
        # 初始化单词结果
        self._word_results = {}
        for word in new_words:
            self._word_results[word.id] = WordResult(word, True)
        for word in review_words:
            self._word_results[word.id] = WordResult(word, False)
        
        # 生成题目
        self._generate_questions()
        self._current_index = 0
        self._show_current_question()
        self._update_progress()
    
    def _generate_questions(self):
        """生成题目 - 每个单词两道题"""
        self._questions = []
        
        # 为每个单词生成两种题型
        for word in self._all_words:
            # 题型1：单词选释义
            q1 = self._create_single_question(word, QuizQuestion.TYPE_WORD_TO_DEFINITION)
            self._questions.append(q1)
            self._word_results[word.id].questions.append(q1)
            
            # 题型2：释义选单词
            q2 = self._create_single_question(word, QuizQuestion.TYPE_DEFINITION_TO_WORD)
            self._questions.append(q2)
            self._word_results[word.id].questions.append(q2)
        
        # 打乱题目顺序
        random.shuffle(self._questions)
    
    def _create_single_question(self, word: Word, question_type: int) -> QuizQuestion:
        """创建单个题目"""
        options = self._generate_options(word, question_type)
        question = QuizQuestion(word, question_type, options)
        
        # 设置正确答案
        if question_type == QuizQuestion.TYPE_WORD_TO_DEFINITION:
            correct_option = word.definition
        else:
            correct_option = word.word
        
        question.correct_answer = options.index(correct_option)
        
        return question
    
    def _generate_options(self, word: Word, question_type: int) -> List[str]:
        """生成选项"""
        if question_type == QuizQuestion.TYPE_WORD_TO_DEFINITION:
            correct_option = word.definition
            all_options = [w.definition for w in self._all_words if w.id != word.id and w.definition]
        else:
            correct_option = word.word
            all_options = [w.word for w in self._all_words if w.id != word.id and w.word]
        
        # 随机选择3个干扰项
        if all_options:
            distractors = random.sample(all_options, min(3, len(all_options)))
        else:
            distractors = []
        
        # 如果干扰项不足3个，用空字符串填充
        while len(distractors) < 3:
            distractors.append("")
        
        # 合并并打乱选项
        options = [correct_option] + distractors
        random.shuffle(options)
        
        return options
    
    def _show_current_question(self):
        """显示当前题目"""
        if self._current_index >= len(self._questions):
            return
        
        question = self._questions[self._current_index]
        
        # 设置题目类型提示
        if question.question_type == QuizQuestion.TYPE_WORD_TO_DEFINITION:
            self._type_label.setText("📝 选择正确的释义")
            display_text = f"{question.word.word}"
            formatted_phonetic = format_phonetic(question.word.phonetic)
            if formatted_phonetic:
                display_text += f"\n{formatted_phonetic}"
            self._question_content_label.setText(display_text)
        else:
            self._type_label.setText("🔤 选择正确的单词")
            self._question_content_label.setText(question.word.definition)
        
        # 先暂时阻止信号，避免误触发
        for btn in self._option_buttons:
            btn.blockSignals(True)
        
        # 清除按钮组的选择
        checked_button = self._option_group.checkedButton()
        if checked_button:
            self._option_group.setExclusive(False)
            checked_button.setChecked(False)
            self._option_group.setExclusive(True)
        
        # 清空所有选项
        for i in range(4):
            self._option_buttons[i].setChecked(False)
        
        # 设置新的选项
        for i, option in enumerate(question.options):
            self._option_buttons[i].setText(option)
        
        # 恢复之前的选择（如果有）
        if question.selected_answer is not None and 0 <= question.selected_answer < 4:
            self._option_buttons[question.selected_answer].setChecked(True)
        
        # 恢复信号
        for btn in self._option_buttons:
            btn.blockSignals(False)
        
        # 更新按钮状态
        self._update_nav_buttons()
    
    def _update_nav_buttons(self):
        """更新导航按钮状态"""
        self._prev_btn.setEnabled(self._current_index > 0)
        
        if self._current_index < len(self._questions) - 1:
            self._next_btn.show()
            self._next_btn.setEnabled(True)
            self._submit_btn.hide()
        else:
            self._next_btn.hide()
            self._submit_btn.show()
    
    def _update_progress(self):
        """更新进度显示"""
        total = len(self._questions)
        current = self._current_index + 1
        
        self._progress_label.setText(f"{current} / {total}")
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)
    
    def _on_option_selected(self, index: int):
        """选项被选中"""
        if self._current_index < len(self._questions):
            self._questions[self._current_index].selected_answer = index
    
    def _on_prev_question(self):
        """上一题"""
        if self._current_index > 0:
            self._current_index -= 1
            self._show_current_question()
            self._update_progress()
    
    def _on_next_question(self):
        """下一题"""
        if self._current_index < len(self._questions) - 1:
            self._current_index += 1
            self._show_current_question()
            self._update_progress()
    
    def _on_submit(self):
        """检查"""
        # 检查是否所有题目都已作答
        unanswered = [q for q in self._questions if q.selected_answer is None]
        if unanswered:
            reply = QMessageBox.question(
                self,
                "确认检查",
                f"还有 {len(unanswered)} 道题目未作答，确定要检查答案吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # 计算成绩
        self._calculate_result()
    
    def _calculate_result(self):
        """计算结果"""
        # 首先计算每道题的对错
        for question in self._questions:
            is_correct = (question.selected_answer == question.correct_answer)
            word_result = self._word_results[question.word.id]
            
            if question.question_type == QuizQuestion.TYPE_WORD_TO_DEFINITION:
                word_result.word_to_def_correct = is_correct
            else:
                word_result.definition_to_word_correct = is_correct
        
        # 然后计算每个单词的整体记忆情况（两道题都对才算成功）
        for word_result in self._word_results.values():
            if word_result.word_to_def_correct and word_result.definition_to_word_correct:
                word_result.overall_success = True
            else:
                word_result.overall_success = False
        
        # 计算总体分数
        total_correct = sum(1 for q in self._questions if q.selected_answer == q.correct_answer)
        total_questions = len(self._questions)
        score = int((total_correct / total_questions) * 100) if total_questions > 0 else 0
        
        # 统计单词记忆情况
        total_words = len(self._word_results)
        success_words = sum(1 for w in self._word_results.values() if w.overall_success)
        success_new_words = sum(1 for w in self._word_results.values() if w.overall_success and w.is_new)
        success_review_words = sum(1 for w in self._word_results.values() if w.overall_success and not w.is_new)
        
        # 更新学习记录 - 只有单词整体记忆成功才算作对
        results = []
        for word_result in self._word_results.values():
            results.append((word_result.word.id, word_result.overall_success))
        
        if self._book_id and self._dal and self._path_manager:
            worker = ReviewBatchWordsWorker(self._dal, self._path_manager, self._book_id, results)
            self._start_worker(worker, 'review_batch')
        
        # 显示结果
        self._show_result(score, total_correct, total_questions, total_words, success_words, success_new_words, success_review_words)
    
    def _show_result(self, score: int, correct_count: int, total: int, 
                     total_words: int, success_words: int, 
                     success_new_words: int, success_review_words: int):
        """显示结果"""
        # 设置标题和分数
        if score >= 90:
            self._result_title.setText("🎉 太棒了！")
            self._result_title.setStyleSheet("color: green;")
        elif score >= 70:
            self._result_title.setText("👍 不错！")
            self._result_title.setStyleSheet("color: blue;")
        elif score >= 60:
            self._result_title.setText("💪 继续加油！")
            self._result_title.setStyleSheet("color: orange;")
        else:
            self._result_title.setText("📚 需要更多练习")
            self._result_title.setStyleSheet("color: red;")
        
        self._score_label.setText(f"{score} 分")
        
        # 设置摘要
        summary_text = f"""
        题目：{correct_count} / {total} 正确<br><br>
        <b>单词记忆情况：</b><br>
        • 总单词数：{total_words}<br>
        • 记忆成功：{success_words} 个<br>
        • 新学单词成功：{success_new_words} / {len(self._new_words)}<br>
        • 复习单词成功：{success_review_words} / {len(self._review_words)}
        """
        self._result_summary.setText(summary_text)
        
        # 清空并重新填充详细结果
        for i in reversed(range(self._details_layout.count())):
            item = self._details_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        # 1. 显示记忆成功的单词
        if success_words > 0:
            success_group = QGroupBox("✅ 记忆成功的单词（两道题都对）")
            success_layout = QVBoxLayout(success_group)
            
            for word_result in self._word_results.values():
                if word_result.overall_success:
                    info_text = f"🔤 {word_result.word.word}"
                    formatted_phonetic = format_phonetic(word_result.word.phonetic)
                    if formatted_phonetic:
                        info_text += f" {formatted_phonetic}"
                    info_text += f" - {word_result.word.definition}"
                    word_label = QLabel(info_text)
                    success_layout.addWidget(word_label)
            
            self._details_layout.insertWidget(self._details_layout.count() - 1, success_group)
        
        # 2. 显示记忆失败的单词
        failed_words = [w for w in self._word_results.values() if not w.overall_success]
        if failed_words:
            failed_group = QGroupBox("❌ 记忆失败的单词")
            failed_layout = QVBoxLayout(failed_group)
            
            for word_result in failed_words:
                # 显示单词信息
                info_text = f"🔤 {word_result.word.word}"
                formatted_phonetic = format_phonetic(word_result.word.phonetic)
                if formatted_phonetic:
                    info_text += f" {formatted_phonetic}"
                info_text += f" - {word_result.word.definition}"
                
                info_label = QLabel(info_text)
                info_label.setStyleSheet("font-weight: bold;")
                failed_layout.addWidget(info_label)
                
                # 显示错误详情
                error_details = []
                if word_result.word_to_def_correct is False:
                    error_details.append("• 「单词选释义」答错")
                if word_result.definition_to_word_correct is False:
                    error_details.append("• 「释义选单词」答错")
                
                if error_details:
                    error_label = QLabel("<br>".join(error_details))
                    error_label.setStyleSheet("color: #d32f2f; margin-left: 20px;")
                    failed_layout.addWidget(error_label)
                
                # 分隔线
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                failed_layout.addWidget(line)
            
            self._details_layout.insertWidget(self._details_layout.count() - 1, failed_group)
        
        # 3. 显示所有错题详情
        wrong_questions = [q for q in self._questions if q.selected_answer != q.correct_answer]
        if wrong_questions:
            wrong_group = QGroupBox("📝 错题回顾")
            wrong_layout = QVBoxLayout(wrong_group)
            
            for i, question in enumerate(wrong_questions, 1):
                # 显示题目
                if question.question_type == QuizQuestion.TYPE_WORD_TO_DEFINITION:
                    q_type = "单词选释义"
                    q_content = f"{question.word.word}"
                    formatted_phonetic = format_phonetic(question.word.phonetic)
                    if formatted_phonetic:
                        q_content += f" {formatted_phonetic}"
                else:
                    q_type = "释义选单词"
                    q_content = question.word.definition
                
                q_label = QLabel(f"<b>{i}. {q_type}</b><br>{q_content}")
                wrong_layout.addWidget(q_label)
                
                # 显示用户选择和正确答案
                user_answer = question.options[question.selected_answer] if question.selected_answer is not None else "（未作答）"
                correct_answer = question.options[question.correct_answer]
                
                answer_text = f"""
                你的答案：<span style="color: red;">{user_answer}</span><br>
                正确答案：<span style="color: green;">{correct_answer}</span>
                """
                answer_label = QLabel(answer_text)
                wrong_layout.addWidget(answer_label)
                
                # 分隔线
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                wrong_layout.addWidget(line)
            
            self._details_layout.insertWidget(self._details_layout.count() - 1, wrong_group)
        
        # 切换到结果页面
        self._question_stack.setCurrentIndex(1)
        
        # 启用添加错题按钮
        failed_words = [w for w in self._word_results.values() if not w.overall_success]
        self._add_failed_btn.setEnabled(len(failed_words) > 0)
    
    def _on_add_failed_to_book(self):
        """添加错题到词书"""
        # 获取失败的单词（去重）
        failed_words_dict = {}
        for question in self._questions:
            if question.selected_answer != question.correct_answer:
                word_id = question.word.id
                if word_id not in failed_words_dict:
                    failed_words_dict[word_id] = question.word
        
        failed_words = list(failed_words_dict.values())
        if not failed_words:
            QMessageBox.information(self, "提示", "没有错题需要添加！")
            return
        
        # 打开批量添加对话框
        dialog = AddToBookBatchDialog(failed_words, self._dal, self)
        if dialog.exec_() == QDialog.Accepted:
            book_id = dialog.get_selected_book_id()
            if not book_id:
                return
            
            # 获取用户选中的单词
            selected_words = dialog.get_selected_words()
            if not selected_words:
                return
            
            added_count = 0
            already_exists_count = 0
            
            for word in selected_words:
                # 检查是否已存在
                exists = self._dal.check_word_exists_in_book(book_id, word.word)
                if exists:
                    already_exists_count += 1
                    continue
                
                # 添加单词
                new_word = Word(
                    book_id=book_id,
                    word=word.word,
                    phonetic=word.phonetic,
                    definition=word.definition,
                    example=word.example,
                    raw_data=word.raw_data
                )
                
                result = self._dal.add_word(new_word)
                if result:
                    added_count += 1
            
            # 更新词书单词数量
            if added_count > 0:
                book = self._dal.get_book_by_id(book_id)
                if book:
                    book.count += added_count
                    self._dal.update_book(book)
            
            # 显示结果
            msg = f"成功添加 {added_count} 个单词"
            if already_exists_count > 0:
                msg += f"，{already_exists_count} 个单词已存在"
            QMessageBox.information(self, "完成", msg)
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        key = event.key()
        
        # 首先检查当前是否在答题页面
        if self._question_stack.currentIndex() == 0:
            
            # 数字键 1-4 选择选项
            if key == Qt.Key_1:
                self._select_option(0)
            elif key == Qt.Key_2:
                self._select_option(1)
            elif key == Qt.Key_3:
                self._select_option(2)
            elif key == Qt.Key_4:
                self._select_option(3)
            # 左右键导航
            elif key == Qt.Key_Left:
                self._on_prev_question()
            elif key == Qt.Key_Right:
                self._on_next_question()
            # 回车键提交（当是最后一题时）
            elif key == Qt.Key_Return or key == Qt.Key_Enter:
                if self._current_index == len(self._questions) - 1:
                    self._on_submit()
                else:
                    self._on_next_question()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    
    def _select_option(self, index: int):
        """选择选项"""
        if self._current_index < len(self._questions):
            # 设置选项
            if 0 <= index < len(self._option_buttons):
                self._option_buttons[index].click()
    
    def _on_back_to_main(self):
        """返回主页面"""
        self._question_stack.setCurrentIndex(0)
        self.back_requested.emit()
