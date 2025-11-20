from pydantic import BaseModel, field_validator
from typing import List, Optional


class _AttrMixin:
    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)


class TestCase(BaseModel, _AttrMixin):
    id: Optional[str] = None
    name: Optional[str] = None
    hidden: Optional[bool] = None
    secret: Optional[bool] = None
    score: Optional[float] = None
    min_score: float = 0
    max_score: float = 1
    passed: Optional[bool] = None
    feedback: Optional[str] = None
    expected: Optional[str] = None
    observed: Optional[str] = None
    timeout: Optional[float] = None
    # TODO: get student output

    @field_validator("feedback", "expected", "observed", mode="before")
    def fix_str_field(cls, v):
        if isinstance(v, bool):
            return ""
        return v

    @field_validator("feedback", "expected", "observed", mode="before")
    def unicode_escape(cls, v):
        if isinstance(v, str):
            return v.encode("utf-8").decode("unicode_escape")
        return v


class TestSuite(BaseModel, _AttrMixin):
    name: Optional[str] = None
    score: float = 0
    max_score: float = 0
    tests: List[TestCase] = []
