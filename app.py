"""Streamlit UI for MaydaIQ."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.config import LOGO_PATH
from src.orchestrator import run_incident
from src.schemas import IncidentInput
from src.tools.runtime_status import get_runtime_status
from src.tools.sample_incidents import get_sample_incident, list_sample_incidents


LOGO = Path(LOGO_PATH)

st.set_page_config(page_title="MaydaIQ", page_icon=str(LOGO) if LOGO.exists() else "!", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --navy: #061b49;
        --navy-2: #0d2b67;
        --teal: #12b8b3;
        --red: #f04e3e;
        --amber: #d98b1f;
        --green: #218358;
        --ink: #13213b;
        --muted: #667085;
        --line: #d9e2ef;
        --panel: #ffffff;
        --wash: #f4f8fb;
    }
    .stApp, [data-testid="stAppViewContainer"] {
        background: #f4f8fb;
        color: var(--ink);
    }
    .block-container {
        padding-top: 1.2rem;
        max-width: 1360px;
    }
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        letter-spacing: 0;
    }
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li {
        color: var(--ink);
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #061b49 0%, #0a275f 55%, #08204d 100%);
    }
    section[data-testid="stSidebar"] * {
        color: #f7fbff;
    }
    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: #13213b !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        color: #f7fbff;
    }
    section[data-testid="stSidebar"] .stButton button {
        background: #ffffff;
        color: #061b49 !important;
        border: 1px solid #bdd7ff;
        font-weight: 800;
        white-space: normal;
        min-height: 44px;
    }
    section[data-testid="stSidebar"] .stButton button p,
    section[data-testid="stSidebar"] .stButton button span {
        color: #061b49 !important;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background: #e9fbfa;
        border-color: #12b8b3;
    }
    .stButton button[kind="primary"] {
        background: #f04e3e;
        color: #ffffff !important;
        border: 1px solid #f04e3e;
        font-weight: 850;
    }
    .stTextArea textarea,
    .stTextInput input {
        background: #ffffff !important;
        color: #101828 !important;
        border: 1px solid #b8c7da !important;
    }
    .hero {
        display: grid;
        grid-template-columns: minmax(0, 1.25fr) minmax(280px, 0.75fr);
        gap: 1rem;
        align-items: stretch;
        padding: 1rem 0 0.8rem;
    }
    .brand-row {
        display: flex;
        gap: 1rem;
        align-items: center;
    }
    .brand-copy h1 {
        margin: 0;
        font-size: clamp(2.1rem, 4vw, 4.2rem);
        line-height: 1;
        color: var(--navy);
        letter-spacing: 0;
    }
    .brand-copy p {
        margin: 0.45rem 0 0;
        color: #344054;
        font-size: 1.05rem;
    }
    .logo-shell {
        width: 92px;
        height: 92px;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: white;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 16px 42px rgba(6, 27, 73, 0.12);
        overflow: hidden;
    }
    .chips {
        display: flex;
        gap: 0.45rem;
        flex-wrap: wrap;
        margin-top: 0.85rem;
    }
    .chip {
        display: inline-flex;
        align-items: center;
        min-height: 28px;
        padding: 0.2rem 0.55rem;
        border: 1px solid var(--line);
        border-radius: 6px;
        background: #ffffff;
        color: var(--navy);
        font-size: 0.82rem;
        font-weight: 700;
    }
    .chip.live { border-color: rgba(18, 184, 179, 0.6); background: #e9fbfa; color: #086460; }
    .chip.local { border-color: #d7b16a; background: #fff7e8; color: #80570e; }
    .mission-panel {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: linear-gradient(180deg, #ffffff 0%, #f4f8fb 100%);
        padding: 0.9rem;
        box-shadow: 0 12px 32px rgba(6, 27, 73, 0.08);
    }
    .mission-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.55rem;
    }
    .mission-tile {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 0.7rem;
        background: white;
        min-height: 118px;
    }
    .mission-tile .num {
        color: var(--teal);
        font-weight: 800;
        font-size: 1.45rem;
    }
    .mission-tile .label {
        color: var(--navy);
        font-weight: 800;
        margin-top: 0.15rem;
    }
    .mission-tile .text {
        color: var(--muted);
        font-size: 0.84rem;
        margin-top: 0.35rem;
    }
    .workband {
        border-top: 1px solid var(--line);
        margin-top: 0.6rem;
        padding-top: 1rem;
    }
    .section-title {
        font-size: 1.05rem;
        color: #06306f;
        font-weight: 850;
        margin: 0.1rem 0 0.65rem;
    }
    .sample-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.45rem;
    }
    .status-card, .result-card {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: white;
        padding: 0.85rem;
        min-height: 100%;
    }
    .status-label {
        font-size: 0.76rem;
        font-weight: 800;
        color: var(--muted);
        text-transform: uppercase;
    }
    .status-value {
        margin-top: 0.25rem;
        color: var(--navy);
        font-size: 1.08rem;
        font-weight: 850;
        overflow-wrap: anywhere;
        line-height: 1.18;
    }
    .status-card {
        overflow: hidden;
    }
    .risk-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        font-weight: 850;
        letter-spacing: 0;
        color: white;
    }
    .risk-low { background: var(--green); }
    .risk-moderate { background: var(--amber); }
    .risk-high { background: #b54708; }
    .risk-critical { background: var(--red); }
    .trace-row {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.55rem;
    }
    .trace-step {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 0.65rem;
        background: #fbfdff;
        min-height: 94px;
    }
    .trace-step b {
        color: var(--navy);
    }
    .trace-step p {
        color: var(--muted);
        font-size: 0.84rem;
        margin: 0.25rem 0 0;
    }
    .safety-note {
        border: 1px solid #ffd0ca;
        border-left: 5px solid var(--red);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        background: #fff7f5;
        color: #681f17;
    }
    .small-muted {
        color: var(--muted);
        font-size: 0.85rem;
        overflow-wrap: anywhere;
    }
    div[data-testid="stTabs"] button p {
        color: #101828 !important;
        font-weight: 750;
    }
    @media (max-width: 900px) {
        .hero, .mission-grid, .sample-grid, .trace-row {
            grid-template-columns: 1fr;
        }
        .logo-shell {
            width: 74px;
            height: 74px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _risk_badge(level: str) -> str:
    return f'<span class="risk-badge risk-{level.lower()}">{level}</span>'


def _set_sample(sample_key: str) -> None:
    sample = get_sample_incident(sample_key)
    st.session_state["sample_scenario"] = sample_key
    st.session_state["pending_prompt"] = str(sample["text"])


def _render_list(title: str, items: list[str]) -> None:
    st.markdown(f"**{title}**")
    if not items:
        st.caption("None")
        return
    for item in items:
        st.markdown(f"- {item}")


def _runtime_chip(status: dict[str, object]) -> str:
    mode = str(status["mode"])
    if mode == "FOUNDRY_LIVE_READY":
        return '<span class="chip live">Foundry live ready</span>'
    if mode == "LOCAL_DEMO":
        return '<span class="chip local">Local demo mode</span>'
    return '<span class="chip local">Local fallback</span>'


def _source_label(playbook_source: str) -> str:
    if playbook_source.startswith("foundry"):
        return "Microsoft Foundry agent"
    if playbook_source.startswith("runtime"):
        return "Runtime fallback"
    return "Local knowledge pack"


def _assistant_message(result) -> str:
    risk = result.risk_assessment
    plan = result.action_plan
    packet = result.responder_packet
    lead = plan.do_now[0] if plan.do_now else plan.situation_summary
    avoid = plan.avoid[0] if plan.avoid else "Avoid unsafe areas while details are uncertain."
    escalation = plan.call_or_escalate[0] if plan.call_or_escalate else "No immediate emergency escalation was triggered by this report."
    return (
        f"I classify this as **{risk.risk_level}** risk in **{risk.selected_mode}** mode with **{risk.confidence}** confidence.\n\n"
        f"**Do now:** {lead}\n\n"
        f"**Avoid:** {avoid}\n\n"
        f"**Escalation:** {escalation}\n\n"
        f"Human escalation required: **{str(packet.human_escalation_required).lower()}**. "
        "I did not contact authorities; this is a responder-ready simulation packet."
    )


if "sample_scenario" not in st.session_state:
    st.session_state["sample_scenario"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "pending_prompt" not in st.session_state:
    st.session_state["pending_prompt"] = None
if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "last_source" not in st.session_state:
    st.session_state["last_source"] = None

runtime_status = get_runtime_status()

with st.sidebar:
    if LOGO.exists():
        st.image(str(LOGO), width=118)
    st.header("Mission Control")
    st.caption("Reasoning Agents track")
    st.markdown(_runtime_chip(runtime_status), unsafe_allow_html=True)
    st.markdown(f"<span class='chip'>Auth: {runtime_status['auth_mode']}</span>", unsafe_allow_html=True)
    if runtime_status["missing_for_live"]:
        st.caption("Live missing: " + ", ".join(runtime_status["missing_for_live"]))
    st.markdown("---")
    mode = st.radio("Mode", ["Auto", "Alert", "Calm"], horizontal=True)
    language = st.selectbox("Language", ["English", "Spanish", "French", "Japanese", "Russian"])
    location_text = st.text_input("Approximate location or context")
    uploaded_file = st.file_uploader("Optional image upload", type=["jpg", "jpeg", "png"])
    st.markdown("---")
    st.subheader("Demo Scenarios")
    for key, label in list_sample_incidents():
        if st.button(label, key=f"sample_{key}", width="stretch"):
            _set_sample(key)

logo_html = ""
if LOGO.exists():
    st.markdown(
        """
        <style>
        .maydaiq-logo img {
            width: 76px;
            height: 76px;
            object-fit: contain;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

hero_cols = st.columns([0.09, 0.91])
with hero_cols[0]:
    if LOGO.exists():
        st.image(str(LOGO), width="stretch")
with hero_cols[1]:
    st.markdown(
        f"""
        <div class="brand-copy">
            <h1>MaydaIQ</h1>
            <p>Multimodal crisis reasoning for immediate safety, grounded response plans, and responder-ready packets.</p>
            <div class="chips">
                <span class="chip">Reasoning Agents</span>
                <span class="chip">Microsoft Foundry</span>
                <span class="chip">Foundry IQ grounding</span>
                {_runtime_chip(runtime_status)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="mission-panel">
        <div class="mission-grid">
            <div class="mission-tile">
                <div class="num">60s</div>
                <div class="label">Act safely</div>
                <div class="text">Alert mode compresses crisis guidance into immediate physical-safety actions.</div>
            </div>
            <div class="mission-tile">
                <div class="num">60m</div>
                <div class="label">Coordinate</div>
                <div class="text">The agent pipeline turns reports into cited plans, unknowns, and escalation flags.</div>
            </div>
            <div class="mission-tile">
                <div class="num">60d</div>
                <div class="label">Learn</div>
                <div class="text">Anonymized community memory supports prevention and citizen-science follow-up.</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="workband"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">MaydaIQ Chat</div>', unsafe_allow_html=True)
st.caption("Use the message bar at the bottom. Press Enter to analyze a new report.")

if st.session_state["chat_history"]:
    for message in st.session_state["chat_history"][-8:]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
else:
    with st.chat_message("assistant"):
        st.markdown(
            "Tell me what is happening, or choose a demo scenario. I will classify risk, give safe next steps, "
            "and prepare a simulated responder packet."
        )

right = st.container()
with right:
    st.markdown('<div class="section-title">Readiness Snapshot</div>', unsafe_allow_html=True)
    endpoint_state = "configured" if runtime_status["endpoint_present"] else "missing"
    agent_id_state = "configured" if runtime_status["agent_id_present"] else "missing"
    api_key_state = "configured" if runtime_status["api_key_present"] else "missing"
    agent_name_state = "configured" if runtime_status["agent_name_present"] else "missing"
    vision_state = "configured" if runtime_status["azure_openai_vision_configured"] or runtime_status["azure_vision_configured"] else "fallback"
    st.markdown(
        f"""
        <div class="status-card">
            <div class="status-label">Retrieval source</div>
            <div class="status-value">{runtime_status['mode']}</div>
            <div class="small-muted">Endpoint: {endpoint_state} / Agent ID: {agent_id_state} / API key: {api_key_state} / Agent name: {agent_name_state} / Vision: {vision_state}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**Fast scenario launch**")
    for key, label in list_sample_incidents():
        if st.button(label, key=f"quick_{key}", width="stretch"):
            _set_sample(key)
            st.rerun()

chat_prompt = st.chat_input("Message MaydaIQ. Press Enter to analyze.")
submitted_text = chat_prompt or st.session_state.get("pending_prompt")
if chat_prompt:
    st.session_state["sample_scenario"] = None

if submitted_text:
    st.session_state["pending_prompt"] = None
    if not str(submitted_text).strip() and not st.session_state.get("sample_scenario") and not uploaded_file:
        st.warning("Add a report, choose a sample scenario, or upload an image.")
        st.stop()

    image_bytes = uploaded_file.getvalue() if uploaded_file else None
    incident = IncidentInput(
        text=str(submitted_text).strip(),
        mode=mode,
        language=language,
        location_text=location_text.strip() or None,
        image_filename=uploaded_file.name if uploaded_file else None,
        sample_scenario=st.session_state.get("sample_scenario"),
        image_bytes_present=bool(uploaded_file),
    )

    with st.spinner("MaydaIQ agents are coordinating the incident packet..."):
        result = run_incident(incident, image_bytes=image_bytes, persist_memory=True)

    risk = result.risk_assessment
    plan = result.action_plan
    packet = result.responder_packet
    source = _source_label(result.retrieved_playbooks[0].source_id if result.retrieved_playbooks else "")
    assistant_reply = _assistant_message(result)
    st.session_state["chat_history"].append({"role": "user", "content": str(submitted_text).strip()})
    st.session_state["chat_history"].append({"role": "assistant", "content": assistant_reply})
    st.session_state["last_result"] = result
    st.session_state["last_source"] = source

    st.markdown('<div class="section-title">MaydaIQ Reply</div>', unsafe_allow_html=True)
    with st.chat_message("assistant"):
        st.markdown(assistant_reply)

result = st.session_state.get("last_result")
source = st.session_state.get("last_source")

if result:
    risk = result.risk_assessment
    plan = result.action_plan
    packet = result.responder_packet
    st.markdown('<div class="section-title">Response Dashboard</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    with cols[0]:
        st.markdown('<div class="status-card"><div class="status-label">Risk</div></div>', unsafe_allow_html=True)
        st.markdown(_risk_badge(risk.risk_level), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(
            f'<div class="status-card"><div class="status-label">Mode</div><div class="status-value">{risk.selected_mode}</div></div>',
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            f'<div class="status-card"><div class="status-label">Confidence</div><div class="status-value">{risk.confidence}</div></div>',
            unsafe_allow_html=True,
        )
    with cols[3]:
        st.markdown(
            f'<div class="status-card"><div class="status-label">Escalation</div><div class="status-value">{str(packet.human_escalation_required).lower()}</div></div>',
            unsafe_allow_html=True,
        )
    with cols[4]:
        st.markdown(
            f'<div class="status-card"><div class="status-label">Grounding</div><div class="status-value">{source}</div></div>',
            unsafe_allow_html=True,
        )

    alert_tab, calm_tab, trace_tab, packet_tab = st.tabs(
        ["Alert Card", "Calm Plan", "Agent Trace", "Responder Packet"]
    )

    with alert_tab:
        alert_cols = st.columns(4)
        with alert_cols[0]:
            _render_list("Do now", plan.do_now)
        with alert_cols[1]:
            _render_list("Avoid", plan.avoid)
        with alert_cols[2]:
            _render_list("Call / Escalate", plan.call_or_escalate)
        with alert_cols[3]:
            st.markdown("**Report summary**")
            st.write(plan.report_summary)

    with calm_tab:
        calm_cols = st.columns([0.48, 0.52], gap="large")
        with calm_cols[0]:
            st.markdown("**Situation summary**")
            st.write(plan.situation_summary)
            st.markdown("**Step-by-step plan**")
            for step in plan.step_by_step_plan or plan.next_steps:
                st.markdown(f"- {step}")
            st.markdown("**Prevention suggestions**")
            for suggestion in plan.prevention_suggestions:
                st.markdown(f"- {suggestion}")
        with calm_cols[1]:
            st.markdown("**Evidence / citations**")
            if plan.evidence:
                for evidence in plan.evidence:
                    st.markdown(f"- {evidence}")
            else:
                st.caption("No retrieved evidence.")
            if plan.citations:
                st.caption("Citations: " + ", ".join(plan.citations))
            st.markdown("**Unknowns**")
            for unknown in plan.unknowns:
                st.markdown(f"- {unknown}")

    with trace_tab:
        trace_html = ['<div class="trace-row">']
        for step in result.agent_trace:
            trace_html.append(
                f'<div class="trace-step"><b>{step.agent}</b><p>{step.summary}</p></div>'
            )
        trace_html.append("</div>")
        st.markdown("".join(trace_html), unsafe_allow_html=True)

    with packet_tab:
        packet_json = packet.model_dump(mode="json")
        st.json(packet_json)
        st.download_button(
            "Download responder packet JSON",
            data=json.dumps(packet_json, indent=2),
            file_name=f"{packet.incident_id}.json",
            mime="application/json",
            width="stretch",
        )

    st.markdown(
        f'<div class="safety-note"><strong>Safety disclaimer:</strong> {result.disclaimer}</div>',
        unsafe_allow_html=True,
    )

