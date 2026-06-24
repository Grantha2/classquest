import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

const PAGE_SIZE = 25;

export async function GET(request: NextRequest) {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const sp = request.nextUrl.searchParams;
  const districts = sp.getAll("district").filter(Boolean);
  const subject = sp.get("subject");
  const minScore = Number(sp.get("minScore") ?? "1");
  const isNew = sp.get("isNew") === "true";
  const dateRange = sp.get("dateRange"); // '7d' | '30d' | null
  const sortBy = sp.get("sortBy") ?? "relevance";
  const page = Math.max(1, Number(sp.get("page") ?? "1"));

  let query = supabase
    .from("job_postings")
    .select("*", { count: "exact" });

  if (districts.length > 0) {
    query = query.in("district_id", districts);
  }

  if (subject) {
    // Match the specialization against title / category / description text.
    query = query.or(
      `title.ilike.%${subject}%,category.ilike.%${subject}%,description.ilike.%${subject}%`,
    );
  }

  if (minScore > 1) {
    // Only apply when above the floor, so unscored postings still appear by default.
    query = query.gte("relevance_score", minScore);
  }

  if (isNew) {
    query = query.eq("is_new", true);
  }

  if (dateRange === "7d" || dateRange === "30d") {
    const days = dateRange === "7d" ? 7 : 30;
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
      .toISOString()
      .slice(0, 10);
    query = query.gte("posting_date", cutoff);
  }

  if (sortBy === "date") {
    query = query.order("posting_date", { ascending: false, nullsFirst: false });
  } else {
    query = query
      .order("relevance_score", { ascending: false, nullsFirst: false })
      .order("scraped_at", { ascending: false });
  }

  const from = (page - 1) * PAGE_SIZE;
  query = query.range(from, from + PAGE_SIZE - 1);

  const { data, error, count } = await query;

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({
    jobs: data ?? [],
    page,
    pageSize: PAGE_SIZE,
    total: count ?? 0,
  });
}
