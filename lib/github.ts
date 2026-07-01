// Fire the scrape/score GitHub Actions workflow when the profile changes, so
// scores re-personalize within ~a minute instead of waiting for the next cron.
// Server-only (uses a repo-scoped token). Failing here must never fail a
// profile save — callers treat `false` as "will refresh at the next cron run".

const WORKFLOW_FILE = "scrape.yml";

export async function triggerScoreRefresh(): Promise<boolean> {
  const token = process.env.GITHUB_DISPATCH_TOKEN;
  const repo = process.env.GITHUB_REPO; // "owner/repo"
  if (!token || !repo) return false;

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
