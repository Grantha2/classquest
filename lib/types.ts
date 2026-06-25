// ClassQuest — shared TypeScript types.
// These mirror the Supabase schema (see supabase/schema.sql).

export type ApplicationStatus =
  | "saved"
  | "applied"
  | "interviewing"
  | "offered"
  | "rejected";

export const APPLICATION_STATUSES: ApplicationStatus[] = [
  "saved",
  "applied",
  "interviewing",
  "offered",
  "rejected",
];

export interface JobPosting {
  id: string;
  district_id: string;
  district_name: string;
  title: string;
  description: string | null;
  category: string | null;
  location: string | null;
  posting_date: string | null; // ISO date
  closing_date: string | null; // ISO date
  external_url: string;
  external_id: string | null;
  is_new: boolean;
  scraped_at: string; // ISO timestamp
  relevance_score: number | null; // 1-10
  relevance_reason: string | null;
  latitude: number | null;
  longitude: number | null;
  geocoded_address: string | null;
  // Computed by /api/jobs when a home-base radius filter is active.
  distance_mi?: number | null;
}

export interface UserProfile {
  id?: string;
  user_id: string;
  resume_text: string | null;
  target_subjects: string[] | null;
  preferred_districts: string[] | null;
  ideal_role_description: string | null;
  must_haves: string | null;
  nice_to_haves: string | null;
  home_address: string | null;
  home_latitude: number | null;
  home_longitude: number | null;
  updated_at?: string;
}

export interface TrackerEntry {
  id: string;
  user_id: string;
  job_posting_id: string;
  status: ApplicationStatus;
  notes: string | null;
  applied_at: string | null;
  updated_at: string;
  // joined posting (from GET /api/tracker)
  job_postings?: JobPosting | null;
}

// ── Dashboard filter query shape ──
export interface JobFilters {
  district?: string[];
  subject?: string;
  minScore?: number;
  isNew?: boolean;
  dateRange?: "all" | "7d" | "30d";
  sortBy?: "relevance" | "date" | "distance";
  radiusMi?: number; // within N miles of the user's home base
  page?: number;
}

export interface JobsResponse {
  jobs: JobPosting[];
  page: number;
  pageSize: number;
  total: number;
}
