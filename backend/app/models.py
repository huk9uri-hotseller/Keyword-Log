import enum
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime, 
    ForeignKey, Numeric, Float, JSON, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base

# =====================================================================
# 0) ENUM 타입 정의
# =====================================================================

class SerpResultType(str, enum.Enum):
    ORGANIC = "ORGANIC"
    ADS = "ADS"
    LOCAL = "LOCAL"

class SerpDeviceType(str, enum.Enum):
    DESKTOP = "DESKTOP"
    MOBILE = "MOBILE"

class SerpTargetType(str, enum.Enum):
    OWN = "OWN"
    COMPETITOR = "COMPETITOR"

class SerpEngine(str, enum.Enum):
    GOOGLE = "GOOGLE"
    NAVER = "NAVER"

class SerpProvider(str, enum.Enum):
    SERPAPI = "SERPAPI"
    DATAFORSEO = "DATAFORSEO"
    OTHER = "OTHER"

class MetricSource(str, enum.Enum):
    NAVER_DATALAB = "NAVER_DATALAB"
    NAVER_ADS = "NAVER_ADS"
    GOOGLE_TRENDS = "GOOGLE_TRENDS"
    GOOGLE_ADS = "GOOGLE_ADS"

# =====================================================================
# 1) 사용자 (users)
# =====================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_sub = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(100))
    picture_url = Column(Text)
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    keyword_groups = relationship("KeywordGroup", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")


# =====================================================================
# 2) 키워드 그룹 (keyword_groups)
# =====================================================================

class KeywordGroup(Base):
    __tablename__ = "keyword_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    group_name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="keyword_groups")
    keywords = relationship("Keyword", back_populates="group", cascade="all, delete-orphan")
    serp_targets = relationship("SerpTarget", back_populates="group", cascade="all, delete-orphan")
    serp_profiles = relationship("SerpProfile", back_populates="group", cascade="all, delete-orphan")


# =====================================================================
# 3) 키워드 (keywords)
# =====================================================================

class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("keyword_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    keyword = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('group_id', 'keyword', name='uq_keyword_group_keyword'),
    )

    # Relationships
    group = relationship("KeywordGroup", back_populates="keywords")
    search_trends = relationship("SearchTrend", back_populates="keyword", cascade="all, delete-orphan")
    search_volumes = relationship("SearchVolume", back_populates="keyword", cascade="all, delete-orphan")
    change_events = relationship("KeywordChangeEvent", back_populates="keyword", cascade="all, delete-orphan")
    news_articles = relationship("NewsArticle", back_populates="keyword", cascade="all, delete-orphan")
    serp_queries = relationship("SerpQuery", back_populates="keyword", cascade="all, delete-orphan")
    serp_rank_change_events = relationship("SerpRankChangeEvent", back_populates="keyword", cascade="all, delete-orphan")


# =====================================================================
# 4) 트렌드/검색량 데이터 (search_trends, search_volumes)
# =====================================================================

class SearchTrend(Base):
    __tablename__ = "search_trends"

    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False)
    source = Column(String, nullable=False) # Enum as String for simplicity or use SQLAlchemy Enum
    search_date = Column(Date, nullable=False, index=True)
    interest_score = Column(Numeric(5, 2))
    estimated_daily_volume = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('keyword_id', 'source', 'search_date', name='uq_search_trend'),
        CheckConstraint("source IN ('NAVER_DATALAB', 'GOOGLE_TRENDS')", name='ck_search_trends_source'),
    )

    # Relationships
    keyword = relationship("Keyword", back_populates="search_trends")


class SearchVolume(Base):
    __tablename__ = "search_volumes"

    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False)
    source = Column(String, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    volume = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("source IN ('NAVER_ADS', 'GOOGLE_ADS')", name='ck_search_volumes_source'),
    )

    # Relationships
    keyword = relationship("Keyword", back_populates="search_volumes")


# =====================================================================
# 5) 변동 이벤트 (keyword_change_events)
# =====================================================================

class KeywordChangeEvent(Base):
    __tablename__ = "keyword_change_events"

    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False)
    event_date = Column(Date, nullable=False, index=True)
    change_rate = Column(Float, nullable=False)
    event_type = Column(String(10), nullable=False)
    threshold_value = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("event_type IN ('SPIKE', 'DROP')", name='ck_keyword_change_event_type'),
    )

    # Relationships
    keyword = relationship("Keyword", back_populates="change_events")
    news_articles = relationship("NewsArticle", back_populates="event")


# =====================================================================
# 6) 뉴스 기사 + 요약 (news_articles, news_summaries)
# =====================================================================

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("keyword_change_events.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    media_source = Column(String(100))
    published_at = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    keyword = relationship("Keyword", back_populates="news_articles")
    event = relationship("KeywordChangeEvent", back_populates="news_articles")
    summary = relationship("NewsSummary", uselist=False, back_populates="article", cascade="all, delete-orphan")


class NewsSummary(Base):
    __tablename__ = "news_summaries"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, unique=True)
    summary_text = Column(Text, nullable=False)
    model_name = Column(String(50), default='gpt-5-mini')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    article = relationship("NewsArticle", back_populates="summary")


