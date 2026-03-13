"""Look up an Amazon product by ASIN or URL and extract structured details.

Usage: uv run python product_extract.py <ASIN or Amazon URL>
Outputs JSON object to stdout.
"""

import argparse
import re
import json
import html as html_mod
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_shared"))
from fetch import fetch, check_captcha


def parse_asin(value: str) -> str:
    """Extract ASIN from a raw ASIN string or Amazon URL."""
    # Already a bare ASIN
    if re.fullmatch(r"B[A-Z0-9]{9}", value):
        return value
    # URL containing /dp/ASIN or /gp/product/ASIN
    m = re.search(r"(?:/dp/|/gp/product/)(B[A-Z0-9]{9})", value)
    if m:
        return m.group(1)
    print(json.dumps({"error": f"Could not extract ASIN from: {value}"}))
    sys.exit(1)


def extract_product(html: str) -> dict:
    info = {}

    # Title
    m = re.search(r'<span id="productTitle"[^>]*>(.*?)</span>', html, re.DOTALL)
    info["title"] = html_mod.unescape(m.group(1).strip()) if m else "N/A"

    # Price (try multiple sources)
    m = re.search(r'"priceAmount":"?([\d.]+)', html)
    if m:
        info["price"] = f"${m.group(1)}"
    else:
        m = re.search(r'<span class="a-offscreen">(\$[\d.]+)</span>', html)
        info["price"] = m.group(1) if m else "N/A"

    # Rating
    m = re.search(r"(\d+\.?\d*) out of 5 stars", html)
    info["rating"] = m.group(1) if m else "N/A"

    # Review count
    m = re.search(r"([\d,]+) (?:global )?ratings", html)
    info["reviews"] = m.group(1) if m else "N/A"

    # Feature bullets - only from the "About this item" section
    fb_match = re.search(
        r'id="feature-bullets"[^>]*>(.*?)</div>\s*(?:</div>|\s*<!--)',
        html,
        re.DOTALL,
    )
    if fb_match:
        bullets = re.findall(
            r'<span class="a-list-item">\s*(.*?)\s*</span>', fb_match.group(1)
        )
        info["features"] = [
            html_mod.unescape(b.strip()) for b in bullets if b.strip()
        ]
    else:
        info["features"] = []

    # Product description
    m = re.search(r'<div id="productDescription"[^>]*>(.*?)</div>', html, re.DOTALL)
    if m:
        desc = re.sub(r"<[^>]+>", " ", m.group(1)).strip()
        info["description"] = re.sub(r"\s+", " ", desc)

    # Brand
    m = re.search(r'"brand":"([^"]+)"', html)
    if not m:
        m = re.search(
            r'id="bylineInfo"[^>]*>.*?(?:Brand|Visit)[:\s]*(.*?)<',
            html,
            re.DOTALL,
        )
    info["brand"] = m.group(1).strip() if m else "N/A"

    # Availability
    m = re.search(
        r'id="availability"[^>]*>.*?<span[^>]*>(.*?)</span>', html, re.DOTALL
    )
    if m:
        info["availability"] = re.sub(r"\s+", " ", m.group(1)).strip()

    # ASIN
    m = re.search(r'"asin":"(B[A-Z0-9]{9})"', html)
    if m:
        info["asin"] = m.group(1)
        info["url"] = f"https://www.amazon.com/dp/{m.group(1)}"

    # Product images from all sections, grouped by source
    images = {}

    # 1. Gallery images (top of page)
    gallery = list(
        dict.fromkeys(
            re.findall(
                r'"hiRes":"(https://m\.media-amazon\.com/images/I/[^"]+)"', html
            )
        )
    )
    if gallery:
        images["gallery"] = gallery

    # 2. A+ / Enhanced Brand Content images
    aplus_match = re.search(r'id="aplus"', html)
    if aplus_match:
        aplus_chunk = html[aplus_match.start() : aplus_match.start() + 100000]
        aplus_imgs = list(
            dict.fromkeys(
                re.findall(
                    r'<img[^>]*src="(https://m\.media-amazon\.com/images/S/aplus-media-library-service-media/[^"]+)"',
                    aplus_chunk,
                )
            )
        )
        if aplus_imgs:
            images["aplus"] = aplus_imgs

    # 3. Product description section images
    desc_div_match = re.search(r'id="productDescription_feature_div"', html)
    if desc_div_match:
        desc_chunk = html[
            desc_div_match.start() : desc_div_match.start() + 50000
        ]
        desc_imgs = list(
            dict.fromkeys(
                re.findall(
                    r'<img[^>]*src="(https://m\.media-amazon\.com/images/I/[^"]+)"',
                    desc_chunk,
                )
            )
        )
        # Filter out images already in gallery (desc images are often lower-res dupes)
        gallery_ids = {
            re.search(r"/I/([^._]+)", u).group(1)
            for u in gallery
            if re.search(r"/I/([^._]+)", u)
        }
        desc_imgs = [
            u
            for u in desc_imgs
            if not any(gid in u for gid in gallery_ids)
        ]
        if desc_imgs:
            images["product_description"] = desc_imgs

    info["images"] = images

    return info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Look up an Amazon product by ASIN or URL"
    )
    parser.add_argument("asin", help="ASIN (e.g. B0G7FC4P1K) or Amazon product URL")
    args = parser.parse_args()

    asin = parse_asin(args.asin)
    url = f"https://www.amazon.com/dp/{asin}"

    html = fetch(url)
    check_captcha(html)

    info = extract_product(html)
    print(json.dumps(info, indent=2))
