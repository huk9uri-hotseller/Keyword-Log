from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

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
