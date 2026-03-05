"""
settings.py
환경변수를 한 곳에서 관리합니다.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI ────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = "gpt-4.1-mini"
OPENAI_TEMPERATURE: float = 0.3

# ── ChromaDB (Vector DB) ──────────────────────────────
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DB_PATH: str = os.getenv(
    "CHROMA_DB_PATH",
    os.path.join(_PROJECT_ROOT, "vector_store")
)
print(f"[settings] CHROMA_DB_PATH = {CHROMA_DB_PATH}", flush=True)
CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "skin_knowledge_base")
EMBED_MODEL_NAME: str = os.getenv("EMBED_MODEL_NAME", "jhgan/ko-sroberta-multitask")

# ── Tavily (Web Search) ───────────────────────────────
# .env에 따옴표/공백이 있을 수 있으므로 strip 처리
TAVILY_API_KEY: str = os.getenv("TAVILY_KEY", "").strip().strip("'\"")
if not TAVILY_API_KEY:
    print("[settings] TAVILY_API_KEY 없음 → 올리브영 검색 비활성화", flush=True)

# ── Vision Model ──────────────────────────────────────
# ── Skin AI 딥러닝 모델 ──────────────────────────────────────────
SKIN_AI_CHECKPOINT_DIR: str = os.getenv(
    "SKIN_AI_CHECKPOINT_DIR",
    os.path.join(_PROJECT_ROOT, "skin_ai", "checkpoint")
)
SKIN_AI_FAST_CHECKPOINT: str = os.path.join(SKIN_AI_CHECKPOINT_DIR, "fast")
SKIN_AI_DEEP_CHECKPOINT: str = os.path.join(SKIN_AI_CHECKPOINT_DIR, "deep")

# ── Chat History ──────────────────────────────────────
CHAT_HISTORY_TURNS: int = 10  # 최근 10턴 (20개 메시지)

# ── RAG ───────────────────────────────────────────────
RAG_TOP_K_DEFAULT: int = 5
RAG_TOP_K_PRODUCT: int = 10  # 제품 추천은 후보 더 많이

# ── Run Output ────────────────────────────────────────
RUNS_DIR: str = "outputs/runs"

assert OPENAI_API_KEY, "OPENAI_API_KEY가 비어있음 (.env의 OPENAI_API_KEY 확인)"
