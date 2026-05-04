---
name: Mobile Responsiveness Strategy
description: How the maintenance schedule table is handled on mobile viewports
type: project
---

## Mobile Table Strategy (breakpoint: 640px)

The maintenance schedule is a 4-column table that cannot fit on a 375px mobile screen. The chosen strategy:

- At `max-width: 640px`, hide all three `.col-bucket` columns using `display: none !important`
- The `!important` is required because the browser UA stylesheet sets `<td>` to `display: table-cell` at high specificity
- The task name column (`.col-task`) expands to 100% width
- Status (overdue/due_soon/ok) is still communicated via the 4px colored left border on the first `<td>` of each row — no information is lost

## Notes
- The table caption ("Maintenance schedule — checkmark shows when each item is due") is visible on desktop but hidden on mobile since the bucket columns are gone
- Future improvement: on mobile, consider adding a small inline text badge per row showing the time bucket (e.g., "< 3 months") instead of relying solely on the left border
