-- ============================================================
-- 001_init_tables.sql
-- 실행 순서: FK 의존관계에 따라 순서대로 실행
-- keywords → users → auth_providers → chat_rooms
--          → chat_messages → skin_analysis_results → wishlist
-- ============================================================


-- ------------------------------------------------------------
-- 1. keywords
-- 다른 테이블들이 FK로 참조하는 공통 코드 테이블 (가장 먼저 생성)
-- 피부타입, 성별 등 enum 역할
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS keywords (
    keyword_id  INT          AUTO_INCREMENT PRIMARY KEY COMMENT '고유 ID',
    type        VARCHAR(50)  NOT NULL                  COMMENT '키워드 그룹 (예: skin_type, gender)',
    label       VARCHAR(100) NULL                      COMMENT '화면에 표시되는 이름 (예: 건성)',
    keyword     VARCHAR(100) NOT NULL                  COMMENT '코드 내부에서 사용하는 값 (예: dry)',
    description TEXT         NULL                      COMMENT '설명',
    UNIQUE KEY unique_type_keyword (type, keyword)
) COMMENT='키워드 사전 테이블';


-- ------------------------------------------------------------
-- 2. users
-- 서비스 사용자 기본 정보
-- skin_type → keywords.keyword_id FK
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id           INT          AUTO_INCREMENT PRIMARY KEY                            COMMENT '사용자 고유 ID',
    profile_image_url VARCHAR(500) NULL                                                  COMMENT '사용자 프로필 이미지 URL (S3)',
    email             VARCHAR(255) NOT NULL UNIQUE                                       COMMENT '로그인용 이메일',
    name              VARCHAR(50)  NOT NULL                                              COMMENT '사용자 실명',
    nickname          VARCHAR(50)  NOT NULL UNIQUE                                       COMMENT '서비스 내 표시 닉네임 (중복 불가)',
    age               INT          NULL                                                  COMMENT '사용자 나이',
    gender            VARCHAR(20)  NULL                                                  COMMENT '사용자 성별 (male, female)',
    skin_type         INT          NULL                                                  COMMENT '피부 타입 FK → keywords.keyword_id',
    skin_concern      VARCHAR(255) NULL                                                  COMMENT '피부 고민 (트러블, 주름, 미백 등)',
    is_email_verified BOOLEAN      NOT NULL DEFAULT FALSE                                COMMENT '외부 Auth 인증 완료 여부',
    is_active         BOOLEAN      NOT NULL DEFAULT TRUE                                 COMMENT '계정 활성 상태 (정지 시 FALSE)',
    terms_agreed      BOOLEAN      NOT NULL DEFAULT FALSE                                COMMENT '서비스 이용약관 동의 여부 (필수)',
    privacy_agreed    BOOLEAN      NOT NULL DEFAULT FALSE                                COMMENT '개인정보 처리방침 동의 여부 (필수)',
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP                    COMMENT '계정 생성 시각',
    updated_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '계정 수정 시각',
    deleted_at        DATETIME     NULL                                                  COMMENT '계정 탈퇴 시각 (soft delete)',
    FOREIGN KEY (skin_type) REFERENCES keywords(keyword_id)
) COMMENT='서비스 사용자 기본 정보 테이블';


-- ------------------------------------------------------------
-- 3. auth_providers
-- 사용자 로그인 수단 관리 (local / google / kakao)
-- user_id → users.user_id FK
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auth_providers (
    auth_id       INT          AUTO_INCREMENT PRIMARY KEY COMMENT '인증 제공자 고유 ID',
    user_id       INT          NOT NULL                  COMMENT 'users.user_id 참조',
    provider_type VARCHAR(50)  NOT NULL                  COMMENT '인증 제공자 유형 (local / google / kakao)',
    provider_id   VARCHAR(255) NOT NULL                  COMMENT '각 provider에서의 고유 사용자 ID (local이면 이메일)',
    password_hash VARCHAR(255) NULL                      COMMENT 'local 로그인용 비밀번호 해시 (소셜 로그인 시 NULL)',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '해당 인증 수단이 계정에 연결된 시점',
    UNIQUE KEY uq_provider (provider_type, provider_id),        -- 동일 소셜 계정 중복 등록 방지
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE  -- 유저 삭제 시 인증 수단도 함께 삭제
) COMMENT='사용자의 로그인 수단(local/소셜)을 관리하는 인증 테이블';


