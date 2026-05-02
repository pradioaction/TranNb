
import sqlite3
from pathlib import Path
import sys

# 检查当前工作区
print("=== 检查背诵模式数据库 ===")

# 使用找到的工作区路径
workspace_path = Path(r"C:\Users\Pradio\Downloads\test")
db_path = workspace_path / ".TransRead" / "words.db"

if db_path.exists():
    print(f"\n找到数据库文件: {db_path}")
    print(f"文件大小: {db_path.stat().st_size} 字节")
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\n数据库中的表: {[t['name'] for t in tables]}")
        
        # 检查词书数据
        if 'book' in [t['name'] for t in tables]:
            cursor.execute("SELECT * FROM book")
            books = cursor.fetchall()
            print(f"\n词书数量: {len(books)}")
            for book in books:
                print(f"  - ID: {book['id']}, 名称: {book['name']}, 单词数: {book['count']}")
                
                # 检查该词书的单词
                cursor.execute("SELECT COUNT(*) FROM word WHERE book_id = ?", (book['id'],))
                word_count = cursor.fetchone()[0]
                print(f"    实际单词数: {word_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"读取数据库时出错: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"\n数据库文件不存在: {db_path}")