# =====================================================================
# 7) 리포트 히스토리 (reports)
# =====================================================================

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    report_type = Column(String(20), nullable=False)
    report_date = Column(Date, nullable=False, index=True)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'report_type', 'report_date', name='uq_report_user_type_date'),
    )

    # Relationships
    user = relationship("User", back_populates="reports")


# =====================================================================
# 8) SERP 트래킹: 타깃 (serp_targets)
# =====================================================================

class SerpTarget(Base):
    __tablename__ = "serp_targets"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("keyword_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type = Column(String, nullable=False) # Enum as String
    display_name = Column(String(100), nullable=False)
    match_domain = Column(String(255))
    match_url_prefix = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("match_domain IS NOT NULL OR match_url_prefix IS NOT NULL", name='ck_target_match'),
    )

    # Relationships
    group = relationship("KeywordGroup", back_populates="serp_targets")
    target_ranks = relationship("SerpTargetRank", back_populates="target", cascade="all, delete-orphan")
    rank_change_events = relationship("SerpRankChangeEvent", back_populates="target", cascade="all, delete-orphan")


# =====================================================================
# 9) SERP 트래킹: 측정 프로파일 (serp_profiles)
# =====================================================================

class SerpProfile(Base):
    __tablename__ = "serp_profiles"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("keyword_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    engine = Column(String, nullable=False)
    device = Column(String, nullable=False)
    result_type = Column(String, nullable=False)
    country_code = Column(String(2), nullable=False, default='KR')
    language_code = Column(String(10), nullable=False, default='ko')
    location_name = Column(String(100))
    location_code = Column(String(50))
    google_domain = Column(String(50))
    top_n = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    group = relationship("KeywordGroup", back_populates="serp_profiles")
    serp_queries = relationship("SerpQuery", back_populates="profile", cascade="all, delete-orphan")
    rank_change_events = relationship("SerpRankChangeEvent", back_populates="profile", cascade="all, delete-orphan")


# =====================================================================
# 10) SERP 트래킹: 쿼리 (serp_queries)
# =====================================================================

class SerpQuery(Base):
    __tablename__ = "serp_queries"

    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(Integer, ForeignKey("serp_profiles.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False)
    request_date = Column(Date, nullable=False, index=True)
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    request_params = Column(JSON)
    success = Column(Boolean, nullable=False, default=True)
    http_status = Column(Integer)
    error_message = Column(Text)
    raw_response = Column(JSON)

    __table_args__ = (
        UniqueConstraint('keyword_id', 'profile_id', 'request_date', name='uq_serp_query'),
    )

    # Relationships
    keyword = relationship("Keyword", back_populates="serp_queries")
    profile = relationship("SerpProfile", back_populates="serp_queries")
    results = relationship("SerpResult", back_populates="query", cascade="all, delete-orphan")
    target_ranks = relationship("SerpTargetRank", back_populates="query", cascade="all, delete-orphan")


# =====================================================================
# 11) SERP 트래킹: 결과 리스트 (serp_results)
# =====================================================================

class SerpResult(Base):
    __tablename__ = "serp_results"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("serp_queries.id", ondelete="CASCADE"), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    title = Column(Text)
    url = Column(Text, nullable=False)
    displayed_url = Column(Text)
    snippet = Column(Text)
    domain = Column(String(255), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('query_id', 'position', name='uq_serp_result_position'),
    )

    # Relationships
    query = relationship("SerpQuery", back_populates="results")
    matched_target_ranks = relationship("SerpTargetRank", back_populates="matched_result")


# =====================================================================
# 12) SERP 트래킹: 타깃별 최초 등장 순위 (serp_target_ranks)
# =====================================================================

class SerpTargetRank(Base):
    __tablename__ = "serp_target_ranks"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("serp_queries.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("serp_targets.id", ondelete="CASCADE"), nullable=False, index=True)
    rank_position = Column(Integer)
    matched_result_id = Column(Integer, ForeignKey("serp_results.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('query_id', 'target_id', name='uq_serp_target_rank'),
    )

    # Relationships
    query = relationship("SerpQuery", back_populates="target_ranks")
    target = relationship("SerpTarget", back_populates="target_ranks")
    matched_result = relationship("SerpResult", back_populates="matched_target_ranks")


# =====================================================================
# 13) SERP 랭크 변동 이벤트 (serp_rank_change_events)
# =====================================================================

class SerpRankChangeEvent(Base):
    __tablename__ = "serp_rank_change_events"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("serp_targets.id", ondelete="CASCADE"), nullable=False)
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(Integer, ForeignKey("serp_profiles.id", ondelete="CASCADE"), nullable=False)
    event_date = Column(Date, nullable=False, index=True)
    rank_today = Column(Integer)
    rank_yesterday = Column(Integer)
    delta = Column(Integer)
    threshold = Column(Integer, default=5)
    event_type = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("event_type IN ('UP', 'DOWN')", name='ck_serp_rank_change_event_type'),
        UniqueConstraint('target_id', 'keyword_id', 'profile_id', 'event_date', name='uq_serp_rank_change_event'),
    )

    # Relationships
    target = relationship("SerpTarget", back_populates="rank_change_events")
    keyword = relationship("Keyword", back_populates="serp_rank_change_events")
    profile = relationship("SerpProfile", back_populates="rank_change_events")
