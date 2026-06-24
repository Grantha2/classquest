// ClassQuest wordmark + mascot glyph.
export function Logo({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const dim = size === "lg" ? 44 : size === "sm" ? 28 : 36;
  const text =
    size === "lg" ? "text-3xl" : size === "sm" ? "text-lg" : "text-xl";
  return (
    <div className="flex items-center gap-2.5">
      <svg
        width={dim}
        height={dim}
        viewBox="0 0 40 40"
        fill="none"
        aria-hidden="true"
      >
        <rect width="40" height="40" rx="10" fill="#3b82f6" />
        {/* graduation cap */}
        <path d="M20 11L31 16L20 21L9 16L20 11Z" fill="#fbbf24" />
        <path
          d="M13 18.5V24C13 24 16 26.5 20 26.5C24 26.5 27 24 27 24V18.5"
          stroke="white"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path d="M31 16V22" stroke="white" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <span className={`${text} font-bold tracking-tight text-slate-900`}>
        Class<span className="text-sky-600">Quest</span>
      </span>
    </div>
  );
}
