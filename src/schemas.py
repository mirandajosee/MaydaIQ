"""Pydantic schemas shared across the MaydaIQ agent pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


InputMode = Literal["Auto", "Alert", "Calm"]
SelectedMode = Literal["ALERT", "CALM"]
RiskLevel = Literal["LOW", "MODERATE", "HIGH", "CRITICAL"]
Confidence = Literal["HIGH", "MEDIUM", "LOW"]
SafetyStatus = Literal["PASS", "REVISE", "FAIL"]


class IncidentInput(BaseModel):
    text: str = Field(default="", max_length=5000)
    mode: InputMode = "Auto"
    language: str = "English"
    location_text: str | None = None
    image_filename: str | None = None
    sample_scenario: str | None = None
    image_bytes_present: bool = False


class VisualFinding(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str
    privacy_safe: bool = True


class VisualAnalysis(BaseModel):
    image_used: bool = False
    visual_signals: list[str] = Field(default_factory=list)
    findings: list[VisualFinding] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    incident_type: str
    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    selected_mode: SelectedMode
    confidence: Confidence
    human_escalation_required: bool
    urgency_signals: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)


class RetrievedPlaybook(BaseModel):
    source_id: str
    title: str
    snippet: str
    relevance: float = Field(ge=0.0, le=1.0)
    citations: list[str] = Field(default_factory=list)


class ActionPlan(BaseModel):
    selected_mode: SelectedMode
    situation_summary: str
    do_now: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    call_or_escalate: list[str] = Field(default_factory=list)
    report_summary: str
    step_by_step_plan: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    prevention_suggestions: list[str] = Field(default_factory=list)
    confidence: Confidence
    citations: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class SafetyReview(BaseModel):
    status: SafetyStatus
    issues: list[str] = Field(default_factory=list)
    revisions_applied: list[str] = Field(default_factory=list)
    human_escalation_required: bool
    uncertainty_notes: list[str] = Field(default_factory=list)


class ResponderPacket(BaseModel):
    incident_id: str
    timestamp_utc: datetime
    incident_type: str
    risk_level: RiskLevel
    confidence: Confidence
    location_text: str | None = None
    visual_signals: list[str] = Field(default_factory=list)
    user_report: str
    immediate_actions: list[str] = Field(default_factory=list)
    hazards: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    recommended_resources: list[str] = Field(default_factory=list)
    human_escalation_required: bool
    privacy_redactions: list[str] = Field(default_factory=list)
    simulated_only: bool = True


class AgentTraceStep(BaseModel):
    agent: str
    summary: str
    status: str = "ok"


class MaydaIQResult(BaseModel):
    """Final structured MaydaIQ result."""

    incident_input: IncidentInput
    visual_analysis: VisualAnalysis
    risk_assessment: RiskAssessment
    retrieved_playbooks: list[RetrievedPlaybook] = Field(default_factory=list)
    action_plan: ActionPlan
    safety_review: SafetyReview
    responder_packet: ResponderPacket
    agent_trace: list[AgentTraceStep] = Field(default_factory=list)
    disclaimer: str
