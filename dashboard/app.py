"""Local research dashboard for inspecting v0.1 experiment evidence.

Run with ``python -m dashboard.app`` and open http://127.0.0.1:8080.
This intentionally uses only the standard library and must not be exposed as a
network service: it is a local convenience UI for a research prototype.
"""

from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from simulation.scenarios.config import DeploymentScenarioConfig
from simulation.scenarios.runner import run_deployment_scenario

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).with_name("static")
EXPERIMENTS_DIR = ROOT / "data" / "experiments"


def _load_records() -> list[dict]:
    """Return recent, structurally valid experiment records without failing the UI."""
    records: list[dict] = []
    for path in sorted(EXPERIMENTS_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            payload = raw["payload"]
            outputs = payload["outputs"]
            records.append(
                {
                    "experiment_id": raw["experiment_id"],
                    "created_at_utc": raw["created_at_utc"],
                    "scenario_id": payload["scenario_id"],
                    "validation_passed": payload["validation"]["all_passed"],
                    "tether_length_m": payload["parameters"]["tether_length_m"],
                    "orbit_altitude_m": payload["parameters"]["orbit_altitude_m"],
                    "upper_altitude_m": outputs["tip_diagnostics_free_orbit_if_cut"]["upper"]["altitude_m"],
                    "lower_altitude_m": outputs["tip_diagnostics_free_orbit_if_cut"]["lower"]["altitude_m"],
                    "checks": payload["validation"]["checks"],
                    "limitations": payload["limitations"],
                }
            )
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return records


def dashboard_data() -> dict:
    records = _load_records()
    return {"records": records, "latest": records[0] if records else None}


def run_default_scenario() -> dict:
    """Run the documented baseline scenario and return its dashboard projection."""
    result = run_deployment_scenario(DeploymentScenarioConfig(), output_dir=EXPERIMENTS_DIR)
    records = _load_records()
    matching = next((record for record in records if record["experiment_id"] == result.record.experiment_id), None)
    if matching is None:
        raise RuntimeError("Generated experiment record could not be read back")
    return matching


class DashboardHandler(BaseHTTPRequestHandler):
    """Serve dashboard assets plus a small local-only evidence API."""

    server_version = "OrbitalTetherDashboard/0.1"

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/experiments":
            self._send_json(dashboard_data())
            return
        if path in {"/", "/index.html"}:
            self._send_file(STATIC_DIR / "index.html")
            return
        if path.startswith("/static/"):
            candidate = (STATIC_DIR / path.removeprefix("/static/")).resolve()
            if STATIC_DIR.resolve() in candidate.parents:
                self._send_file(candidate)
                return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/run-baseline":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        try:
            self._send_json({"record": run_default_scenario()}, status=HTTPStatus.CREATED)
        except (OSError, RuntimeError, ValueError) as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, path: Path) -> None:
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        content = path.read_bytes()
        mime, _ = mimetypes.guess_type(path.name)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8080), DashboardHandler)
    print("Orbital Tether research dashboard: http://127.0.0.1:8080")
    print("Local only. This interface is not flight operations software.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
