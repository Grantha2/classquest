// Fire the scrape/score GitHub Actions workflow on demand (e.g. after a
// profile change) so scores re-personalize within ~a minute instead of waiting
// for the next scheduled cron. Server-only (uses a repo-scoped token).
// Best-effort: returns false (never throws) when unconfigured or failing —
// callers treat that as "the scheduled run will cover it".

const WORKFLOW_FILE = "scrape.yml";

export async function triggerScrapeWorkflow(): Promise<boolean> {
  const token = process.env.GITHUB_DISPATCH_TOKEN;
  if (!token) return false;
  const repo = process.env.GITHUB_REPO || "Grantha2/classquest";

  try {
    const res = await fetch(
      `https://api.github.com/repos/${repo}/actions/workflows/${WORKFLOW_FILE}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ ref: "main" }),
      },
    );
    if (res.status !== 204) {
      console.error(`[github] workflow_dispatch failed: ${res.status} ${await res.text()}`);
      return false;
    }
    return true;
  } catch (err) {
    console.error("[github] workflow_dispatch error:", err);
    return false;
  }
}
