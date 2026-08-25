from __future__ import annotations

import streamlit as st


POLISH_VERSION = "2026.08-research-experience-v3"


def research_polish_css() -> str:
    """Final research-demo visual layer.

    The base design system remains in ``services.ui_service``. These overrides
    improve presentation quality without changing application semantics, RBAC,
    persistence, simulation behaviour or evidence generation.
    """
    return r"""
<style>
/* =====================================================================
   Responsible AI Digital Twin · Research Experience v3
   ===================================================================== */
:root {
  --rai-v3-ink:#0b1324;
  --rai-v3-muted:#65758d;
  --rai-v3-line:#dce5ef;
  --rai-v3-blue:#2563eb;
  --rai-v3-indigo:#4338ca;
  --rai-v3-cyan:#0891b2;
  --rai-v3-teal:#0f766e;
  --rai-v3-soft:#f6f9fd;
  --rai-v3-shadow:0 16px 42px rgba(15,23,42,.055);
}

/* ---------- App chrome ---------- */
.stApp {
  background:
    radial-gradient(circle at 88% 2%, rgba(59,130,246,.075), transparent 31rem),
    radial-gradient(circle at 11% 84%, rgba(14,116,144,.045), transparent 28rem),
    linear-gradient(180deg,#f8fbff 0%,#f3f7fc 54%,#f7f9fc 100%) !important;
}
.block-container {
  max-width:1540px !important;
  padding-top:2.2rem !important;
  padding-left:2rem !important;
  padding-right:2rem !important;
  padding-bottom:4.5rem !important;
}
[data-testid="stDeployButton"] { display:none !important; }
header[data-testid="stHeader"] { background:rgba(248,251,255,.80) !important; backdrop-filter:blur(16px); }

/* ---------- Shared hero header: fixes clipping on every page ---------- */
.rai-hero {
  margin-top:.4rem !important;
  margin-bottom:1.2rem !important;
  border-radius:22px !important;
  border:1px solid rgba(203,213,225,.90) !important;
  padding:1.34rem 1.48rem 1.22rem !important;
  background:
    radial-gradient(circle at 94% -12%,rgba(37,99,235,.14),transparent 18rem),
    radial-gradient(circle at 80% 130%,rgba(8,145,178,.10),transparent 20rem),
    linear-gradient(135deg,rgba(255,255,255,.998),rgba(247,250,255,.995)) !important;
  box-shadow:var(--rai-v3-shadow) !important;
  isolation:isolate;
}
.rai-hero:before {
  content:"";
  position:absolute;
  left:0;top:0;bottom:0;width:4px;
  background:linear-gradient(180deg,#2563eb,#0891b2 62%,#0f766e);
  border-radius:22px 0 0 22px;
}
.rai-hero:after { opacity:.72 !important; }
.rai-eyebrow {
  display:inline-flex !important;
  align-items:center;
  gap:.34rem;
  width:fit-content;
  min-height:1.62rem;
  margin:0 0 .52rem 0 !important;
  padding:.22rem .56rem !important;
  border-radius:999px;
  border:1px solid rgba(147,197,253,.62);
  background:linear-gradient(135deg,rgba(239,246,255,.94),rgba(236,254,255,.86));
  color:#1d4ed8 !important;
  font-size:.61rem !important;
  line-height:1.15 !important;
  letter-spacing:.105em !important;
  font-weight:820 !important;
  position:relative;z-index:2;
}
.rai-hero-title {
  color:var(--rai-v3-ink) !important;
  font-size:clamp(1.78rem,2.55vw,2.42rem) !important;
  line-height:1.05 !important;
  letter-spacing:-.045em !important;
  position:relative;z-index:2;
}
.rai-hero-subtitle {
  color:#61718a !important;
  font-size:.93rem !important;
  line-height:1.54 !important;
  max-width:1160px !important;
  position:relative;z-index:2;
}

/* ---------- Typography + surfaces ---------- */
.rai-section { margin-top:.95rem !important; margin-bottom:.6rem !important; }
.rai-section-title { font-size:1.08rem !important; letter-spacing:-.024em !important; }
.rai-section-subtitle { color:#738198 !important; }
[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius:16px !important;
  border-color:#dfe7f0 !important;
  box-shadow:0 8px 25px rgba(15,23,42,.03) !important;
}
[data-testid="stMetric"] {
  min-height:108px !important;
  border-radius:16px !important;
  border:1px solid #dde6f0 !important;
  background:linear-gradient(145deg,#ffffff,#f9fbfe) !important;
  box-shadow:0 8px 24px rgba(15,23,42,.035) !important;
  transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease;
}
[data-testid="stMetric"]:hover {
  transform:translateY(-2px);
  border-color:#c5d5e8 !important;
  box-shadow:0 14px 32px rgba(15,23,42,.055) !important;
}
[data-testid="stMetricLabel"] { color:#7a8aa1 !important; font-size:.66rem !important; }
[data-testid="stMetricValue"] { color:#24324a !important; letter-spacing:-.04em !important; }

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {
  gap:.32rem !important;
  padding:.3rem !important;
  margin:.15rem 0 .62rem !important;
  border:1px solid #e0e7ef;
  border-radius:13px !important;
  background:rgba(238,243,248,.90) !important;
}
.stTabs [data-baseweb="tab"] {
  min-height:2.45rem !important;
  padding-left:1rem !important;
  padding-right:1rem !important;
  border-radius:9px !important;
  font-weight:680 !important;
}
.stTabs [aria-selected="true"] {
  color:#1d4ed8 !important;
  background:linear-gradient(145deg,#ffffff,#f8fbff) !important;
  box-shadow:0 4px 12px rgba(15,23,42,.07) !important;
}

/* ---------- Buttons ---------- */
.stButton > button,.stDownloadButton > button {
  border-radius:11px !important;
  min-height:2.7rem !important;
}
.stButton > button:not(:disabled):hover,.stDownloadButton > button:not(:disabled):hover {
  transform:translateY(-1px);
  box-shadow:0 8px 18px rgba(15,23,42,.07);
}

/* =====================================================================
   Sidebar · three-workspace navigation rail
   ===================================================================== */
[data-testid="stSidebar"] {
  background:
    radial-gradient(circle at 20% -5%,rgba(59,130,246,.07),transparent 13rem),
    linear-gradient(180deg,#fbfdff,#f7f9fc 70%,#f8fafc) !important;
  border-right:1px solid #dce5ef !important;
  box-shadow:10px 0 35px rgba(15,23,42,.035);
}
[data-testid="stSidebar"] > div:first-child { padding-top:.75rem !important; }

.rai-sidebar-brand-v3 {
  display:flex;align-items:center;gap:.72rem;
  position:relative;
  margin:.05rem .15rem .85rem !important;
  padding:.86rem .9rem !important;
  border:1px solid rgba(96,165,250,.18) !important;
  border-radius:16px !important;
  background:
    radial-gradient(circle at 100% 0%,rgba(56,189,248,.24),transparent 8rem),
    linear-gradient(145deg,#09172e,#102b55 68%,#0f4660) !important;
  box-shadow:0 12px 28px rgba(15,23,42,.15) !important;
}
.rai-sidebar-brand-mark {
  display:flex;align-items:center;justify-content:center;
  width:40px;height:40px;flex:0 0 40px;
  border-radius:12px;
  color:#e0f2fe;font-size:.72rem;font-weight:900;letter-spacing:.09em;
  border:1px solid rgba(125,211,252,.28);
  background:linear-gradient(145deg,rgba(37,99,235,.45),rgba(8,145,178,.35));
  box-shadow:inset 0 1px 0 rgba(255,255,255,.08),0 8px 18px rgba(2,6,23,.16);
}
.rai-sidebar-brand-copy { min-width:0; }
.rai-sidebar-brand-copy strong { display:block;color:#fff;font-size:.94rem;letter-spacing:-.02em; }
.rai-sidebar-brand-copy span { display:block;color:#b8c7db;font-size:.63rem;line-height:1.3;margin-top:.12rem; }
.rai-sidebar-live-dot {
  position:absolute;right:.82rem;top:.8rem;width:7px;height:7px;border-radius:50%;
  background:#34d399;box-shadow:0 0 0 4px rgba(52,211,153,.10),0 0 12px rgba(52,211,153,.55);
}

.rai-sidebar-context {
  margin:0 .15rem .58rem;
  padding:.72rem .78rem;
  border:1px solid #dfe7f0;
  border-radius:13px;
  background:rgba(255,255,255,.88);
  box-shadow:0 5px 16px rgba(15,23,42,.025);
}
.rai-sidebar-context-top { display:flex;align-items:center;justify-content:space-between;gap:.4rem; }
.rai-sidebar-overline { color:#94a3b8;font-size:.54rem;font-weight:850;letter-spacing:.11em;text-transform:uppercase; }
.rai-sidebar-overline-block { margin:.45rem .18rem .42rem;display:block; }
.rai-sidebar-role-pill { font-size:.54rem;font-weight:820;border-radius:999px;padding:.18rem .42rem;border:1px solid; }
.rai-sidebar-role-success { color:#047857;background:#ecfdf5;border-color:#a7f3d0; }
.rai-sidebar-role-info { color:#1d4ed8;background:#eff6ff;border-color:#bfdbfe; }
.rai-sidebar-user { margin-top:.35rem;color:#172033;font-size:.79rem;font-weight:760;overflow-wrap:anywhere; }
.rai-sidebar-role-copy { margin-top:.13rem;color:#7a879b;font-size:.61rem;line-height:1.35; }
.rai-sidebar-divider { height:1px;background:linear-gradient(90deg,transparent,#d7e0ea 15%,#d7e0ea 85%,transparent);margin:.72rem .1rem .35rem; }

.rai-sidebar-twin-card {
  margin:0 .15rem .56rem;
  padding:.72rem .78rem;
  border:1px solid #dfe7f0;border-radius:13px;
  background:linear-gradient(145deg,#ffffff,#f8fbff);
  box-shadow:0 5px 16px rgba(15,23,42,.025);
}
.rai-sidebar-twin-head { display:flex;align-items:flex-start;justify-content:space-between;gap:.5rem; }
.rai-sidebar-twin-name { color:#172033;font-size:.76rem;font-weight:770; }
.rai-sidebar-twin-meta { color:#7c8aa0;font-size:.59rem;margin-top:.1rem; }
.rai-sidebar-state-dot { width:8px;height:8px;border-radius:50%;margin-top:.18rem; }
.rai-sidebar-state-dot.online { background:#10b981;box-shadow:0 0 0 4px rgba(16,185,129,.09),0 0 9px rgba(16,185,129,.4); }
.rai-sidebar-state-dot.offline { background:#ef4444;box-shadow:0 0 0 4px rgba(239,68,68,.08); }
.rai-sidebar-status-row { margin-top:.56rem;display:flex;gap:.3rem;flex-wrap:wrap; }
.rai-sidebar-footer { margin:1rem .3rem .6rem;color:#9aa7b8;font-size:.54rem;line-height:1.45;text-align:center; }
.rai-sidebar-footer-sep { margin:0 .18rem;color:#c3ccd7; }

/* Streamlit navigation group labels */
[data-testid="stSidebarNav"] { margin-top:.2rem; }
[data-testid="stSidebarNav"] > div { gap:.15rem; }
[data-testid="stSidebarNav"] span[data-testid="stSidebarNavLink"] { border-radius:10px; }
[data-testid="stSidebarNav"] a {
  position:relative;
  margin:2px 5px !important;
  min-height:2.38rem;
  border-radius:10px !important;
  color:#5d6e85 !important;
  transition:background .14s ease,color .14s ease,transform .14s ease,box-shadow .14s ease;
}
[data-testid="stSidebarNav"] a:hover {
  color:#172033 !important;
  background:rgba(232,239,249,.88) !important;
  transform:translateX(2px);
}
[data-testid="stSidebarNav"] a[aria-current="page"] {
  color:#173b7a !important;
  font-weight:730 !important;
  background:linear-gradient(90deg,rgba(219,234,254,.96),rgba(239,246,255,.82)) !important;
  box-shadow:inset 3px 0 0 #2563eb,0 3px 10px rgba(37,99,235,.045);
}
/* Group names render as non-link text in current Streamlit. */
[data-testid="stSidebarNav"] p {
  margin-top:.62rem !important;
  margin-bottom:.18rem !important;
  padding-left:.52rem !important;
  color:#8796aa !important;
  font-size:.56rem !important;
  line-height:1.2 !important;
  letter-spacing:.105em !important;
  font-weight:850 !important;
  text-transform:uppercase !important;
}

/* =====================================================================
   Digital Twin page surfaces
   ===================================================================== */
.rai-twin-command {
  display:grid;
  grid-template-columns:minmax(0,1.48fr) repeat(3,minmax(0,.72fr));
  gap:.65rem;margin:.25rem 0 .95rem;
}
.rai-twin-command-card {
  position:relative;overflow:hidden;min-height:92px;
  border:1px solid #dfe7f1;border-radius:15px;padding:.78rem .84rem;
  background:linear-gradient(145deg,#fff,#f8fbff);
  box-shadow:0 8px 24px rgba(15,23,42,.035);
}
.rai-twin-command-card:after {
  content:"";position:absolute;right:-35px;top:-42px;width:100px;height:100px;border-radius:50%;
  background:radial-gradient(circle,rgba(59,130,246,.08),transparent 67%);pointer-events:none;
}
.rai-twin-command-card.primary {
  color:white;border-color:rgba(59,130,246,.24);
  background:radial-gradient(circle at 97% -20%,rgba(56,189,248,.32),transparent 8rem),linear-gradient(135deg,#0c2048,#123e66 62%,#0f5d63 125%);
}
.rai-twin-command-kicker { font-size:.58rem;letter-spacing:.095em;text-transform:uppercase;font-weight:820;color:#93a1b4; }
.primary .rai-twin-command-kicker { color:#9bd8ff; }
.rai-twin-command-value { margin-top:.27rem;font-size:.98rem;line-height:1.24;font-weight:770;color:#122039; }
.primary .rai-twin-command-value { color:#fff;font-size:1.04rem; }
.rai-twin-command-detail { margin-top:.22rem;font-size:.66rem;line-height:1.38;color:#728198; }
.primary .rai-twin-command-detail { color:#c6d8e9; }

.rai-operation-grid { display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.6rem;margin:.28rem 0 .35rem; }
.rai-operation-card {
  position:relative;overflow:hidden;min-height:120px;padding:.74rem .8rem;
  border:1px solid #dfe6ef;border-radius:14px;background:linear-gradient(145deg,#fff,#fafcff);
  box-shadow:0 6px 18px rgba(15,23,42,.026);
}
.rai-operation-card:before { content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--op-accent,#2563eb); }
.rai-operation-id { display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:9px;color:var(--op-accent,#1d4ed8);background:#f2f7ff;border:1px solid #dbeafe;font-size:.61rem;font-weight:880; }
.rai-operation-name { margin-top:.47rem;font-size:.83rem;font-weight:780;color:#122039; }
.rai-operation-detail { margin-top:.22rem;font-size:.65rem;line-height:1.42;color:#6f7e94; }
.rai-operation-card.o2 { --op-accent:#d97706; }
.rai-operation-card.o3 { --op-accent:#7c3aed; }
.rai-operation-card.o4 { --op-accent:#059669; }

.rai-twin-hint-grid { display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.55rem;margin:.68rem 0 .8rem; }
.rai-twin-hint { border:1px solid #dce7f3;border-radius:12px;padding:.64rem .72rem;background:linear-gradient(145deg,#f3f8ff,#f7fbff);color:#5f7088;font-size:.67rem;line-height:1.42; }
.rai-twin-hint strong { color:#29496f; }

@media(max-width:1100px) {
  .rai-twin-command { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .rai-operation-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
  .rai-twin-hint-grid { grid-template-columns:1fr; }
}
@media(max-width:760px) {
  .block-container { padding-top:1.7rem !important;padding-left:.9rem !important;padding-right:.9rem !important; }
  .rai-twin-command,.rai-operation-grid { grid-template-columns:1fr; }
}
</style>
"""


def inject_research_polish() -> None:
    st.markdown(research_polish_css(), unsafe_allow_html=True)
