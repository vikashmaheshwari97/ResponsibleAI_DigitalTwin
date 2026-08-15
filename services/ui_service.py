from __future__ import annotations

import html

import streamlit as st


UI_VERSION = "2026.08-research-console-v2"


def _esc(value: object) -> str:
    return html.escape(str(value))


def _render_html(markup: str) -> None:
    """
    Render app-owned HTML without Markdown code-block interpretation.

    Streamlit >= 1.33 exposes st.html(). The fallback keeps older compatible
    Streamlit versions usable while avoiding leading indentation in markup.
    """
    markup = markup.strip()
    if hasattr(st, "html"):
        st.html(markup)
    else:
        st.markdown(markup, unsafe_allow_html=True)


def global_css() -> str:
    return r"""
<style>
:root {
  --rai-bg: #f4f7fb;
  --rai-surface: #ffffff;
  --rai-surface-soft: #f8fafc;
  --rai-border: #dfe6ef;
  --rai-border-strong: #cbd5e1;
  --rai-text: #0f172a;
  --rai-muted: #64748b;
  --rai-primary: #1e40af;
  --rai-primary-2: #2563eb;
  --rai-primary-soft: #eff6ff;
  --rai-accent: #0f766e;
  --rai-success: #047857;
  --rai-success-soft: #ecfdf5;
  --rai-warning: #a16207;
  --rai-warning-soft: #fffbeb;
  --rai-danger: #b91c1c;
  --rai-danger-soft: #fef2f2;
  --rai-radius: 14px;
  --rai-shadow: 0 5px 18px rgba(15, 23, 42, .045);
}

.stApp {
  background:
    radial-gradient(circle at 91% 2%, rgba(37, 99, 235, .055), transparent 31rem),
    radial-gradient(circle at 4% 92%, rgba(15, 118, 110, .035), transparent 28rem),
    var(--rai-bg);
  color: var(--rai-text);
}

.block-container {
  max-width: 1500px;
  padding-top: 1.1rem;
  padding-bottom: 4rem;
  padding-left: 1.8rem;
  padding-right: 1.8rem;
}

[data-testid="stSidebar"] {
  background: #fbfcfe;
  border-right: 1px solid var(--rai-border);
}

[data-testid="stSidebar"] > div:first-child {
  padding-top: .7rem;
}

[data-testid="stSidebarNav"] a {
  border-radius: 8px;
  margin: 1px 5px;
}

[data-testid="stSidebarNav"] a:hover {
  background: #eef4ff;
}

h1,h2,h3,h4,h5,h6 {
  color: var(--rai-text);
  letter-spacing: -.018em;
}

p, li, label, .stCaption {
  color: var(--rai-muted);
}

/* ---------- Native metrics ---------- */
[data-testid="stMetric"] {
  background: rgba(255,255,255,.98);
  border: 1px solid var(--rai-border);
  border-radius: var(--rai-radius);
  padding: .82rem .92rem .72rem .92rem;
  box-shadow: 0 3px 12px rgba(15,23,42,.03);
  min-height: 102px;
}

[data-testid="stMetricLabel"] {
  font-size: .69rem;
  font-weight: 760;
  letter-spacing: .055em;
  text-transform: uppercase;
  color: var(--rai-muted);
}

[data-testid="stMetricValue"] {
  color: var(--rai-text);
  font-weight: 740;
  font-size: clamp(1.25rem, 2vw, 1.75rem);
  overflow: visible;
}

/* ---------- Containers ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-color: var(--rai-border) !important;
  border-radius: var(--rai-radius) !important;
  background: rgba(255,255,255,.96);
  box-shadow: 0 3px 14px rgba(15,23,42,.025);
}

div[data-testid="stAlert"] {
  border-radius: 11px;
  border-width: 1px;
}

/* ---------- Buttons: high contrast, including nested Streamlit text ---------- */
.stButton > button,
.stDownloadButton > button {
  border-radius: 10px;
  min-height: 2.65rem;
  font-weight: 680;
  border: 1px solid var(--rai-border-strong);
  transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}

.stButton > button[kind="primary"]:not(:disabled),
.stDownloadButton > button[kind="primary"]:not(:disabled) {
  background: linear-gradient(135deg, #1e40af 0%, #2563eb 68%, #0f766e 155%) !important;
  border-color: #1d4ed8 !important;
  color: #ffffff !important;
  box-shadow: 0 7px 17px rgba(37,99,235,.18);
}

.stButton > button[kind="primary"]:not(:disabled) *,
.stDownloadButton > button[kind="primary"]:not(:disabled) * {
  color: #ffffff !important;
  opacity: 1 !important;
  fill: #ffffff !important;
}

.stButton > button:not(:disabled):hover,
.stDownloadButton > button:not(:disabled):hover {
  transform: translateY(-1px);
  border-color: #94a3b8;
}

/* Important: do not paint disabled primary buttons blue. */
.stButton > button:disabled,
.stDownloadButton > button:disabled {
  background: #e8edf4 !important;
  border-color: #d5dde8 !important;
  color: #64748b !important;
  opacity: 1 !important;
  box-shadow: none !important;
  cursor: not-allowed !important;
}

.stButton > button:disabled *,
.stDownloadButton > button:disabled * {
  color: #64748b !important;
  opacity: 1 !important;
  fill: #64748b !important;
}

/* ---------- Inputs ---------- */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div {
  border-radius: 9px !important;
  border-color: var(--rai-border-strong) !important;
  background: rgba(255,255,255,.98) !important;
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
  gap: .35rem;
  padding: .32rem;
  background: #edf2f7;
  border-radius: 10px;
}

.stTabs [data-baseweb="tab"] {
  border-radius: 7px;
  padding-left: .9rem;
  padding-right: .9rem;
  font-weight: 650;
}

.stTabs [aria-selected="true"] {
  background: white !important;
  box-shadow: 0 2px 7px rgba(15,23,42,.06);
}

/* ---------- Tables ---------- */
[data-testid="stDataFrame"] {
  border: 1px solid var(--rai-border);
  border-radius: 11px;
  overflow: hidden;
  background: white;
}

/* ---------- Page hero ---------- */
.rai-hero {
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(255,255,255,.99), rgba(249,251,254,.99));
  border: 1px solid var(--rai-border);
  border-radius: 17px;
  padding: 1.15rem 1.3rem 1.05rem 1.3rem;
  box-shadow: var(--rai-shadow);
  margin-bottom: .95rem;
}

.rai-hero:after {
  content: "";
  position: absolute;
  width: 235px;
  height: 235px;
  border-radius: 50%;
  right: -110px;
  top: -145px;
  background: radial-gradient(circle, rgba(37,99,235,.12), rgba(15,118,110,.02) 65%, transparent 71%);
  pointer-events: none;
}

.rai-eyebrow {
  font-size: .68rem;
  text-transform: uppercase;
  letter-spacing: .095em;
  font-weight: 780;
  color: var(--rai-primary);
  margin-bottom: .36rem;
}

.rai-hero-title {
  font-size: clamp(1.55rem, 2.35vw, 2.15rem);
  line-height: 1.12;
  font-weight: 780;
  letter-spacing: -.035em;
  color: var(--rai-text);
  margin: 0;
  max-width: 1050px;
}

.rai-hero-subtitle {
  color: var(--rai-muted);
  font-size: .91rem;
  line-height: 1.5;
  max-width: 1050px;
  margin: .45rem 0 0 0;
}

/* ---------- Section titles ---------- */
.rai-section {
  margin-top: .62rem;
  margin-bottom: .5rem;
}

.rai-section-title {
  color: var(--rai-text);
  font-size: 1.03rem;
  font-weight: 740;
  letter-spacing: -.016em;
  margin-bottom: .08rem;
}

.rai-section-subtitle {
  color: var(--rai-muted);
  font-size: .8rem;
  line-height: 1.4;
}

/* ---------- Chips ---------- */
.rai-chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: .22rem .53rem;
  font-size: .67rem;
  font-weight: 760;
  line-height: 1.1;
  border: 1px solid transparent;
  white-space: nowrap;
}

.rai-chip-success {color:#047857;background:#ecfdf5;border-color:#a7f3d0;}
.rai-chip-warning {color:#92400e;background:#fffbeb;border-color:#fde68a;}
.rai-chip-danger {color:#b91c1c;background:#fef2f2;border-color:#fecaca;}
.rai-chip-info {color:#1d4ed8;background:#eff6ff;border-color:#bfdbfe;}
.rai-chip-neutral {color:#475569;background:#f8fafc;border-color:#e2e8f0;}

/* ---------- Compact service strip ---------- */
.rai-service-strip {
  display:grid;
  grid-template-columns:repeat(3,minmax(0,1fr));
  gap:.55rem;
  margin:.25rem 0 .75rem 0;
}

.rai-service-item {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:.65rem;
  background:rgba(255,255,255,.98);
  border:1px solid var(--rai-border);
  border-radius:11px;
  padding:.67rem .78rem;
  min-width:0;
}

.rai-service-main {
  min-width:0;
}

.rai-service-label {
  color:#94a3b8;
  text-transform:uppercase;
  letter-spacing:.07em;
  font-size:.61rem;
  font-weight:780;
  margin-bottom:.12rem;
}

.rai-service-value {
  color:var(--rai-text);
  font-size:.8rem;
  font-weight:690;
  overflow:hidden;
  text-overflow:ellipsis;
  white-space:nowrap;
}

/* ---------- Compact key/value detail grid ---------- */
.rai-detail-grid {
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:.52rem;
  margin-top:.72rem;
}

.rai-detail {
  background:#f8fafc;
  border:1px solid var(--rai-border);
  border-radius:10px;
  padding:.65rem .72rem;
  min-width:0;
}

.rai-detail-label {
  color:#94a3b8;
  font-size:.61rem;
  text-transform:uppercase;
  letter-spacing:.065em;
  font-weight:770;
  margin-bottom:.2rem;
}

.rai-detail-value {
  color:var(--rai-text);
  font-size:.88rem;
  font-weight:700;
  overflow-wrap:anywhere;
}

/* ---------- Workflow stepper ---------- */
.rai-stepper {
  display:flex;
  align-items:stretch;
  gap:.34rem;
  margin:.38rem 0 .8rem 0;
}

.rai-step {
  flex:1 1 0;
  padding:.5rem .55rem;
  border-radius:9px;
  border:1px solid var(--rai-border);
  background:white;
  color:#64748b;
  font-size:.7rem;
  font-weight:680;
  text-align:center;
}

.rai-step small {
  display:block;
  font-size:.56rem;
  text-transform:uppercase;
  letter-spacing:.05em;
  color:#94a3b8;
  margin-bottom:.08rem;
}

.rai-step.done {
  background:var(--rai-success-soft);
  border-color:#a7f3d0;
  color:#047857;
}

.rai-step.active {
  background:var(--rai-primary-soft);
  border-color:#93c5fd;
  color:#1d4ed8;
  box-shadow:inset 0 0 0 1px rgba(29,78,216,.07);
}

/* ---------- Phase grid: must be rendered with st.html() ---------- */
.rai-phase-grid {
  display:grid;
  grid-template-columns:repeat(5,minmax(0,1fr));
  gap:.55rem;
  margin:.45rem 0 .8rem 0;
}

.rai-phase-card {
  background:white;
  border:1px solid var(--rai-border);
  border-radius:11px;
  padding:.68rem .72rem;
  min-width:0;
  min-height:112px;
}

.rai-phase-number {
  color:var(--rai-primary);
  font-weight:780;
  font-size:.6rem;
  text-transform:uppercase;
  letter-spacing:.075em;
}

.rai-phase-name {
  color:var(--rai-text);
  font-weight:690;
  font-size:.76rem;
  line-height:1.28;
  margin:.13rem 0 .38rem 0;
  min-height:2.0rem;
}

.rai-progress-track {
  width:100%;
  height:5px;
  background:#e2e8f0;
  border-radius:999px;
  overflow:hidden;
}

.rai-progress-fill {
  height:100%;
  border-radius:999px;
  background:linear-gradient(90deg,#2563eb,#0f766e);
}

.rai-kicker {
  color:#64748b;
  font-size:.61rem;
  line-height:1.25;
  margin-top:.3rem;
}

/* ---------- Summary cards ---------- */
.rai-summary-grid {
  display:grid;
  grid-template-columns:repeat(4,minmax(0,1fr));
  gap:.55rem;
  margin:.25rem 0 .7rem 0;
}

.rai-summary-card {
  background:white;
  border:1px solid var(--rai-border);
  border-radius:12px;
  padding:.78rem .82rem;
  min-height:94px;
}

.rai-summary-label {
  color:#94a3b8;
  font-size:.61rem;
  text-transform:uppercase;
  letter-spacing:.065em;
  font-weight:780;
}

.rai-summary-value {
  color:var(--rai-text);
  font-size:1.35rem;
  font-weight:760;
  letter-spacing:-.025em;
  margin-top:.22rem;
  overflow-wrap:anywhere;
}

.rai-summary-detail {
  color:var(--rai-muted);
  font-size:.67rem;
  margin-top:.15rem;
}

/* ---------- Sidebar ---------- */
.rai-sidebar-brand {
  background:linear-gradient(145deg,#0f172a,#172554);
  color:white;
  border-radius:13px;
  padding:.82rem .88rem;
  margin:0 0 .7rem 0;
  box-shadow:0 7px 18px rgba(15,23,42,.12);
}

.rai-sidebar-brand strong {
  color:white;
  font-size:.96rem;
  letter-spacing:-.015em;
}

.rai-sidebar-brand span {
  display:block;
  color:#cbd5e1;
  font-size:.67rem;
  margin-top:.15rem;
  line-height:1.35;
}

.rai-sidebar-line {
  background:white;
  border:1px solid var(--rai-border);
  border-radius:10px;
  padding:.62rem .68rem;
  margin-bottom:.45rem;
}

.rai-sidebar-label {
  color:#94a3b8;
  font-size:.58rem;
  text-transform:uppercase;
  letter-spacing:.08em;
  font-weight:780;
}

.rai-sidebar-value {
  color:var(--rai-text);
  font-size:.75rem;
  font-weight:670;
  margin-top:.14rem;
}

@media (max-width: 1100px) {
  .rai-phase-grid {grid-template-columns:repeat(3,minmax(0,1fr));}
  .rai-detail-grid {grid-template-columns:repeat(2,minmax(0,1fr));}
}

@media (max-width: 800px) {
  .block-container {padding-left:.9rem;padding-right:.9rem;}
  .rai-service-strip,
  .rai-summary-grid,
  .rai-phase-grid {grid-template-columns:1fr;}
  .rai-stepper {flex-wrap:wrap;}
  .rai-step {flex:1 1 120px;}
}
</style>
"""


