
import sqlite3
from pathlib import Path
import sys

# 检查当前工作区
print("=== 检查背诵模式数据库 ===")

# 尝试从常见位置查找数据库
possible_paths = [
    Path.home() / ".TransRead" / "words.db",
    Path.cwd() / ".TransRead" / "words.db",
]

# 检查是否有其他工作区的数据库
for parent in Path.cwd().parents:
    candidate = parent / ".TransRead" / "words.db"
    if candidate.exists() and candidate not in possible_paths:
        possible_paths.append(candidate)

found = False
for db_path in possible_paths:
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
            found = True
            
        except Exception as e:
            print(f"读取数据库时出错: {e}")
            import traceback
            traceback.print_exc()

if not found:
    print("\n没有找到任何数据库文件！")
    print(f"当前工作目录: {Path.cwd()}")
    print(f"用户主目录: {Path.home()}")

# 检查当前目录下是否有.TransRead目录
transread_dir = Path.cwd() / ".TransRead"
if transread_dir.exists():
    print(f"\n当前目录下的.TransRead内容:")
    for item in transread_dir.iterdir():
        print(f"  - {item.name}")
