# Contributing

Thanks for contributing to the **TachyOne SLM** epic. This workspace is the specification/documentation side of the feature; the product code lives in [`munod/tachyone`](https://github.com/munod/tachyone).

## 1. Ground rules

1. **PRD is the source of truth.** `docs/tachyone_prd.md` (v1.1.0) defines KPIs (§2), interface (§5), phases (§6) and acceptance (§7). Never contradict it — propose a PRD change instead.
2. **The wire is frozen.** `/v1/systemone` and `tests/test_contract_wire.py` must never be modified by this epic (ADR-0001, PRD §1.4).
3. **No invented numbers.** Anything unmeasured is written as **"to be measured (Phase 0/5)"**. Baselines, metrics and VRAM figures come only from harness runs under the §2 protocol.
4. **Upstream is read-only (`WS-AD-010` / DEC-005).** Nothing is ever pushed to `munod/tachyone`; architecture decisions live **here** as `DEC-NNN` records (e.g. `docs/decisions/training-export-stack.md`). PRD v2.0.0 dropped the upstream ADR-0017 requirement.

## 2. Language policy (DEC-004)

| Artifact | Language |
| --- | --- |
| `docs/tachyone_prd.md` (PRD) | Portuguese — source of truth, do not translate/overwrite |
| All other docs, specs, PRs, commit bodies (when prose is needed) | **English** (PRD §6 gate) |
| Comments in code (upstream repo) | English (repo convention `AGENTS.md`) |

## 3. Commits — Conventional Commits

```
<type>(<scope>): <short summary in imperative mood>
```

- **Types:** `feat`, `fix`, `docs`, `spec`, `test`, `chore`, `perf`, `refactor`, `build`, `ci`, `revert`.
- **Scopes** (suggested): `baseline`, `data`, `slm`, `export`, `system-two`, `bench`, `docs`, `specs`.
- Subject ≤ 72 chars, no trailing period; body explains *why* when non-obvious.
- Reference requirement IDs (`INT-09`) or PRD sections (`§3.5`) in the body for traceability.

Examples:

```
spec(system-two): add calibration requirements with ECE/Brier/Conf traceability
docs(plan): document daily gates and Phase 0 exit criteria
```

## 4. Daily gates (PRD §6 — all must be green)

| Gate | Command |
| --- | --- |
| Lint | `ruff check` |
| Format | `ruff format --check` |
| Types | `pyright` |
| Tests | `pytest` |
| Docs | `mkdocs build --strict` |
| Commits | Conventional Commits (see above) |
| Language | Docs/PRs in English (see §2) |

> This workspace currently ships **no code**, so the code gates apply once implementation starts (upstream repo). `mkdocs build --strict` applies here — keep `mkdocs.yml` nav in sync when adding pages (`.specs/project/BACKLOG.md` WS-B-013).

## 5. Spec-driven workflow

This project follows the `tlc-spec-driven` methodology:

```
SPECIFY (.specs/features/*/spec.md) → DESIGN (design.md, Large/Complex only) → TASKS → EXECUTE (verify + atomic commits)
```

- **Where things live:** project vision/roadmap/state/backlog in `.specs/project/`; feature specs in `.specs/features/<feature>/`; ad-hoc quick tasks in `.specs/quick/`.
- **Requirement IDs are mandatory** and traceable to PRD §2/§7 (`BSL/DAT/SFT/EXP/INT/DOC-NN`).
- **Workspace decisions** use `WS-AD-NNN` in `.specs/project/STATE.md` — they must not collide with upstream `AD-NNN` IDs.
- **Update `STATE.md`** when a decision, blocker or lesson is created; **update `BACKLOG.md`** when work is deferred; **update `ROADMAP.md`** statuses as phases move PLANNED → IN PROGRESS → COMPLETE.
- **Documentation surfaces are updated as a set** (upstream AD-009): `CHANGELOG`, `docs/cookbook-handoff.md`, `docs/model-card.md`, `README`, `benchmarks/report.md`, ADRs.

## 6. Phase-specific rules

- **Phase 0 fixes the numbers:** accuracy targets in PRD §2 may only change from "a medir (Fase 0)" through measured runs (with GPU declared) and maintainer review.
- **Phase 2 needs DEC-002 first** — no training code before the stack decision is recorded (PRD §6, v2.0).
- **Eval sets are frozen:** `eval_en`, `eval_multi`, `eval_en_domains`, `eval_multi_domains` and public probes never appear in training prompts or the temperature-fit validation split (PRD §3.3).
- **Experiment discipline:** pinned seed (AD-009), config verification (L-011), control before variance claims (L-006), worst domain/language gating, never a routed harness (L-013) (PRD §3.2).

## 7. Pull requests (upstream repo)

- Title follows Conventional Commits; description links requirement IDs and PRD sections.
- Checklist: gates green · contract suite untouched & green · docs set updated together · no invented numbers · English prose · `CHANGELOG.md` entry under Keep a Changelog.
