import re
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from .models import Word


class ArticleGenerator:
    """文章生成器 - 负责格式化和保存文章"""
    
    @staticmethod
    def format_article(
        article_text: str,
        new_words: List[Word],
        review_words: List[Word]
    ) -> str:
        """
        格式化文章 - 给新学单词加下划线，给复习单词加粗
        
        Args:
            article_text: 原始文章文本
            new_words: 新学单词列表
            review_words: 复习单词列表
        
        Returns:
            格式化后的文章（Markdown格式）
        """
        if not article_text:
            return ""
        
        # 创建单词映射
        word_mapping = {}
        for word in new_words:
            word_mapping[word.word.lower()] = ('underline', word.word)
        for word in review_words:
            word_mapping[word.word.lower()] = ('bold', word.word)
        
        # 格式化文章
        formatted_text = article_text
        
        # 按单词长度降序排序，避免短单词先匹配
        sorted_words = sorted(
            word_mapping.keys(),
            key=lambda x: len(x),
            reverse=True
        )
        
        for word_lower in sorted_words:
            style, original_word = word_mapping[word_lower]
            
            # 使用正则表达式进行全词匹配
            pattern = re.compile(r'\b' + re.escape(word_lower) + r'\b', re.IGNORECASE)
            
            def replace_func(match):
                matched_word = match.group(0)
                if style == 'underline':
                    return f"<u>{matched_word}</u>"
                else:
                    return f"**{matched_word}**"
            
            formatted_text = pattern.sub(replace_func, formatted_text)
        
        return formatted_text
    
    @staticmethod
    def extract_title(article_text: str, max_length: int = 20) -> str:
        """
        从文章中提取标题（使用第一句话的前N个字符）
        
        Args:
            article_text: 文章文本
            max_length: 标题最大长度
        
        Returns:
            标题
        """
        if not article_text:
            return "未命名文章"
        
        # 先去除换行符和空白字符
        cleaned_text = article_text.replace('\n', ' ').replace('\r', ' ').strip()
        
        # 查找第一个句子结束符
        sentence_end = cleaned_text.find('.')
        if sentence_end == -1:
            sentence_end = cleaned_text.find('!')
        if sentence_end == -1:
            sentence_end = cleaned_text.find('?')
        if sentence_end == -1:
            sentence_end = min(len(cleaned_text), max_length)
        
        first_sentence = cleaned_text[:sentence_end].strip()
        
        # 如果句子以"标题："或类似前缀开头，去掉前缀
        prefixes = ['标题：', '标题:', '标题', 'Title:', 'Title：']
        for prefix in prefixes:
            if first_sentence.startswith(prefix):
                first_sentence = first_sentence[len(prefix):].strip()
                break
        
        # 取前N个字符
        if len(first_sentence) > max_length:
            title = first_sentence[:max_length].strip()
            if title:
                title += "..."
        else:
            title = first_sentence
        
        if not title:
            title = "未命名文章"
        
        return title
    
    @staticmethod
    def save_article(
        workspace_path: str,
        article_text: str,
        title: str
    ) -> Tuple[bool, str]:
        """
        保存文章到工作区，按照标准 .transnb 格式保存
        
        Args:
            workspace_path: 工作区路径
            article_text: 文章文本
            title: 标题
        
        Returns:
            (成功, 文件路径或错误信息)
        """
        try:
            # 创建 YYMMDD 格式的目录
            today = datetime.now()
            date_dir = today.strftime("%y%m%d")
            
            # 完整的目录路径
            article_dir = Path(workspace_path) / date_dir
            article_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            # 先清理标题中的所有非法字符
            safe_title = title.replace('\n', ' ').replace('\r', ' ').strip()
            # 替换所有文件名字符
            safe_title = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', safe_title)
            # 限制长度
            safe_title = safe_title[:50].strip()
            if not safe_title:
                safe_title = "article"
            
            # 查找可用的文件名
            base_name = safe_title
            counter = 1
            while True:
                if counter == 1:
                    file_name = f"{base_name}.transnb"
                else:
                    file_name = f"{base_name}_{counter}.transnb"
                
                file_path = article_dir / file_name
                if not file_path.exists():
                    break
                counter += 1
            
            # 准备要保存的单元格数据
            # 先添加标题作为第一段
            full_content = f"# {title}\n\n{article_text}"
            
            # 按段落分割
            lines = full_content.replace('\r\n', '\n').split('\n')
            paragraphs = [line.strip() for line in lines if line.strip()]
            
            # 构建单元格数据
            cells_data = [{
                'type': 'markdown',
                'content': paragraph,
                'output': ''
            } for paragraph in paragraphs]
            
            # 保存文件（标准 JSON 格式）
            data = {
                'version': '1.0',
                'cells': cells_data
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True, str(file_path)
        
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def create_words_summary(
        new_words: List[Word],
        review_words: List[Word]
    ) -> str:
        """
        创建单词汇总（用于添加到文章末尾）
        
        Args:
            new_words: 新学单词列表
            review_words: 复习单词列表
        
        Returns:
            Markdown格式的单词汇总
        """
        summary = "\n\n---\n\n## 单词汇总\n\n"
        
        if new_words:
            summary += "### 新学单词\n\n"
            for word in new_words:
                summary += f"- **{word.word}** {word.phonetic}\n  {word.definition}\n"
            summary += "\n"
        
        if review_words:
            summary += "### 复习单词\n\n"
            for word in review_words:
                summary += f"- **{word.word}** {word.phonetic}\n  {word.definition}\n"
        
        return summary
