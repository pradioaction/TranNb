
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试新增的全小写精确搜索接口
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from recitation import RecitationDAL, PathManager, DatabaseManager
from recitation.models import Book, Word
from datetime import datetime


def test_search_interface():
    print("=" * 60)
    print("测试全小写精确搜索接口 - 测试报告")
    print("=" * 60)
    
    # 1. 初始化环境
    print("\n[步骤 1] 初始化测试环境")
    print("-" * 40)
    try:
        path_manager = PathManager()
        # 设置工作区为当前目录
        path_manager.set_workspace(os.path.dirname(__file__))
        
        db_manager = DatabaseManager(path_manager)
        # 确保数据库初始化
        success = db_manager.initialize()
        print(f"  ✓ 数据库初始化: {'成功' if success else '失败'}")
        
        recitation_dal = RecitationDAL(db_manager)
        print("  ✓ RecitationDAL 初始化成功")
        
    except Exception as e:
        print(f"  ✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 2. 获取现有数据
    print("\n[步骤 2] 查看现有数据")
    print("-" * 40)
    try:
        books = recitation_dal.get_all_books()
        print(f"  词书数量: {len(books)}")
        
        all_words = []
        for book in books:
            words = recitation_dal.get_words_by_book_id(book.id)
            print(f"  词书 '{book.name}' (ID: {book.id}): {len(words)} 个单词")
            all_words.extend(words)
        
        if not all_words:
            print("\n  警告: 数据库中没有单词，将先创建测试数据...")
            
            # 创建测试词书
            test_book = Book(
                name="测试词书",
                path="",
                count=0,
                create_time=datetime.now()
            )
            saved_book = recitation_dal.add_book(test_book)
            
            if saved_book:
                # 创建测试单词
                test_words = [
                    Word(
                        book_id=saved_book.id,
                        word="hello",
                        phonetic="/həˈloʊ/",
                        definition="你好；喂",
                        example="Hello, how are you?"
                    ),
                    Word(
                        book_id=saved_book.id,
                        word="world",
                        phonetic="/wɜːrld/",
                        definition="世界",
                        example="The world is beautiful."
                    ),
                    Word(
                        book_id=saved_book.id,
                        word="python",
                        phonetic="/ˈpaɪθɑːn/",
                        definition="蟒蛇；一种编程语言",
                        example="Python is a great language."
                    )
                ]
                
                count = recitation_dal.add_words_batch(test_words)
                print(f"  ✓ 创建了 {count} 个测试单词")
                
                # 重新获取单词列表
                all_words = recitation_dal.get_words_by_book_id(saved_book.id)
                books = recitation_dal.get_all_books()
        
        # 列出所有单词
        print(f"\n  找到的所有单词:")
        for word in all_words:
            print(f"    - '{word.word}' (词书ID: {word.book_id})")
            
    except Exception as e:
        print(f"  ✗ 获取数据失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 开始测试搜索接口
    print("\n[步骤 3] 测试全小写精确搜索接口")
    print("-" * 40)
    
    test_cases = [
        # (测试名称, 搜索词, 期望找到, 指定词书ID)
        ("全小写匹配", "hello", True, None),
        ("全大写匹配", "HELLO", True, None),
        ("混合大小写匹配", "HeLlO", True, None),
        ("精确匹配其他单词", "world", True, None),
        ("不存在的单词", "nonexistentword", False, None),
    ]
    
    # 如果有多个词书，也可以测试指定词书的搜索
    if len(books) &gt; 0:
        first_book_id = books[0].id
        test_cases.extend([
            ("在指定词书中搜索", "python", True, first_book_id),
            ("在指定词书中搜索不存在", "notthere", False, first_book_id),
        ])
    
    all_passed = True
    for i, (test_name, search_term, expect_found, book_id) in enumerate(test_cases, 1):
        print(f"\n  测试 {i}: {test_name}")
        print(f"    搜索词: '{search_term}'")
        
        try:
            result = recitation_dal.search_word_exact_lower(search_term, book_id)
            
            if expect_found:
                if result:
                    print(f"    ✓ 成功找到单词: '{result.word}'")
                    print(f"      音标: {result.phonetic}")
                    print(f"      释义: {result.definition}")
                    print(f"      词书ID: {result.book_id}")
                else:
                    print(f"    ✗ 未找到单词，但期望找到")
                    all_passed = False
            else:
                if not result:
                    print(f"    ✓ 正确：未找到该单词")
                else:
                    print(f"    ✗ 找到了不应该存在的单词: '{result.word}'")
                    all_passed = False
                    
        except Exception as e:
            print(f"    ✗ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    # 4. 接口信息展示
    print("\n" + "=" * 60)
    print("接口说明")
    print("=" * 60)
    print("\n接口名称: search_word_exact_lower(word_text: str, book_id: Optional[int] = None)")
    print("所在类: RecitationDAL")
    print("\n入参说明:")
    print("  - word_text (str): 要搜索的单词文本（支持任意大小写）")
    print("  - book_id (Optional[int], 可选): 指定词书ID，默认为 None（搜索所有词书）")
    print("\n返回值:")
    print("  - Optional[Word]: 返回找到的 Word 对象，未找到返回 None")
    print("\n功能特点:")
    print("  - 全小写不区分大小写比较")
    print("  - 精确匹配，不模糊搜索")
    print("  - 支持全局搜索或限定词书搜索")
    print("  - 只返回第一个匹配结果")
    
    # 5. 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    if all_passed:
        print("\n  ✓ 所有测试通过！")
        return True
    else:
        print("\n  ✗ 部分测试失败！")
        return False


if __name__ == "__main__":
    success = test_search_interface()
    sys.exit(0 if success else 1)

