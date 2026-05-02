from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Book:
    id: Optional[int] = None
    name: str = ""
    path: str = ""
    count: int = 0
    create_time: Optional[datetime] = None


@dataclass
class Word:
    id: Optional[int] = None
    book_id: int = 0
    word: str = ""
    phonetic: str = ""
    definition: str = ""
    example: str = ""
    raw_data: str = ""


@dataclass
class UserStudy:
    id: Optional[int] = None
    book_id: int = 0
    word_id: int = 0
    stage: int = 0
    weight: float = 0.0
    last_review: Optional[datetime] = None
    next_review: Optional[datetime] = None
