---
name: ra-events
description: Find events on Resident Advisor (ra.co) by location, date, and more.
---

# Resident Advisor Event Listings

Find events on ra.co by location and date, and get detailed event info. Uses RA's GraphQL API.

## Listing events

Use `list_events.py` to search for events by city and date range.

```
uv run python .claude/skills/ra-events/scripts/list_events.py "berlin" --from 2026-03-20 --to 2026-03-22
uv run python .claude/skills/ra-events/scripts/list_events.py "new york" --from 2026-03-15
uv run python .claude/skills/ra-events/scripts/list_events.py "tokyo" --from 2026-04-01 --to 2026-04-07 --page-size 100
uv run python .claude/skills/ra-events/scripts/list_events.py "london" --area-id 13 --from 2026-03-15
```

Arguments:
- `location` (required): City name to search for. The script resolves this to an RA area ID automatically.
- `--area-id`: Skip the area search and use a known area ID directly. Useful common IDs:
  8=NYC, 13=London, 17=Chicago, 20=Barcelona, 23=LA, 27=Tokyo, 29=Amsterdam, 34=Berlin, 44=Paris, 218=SF/Oakland.
- `--from` (required): Start date (YYYY-MM-DD).
- `--to`: End date (YYYY-MM-DD). Defaults to same as `--from` (single day).
- `--page`: Page number (default: 1).
- `--page-size`: Results per page (default: 50).

Output JSON fields per event: `id`, `title`, `date`, `start_time`, `end_time`, `venue`, `area`,
`artists`, `genres`, `attending`, `is_ticketed`, `is_pick`, `pick_blurb`, `flyer`, `url`.

RA "picks" are editorially highlighted events -- these tend to be higher quality.

## Getting event details

Use `event_details.py` to get full details for a specific event, including description, cost,
lineup, venue address, and more.

```
uv run python .claude/skills/ra-events/scripts/event_details.py 2361559
uv run python .claude/skills/ra-events/scripts/event_details.py https://ra.co/events/2361559
```

Accepts an event ID or full ra.co URL. Output includes: `description` (HTML), `cost`,
`minimum_age`, `venue.address`, `artists` (with URLs), `promoters`, and all
fields from the listing.

## Tips for helping the user find events

- Start with a listing query for their city and date range.
- Sort/filter results by what matters to them: genre, attendance count, RA picks, specific artists.
- Use `event_details.py` to get descriptions and costs for events that look promising.
- If the user doesn't specify a date, use today's date or the upcoming weekend.
- The `attending` count is a rough popularity signal.
- Events with `is_pick: true` have been editorially selected by RA and have a `pick_blurb`.
