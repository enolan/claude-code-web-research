"""Fetch event listings from Resident Advisor (ra.co) via their GraphQL API."""

import argparse
import json
import sys

import httpx

GRAPHQL_URL = "https://ra.co/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0",
    "Referer": "https://ra.co/events",
    "ra-content-language": "en",
}

LISTINGS_QUERY = """
query GET_EVENT_LISTINGS($filters: FilterInputDtoInput, $filterOptions: FilterOptionsInputDtoInput, $page: Int, $pageSize: Int) {
  eventListings(filters: $filters, filterOptions: $filterOptions, pageSize: $pageSize, page: $page) {
    data {
      id
      listingDate
      event {
        id
        title
        date
        startTime
        endTime
        contentUrl
        flyerFront
        isTicketed
        attending
        pick { id blurb }
        venue { id name area { name } }
        artists { id name }
        genres { id name }
      }
    }
    totalResults
  }
}
"""

AREA_SEARCH_QUERY = """
query SEARCH_AREAS($searchTerm: String, $limit: Int) {
  areas(searchTerm: $searchTerm, limit: $limit) {
    id
    name
    urlName
    country { name urlCode }
  }
}
"""


def search_area(term: str) -> list[dict]:
    """Search for an area by name, return matching areas."""
    resp = httpx.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={
            "operationName": "SEARCH_AREAS",
            "variables": {"searchTerm": term, "limit": 10},
            "query": AREA_SEARCH_QUERY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", {}).get("areas", [])


def fetch_listings(area_id: int, date_from: str, date_to: str, page: int = 1, page_size: int = 50) -> dict:
    """Fetch event listings for an area and date range."""
    variables = {
        "filters": {
            "areas": {"eq": area_id},
            "listingDate": {
                "gte": f"{date_from}T00:00:00.000Z",
                "lte": f"{date_to}T23:59:59.000Z",
            },
        },
        "filterOptions": {"genre": True},
        "pageSize": page_size,
        "page": page,
    }

    resp = httpx.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={
            "operationName": "GET_EVENT_LISTINGS",
            "variables": variables,
            "query": LISTINGS_QUERY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def format_event(listing: dict) -> dict:
    """Extract key fields from a listing into a clean dict."""
    ev = listing.get("event", {})
    venue = ev.get("venue") or {}
    area = venue.get("area") or {}
    return {
        "id": ev.get("id"),
        "title": ev.get("title"),
        "date": ev.get("date"),
        "start_time": ev.get("startTime"),
        "end_time": ev.get("endTime"),
        "venue": venue.get("name"),
        "area": area.get("name"),
        "artists": [a["name"] for a in (ev.get("artists") or [])],
        "genres": [g["name"] for g in (ev.get("genres") or [])],
        "attending": ev.get("attending"),
        "is_ticketed": ev.get("isTicketed"),
        "is_pick": bool(ev.get("pick")),
        "pick_blurb": (ev.get("pick") or {}).get("blurb"),
        "flyer": ev.get("flyerFront"),
        "url": f"https://ra.co{ev.get('contentUrl', '')}",
    }


def main():
    parser = argparse.ArgumentParser(description="List events from Resident Advisor")
    parser.add_argument("location", help="City/area name to search for (e.g. 'berlin', 'new york', 'tokyo')")
    parser.add_argument("--area-id", type=int, help="Use a known area ID directly instead of searching by name")
    parser.add_argument("--from", dest="date_from", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="date_to", help="End date (YYYY-MM-DD). Defaults to same as --from.")
    parser.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    parser.add_argument("--page-size", type=int, default=50, help="Results per page (default: 50, max ~100)")
    args = parser.parse_args()

    date_to = args.date_to or args.date_from

    # Resolve area ID
    area_id = args.area_id
    if not area_id:
        areas = search_area(args.location)
        if not areas:
            print(json.dumps({"error": f"No areas found matching '{args.location}'"}))
            sys.exit(1)
        area_id = int(areas[0]["id"])
        area_info = areas[0]
    else:
        area_info = {"id": area_id, "name": args.location}

    # Fetch listings
    try:
        result = fetch_listings(area_id, args.date_from, date_to, args.page, args.page_size)
    except httpx.HTTPError as e:
        print(json.dumps({"error": f"HTTP request failed: {e}"}))
        sys.exit(1)

    listings_data = result.get("data", {}).get("eventListings", {})
    total = listings_data.get("totalResults", 0)
    events = [format_event(l) for l in (listings_data.get("data") or [])]

    output = {
        "area": {
            "id": area_id,
            "name": area_info.get("name", args.location),
        },
        "date_range": {"from": args.date_from, "to": date_to},
        "page": args.page,
        "page_size": args.page_size,
        "total_results": total,
        "events": events,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
