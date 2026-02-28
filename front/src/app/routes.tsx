import { createBrowserRouter, Navigate } from "react-router";
import { Layout } from "./components/Layout";
import { ChatPage } from "./pages/ChatPage";
import { AnalysisPage } from "./pages/AnalysisPage";
import { WishlistPage } from "./pages/WishlistPage";
import { WishlistDetailPage } from "./pages/WishlistDetailPage";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";
import { ForgotPasswordPage } from "./pages/ForgotPasswordPage";
import { SettingsPage } from "./pages/SettingsPage";
import { OnboardingPage } from "./pages/OnboardingPage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, element: <Navigate to="/chat" replace /> },
      { path: "chat", Component: ChatPage },
      { path: "analysis", Component: AnalysisPage },
      { path: "wishlist", Component: WishlistPage },
      { path: "wishlist/:id", Component: WishlistDetailPage },
      { path: "settings", Component: SettingsPage },
    ],
  },
  { path: "/login", Component: LoginPage },
  { path: "/signup", Component: SignupPage },
  { path: "/forgot-password", Component: ForgotPasswordPage },
  { path: "/onboarding", Component: OnboardingPage },
]);
