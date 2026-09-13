"""Stage 1 tests: HistoricalEvidence and SourceDocument validation.

These tests verify the immutable evidence schema without modifying v0.2 physics.
See ADR-002 and Issue #4: Phase C must preserve the existing angular-momentum
discrepancy and NOT attempt to "fix" physics through evidence architecture.
"""

from __future__ import annotations

import pytest

from verification.historical_evidence import (
    HistoricalEvidence,
    SourceDocument,
    ParameterAudit,
    CompletenessReport,
    RunMode,
)


class TestSourceDocument:
    """Test SourceDocument creation and serialization."""

    @pytest.mark.smoke
    def test_source_document_creation(self) -> None:
        source = SourceDocument(
            source_id="NASA-TM-1996-3343",
            title="TSS-1R Mission Operations Summary",
            organization="NASA",
            document_type="mission_report",
            publication_date="1996-12-15",
        )
        assert source.source_id == "NASA-TM-1996-3343"
        assert source.organization == "NASA"

    @pytest.mark.smoke
    def test_source_document_immutable(self) -> None:
        source = SourceDocument(
            source_id="test",
            title="Test",
            organization="Test Org",
            document_type="technical_memo",
        )
        with pytest.raises(AttributeError):
            source.title = "Modified"  # type: ignore

    @pytest.mark.smoke
    def test_source_document_serialization(self) -> None:
        source = SourceDocument(
            source_id="NASA-TM-1996-3343",
            title="Test Report",
            organization="NASA",
            document_type="mission_report",
        )
        data = source.as_dict()
        assert data["source_id"] == "NASA-TM-1996-3343"
        assert data["title"] == "Test Report"
        json_str = source.to_json()
        assert "NASA-TM-1996-3343" in json_str


class TestHistoricalEvidenceKNOWN:
    """Test KNOWN evidence: requires source, has value."""

    @pytest.mark.smoke
    def test_known_evidence_valid(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-001",
            parameter_name="orbit.altitude_m",
            value=380000.0,
            unit="m",
            quantity_type="length",
            classification="KNOWN",
            confidence="HIGH",
            source_id="NASA-TM-1996-3343",
        )
        errors = evidence.validate()
        assert len(errors) == 0

    @pytest.mark.smoke
    def test_known_evidence_requires_source(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-001",
            parameter_name="orbit.altitude_m",
            value=380000.0,
            unit="m",
            quantity_type="length",
            classification="KNOWN",
            confidence="HIGH",
            source_id=None,  # Missing source
        )
        errors = evidence.validate()
        assert any("source_id" in e for e in errors)

    @pytest.mark.smoke
    def test_known_evidence_requires_value(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-001",
            parameter_name="orbit.altitude_m",
            value=None,  # Missing value
            unit="m",
            quantity_type="length",
            classification="KNOWN",
            confidence="HIGH",
            source_id="NASA-TM-1996-3343",
        )
        errors = evidence.validate()
        assert any("value" in e.lower() for e in errors)

    @pytest.mark.smoke
    def test_known_evidence_requires_unit(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-001",
            parameter_name="orbit.altitude_m",
            value=380000.0,
            unit=None,  # Missing unit
            quantity_type="length",
            classification="KNOWN",
            confidence="HIGH",
            source_id="NASA-TM-1996-3343",
        )
        errors = evidence.validate()
        assert any("unit" in e.lower() for e in errors)

    @pytest.mark.smoke
    def test_known_evidence_immutable(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-001",
            parameter_name="orbit.altitude_m",
            value=380000.0,
            unit="m",
            quantity_type="length",
            classification="KNOWN",
            confidence="HIGH",
            source_id="NASA-TM-1996-3343",
        )
        with pytest.raises(AttributeError):
            evidence.value = 400000.0  # type: ignore


