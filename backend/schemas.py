from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    id: int
    username: str
    email: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SnippetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1)
    language: str = Field(min_length=1, max_length=50)
    description: Optional[str] = None
    is_public: bool = False


class SnippetUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    code: Optional[str] = Field(default=None, min_length=1)
    language: Optional[str] = Field(default=None, min_length=1, max_length=50)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class SnippetOut(BaseModel):
    id: int
    title: str
    code: str
    language: str
    description: Optional[str]
    is_public: bool
    share_token: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}