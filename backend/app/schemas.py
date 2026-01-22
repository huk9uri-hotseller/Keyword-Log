from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr
from datetime import datetime

# =====================================================================
# 사용자 (User)
# =====================================================================

# 공통 속성
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    picture_url: Optional[str] = None
    google_sub: str

# 생성 시 필요한 속성
class UserCreate(UserBase):
    pass

# 응답 시 반환할 속성 (DB ID, 생성 시간 등 포함)
class UserResponse(UserBase):
    id: int
    last_login_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        orm_mode = True

# =====================================================================
# 키워드 (Keyword)
# =====================================================================

class KeywordBase(BaseModel):
    keyword: str
    is_active: bool = True

class KeywordCreate(KeywordBase):
    pass

class KeywordUpdate(BaseModel):
    keyword: Optional[str] = None
    is_active: Optional[bool] = None

class KeywordResponse(KeywordBase):
    id: int
    group_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# =====================================================================
# 키워드 그룹 (Keyword Group)
# =====================================================================

class KeywordGroupBase(BaseModel):
    group_name: str
    keyword_type: Literal["GENERAL", "OWN", "COMPETITOR"] = "GENERAL"

class KeywordGroupCreate(KeywordGroupBase):
    user_id: int  # 현재 인증 미구현으로 user_id를 직접 받음

class KeywordGroupUpdate(BaseModel):
    group_name: Optional[str] = None

class KeywordGroupResponse(KeywordGroupBase):
    id: int
    user_id: int
    created_at: datetime
    keywords: List[KeywordResponse] = []

    class Config:
        orm_mode = True