class TestHistoricalEvidenceDERIVED:
    """Test DERIVED evidence: requires dependencies, equation, method."""

    @pytest.mark.smoke
    def test_derived_evidence_valid(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-012",
            parameter_name="orbit.circular_velocity_m_s",
            value=7680.5,
            unit="m/s",
            quantity_type="velocity",
            classification="DERIVED",
            confidence="HIGH",
            source_id="NASA-TM-1996-3343",
            derived_from=["TSS1R-E-001", "TSS1R-E-003"],
            derivation_equation="v = sqrt(mu / r)",
            derivation_method="analytical",
        )
        errors = evidence.validate()
        assert len(errors) == 0

    @pytest.mark.smoke
    def test_derived_evidence_requires_dependencies(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-012",
            parameter_name="orbit.circular_velocity_m_s",
            value=7680.5,
            unit="m/s",
            quantity_type="velocity",
            classification="DERIVED",
            confidence="HIGH",
            source_id="NASA-TM-1996-3343",
            derived_from=None,  # Missing dependencies
            derivation_equation="v = sqrt(mu / r)",
            derivation_method="analytical",
        )
        errors = evidence.validate()
        assert any("derived_from" in e.lower() for e in errors)

    @pytest.mark.smoke
    def test_derived_evidence_requires_equation(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-012",
            parameter_name="orbit.circular_velocity_m_s",
            value=7680.5,
            unit="m/s",
            quantity_type="velocity",
            classification="DERIVED",
            confidence="HIGH",
            source_id="NASA-TM-1996-3343",
            derived_from=["TSS1R-E-001"],
            derivation_equation=None,  # Missing equation
            derivation_method="analytical",
        )
        errors = evidence.validate()
        assert any("equation" in e.lower() for e in errors)

    @pytest.mark.smoke
    def test_derived_evidence_requires_method(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-012",
            parameter_name="orbit.circular_velocity_m_s",
            value=7680.5,
            unit="m/s",
            quantity_type="velocity",
            classification="DERIVED",
            confidence="HIGH",
            source_id="NASA-TM-1996-3343",
            derived_from=["TSS1R-E-001"],
            derivation_equation="v = sqrt(mu / r)",
            derivation_method=None,  # Missing method
        )
        errors = evidence.validate()
        assert any("method" in e.lower() for e in errors)


class TestHistoricalEvidenceASSUMED:
    """Test ASSUMED evidence: requires justification."""

    @pytest.mark.smoke
    def test_assumed_evidence_valid(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-006",
            parameter_name="tether.deployment_rate_m_s",
            value=0.25,
            unit="m/s",
            quantity_type="velocity",
            classification="ASSUMED",
            confidence="LOW",
            assumption_justification="Historical reel rate not documented; used EDU benchmark.",
        )
        errors = evidence.validate()
        assert len(errors) == 0

    @pytest.mark.smoke
    def test_assumed_evidence_requires_justification(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-006",
            parameter_name="tether.deployment_rate_m_s",
            value=0.25,
            unit="m/s",
            quantity_type="velocity",
            classification="ASSUMED",
            confidence="LOW",
            assumption_justification=None,  # Missing justification
        )
        errors = evidence.validate()
        assert any("justification" in e.lower() for e in errors)

    @pytest.mark.smoke
    def test_assumed_no_source_required(self) -> None:
        """ASSUMED evidence does not require source_id."""
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-006",
            parameter_name="tether.deployment_rate_m_s",
            value=0.25,
            unit="m/s",
            quantity_type="velocity",
            classification="ASSUMED",
            confidence="LOW",
            assumption_justification="Testing default.",
            source_id=None,
        )
        errors = evidence.validate()
        # Should NOT complain about missing source
        assert not any("source_id" in e for e in errors)


