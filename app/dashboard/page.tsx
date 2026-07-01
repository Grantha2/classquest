import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { NavBar } from "@/components/NavBar";
import { DashboardClient } from "./DashboardClient";

export const dynamic = "force-dynamic";
// Never serve cached Supabase reads here — the header must reflect the live DB
// after each scrape (Next caches server-component fetches even on dynamic routes).
export const fetchCache = "force-no-store";

export default async function DashboardPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/login");

  // Scrape-driven freshness: the latest recorded run.
  const { data: lastRun } = await supabase
    .from("scrape_runs")
    .select("run_at, new_postings, active_total")
    .order("run_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  const friendlyName = user.email?.split("@")[0] ?? "there";

  return (
    <div className="min-h-screen bg-slate-50">
      <NavBar email={user.email} />
      <main className="mx-auto max-w-5xl px-4 py-6">
        <div className="mb-5">
          <h1 className="text-2xl font-bold text-slate-900">
            Welcome back, {friendlyName} 👋
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            {lastRun
              ? `${lastRun.active_total ?? 0} active posting${
                  lastRun.active_total === 1 ? "" : "s"
                } · ${lastRun.new_postings ?? 0} new in the latest scrape · Last scraped ${new Date(
                  lastRun.run_at,
                ).toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" })}`
              : "Scrapers run at 7am, 12pm, and 5pm daily."}
          </p>
        </div>

        <DashboardClient />
      </main>
    </div>
  );
}
