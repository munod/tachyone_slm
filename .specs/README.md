# `.specs/` — Specification Workspace

Spec-driven artifacts for the **TachyOne SLM** epic (System-2 local of the TachyOne hybrid), following the `tlc-spec-driven` methodology.

## Why `.specs/` (and not `specs/`)

Decision **DEC-003** (`docs/decisions/spec-location.md`): the skill's canonical layout is `.specs/`, and the upstream repository `munod/tachyone` referenced by the PRD (§10) already uses `.specs/project/BACKLOG.md`, `.specs/project/STATE.md` and `.specs/features/...`. Using the same path keeps this workspace compatible with the target repo.

## Layout

```
.specs/
├── project/
│   ├── PROJECT.md      # Vision, goals, stack, scope, constraints (PRD v1.2.0 derived)
│   ├── ROADMAP.md      # Phases 0–5 as milestones, feature status
│   ├── STATE.md        # Persistent memory: decisions, blockers, lessons, deferred ideas, todos
│   └── BACKLOG.md      # Workspace-owned backlog items (open decisions & follow-ups)
├── features/
│   ├── baseline-system2/spec.md        # Phase 0 (Day 1)
│   ├── slm-mixture-data/spec.md        # Phase 1 (Days 2–3)
│   ├── slm-lora-sft/spec.md            # Phase 2 (Days 4–5)
│   ├── slm-export-quant/spec.md        # Phase 3 (Day 6)
│   ├── system-two-integration/spec.md  # Phase 4 (Days 7–8) + design.md
│   └── slm-benchmark-docs/spec.md      # Phase 5 (Days 9–10)
└── quick/                               # Reserved for quick-mode tasks (none yet)
```

## Rules

- **Source of truth:** `docs/tachyone_prd.md` (PRD **v1.2.0**). Specs never contradict it; every requirement traces back to a PRD section (§2 KPIs, §7 acceptance criteria).
- **No invented numbers.** Anything the PRD marks as *a medir* stays `to be measured` until its own phase runs — Phase 0 has run, so its rows now carry measured values (`docs/phase0-baseline.md`).
- **Language:** English (PRD §6 gate: docs/PRs in English). The PRD itself remains the Portuguese source of truth (DEC-004).
- **IDs:** feature requirements use `BSL/DAT/SFT/EXP/INT/DOC-NN`. Workspace decisions use `WS-AD-NNN` in `STATE.md` — they do **not** collide with upstream `AD-NNN` IDs of `munod/tachyone`.
- **Phase depth:** this epic is *Complex* (new domain, ambiguity around the stack decision), so specs carry full requirement IDs; `design.md` exists for the largest feature (`system-two-integration`); **since PRD v2.0.0 the product code is produced in *this* repository** — `munod/tachyone` is a read-only dependency (WS-AD-010 / DEC-005).
