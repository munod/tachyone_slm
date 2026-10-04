# DEC-003 — Specifications live in `.specs/`

**Status:** ✅ Decided
**Date:** 2026-10-03
**Workspace ID:** WS-AD-001 (`.specs/project/STATE.md`)

---

## Context

The spec-driven methodology (`tlc-spec-driven`) standardizes on a `.specs/` directory, but a plain `specs/` path is a common alternative. The target repository `munod/tachyone` already ships `.specs/project/BACKLOG.md`, `.specs/project/STATE.md` and `.specs/features/<feature>/spec.md` (referenced by PRD §10), so this workspace must stay path-compatible with it.

## Decision

Use **`.specs/`** (hidden directory) with the skill's canonical layout:

```
.specs/
├── project/    # PROJECT.md · ROADMAP.md · STATE.md · BACKLOG.md
├── features/   # <feature>/spec.md (+ design.md for the largest features)
└── quick/      # quick-mode tasks
```

## Alternatives

| Alternative | Verdict | Why |
| --- | --- | --- |
| `specs/` (visible) | ❌ | Diverges from both the skill and the upstream repo — migration cost later |
| `docs/specs/` | ❌ | Conflates publication docs (`docs/`, mkdocs site) with working spec artifacts; would leak internal state into the published site |

## Consequences

- ✅ Same paths as upstream → artifacts can be moved/merged into `munod/tachyone` without renaming.
- ✅ `mkdocs.yml` (`docs_dir: docs`) keeps the published site clean; specs are linked from `docs/index.md`, not rendered.
- ⚠️ Hidden directory is less discoverable — mitigated by root `README.md` and `.specs/README.md`.
