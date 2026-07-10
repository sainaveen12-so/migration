import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          original.headers.Authorization = `Bearer ${data.access_token}`;
          return api(original);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      } else {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post("/auth/register", data),
  forgotPassword: (email: string) => api.post("/auth/forgot-password", { email }),
  resetPassword: (token: string, new_password: string) =>
    api.post("/auth/reset-password", { token, new_password }),
};

// Projects
export const projectsApi = {
  list: () => api.get("/projects"),
  get: (id: number) => api.get(`/projects/${id}`),
  create: (data: Record<string, unknown>) => api.post("/projects", data),
  update: (id: number, data: Record<string, unknown>) => api.patch(`/projects/${id}`, data),
  delete: (id: number) => api.delete(`/projects/${id}`),
  upload: (id: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post(`/projects/${id}/upload`, form);
  },
  cloneGithub: (id: number, data: { github_url: string; branch?: string; name?: string }) =>
    api.post(`/projects/${id}/clone-github`, data),
  analyze: (id: number, async_mode = true) =>
    api.post(`/projects/${id}/analyze`, null, { params: { async_mode } }),
  migrate: (id: number, data: { target_language: string; target_framework?: string; migration_type: string }) =>
    api.post(`/projects/${id}/migrate`, data),
  getFiles: (id: number) => api.get(`/projects/${id}/files`),
  getFile: (id: number, fileId: number) => api.get(`/projects/${id}/files/${fileId}`),
  getAnalysis: (id: number) => api.get(`/projects/${id}/analysis`),
  getVersions: (id: number) => api.get(`/projects/${id}/versions`),
  download: (id: number) => api.get(`/projects/${id}/download`, { responseType: "blob" }),
};

// AI
export const aiApi = {
  listProviders: () => api.get("/ai/providers"),
  switchProvider: (provider: string, model?: string) =>
    api.post("/ai/providers/switch", { provider, model }),
  chat: (projectId: number, content: string, file_path?: string) =>
    api.post(`/ai/projects/${projectId}/chat`, { content, file_path }),
  getChatHistory: (projectId: number) => api.get(`/ai/projects/${projectId}/chat`),
  explain: (projectId: number, file_path: string, code?: string) =>
    api.post(`/ai/projects/${projectId}/explain`, { file_path, code }),
  refactor: (projectId: number, data: { file_path: string; code: string; refactor_type: string }) =>
    api.post(`/ai/projects/${projectId}/refactor`, data),
  detectBugs: (projectId: number, file_path: string, code: string) =>
    api.post(`/ai/projects/${projectId}/bugs`, { file_path, code }),
  generateTests: (projectId: number, data: Record<string, unknown>) =>
    api.post(`/ai/projects/${projectId}/generate-tests`, data),
  generateDocs: (projectId: number, doc_types: string[]) =>
    api.post(`/ai/projects/${projectId}/generate-docs`, { doc_types }),
  getDiagrams: (projectId: number) => api.get(`/ai/projects/${projectId}/diagrams`),
};

// Dashboard
export const dashboardApi = {
  getStats: () => api.get("/dashboard/stats"),
  getJob: (jobId: number) => api.get(`/jobs/${jobId}`),
  getProjectJobs: (projectId: number) => api.get(`/jobs/project/${projectId}`),
  getNotifications: (unread_only = false) =>
    api.get("/notifications", { params: { unread_only } }),
  markNotificationRead: (id: number) => api.patch(`/notifications/${id}/read`),
  search: (q: string) => api.get("/search", { params: { q } }),
  health: () => api.get("/health"),
};
