import { dashboardApi } from "@/lib/api";

export interface JobStatus {
  id: number;
  project_id: number;
  job_type: string;
  status: string;
  progress: number;
  error_message?: string | null;
}

const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);

export async function pollJobUntilDone(
  jobId: number,
  options?: { intervalMs?: number; maxAttempts?: number; onProgress?: (job: JobStatus) => void }
): Promise<JobStatus> {
  const intervalMs = options?.intervalMs ?? 2000;
  const maxAttempts = options?.maxAttempts ?? 150;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const { data } = await dashboardApi.getJob(jobId);
    const job = data as JobStatus;
    options?.onProgress?.(job);

    if (TERMINAL_STATUSES.has(job.status)) {
      if (job.status === "failed") {
        throw new Error(job.error_message || "Job failed");
      }
      return job;
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error("Job timed out");
}
