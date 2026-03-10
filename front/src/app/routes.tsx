import { ChatPage } from "./pages/ChatPage";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";
import { AnalysisPage } from "./pages/AnalysisPage";
import { SettingsPage } from "./pages/SettingsPage";
import { WishlistPage } from "./pages/WishlistPage";
import { OnboardingPage } from "./pages/OnboardingPage";
import { OAuthCallbackPage } from "./pages/OAuthCallbackPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { createBrowserRouter, Navigate, Outlet } from "react-router";

/** 로그인 필요 페이지 — 미인증 시 /chat으로 리다이렉트 */
function PrivateRoute() {
    return localStorage.getItem("access_token")
        ? <Outlet />
        : <Navigate to="/chat" replace />;
}

export const router = createBrowserRouter([
    {
        path: "/",
        Component: Layout,
        children: [
            { index: true, element: <Navigate to="/chat" replace /> },
            { path: "chat", Component: ChatPage },      // 비로그인 접근 가능
            {
                element: <PrivateRoute />,              // 로그인 필요
                children: [
                    { path: "analysis", Component: AnalysisPage },
                    { path: "wishlist", Component: WishlistPage },
                    { path: "settings", Component: SettingsPage },
                ],
            },
        ],
    },
    { path: "/login", Component: LoginPage },
    { path: "/signup", Component: SignupPage },
    { path: "/onboarding", Component: OnboardingPage },
    { path: "/forgot-password", Component: ForgotPasswordPage },
    { path: "/oauth/callback", Component: OAuthCallbackPage },
]);
