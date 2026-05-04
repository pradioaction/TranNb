
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试新增的全小写精确搜索接口 - 简化版
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from recitation import RecitationDAL, PathManager, DatabaseManager
from recitation.models import Book, Word
from datetime import datetime


def main():
    print("=" * 60)
    print("全小写精确搜索接口 - 测试报告")
    print("=" * 60)
    
    # 1. 初始化
    print("\n[1] 初始化测试环境")
    print("-" * 40)
    try:
        path_manager = PathManager()
        path_manager.set_workspace(os.path.dirname(__file__))
        db_manager = DatabaseManager(path_manager)
        db_manager.initialize()
        dal = RecitationDAL(db_manager)
        print("  [OK] 环境初始化成功")
    except Exception as e:
        print(f"  [FAIL] 初始化失败: {e}")
        return
    
    # 2. 确保有测试数据
    print("\n[2] 准备测试数据")
    print("-" * 40)
    books = dal.get_all_books()
    if not books:
        # 创建测试词书
        book = Book(name="测试词书", path="", count=0, create_time=datetime.now())
        book = dal.add_book(book)
        print("  [OK] 创建测试词书")
        
        # 创建测试单词
        words = [
            Word(book_id=book.id, word="hello", phonetic="/həˈloʊ/", 
                 definition="你好", example="Hello!"),
            Word(book_id=book.id, word="world", phonetic="/wɜːrld/", 
                 definition="世界", example="World!"),
        ]
        dal.add_words_batch(words)
        print("  [OK] 创建测试单词")
        books = dal.get_all_books()
    
    # 显示当前数据
    print("\n[3] 当前数据")
    print("-" * 40)
    for book in books:
        words = dal.get_words_by_book_id(book.id)
        print(f"  词书: {book.name} (ID: {book.id})")
        for w in words:
            print(f"    - {w.word}")
    
    # 4. 测试搜索
    print("\n[4] 搜索测试")
    print("-" * 40)
    
    test_cases = [
        ("hello", "全小写"),
        ("HELLO", "全大写"),
        ("HeLlO", "混合大小写"),
        ("world", "其他单词"),
        ("xyz123", "不存在的单词"),
    ]
    
    all_passed = True
    for search_word, desc in test_cases:
        result = dal.search_word_exact_lower(search_word)
        if result:
            print(f"\n  搜索: '{search_word}' ({desc})")
            print(f"  [OK] 找到: {result.word}")
            print(f"       音标: {result.phonetic}")
            print(f"       释义: {result.definition}")
        else:
            print(f"\n  搜索: '{search_word}' ({desc})")
            print(f"  [INFO] 未找到")
    
    # 5. 接口文档
    print("\n" + "=" * 60)
    print("接口文档")
    print("=" * 60)
    print("\n函数签名:")
    print("  search_word_exact_lower(word_text: str, book_id: Optional[int] = None) -> Optional[Word]")
    print("\n入参:")
    print("  word_text: 搜索的单词（任意大小写）")
    print("  book_id: 可选，指定词书搜索")
    print("\n返回:")
    print("  Word 对象或 None")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()

