import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { NavBar } from "@/components/NavBar";
import { DashboardClient } from "./DashboardClient";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) redirect("/login");

  // Summary bar stats.
  const { count: newCount } = await supabase
    .from("job_postings")
    .select("*", { count: "exact", head: true })
    .eq("is_new", true)
    .eq("is_active", true);

  const { data: latest } = await supabase
    .from("job_postings")
    .select("scraped_at")
    .order("scraped_at", { ascending: false })
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
            {newCount ?? 0} new posting{newCount === 1 ? "" : "s"} today
            {latest?.scraped_at
              ? ` · Last updated ${new Date(latest.scraped_at).toLocaleString(
                  "en-US",
                  { dateStyle: "medium", timeStyle: "short" },
                )}`
              : ""}
          </p>
        </div>

        <DashboardClient />
      </main>
    </div>
  );
}
