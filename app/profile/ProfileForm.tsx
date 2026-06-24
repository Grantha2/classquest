"use client";

import { useRef, useState } from "react";
import type { UserProfile } from "@/lib/types";
import { DISTRICTS, SUBJECT_OPTIONS } from "@/lib/districts";

export function ProfileForm({
  initialProfile,
}: {
  initialProfile: UserProfile | null;
}) {
  const [subjects, setSubjects] = useState<string[]>(
    initialProfile?.target_subjects ?? [],
  );
  const [subjectInput, setSubjectInput] = useState("");
  const [districts, setDistricts] = useState<string[]>(
    initialProfile?.preferred_districts ?? [],
  );
  const [ideal, setIdeal] = useState(
    initialProfile?.ideal_role_description ?? "",
  );
  const [mustHaves, setMustHaves] = useState(initialProfile?.must_haves ?? "");
  const [niceToHaves, setNiceToHaves] = useState(
    initialProfile?.nice_to_haves ?? "",
  );
  const [resumeText, setResumeText] = useState(
    initialProfile?.resume_text ?? "",
  );

  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function addSubject(value: string) {
    const v = value.trim();
    if (v && !subjects.includes(v)) setSubjects([...subjects, v]);
    setSubjectInput("");
  }

  function toggleDistrict(id: string) {
    setDistricts((cur) =>
      cur.includes(id) ? cur.filter((d) => d !== id) : [...cur, id],
    );
  }

  async function handleResumeUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    setMessage(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch("/api/profile/resume", {
        method: "POST",
        body: fd,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Upload failed.");
      setResumeText(data.resume_text);
      setMessage("Resume parsed and saved ✓");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function save() {
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const res = await fetch("/api/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText || null,
          target_subjects: subjects,
          preferred_districts: districts,
          ideal_role_description: ideal || null,
          must_haves: mustHaves || null,
          nice_to_haves: niceToHaves || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Save failed.");
      setMessage("Profile saved ✓");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Resume upload */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold text-slate-900">Resume</h2>
        <p className="mt-1 text-sm text-slate-500">
          Upload a PDF — we extract the text to help Claude rank jobs. The file
          itself is never stored.
        </p>
        <div className="mt-3 flex items-center gap-3">
          <input
            ref={fileRef}
            type="file"
            accept="application/pdf"
            onChange={handleResumeUpload}
            disabled={uploading}
            className="text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-sky-50 file:px-3 file:py-2 file:text-sm file:font-medium file:text-sky-700 hover:file:bg-sky-100"
          />
          {uploading && (
            <span className="text-sm text-slate-400">Parsing…</span>
          )}
        </div>
        {resumeText && (
          <p className="mt-3 line-clamp-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
            {resumeText.slice(0, 300)}
            {resumeText.length > 300 ? "…" : ""}
          </p>
        )}
      </section>

      {/* Target subjects */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold text-slate-900">
          Target subjects / specializations
        </h2>
        <div className="mt-3 flex flex-wrap gap-2">
          {subjects.map((s) => (
            <span
              key={s}
              className="inline-flex items-center gap-1 rounded-full bg-sky-100 px-3 py-1 text-sm text-sky-700"
            >
              {s}
              <button
                onClick={() => setSubjects(subjects.filter((x) => x !== s))}
                className="text-sky-400 hover:text-sky-700"
                aria-label={`Remove ${s}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
        <div className="mt-3 flex gap-2">
          <input
            list="subject-options"
            value={subjectInput}
            onChange={(e) => setSubjectInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                addSubject(subjectInput);
              }
            }}
            placeholder="Type and press Enter (e.g. Reading Specialist)"
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-100"
          />
          <datalist id="subject-options">
            {SUBJECT_OPTIONS.map((s) => (
              <option key={s} value={s} />
            ))}
          </datalist>
          <button
            onClick={() => addSubject(subjectInput)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Add
          </button>
        </div>
      </section>

      {/* Preferred districts */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold text-slate-900">Preferred districts</h2>
        <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {DISTRICTS.map((d) => (
            <label
              key={d.district_id}
              className="flex cursor-pointer items-center gap-2 text-sm text-slate-700"
            >
              <input
                type="checkbox"
                checked={districts.includes(d.district_id)}
                onChange={() => toggleDistrict(d.district_id)}
                className="accent-sky-600"
              />
              {d.name}
            </label>
          ))}
        </div>
      </section>

      {/* Freeform fields */}
      <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div>
          <label className="font-semibold text-slate-900">
            Describe your ideal elementary teaching role
          </label>
          <textarea
            value={ideal}
            onChange={(e) => setIdeal(e.target.value)}
            rows={3}
            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-100"
          />
        </div>
        <div>
          <label className="font-semibold text-slate-900">
            Must-haves in a position
          </label>
          <textarea
            value={mustHaves}
            onChange={(e) => setMustHaves(e.target.value)}
            rows={2}
            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-100"
          />
        </div>
        <div>
          <label className="font-semibold text-slate-900">Nice-to-haves</label>
          <textarea
            value={niceToHaves}
            onChange={(e) => setNiceToHaves(e.target.value)}
            rows={2}
            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-100"
          />
        </div>
      </section>

      {message && <p className="text-sm font-medium text-grow-600">{message}</p>}
      {error && <p className="text-sm font-medium text-red-600">{error}</p>}

      <div className="flex justify-end">
        <button
          onClick={save}
          disabled={saving}
          className="rounded-lg bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:opacity-60"
        >
          {saving ? "Saving…" : "Save profile"}
        </button>
      </div>
    </div>
  );
}
