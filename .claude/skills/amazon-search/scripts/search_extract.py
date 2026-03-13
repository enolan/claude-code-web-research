"""Search Amazon and extract structured product data.

Usage: uv run python search_extract.py <search query> [--page N]
Outputs JSON array of products to stdout.
"""

import argparse
import re
import html as html_mod
import json
import sys
from pathlib import Path
from urllib.parse import quote_plus

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from fetch import fetch, check_captcha


def extract_search_results(html: str) -> list[dict]:
    asin_positions = [
        (m.start(), m.group(1))
        for m in re.finditer(
            r'data-asin="(B[A-Z0-9]{9})"[^>]*data-component-type="s-search-result"',
            html,
        )
    ]

    results = []
    seen = set()
    for i, (pos, asin) in enumerate(asin_positions):
        if asin in seen:
            continue
        seen.add(asin)
        end = (
            asin_positions[i + 1][0] if i + 1 < len(asin_positions) else pos + 15000
        )
        chunk = html[pos:end]

        # Title from h2 aria-label
        title_m = re.search(r'<h2[^>]*aria-label="([^"]+)"', chunk)
        title = html_mod.unescape(title_m.group(1)) if title_m else "N/A"
        title = re.sub(r"^Sponsored Ad - ", "", title)

        # Price from a-offscreen span
        price_m = re.search(
            r'<span class="a-price"[^>]*>\s*<span class="a-offscreen">(.*?)</span>',
            chunk,
            re.DOTALL,
        )
        price = price_m.group(1) if price_m else "N/A"

        # Rating
        rating_m = re.search(r"(\d+\.?\d*) out of 5 stars", chunk)
        rating = rating_m.group(1) if rating_m else "N/A"

        # Review count
        reviews_m = re.search(r'aria-label="(\d[\d,]*)\s', chunk)
        reviews = reviews_m.group(1) if reviews_m else "N/A"

        # Sponsored?
        sponsored = bool(re.search(r"Sponsored", chunk[:500]))

        results.append(
            {
                "asin": asin,
                "title": title,
                "price": price,
                "rating": rating,
                "reviews": reviews,
                "sponsored": sponsored,
                "url": f"https://www.amazon.com/dp/{asin}",
            }
        )

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search Amazon product listings")
    parser.add_argument("query", nargs="+", help="Search query terms")
    parser.add_argument("--page", type=int, default=1, help="Results page number")
    args = parser.parse_args()

    query = " ".join(args.query)
    url = f"https://www.amazon.com/s?k={quote_plus(query)}"
    if args.page > 1:
        url += f"&page={args.page}"

    html = fetch(url)
    check_captcha(html)

    results = extract_search_results(html)
    print(json.dumps(results, indent=2))
