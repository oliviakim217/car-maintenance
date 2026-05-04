---
name: App Design System
description: Established color palette, typography, spacing, and component patterns in the car maintenance tracker
type: project
---

## Color Palette
- Background: `#f0f2f5` (light grey page bg)
- Header/table header bg: `#1a1a2e` (very dark navy)
- Primary text: `#1a1a2e`
- Secondary/muted text: `#64748b`, `#94a3b8`
- Primary button: `#3b82f6` (blue)
- Success button/toast: `#22c55e` (green)
- Status overdue: `#ef4444` (red), left-border on table row
- Status due soon: `#f59e0b` (amber), left-border on table row
- Status ok: `#22c55e` (green), left-border on table row
- Card background: `#fff`, shadow `0 1px 6px rgba(0,0,0,.08)`

## Typography
- Body font: system font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial`)
- Base size: 15px, line-height 1.5
- Stat values: 2rem normal, 2.6rem large
- Labels: uppercase, letter-spacing 0.6px, 0.75rem, color #64748b

## Component Patterns
- Buttons: `.btn` base + `.btn-primary` / `.btn-success` / `.btn-ghost` + `.btn-sm`
- Cards: `.card` (white bg, 10px radius, subtle shadow, 20px 24px padding)
- Badges: `.badge .badge-{category}` — colored by category (engine=blue, tires=pink, fluids=green, etc.)
- Toast notifications: fixed bottom-right, green for success, red for error
- Forms: inline expand/collapse pattern (`.open` class toggles `display: flex`)

## Layout
- Max content width: 1100px (updated from 960px in first review session)
- Main padding: 0 24px 60px
- Header: sticky, 60px height, dark navy

## Table Pattern (maintenance schedule)
- 4-column table: Type of Work (52% wide) + 3 time-bucket columns (< 3 months, 3–6 months, > 6 months)
- Bucket columns use colored left-border dividers: red, amber, green
- Status communicated via left border on the `.col-task` td (4px colored)
- Checkmark (`✓`) placed in the matching bucket cell

## Known Design Gaps (as of first review)
- Static files served with strong caching — requires cache-busting during dev
- No dark mode support
- No favicon
