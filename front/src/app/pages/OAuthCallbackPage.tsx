import { useEffect } from "react";
import { useNavigate } from "react-router";
import { Loading } from "@/app/components/ui/loading";

/**
 * OAuthCallbackPage
 * ─────────────────────────────────────────────────────────────
 * 경로: /oauth/callback
 *
 * 소셜 로그인(Google / Kakao) 완료 후 백엔드가 리디렉션하는 페이지.
 * URL 파라미터:
 *   ?token=<jwt>           성공 시 JWT 토큰
 *   ?error=<message>       실패 시 에러 메시지
 *   ?provider=google|kakao 어떤 provider로 로그인했는지 (선택)
 * ─────────────────────────────────────────────────────────────
 */
export function OAuthCallbackPage() {
  const navigate = useNavigate();

  useEffect(() => {
    const params   = new URLSearchParams(window.location.search);
    const token    = params.get("token");
    const errorMsg = params.get("error");
    const isNew    = params.get("is_new") === "true";

    if (token) {
      localStorage.setItem("access_token", token);
      // 신규 가입 유저는 온보딩, 기존 유저는 채팅으로 이동
      navigate(isNew ? "/onboarding" : "/chat", { replace: true });
    } else {
      const msg = errorMsg ?? "소셜 로그인에 실패했습니다.";
      navigate(`/login?error=${encodeURIComponent(msg)}`, { replace: true });
    }
  }, [navigate]);

  return <Loading className="mt-34" />;
}
