from typing import Literal

from pydantic import BaseModel


DocFileType = Literal["doc", "docx", "odt", "txt"]


class DocItem(BaseModel):
    id: str
    filename: str
    display_name: str
    note: str
    source_path: str
    text_path: str
    char_count: int
    file_type: DocFileType
    file_size: int
    created_at: str
    updated_at: str
