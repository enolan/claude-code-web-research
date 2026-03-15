"""Search YouTube and return structured results as JSON."""

import argparse
import json
import re
import sys
import urllib.parse

import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# YouTube encodes search filters as protobuf in the 'sp' URL parameter.
# These are the known values for common filters.
UPLOAD_DATE_FILTERS = {
    "hour": "EgIIAQ%3D%3D",
    "today": "EgIIAg%3D%3D",
    "week": "EgIIAw%3D%3D",
    "month": "EgIIBA%3D%3D",
    "year": "EgIIBQ%3D%3D",
}

DURATION_FILTERS = {
    "short": "EgIYAQ%3D%3D",   # under 4 min
    "medium": "EgIYAw%3D%3D",  # 4-20 min
    "long": "EgIYAg%3D%3D",    # over 20 min
}

SORT_FILTERS = {
    "relevance": None,  # default
    "date": "CAISAhAB",
    "views": "CAMSAhAB",
    "rating": "CAESAhAB",
}


def search(query: str, sp: str | None = None) -> list[dict]:
    """Fetch YouTube search results by scraping ytInitialData from the HTML."""
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    if sp:
        url += f"&sp={sp}"

    resp = httpx.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
    resp.raise_for_status()

    match = re.search(r"var ytInitialData = ({.*?});</script>", resp.text)
    if not match:
        return []

    data = json.loads(match.group(1))
    results = []

    try:
        sections = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]["contents"]
    except KeyError:
        return []

    for section in sections:
        items = section.get("itemSectionRenderer", {}).get("contents", [])
        for item in items:
            vr = item.get("videoRenderer")
            if not vr:
                continue

            vid = vr.get("videoId", "")
            title = vr.get("title", {}).get("runs", [{}])[0].get("text", "")
            channel = vr.get("longBylineText", {}).get("runs", [{}])[0].get("text", "")
            channel_url = vr.get("longBylineText", {}).get("runs", [{}])[0].get(
                "navigationEndpoint", {}
            ).get("commandMetadata", {}).get("webCommandMetadata", {}).get("url", "")
            published = vr.get("publishedTimeText", {}).get("simpleText", "")
            length = vr.get("lengthText", {}).get("simpleText", "")
            views = vr.get("viewCountText", {}).get("simpleText", "")

            # Description snippet
            snippet_parts = []
            for s in vr.get("detailedMetadataSnippets", []):
                for run in s.get("snippetText", {}).get("runs", []):
                    snippet_parts.append(run.get("text", ""))
            snippet = "".join(snippet_parts)

            results.append({
                "video_id": vid,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "channel": channel,
                "channel_url": f"https://www.youtube.com{channel_url}" if channel_url else "",
                "published": published,
                "length": length,
                "views": views,
                "snippet": snippet,
            })

    return results


def main():
    parser = argparse.ArgumentParser(description="Search YouTube")
    parser.add_argument("query", nargs="+", help="Search query")
    parser.add_argument(
        "--upload-date",
        choices=UPLOAD_DATE_FILTERS.keys(),
        help="Filter by upload date",
    )
    parser.add_argument(
        "--duration",
        choices=DURATION_FILTERS.keys(),
        help="Filter by duration: short (<4m), medium (4-20m), long (>20m)",
    )
    parser.add_argument(
        "--sort",
        choices=SORT_FILTERS.keys(),
        default="relevance",
        help="Sort order (default: relevance)",
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=10,
        help="Max results to return (default: 10)",
    )
    args = parser.parse_args()

    query = " ".join(args.query)

    # Determine the sp filter param. Only one sp value can be used at a time
    # (YouTube limitation), so we prioritize: sort > upload-date > duration.
    sp = None
    if args.sort and args.sort != "relevance":
        sp = SORT_FILTERS[args.sort]
    elif args.upload_date:
        sp = UPLOAD_DATE_FILTERS[args.upload_date]
    elif args.duration:
        sp = DURATION_FILTERS[args.duration]

    try:
        results = search(query, sp=sp)
    except httpx.HTTPError as e:
        print(json.dumps({"error": f"HTTP request failed: {e}"}))
        sys.exit(1)

    results = results[: args.limit]
    print(json.dumps({"query": query, "total_shown": len(results), "results": results}, indent=2))


if __name__ == "__main__":
    main()
