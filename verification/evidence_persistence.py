"""JSON persistence for HistoricalEvidence and SourceDocument.

Provides deterministic serialization and validation-on-load for evidence records.
Preserves UNKNOWN values, rejects invalid classifications, validates dependencies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.historical_evidence import (
    HistoricalEvidence,
    SourceDocument,
)


class EvidencePersistenceError(Exception):
    """Raised when evidence loading/saving fails validation."""

    pass


class EvidenceWriter:
    """Deterministic JSON serialization for evidence records."""

    @staticmethod
    def source_to_json(source: SourceDocument) -> str:
        """Serialize SourceDocument to canonical JSON."""
        return json.dumps(
            source.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    @staticmethod
    def evidence_to_json(evidence: HistoricalEvidence) -> str:
        """Serialize HistoricalEvidence to canonical JSON."""
        return json.dumps(
            evidence.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    @staticmethod
    def write_sources_to_file(
        sources: dict[str, SourceDocument],
        file_path: Path,
    ) -> None:
        """Write sources dict to JSON file."""
        data = {sid: src.as_dict() for sid, src in sources.items()}
        file_path.write_text(
            json.dumps(data, sort_keys=True, indent=2, default=str),
            encoding="utf-8",
        )

    @staticmethod
    def write_evidence_to_file(
        evidence: dict[str, HistoricalEvidence],
        file_path: Path,
    ) -> None:
        """Write evidence dict to JSON file."""
        data = {eid: ev.as_dict() for eid, ev in evidence.items()}
        file_path.write_text(
            json.dumps(data, sort_keys=True, indent=2, default=str),
            encoding="utf-8",
        )


class EvidenceLoader:
    """Load and validate evidence from JSON with schema checking."""

    def __init__(self) -> None:
        """Initialize empty evidence and source registries."""
        self.evidence: dict[str, HistoricalEvidence] = {}
        self.sources: dict[str, SourceDocument] = {}

    def load_source_json(
        self,
        data: dict[str, Any],
    ) -> SourceDocument:
        """Load and validate a SourceDocument from dict.

        Raises:
            EvidencePersistenceError: if data is invalid
        """
        try:
            source_id = data.get("source_id")
            if not source_id:
                raise EvidencePersistenceError("source_id is required")

            title = data.get("title")
            if not title:
                raise EvidencePersistenceError("title is required")

            organization = data.get("organization")
            if not organization:
                raise EvidencePersistenceError("organization is required")

            document_type = data.get("document_type")
            if not document_type:
                raise EvidencePersistenceError("document_type is required")

            source = SourceDocument(
                source_id=source_id,
                title=title,
                organization=organization,
                document_type=document_type,
                publication_date=data.get("publication_date"),
                authors=data.get("authors"),
                url=data.get("url"),
                doi=data.get("doi"),
                archive_location=data.get("archive_location"),
                archive_access_date=data.get("archive_access_date"),
                reference_key=data.get("reference_key"),
                version_or_revision=data.get("version_or_revision"),
                scope_summary=data.get("scope_summary"),
                keywords=data.get("keywords", []),
                retrieved_at_utc=data.get("retrieved_at_utc"),
                retrieved_by=data.get("retrieved_by"),
                retrieval_notes=data.get("retrieval_notes"),
                tss1r_relevance=data.get("tss1r_relevance"),
            )
            self.sources[source_id] = source
            return source
        except EvidencePersistenceError:
            raise
        except Exception as e:
            raise EvidencePersistenceError(f"Failed to load source: {e}") from e

    def load_evidence_json(
        self,
        data: dict[str, Any],
        allow_unknown_sources: bool = False,
    ) -> HistoricalEvidence:
        """Load and validate HistoricalEvidence from dict.

        Raises:
            EvidencePersistenceError: if data is invalid or fails schema validation
        """
        try:
            evidence_id = data.get("evidence_id")
            if not evidence_id:
                raise EvidencePersistenceError("evidence_id is required")

            parameter_name = data.get("parameter_name")
            if not parameter_name:
                raise EvidencePersistenceError("parameter_name is required")

            classification = data.get("classification")
            if classification not in ("KNOWN", "DERIVED", "ASSUMED", "UNKNOWN"):
                raise EvidencePersistenceError(
                    f"Invalid classification: {classification}"
                )

            confidence = data.get("confidence")
            if confidence not in ("HIGH", "MEDIUM", "LOW", "UNKNOWN"):
                raise EvidencePersistenceError(f"Invalid confidence: {confidence}")

            value = data.get("value")

            # Classification-specific validation
            if classification == "UNKNOWN":
                if value is not None:
                    raise EvidencePersistenceError(
                        "UNKNOWN evidence must have value=None"
                    )
            else:
                if value is None:
                    raise EvidencePersistenceError(
                        f"{classification} evidence must have a value"
                    )
                if not data.get("unit"):
                    raise EvidencePersistenceError(
                        f"{classification} evidence must specify unit"
                    )
                if not data.get("quantity_type"):
                    raise EvidencePersistenceError(
                        f"{classification} evidence must specify quantity_type"
                    )

            if classification in ("KNOWN", "DERIVED"):
                source_id = data.get("source_id")
                if not source_id:
                    raise EvidencePersistenceError(
                        f"{classification} evidence must reference source_id"
                    )
                if not allow_unknown_sources and source_id not in self.sources:
                    raise EvidencePersistenceError(
                        f"Source {source_id} not found (load sources first)"
                    )

            if classification == "DERIVED":
                derived_from = data.get("derived_from")
                if not derived_from or len(derived_from) == 0:
                    raise EvidencePersistenceError(
                        "DERIVED evidence must list dependencies in derived_from"
                    )
                if not data.get("derivation_equation"):
                    raise EvidencePersistenceError(
                        "DERIVED evidence must include derivation_equation"
                    )
                if not data.get("derivation_method"):
                    raise EvidencePersistenceError(
                        "DERIVED evidence must include derivation_method"
                    )
                # Check dependencies exist
                for dep_id in derived_from:
                    if dep_id not in self.evidence:
                        raise EvidencePersistenceError(
                            f"DERIVED dependency {dep_id} not found"
                        )
                # Check for circular dependencies
                self._check_circular_dependency(evidence_id, derived_from)

            if classification == "ASSUMED":
                if not data.get("assumption_justification"):
                    raise EvidencePersistenceError(
                        "ASSUMED evidence must include assumption_justification"
                    )

            # Create the evidence record
            evidence = HistoricalEvidence(
                evidence_id=evidence_id,
                parameter_name=parameter_name,
                classification=classification,
                confidence=confidence,
                value=value,
                value_min=data.get("value_min"),
                value_max=data.get("value_max"),
                unit=data.get("unit"),
                quantity_type=data.get("quantity_type"),
                uncertainty=data.get("uncertainty"),
                uncertainty_type=data.get("uncertainty_type"),
                source_id=data.get("source_id"),
                source_title=data.get("source_title"),
                source_organization=data.get("source_organization"),
                source_date=data.get("source_date"),
                source_location=data.get("source_location"),
                source_page_range=data.get("source_page_range"),
                source_table_row=data.get("source_table_row"),
                citation_key=data.get("citation_key"),
                extraction_notes=data.get("extraction_notes"),
                assumption_justification=data.get("assumption_justification"),
                derived_from=data.get("derived_from"),
                derivation_equation=data.get("derivation_equation"),
                derivation_method=data.get("derivation_method"),
                created_at_utc=data.get("created_at_utc"),
                created_by=data.get("created_by"),
                updated_at_utc=data.get("updated_at_utc"),
                reviewed=data.get("reviewed", False),
                review_notes=data.get("review_notes"),
                supersedes=data.get("supersedes"),
                superseded_by=data.get("superseded_by"),
                change_reason=data.get("change_reason"),
                used_by_experiment_ids=data.get("used_by_experiment_ids", []),
            )

            # Validate the evidence record
            errors = evidence.validate()
            if errors:
                raise EvidencePersistenceError(
                    f"Evidence validation failed: {'; '.join(errors)}"
                )

            self.evidence[evidence_id] = evidence
            return evidence
        except EvidencePersistenceError:
            raise
        except Exception as e:
            raise EvidencePersistenceError(f"Failed to load evidence: {e}") from e

    def _check_circular_dependency(self, evidence_id: str, depends_on: list[str]) -> None:
        """Check for circular dependencies in derivation chains.

        Raises:
            EvidencePersistenceError: if a circular dependency is detected
        """
        visited = set()
        stack = list(depends_on)

        while stack:
            current = stack.pop()
            if current == evidence_id:
                raise EvidencePersistenceError(
                    f"Circular dependency detected: {evidence_id} depends on itself"
                )
            if current in visited:
                continue
            visited.add(current)

            if current in self.evidence:
                ev = self.evidence[current]
                if ev.derived_from:
                    stack.extend(ev.derived_from)

    def load_sources_from_files(self, directory: Path) -> dict[str, SourceDocument]:
        """Load all source documents from JSON files in a directory."""
        sources_file = directory / "sources.json"
        if not sources_file.exists():
            return {}

        data = json.loads(sources_file.read_text(encoding="utf-8"))
        for source_id, source_data in data.items():
            self.load_source_json(source_data)

        return self.sources

    def load_evidence_from_files(
        self,
        directory: Path,
        allow_unknown_sources: bool = False,
    ) -> dict[str, HistoricalEvidence]:
        """Load all evidence records from JSON files in a directory."""
        evidence_file = directory / "evidence.json"
        if not evidence_file.exists():
            return {}

        data = json.loads(evidence_file.read_text(encoding="utf-8"))
        for evidence_id, evidence_data in data.items():
            self.load_evidence_json(evidence_data, allow_unknown_sources=allow_unknown_sources)

        return self.evidence
