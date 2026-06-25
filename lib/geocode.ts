// Server-side Google Geocoding helper (uses GOOGLE_MAPS_API_KEY, never exposed
// to the browser). Returns null on missing key, empty query, or no result.
const GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json";

export interface GeocodeResult {
  lat: number;
  lng: number;
  formatted_address: string | null;
}

export async function geocodeAddress(
  query: string,
): Promise<GeocodeResult | null> {
  const key = process.env.GOOGLE_MAPS_API_KEY;
  if (!key || !query.trim()) return null;
  try {
    const url = `${GEOCODE_URL}?address=${encodeURIComponent(
      query,
    )}&region=us&key=${key}`;
    const res = await fetch(url);
    if (!res.ok) return null;
    const data = await res.json();
    if (data.status === "OK" && data.results?.length) {
      const r = data.results[0];
      return {
        lat: r.geometry.location.lat,
        lng: r.geometry.location.lng,
        formatted_address: r.formatted_address ?? null,
      };
    }
    return null;
  } catch {
    return null;
  }
}

// Haversine distance in miles.
export function distanceMiles(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number,
): number {
  const toRad = (d: number) => (d * Math.PI) / 180;
  const R = 3958.8; // earth radius in miles
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}
