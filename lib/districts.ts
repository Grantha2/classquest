// ClassQuest — district + subject reference data for the frontend.
// Mirrors scrapers/district_config.py. Keep district_id values in sync.

export interface DistrictRef {
  district_id: string;
  name: string;
}

export const DISTRICTS: DistrictRef[] = [
  { district_id: "cps", name: "Chicago Public Schools" },
  { district_id: "cusd200", name: "Wheaton Warrenville CUSD 200" },
  { district_id: "d203", name: "Naperville Unit 203" },
  { district_id: "d300", name: "Algonquin Unit 300" },
  { district_id: "ip204", name: "Indian Prairie Unit 204" },
  { district_id: "d365", name: "Valley View 365U" },
  { district_id: "d131", name: "Aurora East Unit 131" },
  { district_id: "d303", name: "St. Charles Unit 303" },
  { district_id: "lc202", name: "Plainfield Unit 202" },
  { district_id: "u46", name: "Elgin Unit 46" },
  { district_id: "d129", name: "Aurora West Unit 129" },
  { district_id: "sd54", name: "Schaumburg Elementary District 54" },
  { district_id: "d308", name: "Oswego Unit 308" },
  { district_id: "ccsd15", name: "Palatine CCSD 15" },
  { district_id: "waukeganschools", name: "Waukegan Unit 60" },
  // DuPage County (near Wheaton) — consortium + single-district portals
  { district_id: "gec", name: "Glenbard Elem Consortium (D41/44/45/89)" },
  { district_id: "swdp", name: "SW DuPage (Winfield 34 / W. Chicago 33)" },
  { district_id: "d15", name: "Marquardt SD 15 (Glendale Heights)" },
  { district_id: "d93", name: "CCSD 93 (Bloomingdale / Carol Stream)" },
  { district_id: "d34", name: "Glenview SD 34" },
  { district_id: "d25", name: "Arlington Heights SD 25" },
  { district_id: "d62", name: "Des Plaines CCSD 62" },
  { district_id: "d64", name: "Park Ridge-Niles CCSD 64" },
  { district_id: "ccsd59", name: "Elk Grove Township CCSD 59" },
  { district_id: "d57", name: "Mount Prospect SD 57" },
  { district_id: "d68", name: "Skokie SD 68" },
  { district_id: "d69", name: "Skokie-Morton Grove SD 69" },
  { district_id: "d98", name: "Berwyn North SD 98" },
  // County ROE consortiums (each aggregates many member districts; the real
  // district shows on each posting's label)
  { district_id: "dupage", name: "DuPage County ROE (all districts)" },
  { district_id: "scook", name: "Suburban Cook Consortium" },
  { district_id: "kane", name: "Kane County Consortium" },
  { district_id: "lake", name: "Lake County Consortium" },
  { district_id: "willcounty", name: "Will County ROE" },
];

export function districtName(districtId: string): string {
  return DISTRICTS.find((d) => d.district_id === districtId)?.name ?? districtId;
}

// General elementary (grades 1-6) specializations for the profile tag input +
// dashboard filter. Special education and early childhood are intentionally out
// of scope (see scrapers/title_filter.py).
export const SUBJECT_OPTIONS: string[] = [
  "General Elementary",
  "Reading Specialist",
  "STEM",
  "Bilingual/ESL",
  "Math",
  "Science",
  "Social-Emotional Learning",
  "Gifted/Enrichment",
];
