import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/stores/auth-store";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();
  const hasToken = !!localStorage.getItem("access_token");

  if (!isAuthenticated && !hasToken) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return <>{children}</>;
}
