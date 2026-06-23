import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export interface RecentJob {
  jobId: string;
  filename: string;
  charCount: number;
  chunkCount: number;
  createdAt: number;
  lastStatus?: string;
}

interface JobsState {
  recents: RecentJob[];
  addRecent: (job: RecentJob) => void;
  updateStatus: (jobId: string, status: string) => void;
  remove: (jobId: string) => void;
  clear: () => void;
}

export const useJobsStore = create<JobsState>()(
  persist(
    (set) => ({
      recents: [],
      addRecent: (job) =>
        set((state) => {
          const filtered = state.recents.filter((r) => r.jobId !== job.jobId);
          return { recents: [job, ...filtered].slice(0, 50) };
        }),
      updateStatus: (jobId, status) =>
        set((state) => ({
          recents: state.recents.map((r) =>
            r.jobId === jobId ? { ...r, lastStatus: status } : r,
          ),
        })),
      remove: (jobId) =>
        set((state) => ({ recents: state.recents.filter((r) => r.jobId !== jobId) })),
      clear: () => set({ recents: [] }),
    }),
    {
      name: 'PaperMind:recent-jobs',
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