def inject_global_styles() -> None:
    st.markdown(global_css(), unsafe_allow_html=True)


def status_chip_html(label: str, tone: str = "neutral") -> str:
    tone = tone if tone in {"success", "warning", "danger", "info", "neutral"} else "neutral"
    return f'<span class="rai-chip rai-chip-{tone}">{_esc(label)}</span>'


def page_header(
    title: str,
    subtitle: str,
    *,
    icon: str = "◆",
    eyebrow: str = "Responsible AI Digital Twin",
    badge: str | None = None,
    badge_tone: str = "info",
) -> None:
    badge_html = (
        f'<div style="margin-top:.62rem">{status_chip_html(badge, badge_tone)}</div>'
        if badge
        else ""
    )
    _render_html(
        '<div class="rai-hero">'
        f'<div class="rai-eyebrow">{_esc(icon)} {_esc(eyebrow)}</div>'
        f'<h1 class="rai-hero-title">{_esc(title)}</h1>'
        f'<p class="rai-hero-subtitle">{_esc(subtitle)}</p>'
        f'{badge_html}'
        '</div>'
    )


def section_header(title: str, subtitle: str | None = None) -> None:
    subtitle_html = (
        f'<div class="rai-section-subtitle">{_esc(subtitle)}</div>'
        if subtitle
        else ""
    )
    _render_html(
        '<div class="rai-section">'
        f'<div class="rai-section-title">{_esc(title)}</div>'
        f'{subtitle_html}'
        '</div>'
    )


