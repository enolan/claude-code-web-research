---
name: youtube-search
description: Search YouTube for videos by keyword query.
---

# YouTube Search

Search YouTube and get structured results with video metadata. Works by scraping YouTube's
server-rendered initial data — no API key needed.

## Usage

```
uv run python .claude/skills/youtube-search/scripts/search.py house music DJ set
uv run python .claude/skills/youtube-search/scripts/search.py "Boiler Room Berlin" --duration long
uv run python .claude/skills/youtube-search/scripts/search.py python tutorial --upload-date month --sort views
uv run python .claude/skills/youtube-search/scripts/search.py lo-fi beats -n 5
```

## Arguments

- `query` (required): Search terms (multiple words are joined automatically).
- `--upload-date`: Filter by upload date: `hour`, `today`, `week`, `month`, `year`.
- `--duration`: Filter by duration: `short` (<4 min), `medium` (4–20 min), `long` (>20 min).
- `--sort`: Sort order: `relevance` (default), `date`, `views`, `rating`.
- `-n` / `--limit`: Max results to return (default: 10).

Note: YouTube only supports one filter at a time. If multiple are given, priority is:
sort > upload-date > duration.

## Output

JSON with fields per result: `video_id`, `title`, `url`, `channel`, `channel_url`, `published`,
`length`, `views`, `snippet`.
