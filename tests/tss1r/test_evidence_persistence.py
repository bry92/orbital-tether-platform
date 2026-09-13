"""Stage 2 tests: JSON persistence and evidence loader.

Tests verify:
- Write/read round trip
- Deterministic serialization
- Schema validation on load
- Malformed JSON rejection
- Invalid classification rejection
- Missing source rejection
- Missing DERIVED dependency rejection
- Circular dependency rejection
- UNKNOWN value constraint
- Supersession relationship preservation
- Classification/confidence independence preservation
- UNKNOWN never becoming numerical during load/save
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from verification.evidence_persistence import (
    EvidenceLoader,
    EvidenceWriter,
    EvidencePersistenceError,
)
from verification.historical_evidence import (
    HistoricalEvidence,
    SourceDocument,
)


class TestSourceDocumentPersistence:
    """Test SourceDocument JSON serialization and deserialization."""

    @pytest.mark.smoke
    def test_source_serialization_roundtrip(self) -> None:
        source = SourceDocument(
            source_id="NASA-TM-1996-3343",
            title="TSS-1R Mission Operations Summary",
            organization="NASA",
            document_type="mission_report",
            publication_date="1996-12-15",
            url="https://ntrs.nasa.gov/citations/19970003359",
        )
        # Serialize
        json_str = EvidenceWriter.source_to_json(source)
        # Deserialize
        data = json.loads(json_str)
        loader = EvidenceLoader()
        loaded_source = loader.load_source_json(data)

        assert loaded_source.source_id == source.source_id
        assert loaded_source.title == source.title
        assert loaded_source.organization == source.organization
        assert loaded_source.url == source.url

    @pytest.mark.smoke
    def test_source_deterministic_serialization(self) -> None:
        """Same source should produce identical JSON."""
        source = SourceDocument(
            source_id="NASA-TM-1996-3343",
            title="TSS-1R",
            organization="NASA",
            document_type="mission_report",
        )
        json1 = EvidenceWriter.source_to_json(source)
        json2 = EvidenceWriter.source_to_json(source)
        assert json1 == json2


class TestEvidencePersistence:
    """Test HistoricalEvidence JSON serialization and deserialization."""

    @pytest.mark.smoke
    def test_known_evidence_roundtrip(self) -> None:
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
        json_str = EvidenceWriter.evidence_to_json(evidence)
        data = json.loads(json_str)

        loader = EvidenceLoader()
        loader.load_source_json({
            "source_id": "NASA-TM-1996-3343",
            "title": "NASA-TM-1996-3343",
            "organization": "NASA",
            "document_type": "mission_report",
        })
        loaded_evidence = loader.load_evidence_json(data)

        assert loaded_evidence.evidence_id == evidence.evidence_id
        assert loaded_evidence.value == evidence.value
        assert loaded_evidence.classification == evidence.classification
        assert loaded_evidence.confidence == evidence.confidence

    @pytest.mark.smoke
    def test_derived_evidence_roundtrip(self) -> None:
        loader = EvidenceLoader()
        loader.load_source_json({
            "source_id": "NASA-TM-1996-3343",
            "title": "NASA-TM-1996-3343",
            "organization": "NASA",
            "document_type": "mission_report",
        })

        # Create and load dependency
        dep1 = HistoricalEvidence(
            evidence_id="TSS1R-E-001",
            parameter_name="orbit.altitude_m",
            value=380000.0,
            unit="m",
            quantity_type="length",
            classification="KNOWN",
            confidence="HIGH",
            source_id="NASA-TM-1996-3343",
        )
        loader.load_evidence_json(json.loads(EvidenceWriter.evidence_to_json(dep1)))

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
            derivation_method="analytical",
        )
        loaded_evidence = loader.load_evidence_json(
            json.loads(EvidenceWriter.evidence_to_json(evidence))
        )

        assert loaded_evidence.classification == "DERIVED"
        assert loaded_evidence.derived_from == ["TSS1R-E-001"]
        assert loaded_evidence.derivation_equation == "v = sqrt(mu / r)"

    @pytest.mark.smoke
    def test_assumed_evidence_roundtrip(self) -> None:
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-006",
            parameter_name="tether.deployment_rate_m_s",
            value=0.25,
            unit="m/s",
            quantity_type="velocity",
            classification="ASSUMED",
            confidence="LOW",
            assumption_justification="Historical value not available; EDU benchmark used.",
        )
        json_str = EvidenceWriter.evidence_to_json(evidence)
        data = json.loads(json_str)

        loader = EvidenceLoader()
        loaded_evidence = loader.load_evidence_json(data, allow_unknown_sources=True)

        assert loaded_evidence.classification == "ASSUMED"
        assert loaded_evidence.assumption_justification == (
            "Historical value not available; EDU benchmark used."
        )

    @pytest.mark.smoke
    def test_unknown_evidence_roundtrip(self) -> None:
        """UNKNOWN evidence must preserve value=None exactly."""
        evidence = HistoricalEvidence(
            evidence_id="TSS1R-E-UNK-001",
            parameter_name="tether.tensile_strength_pa",
            value=None,
            unit="Pa",
            quantity_type="stress",
            classification="UNKNOWN",
            confidence="UNKNOWN",
            extraction_notes="Material spec not available.",
        )
        json_str = EvidenceWriter.evidence_to_json(evidence)
        data = json.loads(json_str)

        loader = EvidenceLoader()
        loaded_evidence = loader.load_evidence_json(data, allow_unknown_sources=True)

        assert loaded_evidence.classification == "UNKNOWN"
        assert loaded_evidence.value is None  # NOT converted to 0 or placeholder
        assert loaded_evidence.extraction_notes == "Material spec not available."

    @pytest.mark.smoke
    def test_deterministic_serialization(self) -> None:
        """Same evidence should produce identical JSON."""
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
        json1 = EvidenceWriter.evidence_to_json(evidence)
        json2 = EvidenceWriter.evidence_to_json(evidence)
        assert json1 == json2


class TestEvidenceLoaderValidation:
    """Test EvidenceLoader validation logic."""

    @pytest.mark.smoke
    def test_malformed_json_rejected(self) -> None:
        loader = EvidenceLoader()
        with pytest.raises(EvidencePersistenceError):
            loader.load_source_json({})  # Missing required fields

    @pytest.mark.smoke
    def test_invalid_classification_rejected(self) -> None:
        loader = EvidenceLoader()
        with pytest.raises(EvidencePersistenceError):
            loader.load_evidence_json(
                {
                    "evidence_id": "TEST",
                    "parameter_name": "test",
                    "classification": "INVALID",  # Not KNOWN/DERIVED/ASSUMED/UNKNOWN
                    "confidence": "HIGH",
                },
                allow_unknown_sources=True,
            )

    @pytest.mark.smoke
    def test_known_without_source_rejected(self) -> None:
        loader = EvidenceLoader()
        with pytest.raises(EvidencePersistenceError):
            loader.load_evidence_json(
                {
                    "evidence_id": "TEST",
                    "parameter_name": "test",
                    "value": 100.0,
                    "unit": "m",
                    "quantity_type": "length",
                    "classification": "KNOWN",
                    "confidence": "HIGH",
                    "source_id": None,  # Missing for KNOWN
                },
                allow_unknown_sources=True,
            )

    @pytest.mark.smoke
    def test_derived_without_dependencies_rejected(self) -> None:
        loader = EvidenceLoader()
        with pytest.raises(EvidencePersistenceError):
            loader.load_evidence_json(
                {
                    "evidence_id": "TEST",
                    "parameter_name": "test",
                    "value": 100.0,
                    "unit": "m",
                    "quantity_type": "length",
                    "classification": "DERIVED",
                    "confidence": "HIGH",
                    "source_id": "TEST-SRC",
                    "derived_from": None,  # Missing for DERIVED
                    "derivation_equation": "x=y",
                    "derivation_method": "analytical",
                },
                allow_unknown_sources=True,
            )

    @pytest.mark.smoke
    def test_derived_with_missing_dependency_rejected(self) -> None:
        loader = EvidenceLoader()
        with pytest.raises(EvidencePersistenceError):
            loader.load_evidence_json(
                {
                    "evidence_id": "TEST",
                    "parameter_name": "test",
                    "value": 100.0,
                    "unit": "m",
                    "quantity_type": "length",
                    "classification": "DERIVED",
                    "confidence": "HIGH",
                    "source_id": "TEST-SRC",
                    "derived_from": ["MISSING-DEPENDENCY"],  # Doesn't exist
                    "derivation_equation": "x=y",
                    "derivation_method": "analytical",
                },
                allow_unknown_sources=True,
            )

    @pytest.mark.smoke
    def test_circular_dependency_rejected(self) -> None:
        loader = EvidenceLoader()

        # Create first evidence (KNOWN)
        dep_a = {
            "evidence_id": "DEP-A",
            "parameter_name": "test_a",
            "value": 1.0,
            "unit": "m",
            "quantity_type": "length",
            "classification": "KNOWN",
            "confidence": "HIGH",
            "source_id": "SRC",
        }
        loader.load_source_json({
            "source_id": "SRC",
            "title": "Test",
            "organization": "Test",
            "document_type": "mission_report",
        })
        loader.load_evidence_json(dep_a)

        # Create second evidence that depends on A
        dep_b = {
            "evidence_id": "DEP-B",
            "parameter_name": "test_b",
            "value": 2.0,
            "unit": "m",
            "quantity_type": "length",
            "classification": "DERIVED",
            "confidence": "HIGH",
            "source_id": "SRC",
            "derived_from": ["DEP-A"],
            "derivation_equation": "x",
            "derivation_method": "m",
        }
        loader.load_evidence_json(dep_b)

        # Now try to add C that depends on B (creating A->B->C)
        # then try to make B depend on C (circular)
        # Actually, let's make a simpler circular: A depends on A
        with pytest.raises(EvidencePersistenceError):
            circular = {
                "evidence_id": "CIRC",
                "parameter_name": "circular",
                "value": 3.0,
                "unit": "m",
                "quantity_type": "length",
                "classification": "DERIVED",
                "confidence": "HIGH",
                "source_id": "SRC",
                "derived_from": ["CIRC"],  # Depends on itself
                "derivation_equation": "x",
                "derivation_method": "m",
            }
            loader.load_evidence_json(circular)

    @pytest.mark.smoke
    def test_unknown_with_value_rejected(self) -> None:
        """UNKNOWN evidence with a numerical value must be rejected."""
        loader = EvidenceLoader()
        with pytest.raises(EvidencePersistenceError):
            loader.load_evidence_json(
                {
                    "evidence_id": "TEST",
                    "parameter_name": "test",
                    "value": 500.0,  # NOT allowed for UNKNOWN
                    "unit": "m",
                    "quantity_type": "length",
                    "classification": "UNKNOWN",
                    "confidence": "UNKNOWN",
                },
                allow_unknown_sources=True,
            )

    @pytest.mark.smoke
    def test_missing_source_reference_rejected(self) -> None:
        """KNOWN/DERIVED referencing missing source must be rejected."""
        loader = EvidenceLoader()
        # source_id points to non-existent source
        with pytest.raises(EvidencePersistenceError):
            loader.load_evidence_json(
                {
                    "evidence_id": "TEST",
                    "parameter_name": "test",
                    "value": 100.0,
                    "unit": "m",
                    "quantity_type": "length",
                    "classification": "KNOWN",
                    "confidence": "HIGH",
                    "source_id": "MISSING-SOURCE",
                },
                allow_unknown_sources=False,  # Strict validation
            )


class TestFileIOPersistence:
    """Test reading/writing evidence to files."""

    @pytest.mark.smoke
    def test_source_file_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sources = {
                "NASA-TM-1996-3343": SourceDocument(
                    source_id="NASA-TM-1996-3343",
                    title="Test",
                    organization="NASA",
                    document_type="mission_report",
                )
            }
            file_path = Path(tmpdir) / "sources.json"
            EvidenceWriter.write_sources_to_file(sources, file_path)

            loader = EvidenceLoader()
            loaded = loader.load_sources_from_files(Path(tmpdir))

            assert len(loaded) == 1
            assert "NASA-TM-1996-3343" in loaded

    @pytest.mark.smoke
    def test_evidence_file_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup source
            loader = EvidenceLoader()
            loader.load_source_json({
                "source_id": "NASA-TM-1996-3343",
                "title": "Test",
                "organization": "NASA",
                "document_type": "mission_report",
            })

            evidence = {
                "TSS1R-E-001": HistoricalEvidence(
                    evidence_id="TSS1R-E-001",
                    parameter_name="orbit.altitude_m",
                    value=380000.0,
                    unit="m",
                    quantity_type="length",
                    classification="KNOWN",
                    confidence="HIGH",
                    source_id="NASA-TM-1996-3343",
                )
            }
            file_path = Path(tmpdir) / "evidence.json"
            EvidenceWriter.write_evidence_to_file(evidence, file_path)

            loader2 = EvidenceLoader()
            loader2.load_source_json({
                "source_id": "NASA-TM-1996-3343",
                "title": "Test",
                "organization": "NASA",
                "document_type": "mission_report",
            })
            loaded = loader2.load_evidence_from_files(Path(tmpdir))

            assert len(loaded) == 1
            assert "TSS1R-E-001" in loaded
            assert loaded["TSS1R-E-001"].value == 380000.0

    @pytest.mark.smoke
    def test_classification_independence_preserved(self) -> None:
        """Classification and confidence must remain independent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence = HistoricalEvidence(
                evidence_id="TSS1R-E-001",
                parameter_name="test",
                value=100.0,
                unit="m",
                quantity_type="length",
                classification="KNOWN",
                confidence="LOW",  # LOW confidence but KNOWN classification
                source_id="SRC",
            )

            evidence_dict = {
                "TSS1R-E-001": evidence,
            }
            file_path = Path(tmpdir) / "evidence.json"
            EvidenceWriter.write_evidence_to_file(evidence_dict, file_path)

            loader = EvidenceLoader()
            loader.load_source_json({
                "source_id": "SRC",
                "title": "Test",
                "organization": "Test",
                "document_type": "mission_report",
            })
            loaded = loader.load_evidence_from_files(Path(tmpdir))

            assert loaded["TSS1R-E-001"].classification == "KNOWN"
            assert loaded["TSS1R-E-001"].confidence == "LOW"

    @pytest.mark.smoke
    def test_unknown_preserved_not_converted(self) -> None:
        """UNKNOWN evidence must remain value=None after save/load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence = HistoricalEvidence(
                evidence_id="TSS1R-E-UNK-001",
                parameter_name="unknown_param",
                value=None,
                unit="m",
                quantity_type="length",
                classification="UNKNOWN",
                confidence="UNKNOWN",
                extraction_notes="Not available.",
            )

            evidence_dict = {
                "TSS1R-E-UNK-001": evidence,
            }
            file_path = Path(tmpdir) / "evidence.json"
            EvidenceWriter.write_evidence_to_file(evidence_dict, file_path)

            loader = EvidenceLoader()
            loaded = loader.load_evidence_from_files(Path(tmpdir), allow_unknown_sources=True)

            assert loaded["TSS1R-E-UNK-001"].classification == "UNKNOWN"
            assert loaded["TSS1R-E-UNK-001"].value is None  # Still None, not converted

    @pytest.mark.smoke
    def test_supersession_preserved(self) -> None:
        """Supersession relationships must be preserved through save/load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_evidence = HistoricalEvidence(
                evidence_id="TSS1R-E-001-v1",
                parameter_name="test",
                value=100.0,
                unit="m",
                quantity_type="length",
                classification="KNOWN",
                confidence="HIGH",
                source_id="SRC",
            )
            new_evidence = HistoricalEvidence(
                evidence_id="TSS1R-E-001-v2",
                parameter_name="test",
                value=200.0,
                unit="m",
                quantity_type="length",
                classification="KNOWN",
                confidence="HIGH",
                source_id="SRC",
                supersedes="TSS1R-E-001-v1",
                change_reason="New data discovered.",
            )

            evidence_dict = {
                "TSS1R-E-001-v1": old_evidence,
                "TSS1R-E-001-v2": new_evidence,
            }
            file_path = Path(tmpdir) / "evidence.json"
            EvidenceWriter.write_evidence_to_file(evidence_dict, file_path)

            loader = EvidenceLoader()
            loader.load_source_json({
                "source_id": "SRC",
                "title": "Test",
                "organization": "Test",
                "document_type": "mission_report",
            })
            loaded = loader.load_evidence_from_files(Path(tmpdir))

            assert loaded["TSS1R-E-001-v2"].supersedes == "TSS1R-E-001-v1"
            assert loaded["TSS1R-E-001-v2"].change_reason == "New data discovered."
