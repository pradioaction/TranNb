
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试收藏单词对话框的问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from recitation import RecitationDAL, PathManager, DatabaseManager
from recitation.ui.dialogs import AddWordToBookDialog


def debug_dialog():
    app = QApplication(sys.argv)
    
    print("=" * 60)
    print("调试收藏单词对话框")
    print("=" * 60)
    
    # 初始化
    print("\n[1] 初始化路径和数据库")
    path_manager = PathManager()
    path_manager.set_workspace(os.path.dirname(__file__))
    print(f"  工作区: {path_manager.get_workspace_path()}")
    
    db_manager = DatabaseManager(path_manager)
    success = db_manager.initialize()
    print(f"  数据库初始化: {'成功' if success else '失败'}")
    
    dal = RecitationDAL(db_manager)
    
    # 测试获取词书
    print("\n[2] 测试 get_all_books()")
    books = dal.get_all_books()
    print(f"  找到 {len(books)} 本词书:")
    for book in books:
        print(f"    - {book.name} (ID: {book.id})")
    
    # 显示对话框
    print("\n[3] 显示对话框...")
    dialog = AddWordToBookDialog(dal)
    dialog.set_word("test")
    dialog.show()
    
    print("\n[4] 对话框已显示，请检查词书下拉框")
    print("    如果下拉框为空，说明 _load_books() 有问题")
    print("\n按 Ctrl+C 退出，或关闭对话框退出")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    debug_dialog()

