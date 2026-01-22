from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.models import KeywordGroup, Keyword, User
from app.schemas import KeywordGroupCreate, KeywordGroupResponse, KeywordCreate, KeywordResponse

router = APIRouter(
    prefix="/keyword-groups",
    tags=["keyword-groups"],
    responses={404: {"description": "Not found"}},
)

# 그룹 생성
@router.post("/", response_model=KeywordGroupResponse)
def create_keyword_group(group: KeywordGroupCreate, db: Session = Depends(get_db)):
    # 사용자 존재 확인
    user = db.query(User).filter(User.id == group.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_group = KeywordGroup(
        user_id=group.user_id,
        group_name=group.group_name
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

# 그룹 목록 조회 (특정 사용자 필터링 옵션 추가)
@router.get("/", response_model=List[KeywordGroupResponse])
def read_keyword_groups(user_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(KeywordGroup)
    if user_id:
        query = query.filter(KeywordGroup.user_id == user_id)
    return query.offset(skip).limit(limit).all()

# 그룹 상세 조회
@router.get("/{group_id}", response_model=KeywordGroupResponse)
def read_keyword_group(group_id: int, db: Session = Depends(get_db)):
    db_group = db.query(KeywordGroup).filter(KeywordGroup.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Keyword Group not found")
    return db_group

# 키워드 추가
@router.post("/{group_id}/keywords/", response_model=KeywordResponse)
def create_keyword(group_id: int, keyword: KeywordCreate, db: Session = Depends(get_db)):
    db_group = db.query(KeywordGroup).filter(KeywordGroup.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Keyword Group not found")
    
    # 중복 키워드 체크
    existing_keyword = db.query(Keyword).filter(
        Keyword.group_id == group_id,
        Keyword.keyword == keyword.keyword
    ).first()
    if existing_keyword:
        raise HTTPException(status_code=400, detail="Keyword already exists in this group")

    db_keyword = Keyword(
        group_id=group_id,
        keyword=keyword.keyword,
        is_active=keyword.is_active
    )
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword

# 그룹 내 키워드 조회
@router.get("/{group_id}/keywords/", response_model=List[KeywordResponse])
def read_keywords(group_id: int, db: Session = Depends(get_db)):
    db_group = db.query(KeywordGroup).filter(KeywordGroup.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Keyword Group not found")
    return db_group.keywords
