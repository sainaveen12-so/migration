"use client";

import { useQuery } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { dashboardApi } from "@/lib/api";
import { useNotificationStore } from "@/stores/notification-store";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export function Header({ title, description, actions }: HeaderProps) {
  const { setNotifications } = useNotificationStore();

  useQuery({
    queryKey: ["notifications"],
    queryFn: async () => {
      const { data } = await dashboardApi.getNotifications();
      setNotifications(data);
      return data;
    },
    refetchInterval: 30000,
  });

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6 dark:border-gray-800 dark:bg-gray-950">
      <div>
        <h1 className="text-xl font-semibold">{title}</h1>
        {description && <p className="text-sm text-gray-500">{description}</p>}
      </div>
      <div className="flex items-center gap-3">
        {actions}
        <Button variant="ghost" size="icon">
          <Bell className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}
