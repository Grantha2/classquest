"use client";

import { useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import type {
  ApplicationStatus,
  JobFilters,
  JobPosting,
  JobsResponse,
  TrackerEntry,
  UserProfile,
} from "@/lib/types";
import { profileRichness, SCORING_FIELDS } from "@/lib/types";
import { FilterBar } from "@/components/FilterBar";
import { JobCard } from "@/components/JobCard";

const MapView = dynamic(() => import("@/components/MapView"), {
  ssr: false,
  loading: () => (
    <p className="py-12 text-center text-slate-400">Loading map…</p>
  ),
});

type HomeBase = { lat: number; lng: number } | null;

function buildQuery(
  filters: JobFilters,
  home: HomeBase,
  mapView: boolean,
): string {
  const p = new URLSearchParams();
  (filters.district ?? []).forEach((d) => p.append("district", d));
  (filters.grades ?? []).forEach((g) => p.append("grade", String(g)));
  if (filters.subject) p.set("subject", filters.subject);
  if (filters.minScore && filters.minScore > 1)
    p.set("minScore", String(filters.minScore));
  if (filters.isNew) p.set("isNew", "true");
  if (filters.bilingual) p.set("bilingual", "true");
  if (filters.employment) p.set("employment", filters.employment);
  if (filters.dateRange && filters.dateRange !== "all")
    p.set("dateRange", filters.dateRange);
  p.set("sortBy", filters.sortBy ?? "relevance");
  p.set("page", String(filters.page ?? 1));
  if (home && filters.radiusMi && filters.radiusMi > 0) {
    p.set("lat", String(home.lat));
    p.set("lng", String(home.lng));
    p.set("radius", String(filters.radiusMi));
  }
  if (mapView) p.set("all", "1");
  return p.toString();
}

export function DashboardClient() {
  const [filters, setFilters] = useState<JobFilters>({
    sortBy: "relevance",
    minScore: 1,
    page: 1,
  });
  const [view, setView] = useState<"list" | "map">("list");
  const [jobs, setJobs] = useState<JobPosting[]>([]);
  const [total, setTotal] = useState(0);
  const [home, setHome] = useState<HomeBase>(null);
  // null = profile not loaded yet (don't flash the "generic" banner)
  const [profile, setProfile] = useState<UserProfile | null | undefined>(
    undefined,
  );
  const [statusMap, setStatusMap] = useState<Record<string, ApplicationStatus>>(
    {},
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tracker statuses (for card state) + home base (for radius/map).
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

    fetch("/api/profile")
      .then((r) => (r.ok ? r.json() : { profile: null }))
      .then((data: { profile: UserProfile | null }) => {
        const p = data.profile;
        setProfile(p);
        if (p?.home_latitude != null && p?.home_longitude != null) {
          setHome({ lat: p.home_latitude, lng: p.home_longitude });
        }
      })
      .catch(() => setProfile(null));
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `/api/jobs?${buildQuery(filters, home, view === "map")}`,
      );
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
  }, [filters, home, view]);

  useEffect(() => {
    load();
  }, [load]);

  function update(next: Partial<JobFilters>) {
    setFilters((f) => ({ ...f, ...next, page: 1 }));
  }

  const homeBaseSet = home != null;
  // undefined = still loading; 0 filled fields = scores are generic.
  const richness = profile === undefined ? null : profileRichness(profile);

  return (
    <div className="space-y-5">
      {richness !== null && richness === 0 && (
        <div className="rounded-2xl border border-sunshine-100 bg-sunshine-100/60 px-5 py-4">
          <p className="font-semibold text-slate-800">
            ⚠️ Your scores are generic right now
          </p>
          <p className="mt-1 text-sm text-slate-600">
            Claude is ranking postings without knowing what you want.{" "}
            <Link href="/profile" className="font-semibold text-sky-700 underline">
              Fill out your profile
            </Link>{" "}
            (resume, subjects, ideal role…) and every posting re-scores against
            it automatically.
          </p>
        </div>
      )}

      <FilterBar
        filters={filters}
        onChange={update}
        homeBaseSet={homeBaseSet}
      />

      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">
          {loading
            ? "Loading…"
            : `${total} posting${total === 1 ? "" : "s"} match your filters`}
          {!loading && richness !== null && richness > 0 && (
            <span
              className="ml-2 inline-flex items-center gap-1 rounded-full bg-grow-100 px-2 py-0.5 text-xs font-semibold text-grow-600"
              title={`Ranked against your profile (${richness}/${SCORING_FIELDS.length} fields filled)`}
            >
              ✨ Ranked for you
            </span>
          )}
        </p>
        <div className="inline-flex rounded-lg border border-slate-300 p-0.5">
          {(["list", "map"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`rounded-md px-3 py-1 text-sm font-medium capitalize transition ${
                view === v
                  ? "bg-sky-600 text-white"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {!homeBaseSet && filters.radiusMi ? (
        <p className="rounded-lg bg-sunshine-100 px-4 py-2 text-sm text-sunshine-500">
          Set a home base on your{" "}
          <Link href="/profile" className="font-semibold underline">
            profile
          </Link>{" "}
          to filter by distance.
        </p>
      ) : null}

      {error && (
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {view === "map" ? (
        loading ? (
          <p className="py-12 text-center text-slate-400">Loading map…</p>
        ) : (
          <MapView jobs={jobs} home={home} />
        )
      ) : loading ? (
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
        <div className="grid gap-4">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              posting={job}
              initialStatus={statusMap[job.id] ?? null}
            />
          ))}
        </div>
      )}
    </div>
  );
}
