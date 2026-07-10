"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Search } from "lucide-react";
import Link from "next/link";
import { dashboardApi, aiApi } from "@/lib/api";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: results, isLoading } = useQuery({
    queryKey: ["search", searchQuery],
    queryFn: async () => {
      const { data } = await dashboardApi.search(searchQuery);
      return data;
    },
    enabled: searchQuery.length >= 2,
  });

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header title="Global Search" description="Search projects, files, classes, and APIs" />
        <main className="flex-1 overflow-y-auto p-6">
          <form
            onSubmit={(e) => { e.preventDefault(); setSearchQuery(query); }}
            className="mb-6 flex gap-2"
          >
            <Input
              placeholder="Search projects, files, methods, APIs..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex-1"
            />
            <button type="submit" className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
              <Search className="h-5 w-5" />
            </button>
          </form>

          {isLoading && <p className="text-gray-500">Searching...</p>}

          {results && (
            <div className="space-y-3">
              <p className="text-sm text-gray-500">{results.total} results for &quot;{results.query}&quot;</p>
              {results.results.map((result: { type: string; id: number; name: string; path?: string; project_id?: number; project_name?: string; snippet?: string }) => (
                <Card key={`${result.type}-${result.id}`}>
                  <CardContent className="py-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium capitalize dark:bg-gray-800">{result.type}</span>
                        <p className="mt-1 font-medium">{result.name}</p>
                        {result.path && <p className="font-mono text-xs text-gray-500">{result.path}</p>}
                        {result.snippet && <p className="mt-2 text-sm text-gray-600">...{result.snippet}...</p>}
                      </div>
                      {result.project_id && (
                        <Link href={`/projects/${result.project_id}`} className="text-sm text-blue-600 hover:underline">
                          {result.project_name}
                        </Link>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
