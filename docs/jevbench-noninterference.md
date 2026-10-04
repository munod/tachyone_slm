# JevBench non-interference report — audit of 2026-10-04

> **Why this exists:** Tachyone (System-1 checkpoint) was submitted to the public JevBench
> benchmark as [`fstandhartinger/jevbench#182`](https://github.com/fstandhartinger/jevbench/issues/182)
> (filed 2026-10-02, **open**, in the maintainer's measurement queue). This workspace produced
> new public artifacts (Phase 0 report, dataset, model repo) and planned further work — so the
> question is whether any of it can perturb that evaluation. **Verdict: nothing produced so far
> touches the evaluation surface; the freeze below keeps it that way until #182 closes.**

Audit performed **read-only** on 2026-10-04, mirroring the maintainer's stated
*"reachability checks"* (comment of 2026-10-03).

---

## 1. What the evaluation depends on (pins declared in #182)

| Pin | Value |
| --- | --- |
| Weights | `munod/tachyone-en` @ revision `1c88ebef8f15f68e8a6583c564d636221f22c29f` |
| Base model | `answerdotai/ModernBERT-large` (Apache-2.0) |
| **Inference source** | **`munod/tachyone` commit `538ac68aed2dd36962d242842efbb32bdfa0d41f`** |
| Harness / method | `fstandhartinger/jevbench` @ `bb05a335bc809e61b20c0f745d25499a82b326fc` (`docs/METHOD-v1.5.md` sha256 `c25d3d8b…1c07`) |
| Licences / sources | `training/data/jev_sources.lock.json` (linked at `blob/main/`) |
| Calibration assets | 5 files with sha256 listed in the issue body |
| Endpoint | local `POST /v1/systemone` — no credential, no online endpoint |

## 2. Audit results (7/7 pass, 2026-10-04)

| # | Check | Result |
| --- | --- | --- |
| 1 | Reachability of all 7 external URLs in the issue body | ✅ all **200** (weights revision, harness commit, 3 `blob/main/` files, licence lock, model page) |
| 2 | Inference-source commit `538ac68` exists upstream | ✅ `538ac68aed2d…`, 2026-10-03 00:04Z, *"docs: publish the P3 calibration set"* |
| 3 | sha256 of the 5 pinned files at revision `1c88ebef` | ✅ **5/5 identical** (`adapter 9046aeb7…`, `confidence ae96187f…`, `prototypes 7cb1d45c…`, `temperature 6463e272…`, `README 83645126…`) |
| 4 | sha256 of `METHOD-v1.5.md` at `bb05a335` | ✅ `c25d3d8b8512e4d93370a9e0c99705d19b2a9389956ca33b8a4bd2b0ec501c07` identical |
| 5 | Upstream `munod/tachyone` untouched by this workspace | ✅ `git status --porcelain` **empty**, HEAD `164ed3b` (`chore(release): v0.8.0`) |
| 6 | All our pushes landed only in `munod/tachyone_slm` | ✅ single remote, 4 commits, latest `f82b5f2` |
| 7 | No identifier collision with the submitted artifact | ✅ submitted `tachyone-en` vs ours `tachyone_slm` (empty) and `tachyone_slm_mixture_v1` (dataset) — distinct ids |

*Method note:* the first download attempt used a non-raw HF URL and returned HTML (hence
mismatching hashes); re-running against `/resolve/<rev>/<file>` produced the 5/5 match above.
The artifacts were never wrong — the probe was.

## 3. Interference matrix

Surfaces of the evaluation × everything this workspace has done or plans.

| Work item | Weights `1c88ebef` | Inference commit `538ac68` | Harness `bb05a335` | Licence lock (`blob/main`) | Issue #182 | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| Phase 0 measurement (24 artifacts, `docs/phase0-baseline.md`) | — | — | — | — | — | **SAFE** — local reads only |
| Phase 1 dataset build + `slm_pipeline/` | — | — | — | — | — | **SAFE** — no upstream file touched |
| HF dataset `tachyone_slm_mixture_v1` | — | — | — | — | — | **SAFE** — new id |
| HF model repo `tachyone_slm` (empty) | — | — | — | — | — | **SAFE** — new id, reserved for future weights |
| This workspace's GitHub pushes | — | — | — | — | — | **SAFE** — separate repo |
| **ADR-0017 published upstream** | — | docs-only, but a `main` push | — | risk if files touched | — | ~~CONDICIONAL~~ → **dropped by PRD v2.0.0** (WS-AD-010) |
| **Phase 2 LoRA training** | — | code/deps could change `main` | — | — | — | **FROZEN** (gated by DEC-002; runs in *this* repo since PRD v2.0) |
| **Phase 3 export + new release** | never re-tag/move `1c88ebef` | release changes what `git clone` resolves | — | — | — | **FROZEN** |
| Editing the issue body/comments | — | — | — | — | reachability noise | **PROHIBITED** (your decision) |

**The one real vector:** the issue's snippet runs `git clone … && cd tachyone` **without a
`checkout`**, so *code* pushed to `munod/tachyone` main would change what a literal re-run
resolves — even though the body declares the pinned commit `538ac68`. The freeze removes this
vector entirely.

## 4. Do not touch until #182 closes

1. **`munod/tachyone`** (GitHub) — no pushes at all: no ADR-0017, no code, no docs, no releases/tags.
2. **`munod/tachyone-en` (HF)** — never move, re-tag or replace revision `1c88ebef`; don't rewrite history.
3. **Issue #182** — no edits, no comments, no reactions.
4. **Pinned harness commit / method file / licence lock** — no upstream edits (`blob/main` links must keep serving the same content).
5. **The published dataset** — frozen as uploaded (`0779c95` + card fix `2147442`).

## 5. Freeze policy (maintainer decisions, 2026-10-04)

* 🔴 Frozen: everything above.
* 🟢 Allowed: pushes to **`munod/tachyone_slm`** (this workspace), documentation and specs here.
* 🔎 Monitoring: read-only status checks of #182 **only on explicit request** (never automatic).

## 6. Resume checklist (trigger: #182 **closed** + **board published**)

1. Reload `.specs/HANDOFF.md` and `.specs/project/STATE.md`.
2. **Re-run this audit** — pins may have moved while frozen (step 1–4 of §2).
3. Confirm upstream HEAD and licence lock still serve the submitted content.
4. Only then: record DEC-002 (stack decision) here → Phase 2. *(Note: PRD v2.0.0 made upstream read-only permanent — WS-AD-010 — so item 1 of §4 is no longer a pause but policy.)*
5. If resuming *before* #182 closes, revisit §3 with measurements and decide explicitly.
