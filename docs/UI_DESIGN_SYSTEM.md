# Responsible AI Digital Twin UI Design System

Version: `2026.08-research-console`

The interface is designed as a professional research / governance console rather than a generic Streamlit demo.

## Visual principles

- Light research-console background with restrained blue/teal accents.
- Consistent hero header on every page.
- Native Streamlit metrics styled as compact dashboard cards.
- Persistent status chips for PASS/WARN/FAIL and workflow states.
- Shared rounded cards, tabs, controls, data tables, and runtime panels.
- A seven-step governed workflow indicator across the Scenario Lab and Overview.
- Dense operational information is grouped into tabs instead of long vertical pages.
- Sidebar identity, environment, Twin version, phase, network boundary, and database status are visible at a glance.
- No decorative styling changes the security or governance semantics.

## Shared component module

`services/ui_service.py` contains the design system:

- `inject_global_styles()`
- `page_header()`
- `section_header()`
- `runtime_card()`
- `simple_card()`
- `workflow_stepper()`
- `render_phase_grid()`
- `status_chip_html()`
- `tone_for_status()`

This keeps page-level presentation consistent without adding a front-end framework or changing the database architecture.

## Accessibility / presentation

The palette keeps strong foreground/background contrast, state is never communicated by colour alone, and textual labels remain visible for status and workflow steps.
