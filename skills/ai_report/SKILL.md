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
- Do not commit/push or make external changes unless the user explicitly asks.

## Default behavior
- Repo: `/Users/ouye/workspace/knowledge-producer`
- Days: `1`
- Sources: all
- LLM summaries: enabled via OpenAI (`--llm-provider openai`)
- Dedup: enabled against existing reports (`--dedup all`)
- Output: `reports/report-{date}-{days}d.md`
- Git: do not commit/push unless the user explicitly asks

## What to do

Caching:
- If `reports/report-{today}-1d.md` already exists, skip generation and just send that file.
- Otherwise generate it.

1) Run the report on the host:

- `cd /Users/ouye/workspace/knowledge-producer`
- `source .venv/bin/activate`
- `python -m pip install -e .`
- `python -m knowledge_producer --days 1 --dedup all --llm-provider openai`

2) Find the newest report under:
- `/Users/ouye/workspace/knowledge-producer/reports/`

3) Find the matching newest log under:
- `/Users/ouye/workspace/knowledge-producer/logs/`

4) (Optional) If the user explicitly asks for git commit/push, do it, otherwise skip.

5) Copy the report into the OpenClaw workspace so attachments are allowed:
- copy to: `/Users/ouye/.openclaw/workspace/`

6) Send it back to the user as a file attachment in Discord.

## Options (if user provides)
- If user asks for a different range: pass `--days N` or `--date YYYY-MM-DD`.
- If user asks to disable LLM summaries: pass `--no-llm`.
- If user wants a different provider and they have a key configured: set `--llm-provider anthropic`.
- If there are unrelated git changes, do not include them in the commit.
