"use client";

import { useState } from "react";
import type { JobFilters } from "@/lib/types";
import { DISTRICTS, SUBJECT_OPTIONS } from "@/lib/districts";

export function FilterBar({
  filters,
  onChange,
}: {
  filters: JobFilters;
  onChange: (next: Partial<JobFilters>) => void;
}) {
  const [districtsOpen, setDistrictsOpen] = useState(false);
  const selectedDistricts = filters.district ?? [];

  function toggleDistrict(id: string) {
    const set = new Set(selectedDistricts);
    set.has(id) ? set.delete(id) : set.add(id);
    onChange({ district: Array.from(set) });
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-end gap-4">
        {/* District multi-select */}
        <div className="relative">
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            District
          </label>
          <button
            type="button"
            onClick={() => setDistrictsOpen((o) => !o)}
            className="min-w-[180px] rounded-lg border border-slate-300 px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
          >
            {selectedDistricts.length === 0
              ? "All districts"
              : `${selectedDistricts.length} selected`}
            <span className="float-right text-slate-400">▾</span>
          </button>
          {districtsOpen && (
            <div className="absolute z-10 mt-1 max-h-64 w-64 overflow-auto rounded-lg border border-slate-200 bg-white p-2 shadow-lg">
              {DISTRICTS.map((d) => (
                <label
                  key={d.district_id}
                  className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-slate-50"
                >
                  <input
                    type="checkbox"
                    checked={selectedDistricts.includes(d.district_id)}
                    onChange={() => toggleDistrict(d.district_id)}
                    className="accent-sky-600"
                  />
                  {d.name}
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Subject / specialization */}
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Specialization
          </label>
          <select
            value={filters.subject ?? ""}
            onChange={(e) =>
              onChange({ subject: e.target.value || undefined })
            }
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700"
          >
            <option value="">Any</option>
            {SUBJECT_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Min relevance slider */}
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Min relevance: {filters.minScore ?? 1}
          </label>
          <input
            type="range"
            min={1}
            max={10}
            value={filters.minScore ?? 1}
            onChange={(e) => onChange({ minScore: Number(e.target.value) })}
            className="w-40 accent-sky-600"
          />
        </div>

        {/* Date posted */}
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Date posted
          </label>
          <select
            value={filters.dateRange ?? "all"}
            onChange={(e) =>
              onChange({ dateRange: e.target.value as JobFilters["dateRange"] })
            }
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700"
          >
            <option value="all">All time</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
        </div>

        {/* Sort */}
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Sort by
          </label>
          <select
            value={filters.sortBy ?? "relevance"}
            onChange={(e) =>
              onChange({ sortBy: e.target.value as JobFilters["sortBy"] })
            }
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700"
          >
            <option value="relevance">Relevance score</option>
            <option value="date">Date posted (newest)</option>
          </select>
        </div>

        {/* New only toggle */}
        <label className="flex cursor-pointer items-center gap-2 pb-2 text-sm font-medium text-slate-700">
          <input
            type="checkbox"
            checked={filters.isNew ?? false}
            onChange={(e) => onChange({ isNew: e.target.checked || undefined })}
            className="accent-sky-600"
          />
          New only
        </label>
      </div>
    </div>
  );
}
