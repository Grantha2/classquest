import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { geocodeAddress } from "@/lib/geocode";
import { triggerScrapeWorkflow } from "@/lib/github";
import type { UserProfile } from "@/lib/types";

export async function GET() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { data, error } = await supabase
    .from("user_profile")
    .select("*")
    .eq("user_id", user.id)
    .maybeSingle();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json({ profile: data ?? null });
}

// Fields the Claude scorer reads — a change to any of these makes existing
// scores stale, so we kick the scrape workflow to re-score right away.
const SCORING_FIELDS = [
  "resume_text",
  "target_subjects",
  "preferred_districts",
  "ideal_role_description",
  "must_haves",
  "nice_to_haves",
] as const;

function normalize(v: unknown): string {
  if (v == null) return "";
  if (Array.isArray(v)) return JSON.stringify(v);
  return String(v);
}

export async function POST(request: NextRequest) {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let body: Partial<UserProfile>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { data: existing } = await supabase
    .from("user_profile")
    .select("*") // need scoring fields + home base + updated_at + digest prefs
    .eq("user_id", user.id)
    .maybeSingle();

  // Only re-geocode the home base when the address actually changed.
  const newAddress = body.home_address?.trim() || null;
  let homeLat = existing?.home_latitude ?? null;
  let homeLng = existing?.home_longitude ?? null;

  const addressChanged = newAddress !== (existing?.home_address ?? null);
  const missingCoords = newAddress != null && (homeLat == null || homeLng == null);

  if (!newAddress) {
    homeLat = null;
    homeLng = null;
  } else if (addressChanged || missingCoords) {
    // Geocode when the address changed OR we don't have coordinates yet
    // (e.g. it was first saved before the API key was configured).
    const geo = await geocodeAddress(`${newAddress}, Illinois`);
    homeLat = geo?.lat ?? null;
    homeLng = geo?.lng ?? null;
  }

  // Did a field the scorer reads change? Drives BOTH the immediate re-score
  // kick and updated_at: the scraper re-scores anything with
  // scored_at < updated_at, so updated_at must only move when the scoring
  // inputs move — an address/digest tweak must not trigger a full re-score.
  const scoringValues: Record<(typeof SCORING_FIELDS)[number], unknown> = {
    resume_text: body.resume_text ?? null,
    target_subjects: body.target_subjects ?? null,
    preferred_districts: body.preferred_districts ?? null,
    ideal_role_description: body.ideal_role_description ?? null,
    must_haves: body.must_haves ?? null,
    nice_to_haves: body.nice_to_haves ?? null,
  };
  const scoringChanged = SCORING_FIELDS.some(
    (f) => normalize(scoringValues[f]) !== normalize(existing?.[f]),
  );

  const row = {
    user_id: user.id,
    ...scoringValues,
    home_address: newAddress,
    home_latitude: homeLat,
    home_longitude: homeLng,
    digest_opt_in: body.digest_opt_in ?? false,
    digest_min_score: body.digest_min_score ?? 7,
    updated_at:
      scoringChanged || !existing?.updated_at
        ? new Date().toISOString()
        : existing.updated_at,
  };

  const { data, error } = await supabase
    .from("user_profile")
    .upsert(row, { onConflict: "user_id" })
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  // Kick a re-score only when a field the scorer reads actually changed —
  // an address or digest tweak shouldn't burn a scrape run.
  const scoreRefreshTriggered = scoringChanged
    ? await triggerScrapeWorkflow()
    : false;

  return NextResponse.json({
    profile: data,
    scoring_changed: scoringChanged,
    score_refresh_triggered: scoreRefreshTriggered,
  });
}
