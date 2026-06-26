// Fire the scrape workflow on demand (e.g. after a profile change) so scores
// refresh within ~a minute instead of waiting for the next scheduled cron.
// No-ops if GITHUB_DISPATCH_TOKEN isn't configured — the cron still covers it.
export async function triggerScrapeWorkflow(): Promise<void> {
  const token = process.env.GITHUB_DISPATCH_TOKEN;
  if (!token) return;
  const repo = process.env.GITHUB_REPO || "Grantha2/classquest";
  try {
    await fetch(
      `https://api.github.com/repos/${repo}/actions/workflows/scrape.yml/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
        },
        body: JSON.stringify({ ref: "main" }),
      },
    );
  } catch {
    // best-effort: a failed dispatch just means the scheduled run handles it
  }
}
