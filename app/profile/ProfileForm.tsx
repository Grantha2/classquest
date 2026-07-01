"use client";

import { useRef, useState } from "react";
import type { UserProfile } from "@/lib/types";
import { DISTRICTS, SUBJECT_OPTIONS } from "@/lib/districts";

export function ProfileForm({
  initialProfile,
  userEmail,
}: {
  initialProfile: UserProfile | null;
  userEmail?: string | null;
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
  const [homeAddress, setHomeAddress] = useState(
    initialProfile?.home_address ?? "",
  );
  const [digestOptIn, setDigestOptIn] = useState(
    initialProfile?.digest_opt_in ?? false,
  );
  const [digestMinScore, setDigestMinScore] = useState(
    initialProfile?.digest_min_score ?? 7,
  );

  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Live completeness — these six fields are exactly what Claude scores against.
  const checklist: { label: string; done: boolean }[] = [
    { label: "Resume", done: Boolean(resumeText.trim()) },
    { label: "Subjects / specializations", done: subjects.length > 0 },
    { label: "Preferred districts", done: districts.length > 0 },
    { label: "Ideal role", done: Boolean(ideal.trim()) },
    { label: "Must-haves", done: Boolean(mustHaves.trim()) },
    { label: "Nice-to-haves", done: Boolean(niceToHaves.trim()) },
  ];
  const filled = checklist.filter((c) => c.done).length;

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
      setMessage("Resume parsed ✓ — hit Save profile to apply it to your scores.");
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
          home_address: homeAddress || null,
          digest_opt_in: digestOptIn,
          digest_min_score: digestMinScore,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Save failed.");
      if (data.scoring_changed && data.score_refresh_triggered) {
        setMessage(
          "Profile saved ✓ — re-scoring every posting against it now (scores update in about a minute).",
        );
      } else if (data.scoring_changed) {
        setMessage(
          "Profile saved ✓ — scores will re-personalize at the next scrape run (7am / 12pm / 5pm).",
        );
      } else {
        setMessage("Profile saved ✓");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Why this page matters */}
      <section className="rounded-2xl border border-sky-100 bg-sky-50 p-5">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-slate-900">
            This profile is what Claude ranks jobs against
          </h2>
          <span className="rounded-full bg-sky-600 px-3 py-1 text-xs font-bold text-white">
            {filled}/6 filled
          </span>
        </div>
        <p className="mt-1 text-sm text-slate-600">
          Scores personalize automatically after you save — every posting is
          re-scored against the fields below, and each job card shows{" "}
          <em>why</em> it got its score.
        </p>
        <ul className="mt-3 grid grid-cols-2 gap-1 text-sm sm:grid-cols-3">
          {checklist.map((c) => (
            <li
              key={c.label}
              className={c.done ? "text-grow-600" : "text-slate-500"}
            >
              {c.done ? "✓" : "○"} {c.label}
            </li>
          ))}
        </ul>
      </section>

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

      {/* Home base */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold text-slate-900">Home base</h2>
        <p className="mt-1 text-sm text-slate-500">
          A ZIP code or address. Used to filter postings “within N miles” and to
          center the map. We geocode it on save (not stored as exact address).
        </p>
        <input
          value={homeAddress}
          onChange={(e) => setHomeAddress(e.target.value)}
          placeholder="e.g. 60540 or 123 Main St, Naperville IL"
          className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-100"
        />
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
            placeholder="e.g. 2nd-4th grade general classroom in a collaborative school; strong literacy focus; open to bilingual programs"
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
            placeholder="e.g. full-time; grades 1-6 only; within commuting distance"
            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-100"
          />
        </div>
        <div>
          <label className="font-semibold text-slate-900">Nice-to-haves</label>
          <textarea
            value={niceToHaves}
            onChange={(e) => setNiceToHaves(e.target.value)}
            rows={2}
            placeholder="e.g. mentoring program, small class sizes, dual-language track"
            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-100"
          />
        </div>
      </section>

      {/* Daily email digest */}
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold text-slate-900">Daily email digest</h2>
        <p className="mt-1 text-sm text-slate-500">
          Get new high-match postings by email so you don’t have to check the
          site. Sent once a day from the morning scrape
          {userEmail ? (
            <>
              {" "}
              to <span className="font-medium text-slate-700">{userEmail}</span>
            </>
          ) : null}
          , and only when there’s something new worth seeing.
        </p>
        <label className="mt-3 flex cursor-pointer items-center gap-2 text-sm font-medium text-slate-700">
          <input
            type="checkbox"
            checked={digestOptIn}
            onChange={(e) => setDigestOptIn(e.target.checked)}
            className="accent-sky-600"
          />
          Email me new matches daily
        </label>
        {digestOptIn && (
          <div className="mt-3 flex items-center gap-2 text-sm text-slate-700">
            <span>Only include postings scoring at least</span>
            <select
              value={digestMinScore}
              onChange={(e) => setDigestMinScore(Number(e.target.value))}
              className="rounded-lg border border-slate-300 px-2 py-1 text-sm"
            >
              {[5, 6, 7, 8, 9].map((n) => (
                <option key={n} value={n}>
                  {n}/10
                </option>
              ))}
            </select>
          </div>
        )}
      </section>

      {message && <p className="text-sm font-medium text-grow-600">{message}</p>}
      {error && <p className="text-sm font-medium text-red-600">{error}</p>}

      <div className="flex items-center justify-end gap-3">
        <p className="text-xs text-slate-400">
          Saving re-scores your feed against this profile.
        </p>
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
