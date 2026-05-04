---
name: Static File Caching Behaviour
description: FastAPI serves static files with strong caching; Playwright sessions won't see CSS changes without cache-busting
type: feedback
---

FastAPI's `StaticFiles` mount serves CSS/JS with caching headers. During review sessions using Playwright, the browser will serve the old cached stylesheet even after the file on disk changes.

**Why:** Observed during first review session — `display: none !important` on `.col-bucket` cells had no effect until the stylesheet was force-reloaded.

**How to apply:** After editing `style.css`, force a stylesheet reload in Playwright by evaluating:
```js
document.querySelector('link[rel="stylesheet"]').href = '/static/style.css?v=' + Date.now();
```
Then wait 1 second before taking a screenshot or checking computed styles. Alternatively, navigate to the page again with a full hard reload.
