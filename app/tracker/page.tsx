import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { NavBar } from "@/components/NavBar";
import { TrackerBoard } from "./TrackerBoard";

export const dynamic = "force-dynamic";

export default async function TrackerPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  return (
    <div className="min-h-screen bg-slate-50">
      <NavBar email={user.email} />
      <main className="mx-auto max-w-6xl px-4 py-6">
        <h1 className="text-2xl font-bold text-slate-900">
          Application tracker
        </h1>
        <p className="mb-6 mt-1 text-sm text-slate-500">
          Drag a card between columns to update its status. Click a card to add
          notes.
        </p>
        <TrackerBoard />
      </main>
    </div>
  );
}
