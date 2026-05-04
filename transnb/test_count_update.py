
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试词书数量更新功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from recitation import RecitationDAL, PathManager, DatabaseManager
from recitation.models import Book, Word
from datetime import datetime


def main():
    print("=" * 60)
    print("测试词书数量自动更新功能")
    print("=" * 60)
    
    # 初始化
    print("\n[1] 初始化测试环境")
    path_manager = PathManager()
    path_manager.set_workspace(os.path.dirname(__file__))
    print(f"工作区: {path_manager.get_workspace()}")
    
    db_manager = DatabaseManager(path_manager)
    db_manager.initialize()
    dal = RecitationDAL(db_manager)
    
    # 先刷新一遍历史数据
    print("\n[2] 同步历史数据")
    dal.refresh_all_book_counts()
    
    # 显示现有词书
    print("\n[3] 现有词书")
    books = dal.get_all_books()
    for book in books:
        print(f"  - {book.name} (ID: {book.id}, count: {book.count})")
    
    # 创建测试词书（如果没有的话）
    test_book = None
    if not books:
        test_book = Book(name="测试词书", path="", create_time=datetime.now())
        test_book = dal.add_book(test_book)
        print(f"\n已创建测试词书: {test_book.name} (ID: {test_book.id})")
        test_book = dal.get_book_by_id(test_book.id)
        print(f"初始count: {test_book.count}")
    else:
        test_book = books[0]
    
    # 测试添加单词
    print(f"\n[4] 测试添加单词到: {test_book.name}")
    test_word = Word(
        book_id=test_book.id,
        word=f"test_word_{datetime.now().strftime('%H%M%S')}",
        phonetic="/test/",
        definition="测试单词",
        example="This is a test"
    )
    
    added_word = dal.add_word(test_word)
    if added_word:
        print(f"  成功添加单词: {added_word.word}")
        
        # 重新获取词书查看数量是否更新
        updated_book = dal.get_book_by_id(test_book.id)
        print(f"  词书count已更新为: {updated_book.count}")
        
        # 再添加一个
        print("\n[5] 再添加一个单词")
        test_word2 = Word(
            book_id=test_book.id,
            word=f"test_word2_{datetime.now().strftime('%H%M%S')}",
            phonetic="/test2/",
            definition="测试单词2",
            example="This is test 2"
        )
        added_word2 = dal.add_word(test_word2)
        
        updated_book2 = dal.get_book_by_id(test_book.id)
        print(f"  词书count现在是: {updated_book2.count}")
        
        # 测试删除
        print("\n[6] 测试删除单词")
        if dal.delete_word(added_word.id):
            print(f"  成功删除单词: {added_word.word}")
            updated_book3 = dal.get_book_by_id(test_book.id)
            print(f"  词书count现在是: {updated_book3.count}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()

