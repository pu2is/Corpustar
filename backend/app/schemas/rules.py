from typing import Literal

from pydantic import BaseModel


RuleType = Literal["fvg"]
StructureType = Literal["prep", "akku"]


class RuleItem(BaseModel):
    id: str
    version_id: str
    type: RuleType
    path: str


class FvgEntryItem(BaseModel):
    id: str
    rule_id: str
    verb: str
    phrase: str
    noun: str
    prep: str
    structure_type: StructureType
    semantic_type: str


class AppendFvgEntryRequest(BaseModel):
    rule_id: str
    verb: str
    phrase: str
    noun: str | None = None
    prep: str | None = None
    structure_type: StructureType | None = None
    semantic_type: str | None = None


class CorrectFvgEntryRequest(BaseModel):
    id: str
    verb: str | None = None
    phrase: str | None = None
    noun: str | None = None
    prep: str | None = None
    structure_type: StructureType | None = None
    semantic_type: str | None = None


class RemoveRuleResponse(BaseModel):
    id: str


class RemoveFvgEntryResponse(BaseModel):
    id: str
    rule_id: str
