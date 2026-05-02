
"""背诵模式工具函数"""


def format_phonetic(phonetic: str) -> str:
    """
    格式化音标，统一用 // 包裹
    
    Args:
        phonetic: 原始音标字符串
        
    Returns:
        格式化后的音标字符串，如果输入为空则返回空字符串
    """
    if not phonetic or not phonetic.strip():
        return ""
    
    # 去除首尾空白
    phonetic = phonetic.strip()
    
    # 去除可能已经存在的 / 或 []
    while phonetic.startswith(('/')):
        phonetic = phonetic[1:]
    while phonetic.endswith(('/')):
        phonetic = phonetic[:-1]
    
    # 去除空格
    phonetic = phonetic.strip()
    
    if not phonetic:
        return ""
    
    return f"/{phonetic}/"
