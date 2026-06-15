# Judging Rubric Alignment

| Rubric Area | Evidence In MaydaIQ |
| --- | --- |
| Accuracy & Relevance | Local knowledge pack with source IDs, optional Foundry IQ retrieval, conservative risk scoring, and Pydantic validation. |
| Reasoning & Multi-step Thinking | Multi-agent pipeline with separate intake, vision, triage, retrieval, planning, safety review, and packet generation. |
| Creativity & Originality | Combines real-time crisis action with community preparedness and environmental bioindicator reporting. |
| UX & Presentation | Streamlit interface includes sample scenarios, mode selector, language selector, risk badge, alert card, calm plan, agent trace, JSON viewer, and download. |
| Reliability & Safety | Deterministic demo mode, no secrets, no real dispatch, explicit uncertainty, privacy redaction, and eval coverage for key hazards. |
| Community Vote | Memorable promise: first 60 seconds, next 60 minutes, next 60 days. |

## Submission Notes

- Track: Reasoning Agents.
- Public repo-safe: no secrets, no confidential data, synthetic reports only.
- Microsoft integration: `src/tools/foundry_iq_retrieval.py` is the Foundry IQ adapter boundary.
- Demo reliability: local fallback works without cloud dependencies.

