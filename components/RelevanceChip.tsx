// Color-coded relevance score chip.
// 🟢 green 8-10 · 🟡 yellow 5-7 · ⚪ gray 1-4 · "—" when unscored.
export function RelevanceChip({ score }: { score: number | null }) {
  if (score == null) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-400">
        ⏳ Scoring…
      </span>
    );
  }

  let cls = "bg-slate-100 text-slate-600";
  let dot = "⚪";
  if (score >= 8) {
    cls = "bg-grow-100 text-grow-600";
    dot = "🟢";
  } else if (score >= 5) {
    cls = "bg-sunshine-100 text-sunshine-500";
    dot = "🟡";
  }

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${cls}`}
      title="Relevance score (1-10) from Claude"
    >
      {dot} {score}/10
    </span>
  );
}
