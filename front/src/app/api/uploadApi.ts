/**
 * uploadApi.ts
 * ─────────────────────────────────────────────────────────────
 * back/routers/upload_router.py 의 /upload 엔드포인트와 통신.
 *
 * 사용하는 엔드포인트:
 *   POST /upload    → uploadImage(file)
 * ─────────────────────────────────────────────────────────────
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function getToken(): string {
    const token = localStorage.getItem("access_token");

    if (!token) throw new Error("로그인이 필요합니다.");

    return token;
}

/**
 * 이미지 파일을 서버를 통해 S3에 업로드하고 S3 URL 반환.
 * 
 * POST /upload?analysis_type=...
 * 
 * TODO.? analysis_type을 upload_type으로 변경하고 싶다...
 */
export async function uploadImage(file: File, analysisType: string = "simple"): Promise<string> {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_BASE}/upload?analysis_type=${encodeURIComponent(analysisType)}`, {
        method  : "POST",
        headers : { Authorization: `Bearer ${getToken()}` },
        body    : formData,
    });

    if (!res.ok) {
        const data = await res.json().catch(() => ({}));

        throw new Error((data as { detail?: string }).detail ?? `업로드 실패 (${res.status})`);
    }

    const data = await res.json() as { url: string };

    return data.url;
}