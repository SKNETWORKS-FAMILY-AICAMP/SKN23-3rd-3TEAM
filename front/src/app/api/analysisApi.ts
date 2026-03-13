/**
 * analysisApi.ts
 * ─────────────────────────────────────────────────────────────
 * back/routers/analysis_router.py 의 /analysis 엔드포인트와 통신.
 *
 * 사용하는 엔드포인트:
 *   GET  /analysis             → fetchDetailAnalysis()
 *   GET  /analysis/factorials  → fetchFactorials()
 * ─────────────────────────────────────────────────────────────
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function getToken(): string {
    const token = localStorage.getItem("access_token");

    if (!token) throw new Error("로그인이 필요합니다.");

    return token;
}

// ─────────────────────────────────────────────
// 타입 정의
// ─────────────────────────────────────────────

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
    factorial?       : string[];
}
export interface AnalysisResult {
    analysis_id   : number;
    user_id       : number;
    image_url     : string[];
    model_type    : string;
    analysis_data : SkinAnalysisData;
    created_at    : string;
}
export interface KeywordResponse {
    keyword_id : number;
    keyword    : string;
    label      : string;
}

// ─────────────────────────────────────────────
// API 호출 함수
// ─────────────────────────────────────────────

/**
 * 사용자의 피부 정밀 분석 데이터 전체 조회. (최신순)
 * 
 * GET /analysis
 */
export async function fetchDetailAnalysis(): Promise<AnalysisResult[]> {
    const res = await fetch(`${API_BASE}/analysis/model/detailed`, {
        headers: { Authorization: `Bearer ${getToken()}` },
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));

        throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
    }
    
    return res.json() as Promise<AnalysisResult[]>;
}

/**
 * 추천 관리법 키워드 목록 전체 조회
 * 
 * GET /analysis/factorials
 */
export async function fetchFactorials(): Promise<KeywordResponse[]> {
    const res = await fetch(`${API_BASE}/keywords/factorials`);

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));

        throw new Error((data as { detail?: string }).detail ?? `서버 오류 (${res.status})`);
    }

    return res.json() as Promise<KeywordResponse[]>;
}
