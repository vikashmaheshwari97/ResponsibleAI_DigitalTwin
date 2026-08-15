# Professional UI v2 Hotfix

Version: `0.6.1-professional-ui-v2`

This overlay fixes the UI issues observed after the Phase 1–10 professional-console upgrade.

## Fixed

- Primary action button text now has enforced white contrast.
- Disabled primary buttons no longer keep the blue gradient; they render neutral grey with readable text.
- Project phase cards are rendered through `st.html()` / compact non-indented HTML, preventing raw `<div>` markup from appearing as a Markdown code block.
- The long Alembic schema value is no longer truncated inside a native metric card.

## Reduced repetition

- Sidebar now shows only compact session and current-Twin context.
- Runtime detail remains on Overview / Scenario Lab rather than being repeated verbatim on every page.
- Scenario Lab runtime state uses a compact three-item service strip instead of three large cards.
- Scenario details use one compact summary instead of repeating the same values across multiple large metric cards.
- Agent-state cards were removed from Scenario Lab because Agent Activity is the dedicated operational view.
- Release Readiness now groups detailed commands/evidence in tabs instead of repeating them as separate vertical sections.

## Database

No database migration.
Expected Alembic head remains `005_twin_snapshots`.

## UT deployment

Still deferred.