def runtime_card(
    *,
    label: str,
    value: str,
    detail: str,
    tone: str = "neutral",
    icon: str = "●",
) -> None:
    # Kept for pages that need a larger single-service panel.
    _render_html(
        '<div class="rai-summary-card">'
        f'<div class="rai-summary-label">{_esc(label)}</div>'
        f'<div class="rai-summary-value" style="font-size:.98rem">{_esc(icon)} {_esc(value)}</div>'
        f'<div style="margin-top:.34rem">{status_chip_html(tone.upper(), tone)}</div>'
        f'<div class="rai-summary-detail">{_esc(detail)}</div>'
        '</div>'
    )


def simple_card(title: str, body: str, *, icon: str = "◆") -> None:
    _render_html(
        '<div class="rai-summary-card">'
        f'<div class="rai-summary-label">{_esc(icon)} {_esc(title)}</div>'
        f'<div class="rai-summary-detail" style="margin-top:.42rem;font-size:.78rem;line-height:1.48">'
        f'{_esc(body)}</div>'
        '</div>'
    )


def service_strip(items: list[dict]) -> None:
    parts = ['<div class="rai-service-strip">']
    for item in items:
        tone = item.get("tone", "neutral")
        parts.append(
            '<div class="rai-service-item">'
            '<div class="rai-service-main">'
            f'<div class="rai-service-label">{_esc(item.get("label", ""))}</div>'
            f'<div class="rai-service-value">{_esc(item.get("icon", "●"))} {_esc(item.get("value", ""))}</div>'
            '</div>'
            f'{status_chip_html(item.get("status", tone.upper()), tone)}'
            '</div>'
        )
    parts.append("</div>")
    _render_html("".join(parts))


