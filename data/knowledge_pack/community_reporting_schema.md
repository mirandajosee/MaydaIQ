# Community Reporting Schema

source_id: local:community_reporting_schema

## purpose
Define fields for responder-ready, privacy-preserving incident packets.

## signs
- Report includes approximate location, visible hazards, timing, access constraints, unknowns, and needed resources.
- Report excludes private identities and speculative claims.

## immediate_actions
- Capture what is visible, what is uncertain, and what help may be needed.
- Use approximate location text rather than private addresses when public reporting is enough.

## avoid
- Do not include faces, license plates, suspect names, phone numbers, or private personal details.
- Do not store raw images in community memory.
- Do not claim that a real report has been dispatched.

## when_to_call_emergency_services
- Use local emergency services directly for life risk, fire, injury, violence, floodwater, electricity, or immediate danger.

## calm_mode_guidance
- Keep reports structured: incident type, risk level, confidence, hazards, unknowns, recommended resources, and simulated-only flag.
- Review repeated reports for prevention planning without exposing individuals.

## responder_packet_fields
- incident_id
- timestamp_utc
- incident_type
- risk_level
- confidence
- visual_signals
- immediate_actions
- hazards
- unknowns
- privacy_redactions
- simulated_only

## safety_notes
- Structured packets help humans triage faster but do not replace official systems.
- MaydaIQ community memory stores anonymized hazard labels only.

## citations
- local:community_reporting_schema
- local:safety_policy