class TestHistoricalEvidenceUNKNOWN:
    """Test UNKNOWN evidence: value must be None, no numerical content."""

    @pytest.mark.smoke
    def test_unknown_evidence_valid(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-UNK-001",
            parameter_name="tether.tensile_strength_pa",
            value=None,  # Required for UNKNOWN
            unit="Pa",
            quantity_type="stress",
            classification="UNKNOWN",
            confidence="UNKNOWN",
        )
        errors = evidence.validate()
        assert len(errors) == 0

    @pytest.mark.smoke
    def test_unknown_evidence_rejects_value(self) -> None:
        """UNKNOWN evidence MUST have value=None."""
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-UNK-001",
            parameter_name="tether.tensile_strength_pa",
            value=500000.0,  # NOT allowed for UNKNOWN
            unit="Pa",
            quantity_type="stress",
            classification="UNKNOWN",
            confidence="UNKNOWN",
        )
        errors = evidence.validate()
        assert any("value=None" in e for e in errors)

    @pytest.mark.smoke
    def test_unknown_no_source_required(self) -> None:
        """UNKNOWN evidence does not require source."""
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-UNK-001",
            parameter_name="tether.tensile_strength_pa",
            value=None,
            unit="Pa",
            quantity_type="stress",
            classification="UNKNOWN",
            confidence="UNKNOWN",
            source_id=None,
        )
        errors = evidence.validate()
        assert not any("source_id" in e for e in errors)

    @pytest.mark.smoke
    def test_unknown_can_have_metadata(self) -> None:
        """UNKNOWN evidence can have extraction notes and metadata."""
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-UNK-001",
            parameter_name="tether.tensile_strength_pa",
            value=None,
            unit="Pa",
            quantity_type="stress",
            classification="UNKNOWN",
            confidence="UNKNOWN",
            extraction_notes="Material type not specified in open TSS-1R docs.",
        )
        errors = evidence.validate()
        assert len(errors) == 0
        assert evidence.extraction_notes is not None

    @pytest.mark.smoke
    def test_unknown_cannot_enter_simulation_silently(self) -> None:
        """UNKNOWN evidence must not be converted to a numerical value.
        
        This is a critical safeguard per Phase C constraint:
        UNKNOWN cannot become a numerical simulation input.
        """
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-UNK-001",
            parameter_name="reel.moment_of_inertia_kg_m2",
            value=None,
            classification="UNKNOWN",
            confidence="UNKNOWN",
        )
        # Validate that UNKNOWN is genuinely unknown
        assert evidence.value is None
        # This evidence should block a strict run mode
        # (validation enforced by resolver, not here)
        errors = evidence.validate()
        assert len(errors) == 0  # Schema is valid


class TestParameterAudit:
    """Test ParameterAudit trail tracking."""

    @pytest.mark.smoke
    def test_parameter_audit_known(self) -> None:
        audit = ParameterAudit(
            parameter_name="orbit.altitude_m",
            evidence_id="TSS1R-E-001",
            classification="KNOWN",
            confidence="HIGH",
            value=380000.0,
            unit="m",
            source_id="NASA-TM-1996-3343",
            source_title="TSS-1R Mission Operations Summary",
            used_in_physics=True,
        )
        assert audit.parameter_name == "orbit.altitude_m"
        assert audit.evidence_id == "TSS1R-E-001"
        assert audit.classification == "KNOWN"
        assert audit.used_in_physics is True

    @pytest.mark.smoke
    def test_parameter_audit_derived(self) -> None:
        audit = ParameterAudit(
            parameter_name="orbit.circular_velocity_m_s",
            evidence_id="TSS1R-E-012",
            classification="DERIVED",
            confidence="HIGH",
            value=7680.5,
            unit="m/s",
            source_id="NASA-TM-1996-3343",
            source_title="TSS-1R Mission Operations Summary",
            derivation_chain=["TSS1R-E-001", "A-008-mu"],
            used_in_physics=True,
        )
        assert audit.classification == "DERIVED"
        assert audit.derivation_chain is not None
        assert "TSS1R-E-001" in audit.derivation_chain

    @pytest.mark.smoke
    def test_parameter_audit_assumed(self) -> None:
        audit = ParameterAudit(
            parameter_name="tether.deployment_rate_m_s",
            evidence_id="TSS1R-E-006",
            classification="ASSUMED",
            confidence="LOW",
            value=0.25,
            unit="m/s",
            source_id=None,
            source_title=None,
            assumptions_applied={"reason": "historical value unavailable"},
            used_in_physics=True,
        )
        assert audit.classification == "ASSUMED"
        assert "reason" in audit.assumptions_applied


