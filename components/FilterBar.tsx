"use client";

import { useState } from "react";
import type { EmploymentType, JobFilters } from "@/lib/types";
import { DISTRICTS, SUBJECT_OPTIONS } from "@/lib/districts";

export function FilterBar({
  filters,
  onChange,
  homeBaseSet = false,
}: {
  filters: JobFilters;
  onChange: (next: Partial<JobFilters>) => void;
  homeBaseSet?: boolean;
}) {
  const [districtsOpen, setDistrictsOpen] = useState(false);
  const [gradesOpen, setGradesOpen] = useState(false);
  const selectedDistricts = filters.district ?? [];
  const selectedGrades = filters.grades ?? [];

  function toggleDistrict(id: string) {
    const set = new Set(selectedDistricts);
    set.has(id) ? set.delete(id) : set.add(id);
    onChange({ district: Array.from(set) });
  }

  function toggleGrade(g: number) {
    const set = new Set(selectedGrades);
    set.has(g) ? set.delete(g) : set.add(g);
    onChange({ grades: Array.from(set).sort((a, b) => a - b) });
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

        {/* Grade level */}
        <div className="relative">
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Grade
          </label>
          <button
            type="button"
            onClick={() => setGradesOpen((o) => !o)}
            className="min-w-[120px] rounded-lg border border-slate-300 px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
          >
            {selectedGrades.length === 0
              ? "All grades"
              : selectedGrades.map((g) => `${g}`).join(", ")}
            <span className="float-right text-slate-400">▾</span>
          </button>
          {gradesOpen && (
            <div className="absolute z-10 mt-1 w-40 rounded-lg border border-slate-200 bg-white p-2 shadow-lg">
              {[1, 2, 3, 4, 5, 6].map((g) => (
                <label
                  key={g}
                  className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-slate-50"
                >
                  <input
                    type="checkbox"
                    checked={selectedGrades.includes(g)}
                    onChange={() => toggleGrade(g)}
                    className="accent-sky-600"
                  />
                  Grade {g}
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

        {/* Full-time / part-time */}
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Schedule
          </label>
          <select
            value={filters.employment ?? ""}
            onChange={(e) =>
              onChange({
                employment: (e.target.value || undefined) as
                  | EmploymentType
                  | undefined,
              })
            }
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700"
            title="Postings that don't state a schedule are only shown under Any"
          >
            <option value="">Any</option>
            <option value="full_time">Full-time</option>
            <option value="part_time">Part-time</option>
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

        {/* Distance radius (needs a home base on the profile) */}
        <div>
          <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
            Within
          </label>
          <select
            value={filters.radiusMi ?? 0}
            onChange={(e) =>
              onChange({ radiusMi: Number(e.target.value) || undefined })
            }
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700"
            title={
              homeBaseSet
                ? undefined
                : "Set a home base on your profile to filter by distance"
            }
          >
            <option value={0}>Any distance</option>
            <option value={5}>5 miles</option>
            <option value={10}>10 miles</option>
            <option value={15}>15 miles</option>
            <option value={25}>25 miles</option>
            <option value={50}>50 miles</option>
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
            <option value="closing">Closing soon</option>
            {homeBaseSet && <option value="distance">Distance (nearest)</option>}
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

        {/* Bilingual toggle */}
        <label className="flex cursor-pointer items-center gap-2 pb-2 text-sm font-medium text-slate-700">
          <input
            type="checkbox"
            checked={filters.bilingual ?? false}
            onChange={(e) =>
              onChange({ bilingual: e.target.checked || undefined })
            }
            className="accent-sky-600"
          />
          Bilingual / dual language
        </label>
      </div>
    </div>
  );
}
