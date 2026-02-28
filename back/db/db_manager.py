"""
db_manager.py
─────────────────────────────────────────────────────────────
목적  : AWS RDS(MariaDB) 연결 및 공통 쿼리 실행 담당
역할  :
    1. SSH 터널링을 통한 RDS 안전 접속 (EC2 경유)
    2. pymysql Connection Pool 관리 (재사용 가능)
    3. select / insert / update / delete 공통 헬퍼 함수 제공
    4. init_db() - 서버 시작 시 001_init_tables.sql 자동 실행
─────────────────────────────────────────────────────────────
"""

import os
import pymysql
import pymysql.cursors
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드
load_dotenv()

# ─────────────────────────────────────────────
# 환경변수 로드
# ─────────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", 3306))
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME     = os.getenv("DB_NAME")

SSH_HOST    = os.getenv("SSH_HOST")
SSH_PORT    = int(os.getenv("SSH_PORT", 22))
SSH_USER    = os.getenv("SSH_USER")
SSH_PKEY    = os.getenv("SSH_PKEY")

# ─────────────────────────────────────────────
# SSH 터널 (전역 싱글톤)
# ─────────────────────────────────────────────
_tunnel: SSHTunnelForwarder | None = None


def _get_tunnel() -> SSHTunnelForwarder:
    """
    SSH 터널을 싱글톤으로 관리.
    이미 열려있으면 재사용, 닫혀있으면 새로 생성.
    """
    global _tunnel
    if _tunnel is None or not _tunnel.is_active:
        _tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),           # EC2 주소 + 포트
            ssh_username=SSH_USER,
            ssh_pkey=SSH_PKEY,              # .pem 파일 경로
            remote_bind_address=(DB_HOST, DB_PORT),  # RDS 주소 + 포트
        )
        _tunnel.start()
    return _tunnel


# ─────────────────────────────────────────────
# Connection 생성
# ─────────────────────────────────────────────
def get_connection() -> pymysql.connections.Connection:
    """
    SSH 터널을 통해 RDS에 pymysql Connection 생성 후 반환.
    사용 후 반드시 conn.close() 호출 필요.
    """
    tunnel = _get_tunnel()
    conn = pymysql.connect(
        host="127.0.0.1",                       # 터널 로컬 바인딩 주소
        port=tunnel.local_bind_port,            # 터널이 열어준 로컬 포트
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, # 결과를 dict로 반환
        autocommit=False,                       # 트랜잭션 수동 관리
    )
    return conn


# ─────────────────────────────────────────────
# 공통 쿼리 헬퍼 함수
# ─────────────────────────────────────────────
def execute_query(sql: str, params: tuple = ()) -> list[dict]:
    """
    SELECT 전용 헬퍼.
    결과를 dict 리스트로 반환.

    사용 예시:
        rows = execute_query("SELECT * FROM users WHERE user_id = %s", (user_id,))
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def execute_one(sql: str, params: tuple = ()) -> dict | None:
    """
    SELECT 단건 조회 헬퍼.
    결과가 없으면 None 반환.

    사용 예시:
        user = execute_one("SELECT * FROM users WHERE email = %s", (email,))
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()
    finally:
        conn.close()


def execute_write(sql: str, params: tuple = ()) -> int:
    """
    INSERT / UPDATE / DELETE 전용 헬퍼.
    INSERT 시 생성된 PK(lastrowid) 반환,
    UPDATE/DELETE 시 영향받은 행 수 반환.
    실패 시 롤백 후 예외 발생.

    사용 예시:
        new_id = execute_write(
            "INSERT INTO users (email, name, nickname) VALUES (%s, %s, %s)",
            (email, name, nickname)
        )
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            last_id  = cursor.lastrowid
            row_count = cursor.rowcount
        conn.commit()
        return last_id if last_id else row_count
    except Exception as e:
        conn.rollback()  # 실패 시 롤백
        raise RuntimeError(f"[DB 쓰기 오류] {e}") from e
    finally:
        conn.close()


def execute_many(sql: str, params_list: list[tuple]) -> int:
    """
    다건 INSERT / UPDATE 전용 헬퍼 (executemany).
    영향받은 행 수 반환.
    실패 시 롤백 후 예외 발생.

    사용 예시 (키워드 초기 데이터 삽입 등):
        execute_many(
            "INSERT INTO keywords (type, label, keyword) VALUES (%s, %s, %s)",
            [("skin_type", "건성", "dry"), ("skin_type", "지성", "oily")]
        )
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.executemany(sql, params_list)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"[DB 다건 쓰기 오류] {e}") from e
    finally:
        conn.close()


# ─────────────────────────────────────────────
# DB 초기화 (서버 시작 시 자동 실행)
# ─────────────────────────────────────────────
def init_db() -> None:
    """
    migrations/001_init_tables.sql 을 읽어
    테이블이 없을 경우 자동 생성 (IF NOT EXISTS 조건).
    FastAPI 앱 시작 시 한 번만 호출.

    사용 예시 (main.py):
        from db.db_manager import init_db

        @app.on_event("startup")
        def startup():
            init_db()
    """
    # SQL 파일 경로 (db_manager.py 기준 상대경로)
    sql_path = Path(__file__).parent / "migrations" / "001_init_tables.sql"

    if not sql_path.exists():
        raise FileNotFoundError(f"[init_db] SQL 파일을 찾을 수 없습니다: {sql_path}")

    sql_script = sql_path.read_text(encoding="utf-8")

    # 세미콜론 기준으로 구문 분리 후 순서대로 실행
    statements = [s.strip() for s in sql_script.split(";") if s.strip()]

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
        conn.commit()
        print("[init_db] 테이블 초기화 완료")
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"[init_db] 테이블 초기화 실패: {e}") from e
    finally:
        conn.close()


# ─────────────────────────────────────────────
# SSH 터널 종료 (앱 종료 시 호출)
# ─────────────────────────────────────────────
def close_tunnel() -> None:
    """
    앱 종료 시 SSH 터널 정리.

    사용 예시 (main.py):
        @app.on_event("shutdown")
        def shutdown():
            close_tunnel()
    """
    global _tunnel
    if _tunnel and _tunnel.is_active:
        _tunnel.stop()
        print("[close_tunnel] SSH 터널 종료")