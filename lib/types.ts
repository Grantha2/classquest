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

export type EmploymentType = "full_time" | "part_time";

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
  employment_type: EmploymentType | null; // null = not stated in the posting
  external_url: string;
  external_id: string | null;
  is_new: boolean;
  first_seen_at: string | null; // immutable; basis for the "new" badge
  scraped_at: string; // ISO timestamp
  relevance_score: number | null; // 1-10
  relevance_reason: string | null;
  grade_levels: number[] | null; // grades 1-6 named in the title
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
  // Daily email digest (sent by the scrape cron)
  digest_opt_in?: boolean;
  digest_min_score?: number;
  digest_last_sent_at?: string | null;
  updated_at?: string;
}

// The scoring-relevant profile fields. Filled count drives the profile
// completeness meter and the dashboard's personalized-vs-generic state —
// mirrors scrapers/run_all._profile_richness.
export const SCORING_FIELDS = [
  "resume_text",
  "target_subjects",
  "preferred_districts",
  "ideal_role_description",
  "must_haves",
  "nice_to_haves",
] as const;

export function profileRichness(p: Partial<UserProfile> | null): number {
  if (!p) return 0;
  let n = 0;
  for (const f of SCORING_FIELDS) {
    const v = p[f];
    if (Array.isArray(v) ? v.length > 0 : Boolean(v && String(v).trim())) n++;
  }
  return n;
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
  grades?: number[]; // grade levels 1-6
  subject?: string;
  minScore?: number;
  isNew?: boolean;
  bilingual?: boolean; // bilingual / dual-language postings only
  employment?: EmploymentType; // FT/PT (postings with unknown type are excluded)
  dateRange?: "all" | "7d" | "30d";
  sortBy?: "relevance" | "date" | "distance" | "closing";
  radiusMi?: number; // within N miles of the user's home base
  page?: number;
}

export interface JobsResponse {
  jobs: JobPosting[];
  page: number;
  pageSize: number;
  total: number;
}
