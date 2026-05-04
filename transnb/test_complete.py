
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整测试所有修复和功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from recitation import RecitationDAL, PathManager, DatabaseManager
from recitation.models import Book, Word
from recitation.ui.dialogs import AddWordToBookDialog
from datetime import datetime


def test_complete():
    app = QApplication(sys.argv)
    
    print("=" * 60)
    print("完整功能测试")
    print("=" * 60)
    
    # 1. 初始化
    print("\n[1] 初始化测试环境")
    print("-" * 40)
    
    path_manager = PathManager()
    path_manager.set_workspace(os.path.dirname(__file__))
    print(f"  工作区: {path_manager.get_workspace()}")
    
    db_manager = DatabaseManager(path_manager)
    db_manager.initialize()
    dal = RecitationDAL(db_manager)
    
    # 2. 准备测试数据
    print("\n[2] 准备测试数据")
    print("-" * 40)
    
    # 创建测试词书
    books = dal.get_all_books()
    if not books:
        book1 = Book(name="我的生词本", path="", count=0, create_time=datetime.now())
        book1 = dal.add_book(book1)
        
        book2 = Book(name="英语核心词汇", path="", count=0, create_time=datetime.now())
        book2 = dal.add_book(book2)
        
        # 添加测试单词
        words = [
            Word(book_id=book1.id, word="hello", phonetic="/həˈloʊ/", 
                 definition="你好；喂；您好", example="Hello, nice to meet you!"),
            Word(book_id=book1.id, word="world", phonetic="/wɜːrld/", 
                 definition="世界；世间；天下", example="The world is beautiful."),
            Word(book_id=book2.id, word="python", phonetic="/ˈpaɪθɑːn/", 
                 definition="蟒蛇；一种编程语言", example="Python is easy to learn.")
        ]
        for word in words:
            dal.add_word(word)
            
        print("  ✓ 已创建测试词书和单词")
    else:
        print("  ✓ 使用现有词书")
    
    # 3. 测试搜索功能
    print("\n[3] 测试单词搜索")
    print("-" * 40)
    
    test_cases = [
        ("hello", "全小写"),
        ("HELLO", "全大写"),
        ("HeLlO", "混合大小写"),
        ("  hello world  ", "带空格"),
        ("python", "另一个词书的词"),
        ("notfound", "不存在的词")
    ]
    
    for word_text, desc in test_cases:
        result = dal.search_word_exact_lower(word_text)
        if result:
            print(f"  搜索 '{word_text}' ({desc})")
            print(f"    ✓ 找到: {result.word}")
            print(f"      音: {result.phonetic}")
            print(f"      义: {result.definition}")
            print(f"      书: ID={result.book_id}")
        else:
            print(f"  搜索 '{word_text}' ({desc})")
            print(f"    ✗ 未找到")
    
    # 4. 测试对话框功能
    print("\n[4] 测试收藏单词对话框")
    print("-" * 40)
    print("  对话框即将显示，请测试:")
    print("    1. 检查词书下拉框是否有词书")
    print("    2. 测试自动搜索和回填（输入 'hello' 看是否自动填充）")
    print("    3. 测试单词预处理（输入 '  heLLo  ' 看是否去空格）")
    print("\n  关闭对话框后测试完成")
    
    dialog = AddWordToBookDialog(dal)
    dialog.set_word("  HELLO  ")
    dialog.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    test_complete()

