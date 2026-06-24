"use client";

import { useCallback, useEffect, useState } from "react";
import type {
  ApplicationStatus,
  JobFilters,
  JobPosting,
  JobsResponse,
  TrackerEntry,
} from "@/lib/types";
import { FilterBar } from "@/components/FilterBar";
import { JobCard } from "@/components/JobCard";

function buildQuery(filters: JobFilters): string {
  const p = new URLSearchParams();
  (filters.district ?? []).forEach((d) => p.append("district", d));
  if (filters.subject) p.set("subject", filters.subject);
  if (filters.minScore && filters.minScore > 1)
    p.set("minScore", String(filters.minScore));
  if (filters.isNew) p.set("isNew", "true");
  if (filters.dateRange && filters.dateRange !== "all")
    p.set("dateRange", filters.dateRange);
  p.set("sortBy", filters.sortBy ?? "relevance");
  p.set("page", String(filters.page ?? 1));
  return p.toString();
}

export function DashboardClient() {
  const [filters, setFilters] = useState<JobFilters>({
    sortBy: "relevance",
    minScore: 1,
    page: 1,
  });
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [total, setTotal] = useState(0);
  const [statusMap, setStatusMap] = useState<Record<string, ApplicationStatus>>(
    {},
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load tracker statuses once so cards can show current state.
  useEffect(() => {
    fetch("/api/tracker")
      .then((r) => (r.ok ? r.json() : { entries: [] }))
      .then((data: { entries: TrackerEntry[] }) => {
        const map: Record<string, ApplicationStatus> = {};
        (data.entries ?? []).forEach((e) => {
          map[e.job_posting_id] = e.status;
        });
        setStatusMap(map);
      })
      .catch(() => void 0);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/jobs?${buildQuery(filters)}`);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error ?? "Could not load jobs.");
      }
      const data: JobsResponse = await res.json();
      setJobs(data.jobs);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  function update(next: Partial<JobFilters>) {
    setFilters((f) => ({ ...f, ...next, page: 1 }));
  }

  return (
    <div className="space-y-5">
      <FilterBar filters={filters} onChange={update} />

      {error && (
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {loading ? (
        <p className="py-12 text-center text-slate-400">Loading postings…</p>
      ) : jobs.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white py-16 text-center">
          <p className="text-lg font-medium text-slate-700">
            No postings found yet.
          </p>
          <p className="mt-1 text-sm text-slate-500">
            Scrapers run at 7am, 12pm, and 5pm daily.
          </p>
        </div>
      ) : (
        <>
          <p className="text-sm text-slate-500">
            {total} posting{total === 1 ? "" : "s"} match your filters
          </p>
          <div className="grid gap-4">
            {jobs.map((job) => (
              <JobCard
                key={job.id}
                posting={job}
                initialStatus={statusMap[job.id] ?? null}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
