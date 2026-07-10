"use client";

import { useQuery } from "@tanstack/react-query";
import { FolderKanban, FileCode, GitBranch, Cpu, DollarSign, Activity } from "lucide-react";
import { dashboardApi } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export function DashboardStats() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: async () => {
      const { data } = await dashboardApi.getStats();
      return data;
    },
  });

  if (isLoading) {
    return <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">{[...Array(4)].map((_, i) => (
      <Card key={i} className="animate-pulse"><CardContent className="h-24" /></Card>
    ))}</div>;
  }

  const statCards = [
    { title: "Total Projects", value: stats?.total_projects || 0, icon: FolderKanban, color: "text-blue-600" },
    { title: "Total Files", value: formatNumber(stats?.total_files || 0), icon: FileCode, color: "text-green-600" },
    { title: "Lines of Code", value: formatNumber(stats?.total_lines_of_code || 0), icon: GitBranch, color: "text-purple-600" },
    { title: "AI Usage", value: stats?.ai_usage_count || 0, icon: Cpu, color: "text-orange-600" },
    { title: "Total Tokens", value: formatNumber(stats?.total_tokens || 0), icon: Activity, color: "text-cyan-600" },
    { title: "Total Cost", value: formatCurrency(stats?.total_cost || 0), icon: DollarSign, color: "text-red-600" },
  ];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">{stat.title}</CardTitle>
                <Icon className={`h-5 w-5 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {stats?.migration_status && (
        <Card>
          <CardHeader><CardTitle>Migration Status</CardTitle></CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              {Object.entries(stats.migration_status).map(([status, count]) => (
                <div key={status} className="rounded-lg bg-gray-100 px-4 py-2 dark:bg-gray-800">
                  <span className="text-sm capitalize text-gray-500">{status.replace("_", " ")}</span>
                  <p className="text-xl font-bold">{count as number}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {stats?.recent_projects?.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Recent Projects</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stats.recent_projects.map((project: { id: number; name: string; status: string; updated_at: string }) => (
                <Link
                  key={project.id}
                  href={`/projects/${project.id}`}
                  className="flex items-center justify-between rounded-lg border border-gray-200 p-3 transition-colors hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900"
                >
                  <div>
                    <p className="font-medium">{project.name}</p>
                    <p className="text-sm text-gray-500">{new Date(project.updated_at).toLocaleDateString()}</p>
                  </div>
                  <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700 capitalize dark:bg-blue-950 dark:text-blue-300">
                    {project.status}
                  </span>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
