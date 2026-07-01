"use client";

import { useState } from "react";
import type { ApplicationStatus, JobPosting } from "@/lib/types";
import { ClosingBadge } from "./ClosingBadge";
import { RelevanceChip } from "./RelevanceChip";
import { StatusBadge } from "./StatusBadge";

function formatDate(d: string | null): string {
  if (!d) return "—";
  // Date-only strings ("2026-07-01") parse as UTC midnight, which renders as
  // the PREVIOUS day in Chicago. Append a time so it parses as local.
  const date = new Date(/^\d{4}-\d{2}-\d{2}$/.test(d) ? `${d}T00:00:00` : d);
  if (isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function JobCard({
  posting,
  initialStatus = null,
}: {
  posting: JobPosting;
  initialStatus?: ApplicationStatus | null;
}) {
  const [status, setStatus] = useState<ApplicationStatus | null>(initialStatus);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // "New" = first seen in the last 24h (immutable first_seen_at).
  const isNew =
    posting.first_seen_at != null &&
    Date.now() - Date.parse(posting.first_seen_at) < 24 * 60 * 60 * 1000;

  async function track(next: ApplicationStatus) {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/tracker", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_posting_id: posting.id, status: next }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error ?? "Could not update tracker.");
      }
      setStatus(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        {isNew && (
          <span className="rounded-full bg-sky-500 px-2.5 py-1 text-xs font-bold uppercase tracking-wide text-white">
            New
          </span>
        )}
        <RelevanceChip score={posting.relevance_score} />
        <ClosingBadge closingDate={posting.closing_date} />
        {posting.distance_mi != null && (
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
            📍 {posting.distance_mi.toFixed(1)} mi
          </span>
        )}
        {status && <StatusBadge status={status} />}
      </div>

      <h3 className="text-lg font-bold leading-snug text-slate-900">
        {posting.title}
      </h3>

      <p className="mt-1 text-sm text-slate-500">
        <span className="font-medium text-slate-700">
          {posting.district_name}
        </span>
        {posting.location ? ` · ${posting.location}` : ""} · Posted{" "}
        {formatDate(posting.posting_date)}
      </p>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        {posting.category && (
          <span className="inline-block rounded-md bg-sky-50 px-2 py-0.5 text-xs font-medium text-sky-700">
            {posting.category}
          </span>
        )}
        {posting.grade_levels && posting.grade_levels.length > 0 && (
          <span className="inline-block rounded-md bg-grow-100 px-2 py-0.5 text-xs font-medium text-grow-600">
            Grade{posting.grade_levels.length > 1 ? "s" : ""}{" "}
            {posting.grade_levels.join(", ")}
          </span>
        )}
        {posting.employment_type && (
          <span className="inline-block rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
            {posting.employment_type === "full_time" ? "Full-time" : "Part-time"}
          </span>
        )}
      </div>

      {posting.relevance_reason && (
        <div className="mt-3 rounded-lg border-l-4 border-sky-500 bg-sky-50 px-3 py-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-sky-600">
            Why this score
          </p>
          <p className="mt-0.5 text-sm text-slate-700">
            {posting.relevance_reason}
          </p>
        </div>
      )}

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <button
          onClick={() => track("saved")}
          disabled={busy || status === "saved"}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
        >
          {status === "saved" ? "Saved ✓" : "Save"}
        </button>
        <button
          onClick={() => track("applied")}
          disabled={busy || status === "applied"}
          className="rounded-lg bg-grow-500 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-grow-600 disabled:opacity-50"
        >
          {status === "applied" ? "Applied ✓" : "Mark Applied"}
        </button>
        <a
          href={posting.external_url}
          target="_blank"
          rel="noopener noreferrer"
          className="ml-auto rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-semibold text-white transition hover:bg-sky-700"
        >
          View Posting →
        </a>
      </div>
    </article>
  );
}
