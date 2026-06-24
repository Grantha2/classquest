import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { NavBar } from "@/components/NavBar";
import { ProfileForm } from "./ProfileForm";
import type { UserProfile } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function ProfilePage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: profile } = await supabase
    .from("user_profile")
    .select("*")
    .eq("user_id", user.id)
    .maybeSingle();

  return (
    <div className="min-h-screen bg-slate-50">
      <NavBar email={user.email} />
      <main className="mx-auto max-w-2xl px-4 py-6">
        <h1 className="text-2xl font-bold text-slate-900">Your profile</h1>
        <p className="mb-6 mt-1 text-sm text-slate-500">
          The better this is, the smarter ClassQuest can rank postings for you.
        </p>
        <ProfileForm initialProfile={(profile as UserProfile) ?? null} />
      </main>
    </div>
  );
}