def detail_grid(items: list[tuple[str, str]]) -> None:
    parts = ['<div class="rai-detail-grid">']
    for label, value in items:
        parts.append(
            '<div class="rai-detail">'
            f'<div class="rai-detail-label">{_esc(label)}</div>'
            f'<div class="rai-detail-value">{_esc(value)}</div>'
            '</div>'
        )
    parts.append("</div>")
    _render_html("".join(parts))


def summary_grid(items: list[dict]) -> None:
    parts = ['<div class="rai-summary-grid">']
    for item in items:
        parts.append(
            '<div class="rai-summary-card">'
            f'<div class="rai-summary-label">{_esc(item.get("label", ""))}</div>'
            f'<div class="rai-summary-value">{_esc(item.get("value", ""))}</div>'
            f'<div class="rai-summary-detail">{_esc(item.get("detail", ""))}</div>'
            '</div>'
        )
    parts.append("</div>")
    _render_html("".join(parts))


_WORKFLOW = [
    ("ready", "Ready"),
    ("running", "Validate"),
    ("vulnerable", "Finding"),
    ("awaiting_approval", "Approve"),
    ("remediating", "Apply"),
    ("verifying", "Verify"),
    ("secured", "Secured"),
]


def workflow_stepper(current_phase: str) -> None:
    normalized = "secured" if current_phase == "validated" else current_phase
    ids = [key for key, _ in _WORKFLOW]
    try:
        current_index = ids.index(normalized)
    except ValueError:
        current_index = 0

    parts = ['<div class="rai-stepper">']
    for index, (_, label) in enumerate(_WORKFLOW):
        cls = "done" if index < current_index else "active" if index == current_index else ""
        parts.append(
            f'<div class="rai-step {cls}"><small>{index + 1}</small>{_esc(label)}</div>'
        )
    parts.append("</div>")
    _render_html("".join(parts))


