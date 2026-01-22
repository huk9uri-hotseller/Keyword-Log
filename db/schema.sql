-- =====================================================================
-- K-LOG 통합 최종 DDL (PostgreSQL)
-- - 검색량/트렌드 기반 + 기사 수집/요약 + 리포트 스냅샷
-- - SERP API 기반 페이지 위치 순위(ORGANIC/ADS/LOCAL) 트래킹
-- =====================================================================

BEGIN;

-- =====================================================================
-- 0) ENUM 타입 (오타/불일치 방지용)
-- =====================================================================

CREATE TYPE serp_result_type AS ENUM (
  'ORGANIC',  -- 자연검색 결과
  'ADS',      -- 광고(Sponsored) 결과
  'LOCAL'     -- 로컬팩/지도 결과
);

CREATE TYPE serp_device_type AS ENUM (
  'DESKTOP',  -- 데스크톱 기준
  'MOBILE'    -- 모바일 기준
);

CREATE TYPE serp_target_type AS ENUM (
  'OWN',         -- 자사(우리 브랜드/도메인)
  'COMPETITOR'   -- 경쟁사(경쟁 브랜드/도메인)
);

CREATE TYPE serp_engine AS ENUM (
  'GOOGLE',  -- 구글 SERP
  'NAVER'    -- 네이버 SERP
);

CREATE TYPE serp_provider AS ENUM (
  'SERPAPI',    -- SerpApi
  'DATAFORSEO', -- DataForSEO
  'OTHER'       -- 기타 제공자
);

-- (검색량/트렌드 데이터 출처) - 필요 시 확장
CREATE TYPE metric_source AS ENUM (
  'NAVER_DATALAB',  -- 네이버 데이터랩(상대지표)
  'NAVER_ADS',      -- 네이버 검색광고(월/30일 누적)
  'GOOGLE_TRENDS',  -- Google Trends(pytrends)(상대지표)
  'GOOGLE_ADS'      -- Google Ads Keyword Planner(월 단위/범위)
);

-- =====================================================================
-- 1) 사용자 (Google OAuth 기반)
-- =====================================================================

CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,                         -- 내부 사용자 PK
  google_sub VARCHAR(255) NOT NULL UNIQUE,          -- Google OAuth 'sub' (변하지 않는 고유 식별자)
  email VARCHAR(255) NOT NULL UNIQUE,               -- 로그인 이메일(회사 메일 등)
  name VARCHAR(100),                                -- 사용자 이름(프로필)
  picture_url TEXT,                                 -- 프로필 이미지 URL
  last_login_at TIMESTAMPTZ,                        -- 마지막 로그인 시각(KPI: 재방문율/활성 추적)
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP  -- 생성 시각
);

-- =====================================================================
-- 2) 키워드 그룹 (자사 1 + 경쟁사 최대 5의 묶음 단위)
-- =====================================================================

CREATE TABLE keyword_groups (
  id BIGSERIAL PRIMARY KEY,                         -- 키워드 그룹 PK
  user_id BIGINT NOT NULL REFERENCES users(id)
    ON DELETE CASCADE,                              -- 소유 사용자 FK(사용자 삭제 시 그룹도 삭제)
  group_name VARCHAR(100) NOT NULL,                 -- 그룹 이름(예: "나이키 vs 아디다스")
  keyword_type VARCHAR(20) NOT NULL DEFAULT 'GENERAL', -- 그룹 유형(GENERAL/OWN/COMPETITOR)
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP  -- 생성 시각
);

ALTER TABLE keyword_groups
  ADD CONSTRAINT ck_keyword_groups_type
  CHECK (keyword_type IN ('GENERAL', 'OWN', 'COMPETITOR'));

CREATE INDEX idx_keyword_groups_user_id
  ON keyword_groups(user_id);                       -- 사용자별 그룹 조회 최적화

-- =====================================================================
-- 3) 키워드 (그룹에 속한 검색 키워드)
--    - SERP 트래킹에서 '검색어(query)' 역할
-- =====================================================================

CREATE TABLE keywords (
  id BIGSERIAL PRIMARY KEY,                         -- 키워드 PK
  group_id BIGINT NOT NULL REFERENCES keyword_groups(id)
    ON DELETE CASCADE,                              -- 소속 그룹 FK(그룹 삭제 시 키워드도 삭제)
  keyword VARCHAR(200) NOT NULL,                    -- 실제 검색어 문자열
  is_active BOOLEAN DEFAULT TRUE,                   -- 활성 여부(논리적 비활성)
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, -- 생성 시각
  UNIQUE (group_id, keyword)                        -- 동일 그룹 내 키워드 중복 방지
);

