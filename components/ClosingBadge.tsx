// "Closes in N days" chip — shared by the job feed and the tracker.
// Urgency colors: red <= 3 days, amber <= 7, slate otherwise. Postings with a
// past closing date show "closed" (the scraper usually retires these, but a
// tracked posting can outlive its deadline).

export function daysUntil(isoDate: string | null | undefined): number | null {
  if (!isoDate) return null;
  const target = new Date(`${isoDate}T23:59:59`);
  if (isNaN(target.getTime())) return null;
  return Math.ceil((target.getTime() - Date.now()) / (24 * 60 * 60 * 1000));
}

export function ClosingBadge({ closingDate }: { closingDate: string | null | undefined }) {
  const days = daysUntil(closingDate);
  if (days === null) return null;

  let text: string;
  let cls: string;
  if (days < 0) {
    text = "Closed";
    cls = "bg-slate-200 text-slate-500";
  } else if (days === 0) {
    text = "Closes today";
    cls = "bg-red-100 text-red-700";
  } else if (days <= 3) {
    text = `Closes in ${days} day${days === 1 ? "" : "s"}`;
    cls = "bg-red-100 text-red-700";
  } else if (days <= 7) {
    text = `Closes in ${days} days`;
    cls = "bg-sunshine-100 text-sunshine-500";
  } else {
    const date = new Date(`${closingDate}T00:00:00`).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
    text = `Closes ${date}`;
    cls = "bg-slate-100 text-slate-600";
  }

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${cls}`}
    >
      ⏳ {text}
    </span>
  );
}
