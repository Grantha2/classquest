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
