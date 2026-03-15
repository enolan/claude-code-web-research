---
name: amazon-product
description: Look up Amazon product details by ASIN or URL.
argument-hint: ASIN or Amazon URL
context: fork
---

Use the `product_extract.py` script to fetch detailed product information from Amazon by ASIN or
URL, look at product images, then return all potentially decision-relevant information as a JSON
object.

Examples:
```
uv run python .claude/skills/amazon-product/scripts/product_extract.py B0G7FC4P1K
uv run python .claude/skills/amazon-product/scripts/product_extract.py 'https://www.amazon.com/dp/B0G7FC4P1K'
```

Input detection:
- **ASIN**: 10-char alphanumeric starting with B (e.g. `B01GGKZ2SC`)
- **Amazon URL**: contains `/dp/` or `/gp/product/`

The script outputs JSON with fields: `title`, `price`, `rating`, `reviews`, `features` (bullet
list), `description`, `brand`, `availability`, `asin`, `url`, `images`.

The `images` field contains the original URLs, grouped by source:
- `gallery`: Product image carousel at top of page (product photos + infographics)
- `aplus`: A+ / Enhanced Brand Content images (further down the page, often the richest source of
  specs, measurements, comparison charts, and technical claims)
- `product_description`: Additional images from the product description section (deduplicated
  against gallery)

The `image_files` field contains the same grouping but with local file paths — the script
automatically downloads all images to `/tmp/amazon_images_<ASIN>/` and filters out non-image files.

## Review product images

Amazon sellers embed critical product specs, measurements, certifications, and claims in infographic
images that are NOT in the text. This information can be important (e.g. sensor types, battery
capacity, reference tables).

Use the Read tool to view each image listed in `image_files`. Extract any additional product
specifications, measurements, certifications, sensor types, or technical claims visible in the images
that are not already in the text fields. The A+ content images (`aplus` key) are typically the most
information-rich.

## Present

Respond with the JSON object returned by the Python script, extended with any potentially
decision-relevant information you found in the images. Include no other text.

## Troubleshooting

- **CAPTCHA**: If the script reports a CAPTCHA error, Amazon is rate-limiting. Wait a minute and
  retry. If persistent, use the Chrome browser tools as a fallback.
- **Missing prices**: Some products show prices only after selecting a variant. The script will
  report "N/A" for these.
- **HTTP errors**: The scripts use httpx internally. If network issues occur, the script will print
  an error JSON and exit.
