import type { ApplicationStatus } from "@/lib/types";

const STATUS_STYLES: Record<ApplicationStatus, { label: string; cls: string }> =
  {
    saved: { label: "Saved", cls: "bg-slate-100 text-slate-700" },
    applied: { label: "Applied", cls: "bg-sky-100 text-sky-700" },
    interviewing: {
      label: "Interviewing",
      cls: "bg-sunshine-100 text-sunshine-500",
    },
    offered: { label: "Offered", cls: "bg-grow-100 text-grow-600" },
    rejected: { label: "Rejected", cls: "bg-red-100 text-red-700" },
  };

export function StatusBadge({ status }: { status: ApplicationStatus }) {
  const s = STATUS_STYLES[status] ?? STATUS_STYLES.saved;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${s.cls}`}
    >
      {s.label}
    </span>
  );
}
