import { useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Upload, GitBranch as GithubIcon, Play, Download, FileCode, MessageSquare,
  GitBranch, Bug, Wrench, FileText, TestTube, Loader2, Sparkles,
} from "lucide-react";
import { projectsApi, aiApi } from "@/lib/api";
import { pollJobUntilDone } from "@/lib/job-polling";
import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CodeEditor, DiffViewer } from "@/components/editor/code-editor";
import { AIChat } from "@/components/chat/ai-chat";
import { DiagramViewer } from "@/components/diagrams/diagram-viewer";

const MIGRATION_OPTIONS = [
  { label: "Java → FastAPI", source: "java", target: "python", framework: "fastapi" },
  { label: "Spring Boot → FastAPI", source: "spring_boot", target: "python", framework: "fastapi" },
  { label: "Flask → FastAPI", source: "flask", target: "python", framework: "fastapi" },
  { label: "React → Vite", source: "react", target: "typescript", framework: "vite" },
  { label: "Angular → React", source: "angular", target: "typescript", framework: "react" },
  { label: "JavaScript → TypeScript", source: "javascript", target: "typescript", framework: null },
  { label: ".NET → Python", source: "csharp", target: "python", framework: "fastapi" },
  { label: "PHP → Node.js", source: "php", target: "javascript", framework: "nodejs" },
];

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [activeTab, setActiveTab] = useState<"files" | "editor" | "chat" | "diagrams" | "analysis">("files");
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [showGithub, setShowGithub] = useState(false);
  const [migrationType, setMigrationType] = useState(MIGRATION_OPTIONS[0]);
  const [explainResult, setExplainResult] = useState<Record<string, unknown> | null>(null);
  const [jobProgress, setJobProgress] = useState<number | null>(null);

  const { data: project, isLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: async () => {
      const { data } = await projectsApi.get(projectId);
      return data;
    },
    enabled: !Number.isNaN(projectId),
  });

  const { data: files = [] } = useQuery({
    queryKey: ["project-files", projectId],
    queryFn: async () => {
      const { data } = await projectsApi.getFiles(projectId);
      return data;
    },
    enabled: !Number.isNaN(projectId),
  });

  const { data: selectedFile } = useQuery({
    queryKey: ["project-file", projectId, selectedFileId],
    queryFn: async () => {
      const { data } = await projectsApi.getFile(projectId, selectedFileId!);
      return data;
    },
    enabled: !!selectedFileId,
  });

  const { data: analysis } = useQuery({
    queryKey: ["project-analysis", projectId],
    queryFn: async () => {
      const { data } = await projectsApi.getAnalysis(projectId);
      return data;
    },
    enabled: project?.status === "analyzed" || project?.status === "migrated",
  });

  const { data: diagrams } = useQuery({
    queryKey: ["project-diagrams", projectId],
    queryFn: async () => {
      const { data } = await aiApi.getDiagrams(projectId);
      return data;
    },
    enabled: activeTab === "diagrams" && !!analysis,
  });

  const invalidateProjectData = () => {
    queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    queryClient.invalidateQueries({ queryKey: ["project-files", projectId] });
    queryClient.invalidateQueries({ queryKey: ["project-analysis", projectId] });
    queryClient.invalidateQueries({ queryKey: ["project-diagrams", projectId] });
  };

  const runJobMutation = async (
    request: () => Promise<{ data: { job_id?: number } }>
  ) => {
    const { data } = await request();
    if (data.job_id) {
      setJobProgress(0);
      await pollJobUntilDone(data.job_id, {
        onProgress: (job) => setJobProgress(job.progress),
      });
      setJobProgress(null);
    }
    return data;
  };

  const uploadMutation = useMutation({
    mutationFn: (file: File) => projectsApi.upload(projectId, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["project", projectId] }),
  });

  const cloneMutation = useMutation({
    mutationFn: (url: string) => projectsApi.cloneGithub(projectId, { github_url: url }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      setShowGithub(false);
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: () => runJobMutation(() => projectsApi.analyze(projectId)),
    onSuccess: invalidateProjectData,
  });

  const migrateMutation = useMutation({
    mutationFn: () =>
      runJobMutation(() =>
        projectsApi.migrate(projectId, {
          target_language: migrationType.target,
          target_framework: migrationType.framework || undefined,
          migration_type: migrationType.label,
        })
      ),
    onSuccess: invalidateProjectData,
  });

  const explainMutation = useMutation({
    mutationFn: () =>
      aiApi.explain(projectId, selectedFile!.file_path, selectedFile!.content),
    onSuccess: ({ data }) => setExplainResult(data),
  });

  const handleDownload = async () => {
    const { data } = await projectsApi.download(projectId);
    const url = window.URL.createObjectURL(new Blob([data]));
    const a = document.createElement("a");
    a.href = url;
    a.download = `${project?.name}_migrated.zip`;
    a.click();
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const tabs = [
    { id: "files" as const, label: "Files", icon: FileCode },
    { id: "editor" as const, label: "Editor", icon: FileCode },
    { id: "chat" as const, label: "AI Chat", icon: MessageSquare },
    { id: "diagrams" as const, label: "Diagrams", icon: GitBranch },
    { id: "analysis" as const, label: "Analysis", icon: Sparkles },
  ];

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header
          title={project?.name || "Project"}
          description={project?.description}
          actions={
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()}>
                <Upload className="mr-1 h-4 w-4" /> Upload ZIP
              </Button>
              <Button variant="outline" size="sm" onClick={() => setShowGithub(!showGithub)}>
                <GithubIcon className="mr-1 h-4 w-4" /> Clone GitHub
              </Button>
              <Button size="sm" onClick={() => analyzeMutation.mutate()} disabled={analyzeMutation.isPending}>
                <Play className="mr-1 h-4 w-4" /> Analyze
              </Button>
              {project?.status === "migrated" && (
                <Button variant="secondary" size="sm" onClick={handleDownload}>
                  <Download className="mr-1 h-4 w-4" /> Download
                </Button>
              )}
            </div>
          }
        />

        {jobProgress !== null && (
          <div className="border-b border-blue-200 bg-blue-50 px-6 py-2 text-sm text-blue-800 dark:border-blue-900 dark:bg-blue-950 dark:text-blue-200">
            Job in progress… {jobProgress}%
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept=".zip"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && uploadMutation.mutate(e.target.files[0])}
        />

        {showGithub && (
          <div className="border-b border-gray-200 bg-gray-50 p-4 dark:border-gray-800 dark:bg-gray-900">
            <div className="flex gap-2">
              <Input placeholder="https://github.com/user/repo" value={githubUrl} onChange={(e) => setGithubUrl(e.target.value)} />
              <Button onClick={() => cloneMutation.mutate(githubUrl)} disabled={cloneMutation.isPending}>Clone</Button>
            </div>
          </div>
        )}

        <div className="flex border-b border-gray-200 dark:border-gray-800">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? "border-blue-600 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                <Icon className="h-4 w-4" /> {tab.label}
              </button>
            );
          })}
        </div>

        <main className="flex flex-1 overflow-hidden">
          {activeTab === "files" && (
            <div className="flex flex-1">
              <div className="w-80 overflow-y-auto border-r border-gray-200 p-4 dark:border-gray-800">
                <h3 className="mb-3 font-medium">Source Files ({files.length})</h3>
                <div className="space-y-1">
                  {files.map((file: { id: number; file_path: string; file_name: string; language?: string }) => (
                    <button
                      key={file.id}
                      onClick={() => { setSelectedFileId(file.id); setActiveTab("editor"); }}
                      className={`w-full rounded px-2 py-1.5 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-900 ${
                        selectedFileId === file.id ? "bg-blue-50 text-blue-700 dark:bg-blue-950" : ""
                      }`}
                    >
                      <p className="truncate font-mono text-xs">{file.file_name}</p>
                      {file.language && <p className="text-xs text-gray-500">{file.language}</p>}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex-1 p-6">
                <Card className="mb-4">
                  <CardHeader><CardTitle>Migration</CardTitle></CardHeader>
                  <CardContent className="space-y-4">
                    <select
                      className="w-full rounded-md border border-gray-300 p-2 dark:border-gray-700 dark:bg-gray-900"
                      value={MIGRATION_OPTIONS.indexOf(migrationType)}
                      onChange={(e) => setMigrationType(MIGRATION_OPTIONS[Number(e.target.value)])}
                    >
                      {MIGRATION_OPTIONS.map((opt, i) => (
                        <option key={i} value={i}>{opt.label}</option>
                      ))}
                    </select>
                    <Button onClick={() => migrateMutation.mutate()} disabled={migrateMutation.isPending || project?.status === "pending"}>
                      {migrateMutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <GitBranch className="mr-2 h-4 w-4" />}
                      Start Migration
                    </Button>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => aiApi.generateTests(projectId, { test_framework: "pytest" })}>
                        <TestTube className="mr-1 h-4 w-4" /> Generate Tests
                      </Button>
                      <Button variant="outline" size="sm" onClick={() => aiApi.generateDocs(projectId, ["readme", "api", "architecture"])}>
                        <FileText className="mr-1 h-4 w-4" /> Generate Docs
                      </Button>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader><CardTitle>Project Status</CardTitle></CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div><span className="text-gray-500">Status:</span> <span className="capitalize font-medium">{project?.status}</span></div>
                      <div><span className="text-gray-500">Files:</span> {project?.total_files}</div>
                      <div><span className="text-gray-500">Lines:</span> {project?.total_lines?.toLocaleString()}</div>
                      <div><span className="text-gray-500">Language:</span> {project?.source_language || "N/A"}</div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {activeTab === "editor" && selectedFile && (
            <div className="flex flex-1 flex-col p-4">
              <div className="mb-3 flex items-center justify-between">
                <p className="font-mono text-sm">{selectedFile.file_path}</p>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => explainMutation.mutate()} disabled={explainMutation.isPending}>
                    <Sparkles className="mr-1 h-4 w-4" /> Explain
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => aiApi.detectBugs(projectId, selectedFile.file_path, selectedFile.content || "")}>
                    <Bug className="mr-1 h-4 w-4" /> Find Bugs
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => aiApi.refactor(projectId, { file_path: selectedFile.file_path, code: selectedFile.content || "", refactor_type: "clean_code" })}>
                    <Wrench className="mr-1 h-4 w-4" /> Refactor
                  </Button>
                </div>
              </div>
              {explainResult && (
                <Card className="mb-4">
                  <CardContent className="pt-4">
                    <p className="text-sm"><strong>Purpose:</strong> {String(explainResult.purpose)}</p>
                    <p className="mt-2 text-sm"><strong>Complexity:</strong> {String(explainResult.complexity)}</p>
                  </CardContent>
                </Card>
              )}
              {selectedFile.migrated_content ? (
                <DiffViewer original={selectedFile.content || ""} modified={selectedFile.migrated_content} language={selectedFile.language} />
              ) : (
                <CodeEditor value={selectedFile.content || ""} language={selectedFile.language} readOnly />
              )}
            </div>
          )}

          {activeTab === "editor" && !selectedFile && (
            <div className="flex flex-1 items-center justify-center text-gray-500">Select a file to view</div>
          )}

          {activeTab === "chat" && (
            <div className="flex-1 p-4">
              <AIChat projectId={projectId} filePath={selectedFile?.file_path} />
            </div>
          )}

          {activeTab === "diagrams" && (
            <div className="flex-1 space-y-6 overflow-y-auto p-6">
              {diagrams ? (
                <>
                  {diagrams.flow_diagram && <DiagramViewer diagram={diagrams.flow_diagram} title="Flow Diagram" />}
                  {diagrams.dependency_graph && <DiagramViewer diagram={diagrams.dependency_graph} title="Dependency Graph" />}
                  {diagrams.class_diagram && <DiagramViewer diagram={diagrams.class_diagram} title="Class Diagram" />}
                  {diagrams.sequence_diagram && <DiagramViewer diagram={diagrams.sequence_diagram} title="Sequence Diagram" />}
                </>
              ) : (
                <div className="flex items-center justify-center py-12 text-gray-500">
                  Analyze the project first to generate diagrams
                </div>
              )}
            </div>
          )}

          {activeTab === "analysis" && (
            <div className="flex-1 overflow-y-auto p-6">
              {analysis ? (
                <div className="space-y-6">
                  <Card>
                    <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
                    <CardContent><p>{analysis.summary}</p></CardContent>
                  </Card>
                  <div className="grid gap-4 md:grid-cols-2">
                    <Card>
                      <CardHeader><CardTitle>Detected Stack</CardTitle></CardHeader>
                      <CardContent className="space-y-2 text-sm">
                        <p><strong>Language:</strong> {analysis.language}</p>
                        <p><strong>Framework:</strong> {analysis.framework || "N/A"}</p>
                        <p><strong>ORM:</strong> {analysis.orm || "N/A"}</p>
                        <p><strong>Complexity:</strong> {analysis.complexity_score}/10</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardHeader><CardTitle>Dependencies</CardTitle></CardHeader>
                      <CardContent>
                        <div className="flex flex-wrap gap-1">
                          {(analysis.dependencies || []).slice(0, 20).map((dep: string) => (
                            <span key={dep} className="rounded bg-gray-100 px-2 py-1 text-xs dark:bg-gray-800">{dep}</span>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                  {analysis.rest_apis?.length > 0 && (
                    <Card>
                      <CardHeader><CardTitle>REST APIs ({analysis.rest_apis.length})</CardTitle></CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {analysis.rest_apis.slice(0, 10).map((api: { method: string; path: string; file: string }, i: number) => (
                            <div key={i} className="flex gap-3 text-sm">
                              <span className="rounded bg-green-100 px-2 py-0.5 font-mono text-xs text-green-700">{api.method}</span>
                              <span className="font-mono">{api.path}</span>
                              <span className="text-gray-500">{api.file}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center py-12 text-gray-500">
                  Upload a project and run analysis to see results
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
