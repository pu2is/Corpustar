from typing import Any, Literal
from pydantic import BaseModel

RuleType = Literal["fvg"]

class RuleItem(BaseModel):
    id: str
    type: RuleType
    path: str

class FvgRuleItem(BaseModel):
    id: str
    ruleId: str
    verb: str
    phrase: str

class ImportRuleRequest(BaseModel):
    path: str
    type: RuleType = "fvg"

class AddFvgRuleRequest(BaseModel):
    ruleId: str
    verb: str
    phrase: str

class UpdateFvgRuleRequest(BaseModel):
    verb: str
    phrase: str

class RemoveRuleResponse(BaseModel):
    id: str
    removedFvgCount: int | None = None

class RemoveFvgRuleResponse(BaseModel):
    id: str
    ruleId: str | None = None
