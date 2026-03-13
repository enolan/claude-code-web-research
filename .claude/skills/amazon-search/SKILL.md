---
name: amazon-search
description: Search Amazon for products by keyword query.
---

# Searching Amazon

Use the `search_extract.py` script to search Amazon for products by keyword query. The script
returns results in JSON format.

Amazon's search is awful, it's your job to figure out the query or queries to use that will find
what the user is looking for, and to decide how many pages to look through. Sometimes the thing
the user cares about will not be in the product title or description. Think about how Amazon sellers
write their titles and descriptions, and how products matching what the user is looking for are
likely to be described. Remember, Amazon sellers are targeting the mass market, and often don't
speak English well. Sometimes the thing the user cares about will even only be in the images! You
can parse the images using the amazon-product skill, but text in images doesn't affect what shows up
in search results.

Examples:
```
uv run python .claude/skills/amazon-search/scripts/search_extract.py wireless earbuds
uv run python .claude/skills/amazon-search/scripts/search_extract.py usb c cable --page 2
```

Outputs JSON array with fields: `asin`, `title`, `price`, `rating`, `reviews`, `sponsored`, `url`.

## Troubleshooting

- **CAPTCHA**: If the script reports a CAPTCHA error, Amazon is rate-limiting. Wait a minute and
  retry. If persistent, use the Chrome browser tools as a fallback.
- **Missing prices**: Some products show prices only after selecting a variant. The script will
  report "N/A" for these.
- **HTTP errors**: The scripts use httpx internally. If network issues occur, the script will print
  an error JSON and exit.
