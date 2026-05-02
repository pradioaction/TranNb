import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple
from .models import Book, Word

logger = logging.getLogger(__name__)


class BookImporter:
    """词书导入服务 - 解析KyleBing格式的JSON词书"""
    
    def __init__(self):
        pass
    
    def import_from_file(self, file_path: str) -> Tuple[Optional[Book], List[Word]]:
        """
        从JSON文件导入词书
        
        Args:
            file_path: JSON文件路径
        
        Returns:
            (词书对象, 单词列表)，失败返回(None, [])
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"文件不存在: {file_path}")
                return None, []
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            book_name = path.stem
            words = self._parse_words(data)
            
            book = Book(
                name=book_name,
                path=str(path),
                count=len(words)
            )
            
            logger.info(f"解析词书成功: {book_name}, 单词数: {len(words)}")
            return book, words
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}", exc_info=True)
            return None, []
        except Exception as e:
            logger.error(f"导入词书失败: {e}", exc_info=True)
            return None, []
    
    def _parse_words(self, data) -> List[Word]:
        """
        解析JSON数据为单词列表
        
        Args:
            data: JSON数据
        
        Returns:
            单词列表
        """
        words: List[Word] = []
        
        if not data:
            return words
        
        # 处理可能的嵌套结构
        if isinstance(data, dict):
            # 检查是否有嵌套的单词数组
            possible_keys = ['words', 'data', 'list', 'items']
            for key in possible_keys:
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break
        
        if not isinstance(data, list):
            logger.error(f"数据不是列表格式: {type(data)}")
            return words
        
        for index, item in enumerate(data):
            try:
                word = self._parse_single_word(item)
                if word and word.word.strip():
                    words.append(word)
            except Exception as e:
                logger.warning(f"解析第 {index} 个单词项失败: {e}", exc_info=True)
                continue
        
        return words
    
    def _parse_single_word(self, item: dict) -> Optional[Word]:
        """
        解析单个单词项
        
        Args:
            item: 单个单词的字典数据
        
        Returns:
            Word对象，解析失败返回None
        """
        if not item or not isinstance(item, dict):
            return None
        
        # 1. 保存原始数据
        raw_data = json.dumps(item, ensure_ascii=False)
        
        # 2. 提取单词
        word_text = ''
        if 'headWord' in item and isinstance(item['headWord'], str):
            word_text = item['headWord'].strip()
        if not word_text and 'word' in item:
            if isinstance(item['word'], str):
                word_text = item['word'].strip()
            elif isinstance(item['word'], dict):
                word_node = item['word']
                if 'wordHead' in word_node and isinstance(word_node['wordHead'], str):
                    word_text = word_node['wordHead'].strip()
        
        if not word_text:
            return None
        
        # 3. 查找深层内容节点
        deep_content = None
        if 'content' in item and isinstance(item['content'], dict):
            level1 = item['content']
            if 'word' in level1 and isinstance(level1['word'], dict):
                level2 = level1['word']
                if 'content' in level2 and isinstance(level2['content'], dict):
                    deep_content = level2['content']
        
        # 4. 提取音标
        phonetic = ''
        if deep_content:
            for key in ['usphone', 'phone', 'ukphone', 'phonetic']:
                if key in deep_content and isinstance(deep_content[key], str):
                    val = deep_content[key].strip()
                    if val:
                        # 去除开头可能的逗号
                        if val.startswith(','):
                            val = val[1:].strip()
                        phonetic = val
                        break
        
        # 5. 提取释义
        definition = ''
        if deep_content:
            if 'trans' in deep_content and isinstance(deep_content['trans'], list):
                def_list = []
                for t in deep_content['trans']:
                    if isinstance(t, dict):
                        pos = t.get('pos', '')
                        tran_cn = t.get('tranCn', '')
                        if tran_cn:
                            if pos:
                                def_list.append(f"{pos} {tran_cn}")
                            else:
                                def_list.append(tran_cn)
                if def_list:
                    definition = '\n'.join(def_list)
        
        # 6. 提取例句
        example = ''
        if deep_content:
            if 'sentence' in deep_content and isinstance(deep_content['sentence'], dict):
                sentence_obj = deep_content['sentence']
                if 'sentences' in sentence_obj and isinstance(sentence_obj['sentences'], list):
                    ex_list = []
                    for s in sentence_obj['sentences']:
                        if isinstance(s, dict):
                            s_content = s.get('sContent', '')
                            s_cn = s.get('sCn', '')
                            if s_content:
                                ex_list.append(s_content)
                                if s_cn:
                                    ex_list.append(f"  {s_cn}")
                    if ex_list:
                        example = '\n'.join(ex_list)
        
        return Word(
            word=word_text,
            phonetic=phonetic,
            definition=definition,
            example=example,
            raw_data=raw_data
        )
