# Decision Records

Workspace-level decisions for the **TachyOne SLM** specification epic. These are **spec-decisions** (documentation of choices made *here*) — they are **not** ADRs of the upstream repository `munod/tachyone`.

## Index

| ID | Decision | Status |
| --- | --- | --- |
| [DEC-001](decoding-strategy.md) | Default answer construction = **candidate scoring**, not free generation | ✅ Decided (recorded in PRD v1.1.0 §3.4) |
| [DEC-002](training-export-stack.md) | Training & export/serving stack — **local record** (upstream ADR-0017 dropped by PRD v2.0) | ⏳ **Pending** (Phase 2–3 gate) |
| [DEC-003](spec-location.md) | Specifications live in `.specs/` | ✅ Decided |
| [DEC-004](docs-language.md) | Documentation language: English (PRD stays Portuguese) | ✅ Decided |
| [DEC-005](product-scope.md) | Product scope: **SLM + serving shim in this repo**; `munod/tachyone` **read-only forever** | ✅ Decided (PRD v2.0.0) |

## How these relate to upstream ADRs

| Upstream ADR (`munod/tachyone`) | Role | Status in this workspace |
| --- | --- | --- |
| ADR-0001 | Frozen wire protocol (`docs/protocol.md`) — the SLM consumes/produces it unchanged | Referenced as binding |
| ADR-0012 | Fast path pattern of the encoder (`src/tachyone/fast.py`) | Referenced as pattern only |
| ADR-0014 / ADR-0015 | Labels derived from text (phrase bank / tone / state-named option) | Referenced as binding for Phase 1 |
| **ADR-0017** | Training stack + export/serving stack + wire schema annex | **DROPPED by PRD v2.0.0** — recorded locally as DEC-002 (DEC-005 point 2: upstream read-only) |

## Conventions

- IDs here are `DEC-NNN`; workspace state IDs are `WS-AD-NNN` / `WS-B-NNN` / `WS-L-NNN` (`.specs/project/STATE.md`). Upstream `AD-NNN` / `B-NN` / `L-NNN` IDs belong to `munod/tachyone` and are only referenced.
- A decision record answers: **context** (why), **decision** (what), **alternatives** (what else), **consequences** (trade-offs), **traceability** (PRD section/KPI).
- Anything decided upstream is linked, never re-authored here.