CREATE INDEX idx_keywords_group_id
  ON keywords(group_id);                            -- 그룹별 키워드 조회 최적화
CREATE INDEX idx_keywords_active
  ON keywords(group_id, is_active);                 -- 활성 키워드만 필터링 최적화

-- =====================================================================
-- 4) 트렌드/검색량 데이터
--    - search_trends: 일별 상대지표(0~100 등)
--    - search_volumes: 월/30일 누적(역산 기준용 앵커)
-- =====================================================================

CREATE TABLE search_trends (
  id BIGSERIAL PRIMARY KEY,                         -- 트렌드 PK
  keyword_id BIGINT NOT NULL REFERENCES keywords(id)
    ON DELETE CASCADE,                              -- 대상 키워드 FK
  source metric_source NOT NULL,                    -- 출처(NAVER_DATALAB / GOOGLE_TRENDS)
  search_date DATE NOT NULL,                        -- 해당 일자(일 단위)
  interest_score NUMERIC(5, 2),                     -- 상대 관심도 점수(예: 0~100, 소수 허용)
  estimated_daily_volume INTEGER,                   -- (선택) 역산된 '일별 추정 검색량'(전일 대비/변동 분석용)
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, -- 적재 시각
  UNIQUE(keyword_id, source, search_date)           -- 동일 키워드/출처/날짜 중복 방지
);

-- 트렌드 출처 제한(방어적 체크)
ALTER TABLE search_trends
  ADD CONSTRAINT ck_search_trends_source
  CHECK (source IN ('NAVER_DATALAB', 'GOOGLE_TRENDS'));

CREATE INDEX idx_search_trends_date
  ON search_trends(search_date);                    -- 날짜 기반 조회 최적화
CREATE INDEX idx_search_trends_keyword_date
  ON search_trends(keyword_id, search_date);        -- 키워드별 시계열 조회 최적화

CREATE TABLE search_volumes (
  id BIGSERIAL PRIMARY KEY,                         -- 절대/누적 검색량 PK
  keyword_id BIGINT NOT NULL REFERENCES keywords(id)
    ON DELETE CASCADE,                              -- 대상 키워드 FK
  source metric_source NOT NULL,                    -- 출처(NAVER_ADS / GOOGLE_ADS)
  period_start DATE NOT NULL,                       -- 집계 시작일(예: 최근 30일 시작)
  period_end DATE NOT NULL,                         -- 집계 종료일(예: 최근 30일 종료)
  volume INTEGER,                                   -- 누적/월간 검색량(원천 제공값 또는 범위/중앙값 정책 적용값)
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP  -- 적재 시각
);

ALTER TABLE search_volumes
  ADD CONSTRAINT ck_search_volumes_source
  CHECK (source IN ('NAVER_ADS', 'GOOGLE_ADS'));

CREATE INDEX idx_search_volumes_keyword_period
  ON search_volumes(keyword_id, period_start, period_end); -- 역산 기준값 조회 최적화

-- =====================================================================
-- 5) 변동 이벤트 (검색량/트렌드 기반 임계치 초과 트리거)
-- =====================================================================

CREATE TABLE keyword_change_events (
  id BIGSERIAL PRIMARY KEY,                         -- 이벤트 PK
  keyword_id BIGINT NOT NULL REFERENCES keywords(id)
    ON DELETE CASCADE,                              -- 대상 키워드 FK
  event_date DATE NOT NULL,                         -- 이벤트 기준 일자(보통 배치 날짜)
  change_rate FLOAT NOT NULL,                       -- 전일 대비 변화율(예: +0.25 = +25% 정책)
  event_type VARCHAR(10) NOT NULL
    CHECK (event_type IN ('SPIKE', 'DROP')),        -- 이벤트 유형(SPIKE=급등, DROP=급락)
  threshold_value FLOAT,                            -- 사용된 임계치(예: 0.2 = 20%)
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP  -- 생성 시각
);

CREATE INDEX idx_change_events_date
  ON keyword_change_events(event_date);             -- 날짜 기반 이벤트 조회 최적화
CREATE INDEX idx_change_events_keyword_date
  ON keyword_change_events(keyword_id, event_date); -- 키워드별 이벤트 조회 최적화

-- =====================================================================
-- 6) 뉴스 기사 + 요약 (이벤트와 연결)
-- =====================================================================