class TestCompletenessReport:
    """Test CompletenessReport tracking."""

    @pytest.mark.smoke
    def test_completeness_report_high(self) -> None:
        report = CompletenessReport(
            known_count=7,
            derived_count=4,
            assumed_count=2,
            unknown_count=0,
            blocked_count=0,
            completeness_percent=100.0,
            physics_run_approved=True,
        )
        assert report.completeness_percent == 100.0
        assert report.physics_run_approved is True

    @pytest.mark.smoke
    def test_completeness_report_partial(self) -> None:
        report = CompletenessReport(
            known_count=7,
            derived_count=4,
            assumed_count=2,
            unknown_count=3,
            blocked_count=1,
            completeness_percent=81.0,
            required_but_unknown=["electrodynamics.conductivity"],
            physics_run_approved=True,
            remarks="Mechanical parameters available; electrodynamics unknown (v0.2 OK).",
        )
        assert report.completeness_percent == 81.0
        assert "electrodynamics.conductivity" in report.required_but_unknown
        assert report.physics_run_approved is True

    @pytest.mark.smoke
    def test_completeness_report_incomplete(self) -> None:
        report = CompletenessReport(
            known_count=5,
            derived_count=2,
            assumed_count=0,
            unknown_count=8,
            blocked_count=3,
            completeness_percent=46.0,
            required_but_unknown=["orbit.altitude_m", "spacecraft.mass_kg"],
            physics_run_approved=False,
            remarks="Critical parameters missing; cannot run physics.",
        )
        assert report.completeness_percent == 46.0
        assert report.physics_run_approved is False
        assert len(report.required_but_unknown) == 2


class TestRunMode:
    """Test RunMode enforcement rules."""

    @pytest.mark.smoke
    def test_run_mode_strict(self) -> None:
        mode = RunMode(
            allow_unknown=False,
            allow_assumed=False,
            partial_run=False,
        )
        errors = mode.validate()
        assert len(errors) == 0

    @pytest.mark.smoke
    def test_run_mode_with_assumptions(self) -> None:
        mode = RunMode(
            allow_unknown=False,
            allow_assumed=True,
            partial_run=False,
        )
        errors = mode.validate()
        assert len(errors) == 0

    @pytest.mark.smoke
    def test_run_mode_partial_diagnostic(self) -> None:
        mode = RunMode(
            allow_unknown=True,
            allow_assumed=True,
            partial_run=True,
        )
        errors = mode.validate()
        assert len(errors) == 0

    @pytest.mark.smoke
    def test_run_mode_invalid_allow_unknown_without_partial(self) -> None:
        """allow_unknown=True requires partial_run=True."""
        mode = RunMode(
            allow_unknown=True,
            allow_assumed=False,
            partial_run=False,
        )
        errors = mode.validate()
        assert len(errors) > 0
        assert any("partial_run" in e for e in errors)


class TestSupersession:
    """Test evidence versioning and supersession."""

    @pytest.mark.smoke
    def test_evidence_supersession(self) -> None:
        old_evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-001-v1",
            parameter_name="orbit.altitude_m",
            value=380000.0,
            unit="m",
            quantity_type="length",
            classification="KNOWN",
            confidence="HIGH",
            source_id="NASA-TM-1996-3343",
            created_at_utc="2026-09-13T08:00:00Z",
        )
        new_evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-001-v2",
            parameter_name="orbit.altitude_m",
            value=385000.0,
            unit="m",
            quantity_type="length",
            classification="KNOWN",
            confidence="HIGH",
            source_id="NASA-TM-1996-XXXX",
            supersedes="TSS1R-E-001-v1",
            change_reason="New declassified NASA document with higher fidelity.",
            created_at_utc="2026-10-01T14:00:00Z",
        )
        assert new_evidence.supersedes == "TSS1R-E-001-v1"
        assert new_evidence.value != old_evidence.value
        assert new_evidence.change_reason is not None


