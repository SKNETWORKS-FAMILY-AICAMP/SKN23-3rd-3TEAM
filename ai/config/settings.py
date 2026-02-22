from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    RUNS_DIR: str = "outputs/runs"
    # LLM_BACKEND: "mock" or "openai"
    LLM_BACKEND: str = "mock"
    # Tool backend switches
    VISION_BACKEND: str = "mock"
    RAG_BACKEND: str = "mock"

settings = Settings()