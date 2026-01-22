import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.models import KeywordGroup, Keyword, User
from app.schemas import (
    KeywordGroupCreate, KeywordGroupResponse, KeywordGroupUpdate,
    KeywordCreate, KeywordResponse, KeywordUpdate
)

router = APIRouter(
    prefix="/keyword-groups",
    tags=["keyword-groups"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

# =====================================================================
# 키워드 그룹 관리
# =====================================================================

# 그룹 생성
@router.post("/", response_model=KeywordGroupResponse)
def create_keyword_group(group: KeywordGroupCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == group.user_id).first()
    if not user:
        logger.warning("키워드 그룹 생성 실패: 사용자 없음 (user_id=%s)", group.user_id)
        raise HTTPException(status_code=404, detail="User not found")

    db_group = KeywordGroup(
        user_id=group.user_id,
        group_name=group.group_name
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

# 그룹 목록 조회
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
        logger.warning("키워드 그룹 조회 실패: 그룹 없음 (group_id=%s)", group_id)
        raise HTTPException(status_code=404, detail="Keyword Group not found")
    return db_group

# 그룹 수정 (이름 변경)
@router.put("/{group_id}", response_model=KeywordGroupResponse)
def update_keyword_group(group_id: int, group_update: KeywordGroupUpdate, db: Session = Depends(get_db)):
    db_group = db.query(KeywordGroup).filter(KeywordGroup.id == group_id).first()
    if db_group is None:
        logger.warning("키워드 그룹 수정 실패: 그룹 없음 (group_id=%s)", group_id)
        raise HTTPException(status_code=404, detail="Keyword Group not found")
    
    if group_update.group_name:
        db_group.group_name = group_update.group_name
    
    db.commit()
    db.refresh(db_group)
    return db_group

# 그룹 삭제
@router.delete("/{group_id}")
def delete_keyword_group(group_id: int, db: Session = Depends(get_db)):
    db_group = db.query(KeywordGroup).filter(KeywordGroup.id == group_id).first()
    if db_group is None:
        logger.warning("키워드 그룹 삭제 실패: 그룹 없음 (group_id=%s)", group_id)
        raise HTTPException(status_code=404, detail="Keyword Group not found")
    
    db.delete(db_group)
    db.commit()
    return {"message": "Keyword Group deleted successfully"}


# =====================================================================
# 키워드 관리
# =====================================================================

# 키워드 추가
@router.post("/{group_id}/keywords/", response_model=KeywordResponse)
def create_keyword(group_id: int, keyword: KeywordCreate, db: Session = Depends(get_db)):
    db_group = db.query(KeywordGroup).filter(KeywordGroup.id == group_id).first()
    if db_group is None:
        logger.warning("키워드 생성 실패: 그룹 없음 (group_id=%s)", group_id)
        raise HTTPException(status_code=404, detail="Keyword Group not found")
    
    existing_keyword = db.query(Keyword).filter(
        Keyword.group_id == group_id,
        Keyword.keyword == keyword.keyword
    ).first()
    if existing_keyword:
        logger.warning(
            "키워드 생성 실패: 중복 키워드 (group_id=%s, keyword=%s)",
            group_id,
            keyword.keyword
        )
        raise HTTPException(status_code=400, detail="Keyword already exists in this group")

    db_keyword = Keyword(
        group_id=group_id,
        keyword=keyword.keyword,
        keyword_type=keyword.keyword_type,
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
        logger.warning("키워드 목록 조회 실패: 그룹 없음 (group_id=%s)", group_id)
        raise HTTPException(status_code=404, detail="Keyword Group not found")
    return db_group.keywords

# 키워드 수정
@router.put("/{group_id}/keywords/{keyword_id}", response_model=KeywordResponse)
def update_keyword(group_id: int, keyword_id: int, keyword_update: KeywordUpdate, db: Session = Depends(get_db)):
    # 키워드가 해당 그룹에 속해있는지 확인
    db_keyword = db.query(Keyword).filter(
        Keyword.id == keyword_id,
        Keyword.group_id == group_id
    ).first()
    
    if db_keyword is None:
        logger.warning(
            "키워드 수정 실패: 그룹 내 키워드 없음 (group_id=%s, keyword_id=%s)",
            group_id,
            keyword_id
        )
        raise HTTPException(status_code=404, detail="Keyword not found in this group")
    
    # 키워드 내용 변경 시 중복 체크
    if keyword_update.keyword and keyword_update.keyword != db_keyword.keyword:
        existing_keyword = db.query(Keyword).filter(
            Keyword.group_id == group_id,
            Keyword.keyword == keyword_update.keyword
        ).first()
        if existing_keyword:
            logger.warning(
                "키워드 수정 실패: 중복 키워드 (group_id=%s, keyword=%s)",
                group_id,
                keyword_update.keyword
            )
            raise HTTPException(status_code=400, detail="Keyword already exists in this group")
        db_keyword.keyword = keyword_update.keyword

    if keyword_update.keyword_type:
        db_keyword.keyword_type = keyword_update.keyword_type

    # 활성 상태 변경
    if keyword_update.is_active is not None:
        db_keyword.is_active = keyword_update.is_active

    db.commit()
    db.refresh(db_keyword)
    return db_keyword

# 키워드 삭제
@router.delete("/{group_id}/keywords/{keyword_id}")
def delete_keyword(group_id: int, keyword_id: int, db: Session = Depends(get_db)):
    db_keyword = db.query(Keyword).filter(
        Keyword.id == keyword_id,
        Keyword.group_id == group_id
    ).first()
    
    if db_keyword is None:
        logger.warning(
            "키워드 삭제 실패: 그룹 내 키워드 없음 (group_id=%s, keyword_id=%s)",
            group_id,
            keyword_id
        )
        raise HTTPException(status_code=404, detail="Keyword not found in this group")
    
    db.delete(db_keyword)
    db.commit()
    return {"message": "Keyword deleted successfully"}