def render_phase_grid(rows: list[dict]) -> None:
    # Compact HTML with no Markdown indentation; st.html avoids raw markup/code rendering.
    parts = ['<div class="rai-phase-grid">']
    for row in rows:
        progress_raw = str(row.get("Progress", "0%")).replace("~", "").replace("%", "")
        try:
            progress = max(0, min(100, int(float(progress_raw))))
        except ValueError:
            progress = 0

        parts.append(
            '<div class="rai-phase-card">'
            f'<div class="rai-phase-number">Phase {_esc(row.get("Phase"))}</div>'
            f'<div class="rai-phase-name">{_esc(row.get("Area"))}</div>'
            '<div class="rai-progress-track">'
            f'<div class="rai-progress-fill" style="width:{progress}%"></div>'
            '</div>'
            f'<div class="rai-kicker">{_esc(row.get("Progress"))} · {_esc(row.get("State"))}</div>'
            '</div>'
        )
    parts.append("</div>")
    _render_html("".join(parts))


def tone_for_status(value: str | None) -> str:
    text = (value or "").strip().lower()
    if text in {
        "pass", "passed", "complete", "completed", "secured", "validated",
        "healthy", "online", "applied", "permit", "approved",
    }:
        return "success"
    if text in {
        "fail", "failed", "vulnerable", "offline", "blocked", "block", "error",
    }:
        return "danger"
    if text in {
        "warn", "warning", "running", "testing", "pending",
        "awaiting_approval", "proposal ready", "remediating", "verifying",
    }:
        return "warning"
    if text in {"ready", "standby", "info"}:
        return "info"
    return "neutral"
