import streamlit as st
from services import initialize_session_state, reset_demo
from services.database_service import database_health
from services.policy_registry_service import seed_policy_rules
st.set_page_config(page_title="Responsible AI Digital Twin",page_icon="🛡️",layout="wide",initial_sidebar_state="expanded")
initialize_session_state()
db=database_health()
if db["connected"]:
    try: seed_policy_rules()
    except Exception: pass
st.markdown("""<style>.block-container {padding-top:1.6rem;padding-bottom:3rem;max-width:1500px;}[data-testid='stSidebar']{border-right:1px solid #e5e7eb;}</style>""",unsafe_allow_html=True)
pages={
    "Platform":[st.Page("pages/overview.py",title="Overview",icon="🏠",default=True),st.Page("pages/digital_twin.py",title="Digital Twin",icon="🔷")],
    "AI Validation":[st.Page("pages/scenario_lab.py",title="Security Scenario Lab",icon="🧪"),st.Page("pages/agents.py",title="Agent Activity",icon="🤖")],
    "Governance & Evidence":[st.Page("pages/run_history.py",title="Run History",icon="🗃️"),st.Page("pages/compliance.py",title="Compliance",icon="⚖️"),st.Page("pages/audit.py",title="Audit Trail",icon="📋"),st.Page("pages/reports.py",title="Reports",icon="📊")],
}
navigation=st.navigation(pages)
with st.sidebar:
    st.markdown("### 🛡️ RAI Twin"); st.caption("Digital-Twin-Driven Responsible AI Platform"); st.divider(); st.caption("ENVIRONMENT"); st.success("● SANDBOX PoC")
    st.write(f"**Twin:** {st.session_state.twin['name']}"); st.write(f"**Version:** {st.session_state.twin['version']}"); st.write(f"**State:** {st.session_state.phase.replace('_',' ').title()}"); st.write(f"**Network:** {st.session_state.twin['external_network']}")
    st.write(f"**LLM:** {st.session_state.get('ollama_model') or 'auto-select in Scenario Lab'}")
    db=database_health(); st.write("**Evidence DB:** PostgreSQL ✓" if db["connected"] else "**Evidence DB:** offline")
    st.divider()
    if st.button("↻ Reset Demo",use_container_width=True): reset_demo(); st.rerun()
navigation.run()
