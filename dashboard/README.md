# Local Research Dashboard

A small, local-only UI for inspecting the v0.1 quasi-static deployment experiment evidence. It is deliberately not an operations console, mission-design tool, or flight-software interface.

## Run

```bash
python -m dashboard.app
```

Open <http://127.0.0.1:8080>. The **Run baseline scenario** action writes a new evidence record to `data/experiments/`; the dashboard reads existing JSON evidence from that directory on load.

The server binds only to loopback and uses Python's standard library. Keep it local: it has no authentication and is not designed to be exposed on a network.

## What the UI shows

- The most recent experiment's orbit, tether, and tip-altitude diagnostics.
- The recorded consistency checks and their numerical residuals.
- The model limitations embedded in the experiment record.
- A short, local evidence log of recent runs.

The tip altitude cards are **free-orbit diagnostics if cut**, not validated mission outcomes. See `docs/assumptions/ASSUMPTIONS_REGISTER.md` and the report's claim boundary before interpreting any result.