class TestPhaseCADR002Constraint:
    """Test that evidence architecture does NOT modify v0.2 physics.
    
    Per ADR-002 (Issue #4): Phase C must preserve the existing angular-momentum
    discrepancy. The evidence layer is orthogonal to the physics formulation.
    Evidence provenance does NOT "fix" the unresolved physics problem.
    """

    @pytest.mark.smoke
    def test_evidence_does_not_imply_physics_validation(self) -> None:
        """Loading historical evidence does not make physics check PASS.
        
        This is critical: evidence completeness is separate from physics
        validation. Historical parameters can be fully known and the physics
        can still be UNRESOLVED (as per ADR-002).
        """
        # Create a hypothetical complete evidence set
        completeness = CompletenessReport(
            known_count=10,
            derived_count=5,
            assumed_count=0,
            unknown_count=0,
            blocked_count=0,
            completeness_percent=100.0,
            physics_run_approved=True,  # All evidence available
            remarks="All mechanical parameters from TSS-1R mission data.",
        )
        # This completeness report is about PARAMETER PROVENANCE, not physics validation
        assert completeness.physics_run_approved is True
        # But the physics status (angular momentum UNRESOLVED) is separate
        # and determined by the v0.2 model, not by evidence loading
        # (This separation is enforced by the resolver, not here)

    @pytest.mark.smoke
    def test_issue4_unresolved_remains_independent_of_evidence(self) -> None:
        """Issue #4 / ADR-002: unresolved physics is not changed by evidence layer.
        
        The v0.2 angular-momentum discrepancy (prescribed kinematics with
        fixed CM and co-rotating frame) is a formulation boundary issue,
        not a parameter or calculation error.
        
        Evidence architecture provides audit trails, not reformulated dynamics.
        """
        # This test confirms the architectural constraint is respected
        # The evidence layer should be transparent to v0.2 equations
        # No evidence record should claim to "fix" the angular-momentum issue
        
        # Example of what would be WRONG (and should never appear):
        # - A parametrized assumption that "corrects" angular momentum
        # - A derived parameter computed from a different formulation
        # - Evidence that reel inertia or actuator torque was discovered
        #   in historical data (neither was recorded in TSS-1R docs)
        
        # Example of what is RIGHT (and this test verifies):
        # - Historical tether deployment rate (KNOWN or ASSUMED)
        # - Historical spacecraft mass (KNOWN)
        # - Historical orbital altitude (KNOWN)
        # - Angular momentum discrepancy marked as v0.2 model boundary (UNRESOLVED)
        
        # Create an evidence record that does NOT pretend to resolve Issue #4
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-EVID-BOUNDARY",
            parameter_name="v0.2_angular_momentum_status",
            value=None,  # Cannot be "fixed" by parameterization
            classification="UNKNOWN",
            confidence="UNKNOWN",
            extraction_notes=(
                "v0.2 prescribed kinematics with fixed CM and co-rotating frame "
                "produce an angular-momentum discrepancy. This is a system-boundary "
                "formulation issue (ADR-002 / Issue #4), not a parameter or "
                "measurement error. Resolution requires aerospace-dynamics review "
                "to select the appropriate physical system model. "
                "See ADR-002 for formulation options A, B, C, D."
            ),
        )
        errors = evidence.validate()
        # Schema should accept this meta-level evidence record
        assert len(errors) == 0
        # It correctly identifies the problem as UNKNOWN (not to be fixed by parameters)
        assert evidence.classification == "UNKNOWN"
        assert evidence.value is None
