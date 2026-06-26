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

  // Only re-geocode the home base when the address actually changed.
  const { data: existing } = await supabase
    .from("user_profile")
    .select(
      "home_address, home_latitude, home_longitude, target_subjects, ideal_role_description, must_haves, nice_to_haves, resume_text",
    )
    .eq("user_id", user.id)
    .maybeSingle();

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

  const row = {
    user_id: user.id,
    resume_text: body.resume_text ?? null,
    target_subjects: body.target_subjects ?? null,
    preferred_districts: body.preferred_districts ?? null,
    ideal_role_description: body.ideal_role_description ?? null,
    must_haves: body.must_haves ?? null,
    nice_to_haves: body.nice_to_haves ?? null,
    home_address: newAddress,
    home_latitude: homeLat,
    home_longitude: homeLng,
    updated_at: new Date().toISOString(),
  };

  const { data, error } = await supabase
    .from("user_profile")
    .upsert(row, { onConflict: "user_id" })
    .select()
    .single();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  // If a scoring-relevant field changed, kick off a scrape run so scores refresh
  // soon (the scraper re-scores postings older than the profile's updated_at).
  const scoringChanged =
    JSON.stringify(existing?.target_subjects ?? null) !==
      JSON.stringify(row.target_subjects) ||
    (existing?.ideal_role_description ?? null) !== row.ideal_role_description ||
    (existing?.must_haves ?? null) !== row.must_haves ||
    (existing?.nice_to_haves ?? null) !== row.nice_to_haves ||
    (existing?.resume_text ?? null) !== row.resume_text;
  if (scoringChanged) {
    await triggerScrapeWorkflow();
  }

  return NextResponse.json({ profile: data });
}
