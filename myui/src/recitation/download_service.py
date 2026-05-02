import logging
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

logger = logging.getLogger(__name__)


class DownloadService:
    """词书下载服务 - 从GitHub获取默认词书"""
    
    DEFAULT_BOOK_URL = "https://raw.githubusercontent.com/KyleBing/english-vocabulary/master/json_original/json-full/KaoYan_1.json"
    DEFAULT_BOOK_NAME = "考研词汇"
    
    def __init__(self):
        pass
    
    def download_default_book(self, save_dir: str, progress_callback=None) -> Optional[str]:
        """
        下载默认词书（考研词汇）
        
        Args:
            save_dir: 保存目录
            progress_callback: 进度回调函数 (received_bytes, total_bytes)
        
        Returns:
            保存的文件路径，失败返回None
        """
        return self.download_book(
            self.DEFAULT_BOOK_URL,
            save_dir,
            f"{self.DEFAULT_BOOK_NAME}.json",
            progress_callback
        )
    
    def download_book(self, url: str, save_dir: str, filename: str, progress_callback=None) -> Optional[str]:
        """
        下载词书
        
        Args:
            url: 下载URL
            save_dir: 保存目录
            filename: 保存的文件名
            progress_callback: 进度回调函数 (received_bytes, total_bytes)
        
        Returns:
            保存的文件路径，失败返回None
        """
        try:
            save_path = Path(save_dir) / filename
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"开始下载: {url}")
            
            request = Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            with urlopen(request, timeout=30) as response:
                total_size = int(response.headers.get('Content-Length', -1))
                received = 0
                chunk_size = 8192
                
                with open(save_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        received += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress_callback(received, total_size)
            
            logger.info(f"下载完成: {save_path}")
            return str(save_path)
            
        except HTTPError as e:
            logger.error(f"HTTP错误: {e.code} - {e.reason}", exc_info=True)
            return None
        except URLError as e:
            logger.error(f"URL错误: {e.reason}", exc_info=True)
            return None
        except TimeoutError:
            logger.error("下载超时", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"下载失败: {e}", exc_info=True)
            return None
