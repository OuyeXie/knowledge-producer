---
name: ai_report
description: Generate an AI research Markdown report via knowledge-producer and send it back in Discord.
user-invocable: true
---

# /ai_report

Generate and send an AI research report from the `knowledge-producer` repo.

## Safety + boundaries
- Never request or use Ouye’s passwords.
- Do not print or exfiltrate secrets from `.env`.
- Stage and commit only the generated Markdown report, HTML report, and matching log for this run.

## Default behavior
- Repo: `/Users/ouye/workspace/knowledge-producer`
- Days: `1`
- Sources: all
- LLM summaries: enabled via OpenAI (`--llm-provider openai`)
- Dedup: enabled against existing reports (`--dedup all`)
- Output: `reports/report-{date}-{days}d.md` and `reports/report-{date}-{days}d.html`
- Git: commit the new Markdown report, HTML report, and log, then push to `origin/main`

## What to do

1) Run the report on the host:

- `cd /Users/ouye/workspace/knowledge-producer`
- `source .venv/bin/activate`
- `python -m pip install -e .`
- `python -m knowledge_producer --days 1 --dedup all --llm-provider openai`

2) Find the newest Markdown and HTML reports under:
- `/Users/ouye/workspace/knowledge-producer/reports/`

3) Find the matching newest log under:
- `/Users/ouye/workspace/knowledge-producer/logs/`

4) Commit and push only the generated Markdown report, HTML report, and log:

- `git add reports/<new-report>.md reports/<new-report>.html logs/<new-log>.log`
- `git commit -m "Add AI research report for <date>"`
- `git push origin main`

5) Copy the HTML report into the OpenClaw workspace so attachments are allowed:
- copy to: `/Users/ouye/.openclaw/workspace/`

6) Send the HTML report back to the user as a file attachment in Discord.

## Options (if user provides)
- If user asks for a different range: pass `--days N` or `--date YYYY-MM-DD`.
- If user asks to disable LLM summaries: pass `--no-llm`.
- If user wants a different provider and they have a key configured: set `--llm-provider anthropic`.
- If there are unrelated git changes, do not include them in the commit.
