/**
 * analysisApi.ts
 * ─────────────────────────────────────────────────────────────
 * back/routers/analysis_router.py 의 /analysis 엔드포인트와 통신.
 *
 * 사용하는 엔드포인트:
 *   GET  /analysis/latest   → fetchLatestAnalysis()
 *   GET  /analysis          → fetchAnalysisHistory()
 *   GET  /analysis/{id}     → fetchAnalysisById()
 * ─────────────────────────────────────────────────────────────
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function getToken(): string {
  const token = localStorage.getItem("access_token");
  if (!token) throw new Error("로그인이 필요합니다.");
  return token;
}

// ─────────────────────────────────────────────
// 타입 정의 (back/db/schemas.py 대응)
// ─────────────────────────────────────────────

/** AI 파이프라인이 analysis_data.metrics에 저장하는 지표 구조 */
export interface SkinMetricValue {
  score : number;
  label : string;
}

export interface SkinMetrics {
  moisture?     : SkinMetricValue;
  elasticity?   : SkinMetricValue;
  wrinkle?      : SkinMetricValue;
  pore?         : SkinMetricValue;
  pigmentation? : SkinMetricValue;
}

export interface SkinAnalysisData {
  overall_score?   : number;
  skin_type?       : string;
  skin_type_detail?: string;
  metrics?         : SkinMetrics;
}

export interface AnalysisResult {
  analysis_id   : number;
  user_id       : number;
  image_url     : string[];
  model_type    : string;
  analysis_data : SkinAnalysisData;
  created_at    : string;
}

// ─────────────────────────────────────────────
// API 함수
// ─────────────────────────────────────────────

/**
 * 가장 최근 피부 분석 결과 조회.
 * 분석 결과가 없으면 404 → Error("분석 결과가 없습니다.") throw
 * back: GET /analysis/latest
 */
export async function fetchLatestAnalysis(): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/analysis/latest`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
  }
  return res.json() as Promise<AnalysisResult>;
}

/**
 * 피부 분석 히스토리 전체 조회 (최신순).
 * back: GET /analysis
 */
export async function fetchAnalysisHistory(): Promise<AnalysisResult[]> {
  const res = await fetch(`${API_BASE}/analysis`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
  }
  return res.json() as Promise<AnalysisResult[]>;
}

/**
 * 피부 분석 결과 단건 조회.
 * back: GET /analysis/{analysis_id}
 */
export async function fetchAnalysisById(analysisId: number): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/analysis/${analysisId}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
  }
  return res.json() as Promise<AnalysisResult>;
}