CREATE TABLE news_articles (
  id BIGSERIAL PRIMARY KEY,                         -- 기사 PK
  keyword_id BIGINT NOT NULL REFERENCES keywords(id)
    ON DELETE CASCADE,                              -- 관련 키워드 FK
  event_id BIGINT REFERENCES keyword_change_events(id)
    ON DELETE SET NULL,                             -- 연결 이벤트(없을 수도 있음)
  title TEXT NOT NULL,                              -- 기사 제목
  url TEXT NOT NULL,                                -- 기사 URL(원문 링크)
  media_source VARCHAR(100),                        -- 언론사/출처(예: 연합뉴스)
  published_at TIMESTAMPTZ,                         -- 기사 발행 시각
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP  -- 수집 시각
);

CREATE INDEX idx_news_articles_keyword
  ON news_articles(keyword_id);                     -- 키워드별 기사 조회 최적화
CREATE INDEX idx_news_articles_event
  ON news_articles(event_id);                       -- 이벤트별 기사 묶음 조회 최적화
CREATE INDEX idx_news_articles_published_at
  ON news_articles(published_at);                   -- 최신 기사 조회 최적화

CREATE TABLE news_summaries (
  id BIGSERIAL PRIMARY KEY,                         -- 요약 PK
  article_id BIGINT NOT NULL UNIQUE REFERENCES news_articles(id)
    ON DELETE CASCADE,                              -- 1:1 기사 FK(기사 삭제 시 요약도 삭제)
  summary_text TEXT NOT NULL,                       -- 요약 결과 본문
  model_name VARCHAR(50) DEFAULT 'gpt-5-mini',      -- 사용 모델명(추적/비용 분석용)
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP  -- 생성 시각
);

-- =====================================================================
-- 7) 리포트 히스토리 (일일 스냅샷 저장)
-- =====================================================================

CREATE TABLE reports (
  id BIGSERIAL PRIMARY KEY,                         -- 리포트 PK
  user_id BIGINT NOT NULL REFERENCES users(id)
    ON DELETE CASCADE,                              -- 소유 사용자 FK
  report_type VARCHAR(20) NOT NULL,                 -- 리포트 유형(예: 'DAILY', 'EVENT')
  report_date DATE NOT NULL,                        -- 리포트 기준 날짜
  content JSONB NOT NULL,                           -- 스냅샷(당시 순위/변동/기사 링크 등)
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, -- 생성 시각
  UNIQUE(user_id, report_type, report_date)         -- 동일 사용자/유형/날짜 중복 저장 방지
);

CREATE INDEX idx_reports_user_date
  ON reports(user_id, report_date);                 -- 사용자별 리포트 조회 최적화
CREATE INDEX idx_reports_date
  ON reports(report_date);                          -- 날짜별 리포트 조회 최적화

-- =====================================================================
-- 8) SERP 트래킹: 타깃(자사/경쟁사 도메인/URL 패턴)
--    - SERP 결과에서 "어느 결과가 자사/경쟁사인가" 판별 기준
-- =====================================================================

CREATE TABLE serp_targets (
  id BIGSERIAL PRIMARY KEY,                         -- 타깃 PK
  group_id BIGINT NOT NULL REFERENCES keyword_groups(id)
    ON DELETE CASCADE,                              -- 어느 그룹의 자사/경쟁사인지(그룹 삭제 시 타깃도 삭제)
  target_type serp_target_type NOT NULL,            -- OWN / COMPETITOR
  display_name VARCHAR(100) NOT NULL,               -- 화면 표시명(예: "나이키 공식몰")
  match_domain VARCHAR(255),                        -- 도메인 매칭(예: nike.com, m.nike.com)
  match_url_prefix TEXT,                            -- URL prefix 매칭(예: https://brand.com/product)
  is_active BOOLEAN DEFAULT TRUE,                   -- 활성 여부
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, -- 생성 시각
  CONSTRAINT ck_target_match CHECK (
    match_domain IS NOT NULL OR match_url_prefix IS NOT NULL
  )                                                 -- 도메인 또는 URL prefix 중 최소 하나는 필수
);

CREATE INDEX idx_serp_targets_group
  ON serp_targets(group_id);                        -- 그룹별 타깃 조회 최적화
CREATE INDEX idx_serp_targets_active
  ON serp_targets(group_id, is_active);             -- 활성 타깃 필터 최적화

-- =====================================================================
-- 9) SERP 트래킹: 측정 프로파일(측정 조건 고정)
--    - 엔진/디바이스/영역(ORGANIC/ADS/LOCAL)/국가/언어/위치/TopN
-- =====================================================================

