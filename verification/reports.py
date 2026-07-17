"""Write human- and machine-readable experiment reports."""

from __future__ import annotations

import json
from pathlib import Path

from verification.records import ExperimentRecord, canonical_json


def write_experiment_report(
    record: ExperimentRecord,
    output_dir: str | Path,
) -> dict[str, Path]:
    """Write JSON evidence + a concise Markdown summary.

    Returns paths to written files.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / f"{record.experiment_id}.json"
    md_path = out / f"{record.experiment_id}.md"

    full = record.as_dict()
    json_path.write_text(json.dumps(full, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    p = record.payload
    val = p.get("validation", {})
    checks = val.get("checks", [])
    check_lines = "\n".join(
        f"- {'PASS' if c.get('passed') else 'FAIL'} `{c.get('name')}` "
        f"(residual={c.get('residual')}, tol={c.get('tolerance')})"
        for c in checks
    )
    flags = "\n".join(f"- {f}" for f in p.get("expert_review_flags", [])) or "- (none)"
    limits = "\n".join(f"- {x}" for x in p.get("limitations", [])) or "- (none)"

    md = f"""# Simulation Proof Report

**Experiment ID:** `{record.experiment_id}`  
**Created (UTC):** {record.created_at_utc}  
**Scenario:** `{p.get("scenario_id")}`  
**Content SHA-256:** `{record.content_sha256}`  
**Simulation version:** `{p.get("software", {}).get("simulation_version")}`

## Claim boundary

{p.get("claim_boundary")}

## Assumptions applied

{', '.join(p.get('assumption_ids', []))}

## Validation

**All passed:** {val.get('all_passed')}

{check_lines}

## Limitations

{limits}

## Expert review flags

{flags}

## Machine-readable evidence

See `{json_path.name}` (canonical hash covers payload only; see `verification.records`).

Canonical payload fingerprint source length: {len(canonical_json(p))} characters.
"""
    md_path.write_text(md, encoding="utf-8")
    return {"json": json_path, "markdown": md_path}
