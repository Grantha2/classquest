"use client";

import { MapContainer, TileLayer, CircleMarker, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import type { JobPosting } from "@/lib/types";

// House glyph for the home-base marker (divIcon avoids Leaflet's image-path issues).
const homeIcon = L.divIcon({
  className: "",
  html: '<div style="display:flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:9999px;background:#3b82f6;border:2px solid #1d4ed8;box-shadow:0 1px 5px rgba(0,0,0,.35);font-size:15px;line-height:1">🏠</div>',
  iconSize: [30, 30],
  iconAnchor: [15, 15],
  popupAnchor: [0, -16],
});

// Chicagoland center as a sensible default if there's nothing to show.
const DEFAULT_CENTER: [number, number] = [41.85, -88.1];

function scoreColor(score: number | null): string {
  if (score == null) return "#94a3b8"; // slate
  if (score >= 8) return "#22c55e"; // green
  if (score >= 5) return "#fbbf24"; // yellow
  return "#94a3b8";
}

export default function MapView({
  jobs,
  home,
}: {
  jobs: JobPosting[];
  home?: { lat: number; lng: number } | null;
}) {
  const points = jobs.filter(
    (j) => j.latitude != null && j.longitude != null,
  );
  const center: [number, number] = home
    ? [home.lat, home.lng]
    : points[0]
      ? [points[0].latitude as number, points[0].longitude as number]
      : DEFAULT_CENTER;

  return (
    <MapContainer
      center={center}
      zoom={10}
      scrollWheelZoom
      style={{ height: 480, width: "100%", borderRadius: 16 }}
    >
      {/* CARTO Positron — clean, light basemap (free, no API key). */}
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        subdomains="abcd"
      />

      {home && (
        <Marker position={[home.lat, home.lng]} icon={homeIcon}>
          <Popup>🏠 Your home base</Popup>
        </Marker>
      )}

      {points.map((j) => (
        <CircleMarker
          key={j.id}
          center={[j.latitude as number, j.longitude as number]}
          radius={8}
          pathOptions={{
            color: "#ffffff",
            weight: 1.5,
            fillColor: scoreColor(j.relevance_score),
            fillOpacity: 0.95,
          }}
        >
          <Popup>
            <div style={{ minWidth: 180 }}>
              <strong>{j.title}</strong>
              <br />
              <span style={{ color: "#475569" }}>
                {j.district_name}
                {j.location ? ` · ${j.location}` : ""}
              </span>
              <br />
              <span style={{ color: "#475569" }}>
                {j.relevance_score != null ? `Score ${j.relevance_score}/10` : "Unscored"}
                {j.distance_mi != null ? ` · ${j.distance_mi.toFixed(1)} mi` : ""}
              </span>
              <br />
              <a
                href={j.external_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: "#2563eb", fontWeight: 600 }}
              >
                View posting →
              </a>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