CREATE TABLE serp_profiles (
  id BIGSERIAL PRIMARY KEY,                         -- 프로파일 PK
  group_id BIGINT NOT NULL REFERENCES keyword_groups(id)
    ON DELETE CASCADE,                              -- 어느 그룹에 적용되는 측정 조건인지
  engine serp_engine NOT NULL,                      -- GOOGLE / NAVER
  device serp_device_type NOT NULL,                 -- DESKTOP / MOBILE
  result_type serp_result_type NOT NULL,            -- ORGANIC / ADS / LOCAL
  country_code CHAR(2) NOT NULL DEFAULT 'KR',       -- 국가 코드(예: KR)
  language_code VARCHAR(10) NOT NULL DEFAULT 'ko',  -- 언어 코드(예: ko)
  location_name VARCHAR(100),                       -- 위치(예: "Seoul, South Korea") - 제공자 파라미터 대응
  location_code VARCHAR(50),                        -- 제공자 위치 코드(있으면 저장)
  google_domain VARCHAR(50),                        -- 구글 도메인(예: google.co.kr) - 구글용
  top_n INTEGER NOT NULL DEFAULT 100,               -- 수집할 결과 개수(Top N)
  is_active BOOLEAN DEFAULT TRUE,                   -- 활성 여부
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP  -- 생성 시각
);

CREATE INDEX idx_serp_profiles_group
  ON serp_profiles(group_id);                       -- 그룹별 프로파일 조회 최적화
CREATE INDEX idx_serp_profiles_active
  ON serp_profiles(group_id, is_active);            -- 활성 프로파일 필터 최적화

-- =====================================================================
-- 10) SERP 트래킹: 쿼리(요청/응답 로그 + 원본 JSON)
--     - 키워드 × 프로파일 × 날짜 단위로 1회 수집
-- =====================================================================

CREATE TABLE serp_queries (
  id BIGSERIAL PRIMARY KEY,                         -- SERP 요청 PK
  keyword_id BIGINT NOT NULL REFERENCES keywords(id)
    ON DELETE CASCADE,                              -- 어떤 검색어를 조회했는지
  profile_id BIGINT NOT NULL REFERENCES serp_profiles(id)
    ON DELETE CASCADE,                              -- 어떤 측정 조건으로 조회했는지
  provider serp_provider NOT NULL,                  -- 어떤 SERP API 제공자인지
  request_date DATE NOT NULL,                       -- 배치 기준 날짜(전일 대비 산정의 기준축)
  requested_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, -- 실제 요청 시각
  request_params JSONB,                             -- 요청 파라미터 원문(디버깅/재현 용)
  success BOOLEAN NOT NULL DEFAULT TRUE,            -- 요청 성공 여부
  http_status INTEGER,                              -- HTTP 상태 코드(실패/성공 메타)
  error_message TEXT,                               -- 실패 사유(예외 메시지)
  raw_response JSONB,                               -- 원본 응답(JSON). 크면 외부 저장 후 링크만 저장하도록 변경 가능
  UNIQUE(keyword_id, profile_id, request_date)      -- 동일 키워드/프로파일/날짜 중복 수집 방지
);

CREATE INDEX idx_serp_queries_date
  ON serp_queries(request_date);                    -- 날짜별 조회 최적화
CREATE INDEX idx_serp_queries_keyword_date
  ON serp_queries(keyword_id, request_date);        -- 키워드별 날짜 조회 최적화
CREATE INDEX idx_serp_queries_profile_date
  ON serp_queries(profile_id, request_date);        -- 프로파일별 날짜 조회 최적화

-- =====================================================================
-- 11) SERP 트래킹: 결과 리스트(Top N)
--     - query_id 아래에 position(1..N) 순서대로 저장
-- =====================================================================

CREATE TABLE serp_results (
  id BIGSERIAL PRIMARY KEY,                         -- SERP 결과 PK
  query_id BIGINT NOT NULL REFERENCES serp_queries(id)
    ON DELETE CASCADE,                              -- 어떤 SERP 요청의 결과인지
  position INTEGER NOT NULL,                        -- 결과 내 순위(1..N)
  title TEXT,                                       -- 결과 제목(없을 수 있음)
  url TEXT NOT NULL,                                -- 결과 URL(매칭/클릭의 핵심)
  displayed_url TEXT,                               -- 화면 표시용 URL(제공자에 따라 존재)
  snippet TEXT,                                     -- 결과 요약문(제공자에 따라 존재)
  domain VARCHAR(255),                              -- URL에서 추출한 도메인(애플리케이션에서 파싱 후 저장 권장)
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, -- 저장 시각
  UNIQUE(query_id, position)                        -- 동일 요청에서 position 중복 방지
);

