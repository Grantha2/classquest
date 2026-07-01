import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { distanceMiles } from "@/lib/geocode";
import type { JobPosting } from "@/lib/types";

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
  const bilingual = sp.get("bilingual") === "true";
  const employment = sp.get("employment"); // 'full_time' | 'part_time' | null
  const dateRange = sp.get("dateRange"); // '7d' | '30d' | null
  const sortBy = sp.get("sortBy") ?? "relevance";
  const page = Math.max(1, Number(sp.get("page") ?? "1"));
  const all = sp.get("all") === "1"; // map view: return all matches, unpaginated
  const ALL_CAP = 500;

  const lat = parseFloat(sp.get("lat") ?? "");
  const lng = parseFloat(sp.get("lng") ?? "");
  const radius = Number(sp.get("radius") ?? "0");
  const hasGeoFilter =
    Number.isFinite(lat) && Number.isFinite(lng) && radius > 0;

  let query = supabase
    .from("job_postings")
    .select("*", { count: "exact" })
    .eq("is_active", true); // hide closed/filled postings

  if (districts.length > 0) query = query.in("district_id", districts);
  const grades = sp
    .getAll("grade")
    .map((g) => parseInt(g, 10))
    .filter((g) => g >= 1 && g <= 6);
  if (grades.length > 0) {
    // posting matches if its grade_levels array overlaps the selected grades
    query = query.overlaps("grade_levels", grades);
  }
  if (subject) {
    query = query.or(
      `title.ilike.%${subject}%,category.ilike.%${subject}%,description.ilike.%${subject}%`,
    );
  }
  if (bilingual) {
    // Bilingual / dual-language roles are tagged in the title by the scrapers'
    // title filter, so a title match is reliable. Separate .or() groups AND.
    query = query.or("title.ilike.%bilingual%,title.ilike.%dual language%");
  }
  if (employment === "full_time" || employment === "part_time") {
    query = query.eq("employment_type", employment);
  }
  if (minScore > 1) query = query.gte("relevance_score", minScore);
  if (isNew) {
    // "New" = first seen in the last 24h (first_seen_at is immutable; is_new/
    // scraped_at are unreliable because scraped_at is refreshed every run).
    const cutoff = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    query = query.gte("first_seen_at", cutoff);
  }
  if (dateRange === "7d" || dateRange === "30d") {
    const days = dateRange === "7d" ? 7 : 30;
    const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
      .toISOString()
      .slice(0, 10);
    query = query.gte("posting_date", cutoff);
  }

  const applyOrder = (q: typeof query) => {
    if (sortBy === "date") {
      return q.order("posting_date", { ascending: false, nullsFirst: false });
    }
    if (sortBy === "closing") {
      // Soonest deadline first; postings without one sink to the bottom,
      // tie-broken by score.
      return q
        .order("closing_date", { ascending: true, nullsFirst: false })
        .order("relevance_score", { ascending: false, nullsFirst: false });
    }
    return q
      .order("relevance_score", { ascending: false, nullsFirst: false })
      .order("scraped_at", { ascending: false });
  };

  // ── Geo path: bounding-box prefilter in SQL, exact distance in JS ──
  if (hasGeoFilter) {
    const latDelta = radius / 69; // ~69 miles per degree latitude
    const lngDelta =
      radius / (69 * Math.max(Math.cos((lat * Math.PI) / 180), 0.01));

    query = query
      .not("latitude", "is", null)
      .gte("latitude", lat - latDelta)
      .lte("latitude", lat + latDelta)
      .gte("longitude", lng - lngDelta)
      .lte("longitude", lng + lngDelta);

    const { data, error } = await applyOrder(query).limit(1000);
    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    let jobs: JobPosting[] = (data ?? [])
      .map((j) => ({
        ...j,
        distance_mi: distanceMiles(lat, lng, j.latitude, j.longitude),
      }))
      .filter((j) => (j.distance_mi ?? Infinity) <= radius);

    if (sortBy === "distance") {
      jobs.sort((a, b) => (a.distance_mi ?? 0) - (b.distance_mi ?? 0));
    }

    const total = jobs.length;
    if (!all) {
      const from = (page - 1) * PAGE_SIZE;
      jobs = jobs.slice(from, from + PAGE_SIZE);
    } else {
      jobs = jobs.slice(0, ALL_CAP);
    }
    return NextResponse.json({ jobs, page, pageSize: PAGE_SIZE, total });
  }

  // ── Non-geo path: SQL ordering + pagination ──
  const ordered = applyOrder(query);
  const from = (page - 1) * PAGE_SIZE;
  const { data, error, count } = all
    ? await ordered.limit(ALL_CAP)
    : await ordered.range(from, from + PAGE_SIZE - 1);

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
