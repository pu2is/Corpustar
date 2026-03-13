from typing import Literal

from pydantic import BaseModel

DocFileType = Literal["doc", "docx", "odt", "txt"]


class DocItem(BaseModel):
    id: str
    filename: str
    displayName: str
    note: str
    sourcePath: str
    textPath: str
    textCharCount: int
    fileType: DocFileType
    fileSize: int
    createdAt: str
    updatedAt: str
