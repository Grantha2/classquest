import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { APPLICATION_STATUSES, type ApplicationStatus } from "@/lib/types";

export async function GET() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { data, error } = await supabase
    .from("application_tracker")
    .select("*, job_postings(*)")
    .eq("user_id", user.id)
    .order("updated_at", { ascending: false });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ entries: data ?? [] });
}

export async function POST(request: NextRequest) {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let body: {
    job_posting_id?: string;
    status?: ApplicationStatus;
    notes?: string;
  };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  if (!body.job_posting_id) {
    return NextResponse.json(
      { error: "job_posting_id is required" },
      { status: 400 },
    );
  }
  const status = body.status ?? "saved";
  if (!APPLICATION_STATUSES.includes(status)) {
    return NextResponse.json({ error: "Invalid status" }, { status: 400 });
  }

  const row: Record<string, unknown> = {
    user_id: user.id,
    job_posting_id: body.job_posting_id,
    status,
    updated_at: new Date().toISOString(),
  };
  if (body.notes !== undefined) row.notes = body.notes;
  if (status === "applied") row.applied_at = new Date().toISOString();

  const { data, error } = await supabase
    .from("application_tracker")
    .upsert(row, { onConflict: "user_id,job_posting_id" })
    .select("*, job_postings(*)")
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ entry: data });
}