CREATE INDEX idx_serp_results_query
  ON serp_results(query_id);                        -- 요청별 결과 조회 최적화
CREATE INDEX idx_serp_results_domain
  ON serp_results(domain);                          -- 도메인 매칭/통계용 조회 최적화

-- =====================================================================
-- 12) SERP 트래킹: 타깃별 최초 등장 순위(대시보드 핵심)
--     - 한 query에 대해, 각 타깃(자사/경쟁사)의 첫 등장 position 저장
-- =====================================================================

CREATE TABLE serp_target_ranks (
  id BIGSERIAL PRIMARY KEY,                         -- 타깃 랭크 PK
  query_id BIGINT NOT NULL REFERENCES serp_queries(id)
    ON DELETE CASCADE,                              -- 어떤 SERP 요청에 대한 랭크인지
  target_id BIGINT NOT NULL REFERENCES serp_targets(id)
    ON DELETE CASCADE,                              -- 어느 타깃(자사/경쟁사)인지
  rank_position INTEGER,                            -- 최초 등장 position(Top N 내 없으면 NULL 정책 권장)
  matched_result_id BIGINT REFERENCES serp_results(id)
    ON DELETE SET NULL,                             -- 매칭된 실제 결과 row (근거 추적)
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, -- 저장 시각
  UNIQUE(query_id, target_id)                       -- 동일 요청-타깃 중복 방지
);

CREATE INDEX idx_serp_target_ranks_query
  ON serp_target_ranks(query_id);                   -- 요청별 타깃 랭크 조회 최적화
CREATE INDEX idx_serp_target_ranks_target
  ON serp_target_ranks(target_id);                  -- 타깃별 랭크 추적 조회 최적화

-- =====================================================================
-- 13) SERP 랭크 변동 이벤트(선택)
--     - 전일 대비 "페이지 위치 순위" 상승/하락 트리거용
-- =====================================================================

CREATE TABLE serp_rank_change_events (
  id BIGSERIAL PRIMARY KEY,                         -- SERP 변동 이벤트 PK
  target_id BIGINT NOT NULL REFERENCES serp_targets(id)
    ON DELETE CASCADE,                              -- 어떤 타깃(자사/경쟁사)의 변동인지
  keyword_id BIGINT NOT NULL REFERENCES keywords(id)
    ON DELETE CASCADE,                              -- 어떤 키워드(검색어) 기준인지
  profile_id BIGINT NOT NULL REFERENCES serp_profiles(id)
    ON DELETE CASCADE,                              -- 어떤 측정 조건(엔진/디바이스/영역)인지
  event_date DATE NOT NULL,                         -- 이벤트 발생일(배치 날짜)
  rank_today INTEGER,                               -- 오늘 순위(작을수록 상위)
  rank_yesterday INTEGER,                           -- 어제 순위
  delta INTEGER,                                    -- 변화량 = (어제 - 오늘). 양수면 상승(순위 개선), 음수면 하락
  threshold INTEGER DEFAULT 5,                      -- 임계치(예: 5계단 이상 변화 시 이벤트)
  event_type VARCHAR(10) NOT NULL
    CHECK (event_type IN ('UP', 'DOWN')),           -- 상승/하락 이벤트 타입
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, -- 생성 시각
  UNIQUE(target_id, keyword_id, profile_id, event_date) -- 중복 이벤트 방지
);

CREATE INDEX idx_serp_events_date
  ON serp_rank_change_events(event_date);           -- 날짜별 이벤트 조회 최적화
CREATE INDEX idx_serp_events_target_date
  ON serp_rank_change_events(target_id, event_date);-- 타깃별 이벤트 조회 최적화

COMMIT;

-- =====================================================================
-- (운영 메모)
-- 1) "자사 1 + 경쟁사 최대 5" 제약은 DB에서 완전 강제하려면 트리거/부분인덱스가 필요합니다.
--    MVP에서는 애플리케이션 레벨 검증(등록 시 카운트 체크)로 처리하는 것을 권장합니다.
-- 2) serp_queries.raw_response가 커지면:
--    - S3 같은 외부 스토리지에 JSON 저장 후 URL만 DB에 저장하는 방식으로 전환 가능합니다.
-- =====================================================================
