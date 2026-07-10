import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/stores/auth-store";

export function GuestRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  const hasToken = !!localStorage.getItem("access_token");

  if (isAuthenticated || hasToken) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
