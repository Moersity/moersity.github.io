# AGENTS.md

## Cursor Cloud specific instructions

This is a **GitHub Pages static site** (`moersity.github.io`). There are no build tools, no package managers, and no external dependencies.

### Serving locally

Preview the site with Python's built-in HTTP server:

```sh
python3 -m http.server 8080
```

Then open `http://localhost:8080/` in Chrome.

### Key notes

- The repo has no linter, test framework, or build step — it is plain HTML/CSS served directly by GitHub Pages.
- `index.html` is the site entry point. Any changes to HTML/CSS are visible immediately on refresh (no compilation needed).
- There is no `package.json`, so no `npm install` or similar step is required.
