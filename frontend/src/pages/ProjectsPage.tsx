import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Upload } from "lucide-react";
import { projectsApi } from "@/lib/api";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Project {
  id: number;
  name: string;
  description?: string;
  status: string;
  source_language?: string;
  target_language?: string;
  total_files: number;
  total_lines: number;
  updated_at: string;
}

export function ProjectsPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newProject, setNewProject] = useState({ name: "", description: "" });

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: async () => {
      const { data } = await projectsApi.list();
      return data as Project[];
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description: string }) => projectsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setShowCreate(false);
      setNewProject({ name: "", description: "" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => projectsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header
          title="Projects"
          description="Manage your code migration projects"
          actions={
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="mr-2 h-4 w-4" /> New Project
            </Button>
          }
        />
        <main className="flex-1 overflow-y-auto p-6">
          {showCreate && (
            <Card className="mb-6">
              <CardHeader><CardTitle>Create New Project</CardTitle></CardHeader>
              <CardContent>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    createMutation.mutate(newProject);
                  }}
                  className="space-y-4"
                >
                  <div className="space-y-2">
                    <Label>Project Name</Label>
                    <Input value={newProject.name} onChange={(e) => setNewProject({ ...newProject, name: e.target.value })} required />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Input value={newProject.description} onChange={(e) => setNewProject({ ...newProject, description: e.target.value })} />
                  </div>
                  <div className="flex gap-2">
                    <Button type="submit" disabled={createMutation.isPending}>Create</Button>
                    <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          )}

          {isLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(3)].map((_, i) => <Card key={i} className="animate-pulse"><CardContent className="h-32" /></Card>)}
            </div>
          ) : projects.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Upload className="mb-4 h-12 w-12 text-gray-400" />
                <p className="text-lg font-medium">No projects yet</p>
                <p className="text-sm text-gray-500">Create your first migration project</p>
                <Button className="mt-4" onClick={() => setShowCreate(true)}>
                  <Plus className="mr-2 h-4 w-4" /> Create Project
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {projects.map((project) => (
                <Card key={project.id} className="transition-shadow hover:shadow-md">
                  <CardHeader className="flex flex-row items-start justify-between">
                    <div>
                      <Link to={`/projects/${project.id}`}>
                        <CardTitle className="hover:text-blue-600">{project.name}</CardTitle>
                      </Link>
                      <p className="text-sm text-gray-500">{project.description}</p>
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => deleteMutation.mutate(project.id)}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between text-sm">
                      <span className="rounded-full bg-blue-100 px-2 py-1 text-xs font-medium capitalize text-blue-700 dark:bg-blue-950">
                        {project.status}
                      </span>
                      <span className="text-gray-500">{project.total_files} files</span>
                    </div>
                    {(project.source_language || project.target_language) && (
                      <p className="mt-2 text-xs text-gray-500">
                        {project.source_language || "?"} → {project.target_language || "?"}
                      </p>
                    )}
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
