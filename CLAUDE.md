# Repo description

This repo is used for doing web research tasks with Claude Code. You can use Python (with `uv`) or
`curl`, or your Chrome browser tools. Use whatever's most effective. Chrome tools are extremely slow
but can be useful if you can't access things programmatically. When working with a site that you're
not familiar with, you can use Chrome to explore first, then ideally access the site without
interacting with a whole web browser.

Note: NEVER use the system python installation, always use `uv`. e.g. `uv run python my_script.py`
or `uv run python -c 'print("Hello, world!")'`.