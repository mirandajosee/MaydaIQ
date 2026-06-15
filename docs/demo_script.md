# Five-Minute Demo Script

## 1. Calm Flood Preparedness

Open MaydaIQ, choose **Calm**, and enter:

> Our neighborhood floods every summer. How should we prepare before the next heavy storm?

Show the Calm Plan, citations from the local knowledge pack or Foundry IQ, unknowns, and prevention suggestions.

## 2. Auto Mode With Simulated Flood Image

Choose **Auto** and click **Flooded street with possible electrical hazard**. Optionally upload any JPG/PNG with a filename containing `flood` or `wire`.

Point out that VisionAgent returns hazard labels such as `floodwater`, `fast_water`, and `possible_electrical_hazard`.

## 3. Alert Mode Concision

Run the scenario. Auto Mode should select **ALERT** because floodwater plus electricity is high severity.

Show the Alert Card:

- Do now.
- Avoid.
- Call / Escalate.
- Report summary.

Explain that Alert Mode is intentionally short and avoids detailed reasoning.

## 4. Agent Trace

Expand **Agent Trace**.

Narrate the visible trace:

Intake -> Vision -> Triage -> Foundry IQ Retrieval -> Planner -> Safety Critic -> Responder Packet.

Emphasize that it is a short trace, not hidden chain-of-thought.

## 5. Responder Packet JSON

Open **Responder Packet JSON** and show:

- `incident_id`
- `risk_level`
- `confidence`
- `visual_signals`
- `immediate_actions`
- `hazards`
- `human_escalation_required`
- `privacy_redactions`
- `simulated_only: true`

Use the download button to show the packet is responder-ready but not dispatched.

## 6. Environmental Citizen Science

Click **Air quality / lichen citizen science report** or **Suspicious water pollution / benthic bioindicator report**.

Show that MaydaIQ supports slower community intelligence: screening observations, citations, unknowns, and no overclaiming exact diagnosis.

## 7. Close

Close with:

> MaydaIQ turns crisis reports into safe action for the first 60 seconds, the next 60 minutes, and the community's next 60 days.

