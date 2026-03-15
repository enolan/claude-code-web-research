"""Fetch detailed information about a single Resident Advisor event."""

import argparse
import json
import re
import sys

import httpx

GRAPHQL_URL = "https://ra.co/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "Referer": "https://ra.co/events",
    "ra-content-language": "en",
}

EVENT_DETAIL_QUERY = """
query GET_EVENT($id: ID!) {
  event(id: $id) {
    id
    title
    date
    startTime
    endTime
    content
    cost
    minimumAge
    contentUrl
    flyerFront
    isTicketed
    attending
    pick { id blurb }
    venue {
      id
      name
      address
      contentUrl
      area { id name urlName country { name urlCode } }
    }
    artists {
      id
      name
      contentUrl
    }
    promoters {
      id
      name
    }
    genres {
      id
      name
    }
  }
}
"""


def fetch_event(event_id: str) -> dict:
    resp = httpx.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={
            "operationName": "GET_EVENT",
            "variables": {"id": event_id},
            "query": EVENT_DETAIL_QUERY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def parse_event_id(input_str: str) -> str:
    """Extract event ID from a URL or raw ID string."""
    # Handle URLs like https://ra.co/events/2361559
    match = re.search(r"ra\.co/events/(\d+)", input_str)
    if match:
        return match.group(1)
    # Handle raw numeric IDs
    if input_str.strip().isdigit():
        return input_str.strip()
    print(json.dumps({"error": f"Could not parse event ID from: {input_str}"}))
    sys.exit(1)


def format_event(ev: dict) -> dict:
    venue = ev.get("venue") or {}
    area = venue.get("area") or {}
    country = area.get("country") or {}
    return {
        "id": ev.get("id"),
        "title": ev.get("title"),
        "date": ev.get("date"),
        "start_time": ev.get("startTime"),
        "end_time": ev.get("endTime"),
        "description": ev.get("content"),
        "cost": ev.get("cost"),
        "minimum_age": ev.get("minimumAge"),
        "is_ticketed": ev.get("isTicketed"),

        "attending": ev.get("attending"),
        "is_pick": bool(ev.get("pick")),
        "pick_blurb": (ev.get("pick") or {}).get("blurb"),
        "flyer": ev.get("flyerFront"),
        "url": f"https://ra.co{ev.get('contentUrl', '')}",
        "venue": {
            "name": venue.get("name"),
            "address": venue.get("address"),
            "area": area.get("name"),
            "country": country.get("name"),
            "url": f"https://ra.co{venue.get('contentUrl', '')}" if venue.get("contentUrl") else None,
        },
        "artists": [
            {"name": a["name"], "url": f"https://ra.co{a.get('contentUrl', '')}"}
            for a in (ev.get("artists") or [])
        ],
        "promoters": [p.get("name") for p in (ev.get("promoters") or [])],
        "genres": [g.get("name") for g in (ev.get("genres") or [])],
    }


def main():
    parser = argparse.ArgumentParser(description="Get details for a Resident Advisor event")
    parser.add_argument("event", help="Event ID or ra.co event URL")
    args = parser.parse_args()

    event_id = parse_event_id(args.event)

    try:
        result = fetch_event(event_id)
    except httpx.HTTPError as e:
        print(json.dumps({"error": f"HTTP request failed: {e}"}))
        sys.exit(1)

    ev = result.get("data", {}).get("event")
    if not ev:
        print(json.dumps({"error": f"Event {event_id} not found"}))
        sys.exit(1)

    print(json.dumps(format_event(ev), indent=2))


if __name__ == "__main__":
    main()
