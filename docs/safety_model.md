# Safety Model

MaydaIQ is a crisis assistant, not an emergency service.

## Core Constraints

- Never claim to contact real authorities.
- Implement only `simulate_emergency_report()`.
- Do not make real calls, SMS messages, emails, police reports, or dispatch requests.
- Do not identify people, faces, license plates, suspects, or private individuals.
- For robbery or violence, advise escape, distance, safety, and emergency services. Never advise confrontation or pursuit.
- For medical emergencies, avoid invasive instructions and prioritize emergency services plus basic safety.
- For fire or smoke, advise evacuation and air safety. Never tell users to re-enter unsafe areas.
- For flood or electrical hazards, advise avoiding floodwater, wires, and submerged electrical equipment.

## Confidence Gate

Each result includes:

- `confidence`
- `uncertainty_notes`
- `human_escalation_required`

High severity incidents and low-confidence incidents force `human_escalation_required=true`. This creates a human-in-the-loop checkpoint instead of pretending the app can resolve emergencies alone.

## No Real Emergency Calls

MaydaIQ generates structured packets for demonstration and human review only. The simulated reporting tool returns:

```json
{
  "status": "simulated_only_not_sent",
  "simulated_only": true
}
```

## Privacy And Redaction

MaydaIQ redacts obvious emails, phone numbers, and possible plate/ID strings. Vision outputs are restricted to hazard labels. Community memory stores:

- approximate location text
- incident type
- risk level
- hazard labels
- redaction notes

It does not store raw images or private identities.

## Human-In-The-Loop

The system is built to assist trained responders, local officials, community leads, and residents. Human judgment and official guidance override MaydaIQ.

