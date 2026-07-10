import { create } from "zustand";

interface Project {
  id: number;
  name: string;
  description?: string;
  source_language?: string;
  target_language?: string;
  source_framework?: string;
  target_framework?: string;
  status: string;
  total_files: number;
  total_lines: number;
  complexity_score?: number;
  created_at: string;
  updated_at: string;
}

interface ProjectFile {
  id: number;
  project_id: number;
  file_path: string;
  file_name: string;
  language?: string;
  lines_of_code: number;
  complexity?: number;
  content?: string;
  migrated_content?: string;
}

interface ProjectState {
  currentProject: Project | null;
  selectedFile: ProjectFile | null;
  aiProvider: string;
  setCurrentProject: (project: Project | null) => void;
  setSelectedFile: (file: ProjectFile | null) => void;
  setAiProvider: (provider: string) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  currentProject: null,
  selectedFile: null,
  aiProvider: "openai",
  setCurrentProject: (project) => set({ currentProject: project }),
  setSelectedFile: (file) => set({ selectedFile: file }),
  setAiProvider: (provider) => set({ aiProvider: provider }),
}));
