import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { DashboardStats } from "@/components/dashboard/stats";

export function DashboardPage() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Dashboard" description="Overview of your migration projects" />
        <main className="flex-1 overflow-y-auto p-6">
          <DashboardStats />
        </main>
      </div>
    </div>
  );
}
