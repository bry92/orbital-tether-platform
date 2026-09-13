"""Immutable historical evidence structures for TSS-1R parameter documentation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal
import json


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """Canonical source metadata. Reusable across multiple evidence records."""

    source_id: str
    title: str
    organization: str
    document_type: Literal[
        "mission_report",
        "technical_memo",
        "peer_reviewed_paper",
        "flight_data_telemetry",
        "mission_log",
        "engineering_specification",
        "other",
    ]
    publication_date: str | None = None
    authors: list[str] | None = None
    url: str | None = None
    doi: str | None = None
    archive_location: str | None = None
    archive_access_date: str | None = None
    reference_key: str | None = None
    version_or_revision: str | None = None
    scope_summary: str | None = None
    keywords: list[str] = field(default_factory=list)
    retrieved_at_utc: str | None = None
    retrieved_by: str | None = None
    retrieval_notes: str | None = None
    tss1r_relevance: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return asdict(self)

    def to_json(self) -> str:
        """Canonical JSON representation."""
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True, slots=True)
class HistoricalEvidence:
    """A single historical evidence record for a physical or derived parameter.
    
    Classification semantics:
    - KNOWN: Direct measurement or statement from authoritative source
    - DERIVED: Calculated from other evidence via explicit equation
    - ASSUMED: Introduced by researcher; not from historical data
    - UNKNOWN: No available evidence; cannot resolve to numerical value
    
    UNKNOWN is first-class: value must be None. UNKNOWN cannot become a
    numerical simulation input under any RunMode. An UNKNOWN parameter either
    blocks execution or remains unresolved in a diagnostic/partial result.
    """

    evidence_id: str
    parameter_name: str
    classification: Literal["KNOWN", "DERIVED", "ASSUMED", "UNKNOWN"]
    confidence: Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"]

    # Value and unit (required if not UNKNOWN, null if UNKNOWN)
    value: float | None = None
    value_min: float | None = None
    value_max: float | None = None
    unit: str | None = None
    quantity_type: str | None = None

    # Uncertainty
    uncertainty: float | None = None
    uncertainty_type: str | None = None

    # Source attribution (required if KNOWN/DERIVED)
    source_id: str | None = None
    source_title: str | None = None
    source_organization: str | None = None
    source_date: str | None = None
    source_location: str | None = None
    source_page_range: str | None = None
    source_table_row: str | None = None
    citation_key: str | None = None

    # Notes
    extraction_notes: str | None = None
    assumption_justification: str | None = None

    # For DERIVED values
    derived_from: list[str] | None = None
    derivation_equation: str | None = None
    derivation_method: str | None = None

    # Versioning and audit
    created_at_utc: str | None = None
    created_by: str | None = None
    updated_at_utc: str | None = None
    reviewed: bool = False
    review_notes: str | None = None

    # Supersession chain
    supersedes: str | None = None
    superseded_by: str | None = None
    change_reason: str | None = None

    # Runtime usage tracking
    used_by_experiment_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return asdict(self)

    def to_json(self) -> str:
        """Canonical JSON representation."""
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))

    def validate(self) -> list[str]:
        """
        Validate evidence record consistency.
        
        Returns:
            List of validation errors (empty if valid).
        """
        errors = []

        # Basic field requirements
        if not self.evidence_id:
            errors.append("evidence_id is required")
        if not self.parameter_name:
            errors.append("parameter_name is required")
        if self.classification not in ("KNOWN", "DERIVED", "ASSUMED", "UNKNOWN"):
            errors.append(f"Invalid classification: {self.classification}")
        if self.confidence not in ("HIGH", "MEDIUM", "LOW", "UNKNOWN"):
            errors.append(f"Invalid confidence: {self.confidence}")

        # Classification-specific requirements
        if self.classification == "UNKNOWN":
            # UNKNOWN must have value=None and no numerical content
            if self.value is not None:
                errors.append("UNKNOWN evidence must have value=None")
            # UNKNOWN may have other metadata for documentation purposes
        else:
            # KNOWN, DERIVED, ASSUMED must have numerical content
            if self.value is None:
                errors.append(
                    f"{self.classification} evidence must have a value "
                    "(use UNKNOWN if value unavailable)"
                )
            if self.unit is None:
                errors.append(f"{self.classification} evidence must specify unit")
            if self.quantity_type is None:
                errors.append(f"{self.classification} evidence must specify quantity_type")

        if self.classification in ("KNOWN", "DERIVED"):
            if not self.source_id:
                errors.append(f"{self.classification} evidence must reference source_id")

        if self.classification == "DERIVED":
            if not self.derived_from or len(self.derived_from) == 0:
                errors.append("DERIVED evidence must list dependencies in derived_from")
            if not self.derivation_equation:
                errors.append("DERIVED evidence must include derivation_equation")
            if not self.derivation_method:
                errors.append("DERIVED evidence must include derivation_method")

        if self.classification == "ASSUMED":
            if not self.assumption_justification:
                errors.append("ASSUMED evidence must include assumption_justification")

        return errors


@dataclass(frozen=True, slots=True)
class ParameterAudit:
    """Audit trail for a single parameter from evidence to simulation input.
    
    Records the actual evidence record used, its classification, and whether
    it was permitted to enter the simulation based on RunMode.
    """

    parameter_name: str
    evidence_id: str | None
    classification: str
    confidence: str
    value: float | None
    unit: str | None
    source_id: str | None
    source_title: str | None
    
    # For DERIVED: the dependency chain back to sources
    derivation_chain: list[str] | None = None
    
    # For ASSUMED: the justification and reason
    assumptions_applied: dict[str, Any] = field(default_factory=dict)
    
    # Did this parameter actually enter the simulation?
    used_in_physics: bool = False
    
    # Metadata about resolution
    notes: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class CompletenessReport:
    """High-level summary of evidence coverage for a scenario.
    
    Tracks whether required parameters are KNOWN, DERIVED, ASSUMED, or
    UNKNOWN/BLOCKED. Determines whether a physics run can proceed.
    """

    known_count: int
    derived_count: int
    assumed_count: int
    unknown_count: int
    blocked_count: int
    completeness_percent: float
    
    # Parameters that could not be resolved
    required_but_unknown: list[str] = field(default_factory=list)
    required_but_assumed: list[str] = field(default_factory=list)
    
    # Did the resolver approve a physics run?
    physics_run_approved: bool = False
    
    # Human-readable summary
    remarks: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RunMode:
    """Control resolver behavior for UNKNOWN and ASSUMED evidence.
    
    HISTORICAL_STRICT (all False):
        - Accept KNOWN and valid DERIVED evidence
        - UNKNOWN → blocks run (cannot enter simulation as numerical input)
        - ASSUMED → blocks run
    
    HISTORICAL_WITH_ASSUMPTIONS (allow_assumed=True, others False):
        - Accept KNOWN and valid DERIVED evidence
        - ASSUMED → allowed if explicitly authorized
        - UNKNOWN → blocks run (cannot enter simulation as numerical input)
    
    PARTIAL/DIAGNOSTIC (partial_run=True):
        - Returns unresolved result for inspection
        - Does NOT execute physics simulation
        - Allows inspection of missing UNKNOWN and ASSUMED parameters
        - Does NOT substitute UNKNOWN with numerical values
    
    CRITICAL: allow_unknown=True does NOT mean "use UNKNOWN as zero".
    UNKNOWN can never become a numerical simulation input. Setting
    allow_unknown=True is a reserved flag for future use (e.g., pure
    diagnostics), but does not permit UNKNOWN→numerical substitution.
    """

    allow_unknown: bool = False
    allow_assumed: bool = False
    partial_run: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> list[str]:
        """Validate RunMode consistency."""
        errors = []
        
        if self.allow_unknown and not self.partial_run:
            errors.append(
                "allow_unknown=True is only meaningful with partial_run=True "
                "(UNKNOWN values cannot enter numerical simulation)"
            )
        
        return errors
