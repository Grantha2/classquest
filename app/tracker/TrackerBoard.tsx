"use client";

import { useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragEndEvent,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  APPLICATION_STATUSES,
  type ApplicationStatus,
  type TrackerEntry,
} from "@/lib/types";
import { RelevanceChip } from "@/components/RelevanceChip";

const COLUMN_LABELS: Record<ApplicationStatus, string> = {
  saved: "Saved",
  applied: "Applied",
  interviewing: "Interviewing",
  offered: "Offered",
  rejected: "Rejected",
};

function Card({
  entry,
  onClick,
}: {
  entry: TrackerEntry;
  onClick: () => void;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({ id: entry.id });
  const style = transform
    ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        opacity: isDragging ? 0.5 : 1,
      }
    : undefined;

  const job = entry.job_postings;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={onClick}
      className="cursor-grab rounded-xl border border-slate-200 bg-white p-3 shadow-sm active:cursor-grabbing"
    >
      <div className="mb-1.5">
        <RelevanceChip score={job?.relevance_score ?? null} />
      </div>
      <p className="text-sm font-semibold leading-snug text-slate-900">
        {job?.title ?? "Untitled posting"}
      </p>
      <p className="mt-1 text-xs text-slate-500">{job?.district_name}</p>
      {entry.notes && (
        <p className="mt-2 line-clamp-2 text-xs italic text-slate-400">
          {entry.notes}
        </p>
      )}
    </div>
  );
}

function Column({
  status,
  entries,
  onCardClick,
}: {
  status: ApplicationStatus;
  entries: TrackerEntry[];
  onCardClick: (e: TrackerEntry) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: status });
  return (
    <div className="flex w-64 flex-shrink-0 flex-col">
      <div className="mb-2 flex items-center justify-between px-1">
        <h2 className="text-sm font-semibold text-slate-700">
          {COLUMN_LABELS[status]}
        </h2>
        <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-600">
          {entries.length}
        </span>
      </div>
      <div
        ref={setNodeRef}
        className={`flex min-h-[120px] flex-1 flex-col gap-2 rounded-xl border-2 border-dashed p-2 transition ${
          isOver ? "border-sky-400 bg-sky-50" : "border-slate-200 bg-slate-100/50"
        }`}
      >
        {entries.map((e) => (
          <Card key={e.id} entry={e} onClick={() => onCardClick(e)} />
        ))}
      </div>
    </div>
  );
}

export function TrackerBoard() {
  const [entries, setEntries] = useState<TrackerEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<TrackerEntry | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
  );

  useEffect(() => {
    fetch("/api/tracker")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("Load failed"))))
      .then((data: { entries: TrackerEntry[] }) => setEntries(data.entries ?? []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const byStatus = useMemo(() => {
    const map: Record<ApplicationStatus, TrackerEntry[]> = {
      saved: [],
      applied: [],
      interviewing: [],
      offered: [],
      rejected: [],
    };
    for (const e of entries) (map[e.status] ?? map.saved).push(e);
    return map;
  }, [entries]);

  async function persist(entry: TrackerEntry, patch: Partial<TrackerEntry>) {
    const res = await fetch("/api/tracker", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_posting_id: entry.job_posting_id,
        status: patch.status ?? entry.status,
        notes: patch.notes ?? entry.notes ?? "",
      }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error ?? "Update failed.");
    }
  }

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over) return;
    const newStatus = over.id as ApplicationStatus;
    const entry = entries.find((e) => e.id === active.id);
    if (!entry || entry.status === newStatus) return;

    const prev = entries;
    setEntries((cur) =>
      cur.map((e) => (e.id === entry.id ? { ...e, status: newStatus } : e)),
    );
    try {
      await persist(entry, { status: newStatus });
    } catch (err) {
      setEntries(prev); // rollback
      setError(err instanceof Error ? err.message : "Update failed.");
    }
  }

  async function saveNotes(notes: string) {
    if (!selected) return;
    const prev = entries;
    setEntries((cur) =>
      cur.map((e) => (e.id === selected.id ? { ...e, notes } : e)),
    );
    setSelected(null);
    try {
      await persist(selected, { notes });
    } catch (err) {
      setEntries(prev);
      setError(err instanceof Error ? err.message : "Update failed.");
    }
  }

  if (loading) {
    return <p className="py-12 text-center text-slate-400">Loading board…</p>;
  }

  if (entries.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white py-16 text-center">
        <p className="text-lg font-medium text-slate-700">
          Nothing tracked yet.
        </p>
        <p className="mt-1 text-sm text-slate-500">
          Save or mark jobs as applied from the Jobs feed and they’ll show up
          here.
        </p>
      </div>
    );
  }

  return (
    <>
      {error && (
        <p className="mb-4 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
      <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {APPLICATION_STATUSES.map((status) => (
            <Column
              key={status}
              status={status}
              entries={byStatus[status]}
              onCardClick={setSelected}
            />
          ))}
        </div>
      </DndContext>

      {selected && (
        <NotesModal
          entry={selected}
          onClose={() => setSelected(null)}
          onSave={saveNotes}
        />
      )}
    </>
  );
}

function NotesModal({
  entry,
  onClose,
  onSave,
}: {
  entry: TrackerEntry;
  onClose: () => void;
  onSave: (notes: string) => void;
}) {
  const [notes, setNotes] = useState(entry.notes ?? "");
  const job = entry.job_postings;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-lg font-bold text-slate-900">{job?.title}</h3>
        <p className="mt-1 text-sm text-slate-500">
          {job?.district_name}
          {entry.applied_at
            ? ` · Applied ${new Date(entry.applied_at).toLocaleDateString()}`
            : ""}
        </p>
        <p className="mt-1 text-xs text-slate-400">
          Last updated {new Date(entry.updated_at).toLocaleString()}
        </p>

        <label className="mt-4 block text-sm font-medium text-slate-700">
          Notes
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={5}
          autoFocus
          className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-100"
          placeholder="Interview prep, contacts, follow-up dates…"
        />

        <div className="mt-4 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            onClick={() => onSave(notes)}
            className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700"
          >
            Save notes
          </button>
          {job?.external_url && (
            <a
              href={job.external_url}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg bg-grow-500 px-4 py-2 text-sm font-semibold text-white hover:bg-grow-600"
            >
              View Posting →
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