-- ------------------------------------------------------------
-- 4. chat_rooms
-- 사용자별 채팅 세션 단위
-- user_id → users.user_id FK
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_rooms (
    chat_room_id INT          AUTO_INCREMENT PRIMARY KEY          COMMENT '채팅방 ID',
    user_id      INT          NOT NULL                            COMMENT 'users.user_id 참조',
    title        VARCHAR(255) NULL                                COMMENT '채팅방 제목 (첫 질문 요약)',
    created_at   DATETIME     NULL DEFAULT CURRENT_TIMESTAMP      COMMENT '채팅방 생성 시각',
    deleted_at   DATETIME     NULL                                COMMENT '채팅방 삭제 시각 (soft delete)',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) COMMENT='사용자별 채팅 세션 관리 테이블';


-- ------------------------------------------------------------
-- 5. chat_messages
-- 채팅방 내 메시지 저장 (user / assistant / system)
-- chat_room_id → chat_rooms.chat_room_id FK
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id   INT         AUTO_INCREMENT PRIMARY KEY      COMMENT '메시지 ID',
    chat_room_id INT         NOT NULL                        COMMENT 'chat_rooms.chat_room_id 참조',
    role         VARCHAR(20) NOT NULL                        COMMENT '메시지 주체 (user / assistant / system)',
    content      TEXT        NULL                            COMMENT '텍스트 내용 (이미지 전용 메시지일 경우 NULL)',
    image_url    JSON        NULL                            COMMENT '사용자 업로드 이미지 경로 (S3 URL 배열)',
    model_type   VARCHAR(20) NOT NULL                        COMMENT '사용된 분석 모델 유형 (simple / detailed)',
    created_at   DATETIME    NULL DEFAULT CURRENT_TIMESTAMP  COMMENT '메시지 생성 시각',
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(chat_room_id) ON DELETE CASCADE
) COMMENT='LLM 챗봇 대화 메시지 저장 테이블';


-- ------------------------------------------------------------
-- 6. skin_analysis_results
-- AI 피부 분석 결과 저장
-- user_id → users.user_id FK
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS skin_analysis_results (
    analysis_id   INT          AUTO_INCREMENT PRIMARY KEY          COMMENT '피부 분석 결과 ID',
    user_id       INT          NOT NULL                            COMMENT 'users.user_id 참조',
    image_url     JSON         NOT NULL                            COMMENT '분석에 사용된 이미지 URL 배열 (S3)',
    model_type    VARCHAR(20)  NOT NULL                            COMMENT '사용된 분석 모델 유형 (simple / detailed)',
    analysis_data JSON         NOT NULL                            COMMENT '피부 분석 구조화 데이터 (정량 지표 등)',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP  COMMENT '분석 생성 시각',
    deleted_at    DATETIME     NULL                                COMMENT '분석 삭제 시각 (soft delete)',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) COMMENT='AI 피부 분석 결과 저장 테이블';


-- ------------------------------------------------------------
-- 7. wishlist
-- 사용자가 추천받은 제품 중 저장해둔 목록
-- user_id → users.user_id FK
-- message_id → chat_messages.message_id FK
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS wishlist (
    wish_id             INT          AUTO_INCREMENT PRIMARY KEY          COMMENT '위시리스트 고유 ID',
    user_id             INT          NOT NULL                            COMMENT 'users.user_id 참조',
    message_id          INT          NULL                                COMMENT '제품을 추천한 assistant 메시지 ID',
    product_vector_id   VARCHAR(50)  NOT NULL                            COMMENT '벡터DB에 저장된 제품의 고유 ID',
    product_name        VARCHAR(50)  NOT NULL                            COMMENT '제품명 (위시리스트 화면 표시용)',
    product_description TEXT         NULL                                COMMENT '제품 간단 설명 (요약 정보 표시용)',
    added_at            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP  COMMENT '위시리스트에 추가된 시각',
    FOREIGN KEY (user_id)    REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES chat_messages(message_id) ON DELETE SET NULL  -- 메시지 삭제돼도 위시리스트는 유지
) COMMENT='사용자가 추천받은 제품을 저장하는 위시리스트 테이블';