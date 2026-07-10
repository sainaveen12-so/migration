import { lazy, Suspense, useState } from "react";
import { Loader2 } from "lucide-react";

const MonacoEditor = lazy(() => import("@monaco-editor/react"));

interface CodeEditorProps {
  value: string;
  language?: string;
  onChange?: (value: string | undefined) => void;
  readOnly?: boolean;
  height?: string;
}

const LANG_MAP: Record<string, string> = {
  java: "java",
  python: "python",
  javascript: "javascript",
  typescript: "typescript",
  csharp: "csharp",
  php: "php",
  sql: "sql",
  go: "go",
  ruby: "ruby",
  html: "html",
  css: "css",
  json: "json",
  yaml: "yaml",
};

function EditorLoading() {
  return (
    <div className="flex h-full items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
    </div>
  );
}

export function CodeEditor({ value, language = "python", onChange, readOnly = false, height = "500px" }: CodeEditorProps) {
  const [theme, setTheme] = useState<"vs-dark" | "light">("vs-dark");

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-800">
      <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-3 py-1 dark:border-gray-800 dark:bg-gray-900">
        <span className="text-xs text-gray-500">{language}</span>
        <button
          onClick={() => setTheme(theme === "vs-dark" ? "light" : "vs-dark")}
          className="text-xs text-gray-500 hover:text-gray-700"
        >
          Toggle Theme
        </button>
      </div>
      <Suspense fallback={<EditorLoading />}>
        <MonacoEditor
          height={height}
          language={LANG_MAP[language] || language}
          value={value}
          onChange={onChange}
          theme={theme}
          options={{
            readOnly,
            minimap: { enabled: true },
            fontSize: 14,
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            automaticLayout: true,
            wordWrap: "on",
          }}
        />
      </Suspense>
    </div>
  );
}

interface DiffViewerProps {
  original: string;
  modified: string;
  language?: string;
}

export function DiffViewer({ original, modified, language = "python" }: DiffViewerProps) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <div>
        <p className="mb-2 text-sm font-medium text-gray-500">Original</p>
        <CodeEditor value={original} language={language} readOnly height="400px" />
      </div>
      <div>
        <p className="mb-2 text-sm font-medium text-gray-500">Migrated</p>
        <CodeEditor value={modified} language={language} readOnly height="400px" />
      </div>
    </div>
  );
}
