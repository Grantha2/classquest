import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { triggerScrapeWorkflow } from "@/lib/github";
// Import the implementation directly to avoid pdf-parse's debug-mode
// "read a sample PDF on import" behavior that breaks in serverless builds.
import pdfParse from "pdf-parse/lib/pdf-parse.js";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const form = await request.formData();
  const file = form.get("file");

  if (!(file instanceof File)) {
    return NextResponse.json({ error: "No file uploaded" }, { status: 400 });
  }
  if (file.type !== "application/pdf") {
    return NextResponse.json(
      { error: "Please upload a PDF file." },
      { status: 400 },
    );
  }

  let text = "";
  try {
    const buffer = Buffer.from(await file.arrayBuffer());
    const parsed = await pdfParse(buffer);
    text = (parsed.text ?? "").trim();
  } catch (err) {
    return NextResponse.json(
      {
        error:
          err instanceof Error
            ? `Could not read PDF: ${err.message}`
            : "Could not read PDF.",
      },
      { status: 422 },
    );
  }

  if (!text) {
    return NextResponse.json(
      { error: "No text could be extracted from that PDF." },
      { status: 422 },
    );
  }

  const { data: existing } = await supabase
    .from("user_profile")
    .select("resume_text")
    .eq("user_id", user.id)
    .maybeSingle();

  // Persist the extracted text (never the raw binary).
  const { error } = await supabase
    .from("user_profile")
    .upsert(
      { user_id: user.id, resume_text: text, updated_at: new Date().toISOString() },
      { onConflict: "user_id" },
    );

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  if ((existing?.resume_text ?? null) !== text) {
    await triggerScrapeWorkflow();
  }

  return NextResponse.json({ resume_text: text });
}
