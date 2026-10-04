# DEC-004 — Documentation language: English (PRD stays Portuguese)

**Status:** ✅ Decided
**Date:** 2026-10-03
**Workspace ID:** WS-AD-002 (`.specs/project/STATE.md`)
**PRD traceability:** §6 ("docs/PRs em inglês", `AGENTS.md`/`CONTRIBUTING.md`)

---

## Context

The PRD of this project is written in **Portuguese** (v1.1.0, `docs/tachyone_prd.md`), yet PRD §6 defines the repository gates with an explicit language rule: *conventional commits · docs/PRs em inglês*. New documentation therefore has to follow the gate, while the product source of truth must not be rewritten.

## Decision

| Artifact | Language | Note |
| --- | --- | --- |
| `docs/tachyone_prd.md` (PRD) | 🇧🇷 **Portuguese** — untouched | Product source of truth; referenced, never overwritten |
| `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md` | 🇬🇧 **English** | Publication surfaces |
| `docs/**` (architecture, plan, model card, decisions, index) | 🇬🇧 **English** | Site pages (`mkdocs build --strict`) |
| `.specs/**` (project, features) | 🇬🇧 **English** | Same gate applies; also upstream-ready |
| Commits / PRs (upstream) | 🇬🇧 **English** subject + prose | Conventional Commits |

The language choice is made **explicit in `README.md` and `CHANGELOG.md`** so readers are never surprised by the two-language repository.

## Alternatives

| Alternative | Verdict | Why |
| --- | --- | --- |
| Everything in Portuguese | ❌ | Violates the PRD's own §6 gate for docs/PRs |
| Everything in English (incl. translating the PRD) | ❌ | The PRD is a versioned product artifact (v1.1.0); translating it would fork the source of truth and break references (§9, §10) |
| Mixed without documentation | ❌ | Ambiguity for contributors; this record removes it |

## Consequences

- ✅ Contributors know exactly which language to use for each surface (also encoded in `CONTRIBUTING.md` §2).
- ✅ Specs/decisions remain merge-compatible with the English-language upstream repo.
- ⚠️ Portuguese readers must read new docs in English — accepted as the cost of matching the repository gate; quotes of PRD section titles remain in Portuguese where useful for traceability.
