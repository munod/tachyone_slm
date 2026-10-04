# Phase 4 — System-2 Integration Specification (`system_two()`)

**Feature ID:** `system-two-integration` · **Prefix:** `INT` · **Phase:** 4 (Days 7–8) · **Status:** Planned
**PRD source:** `docs/tachyone_prd.md` v1.1.0 — §1.2 (handoff), §3.4 (decoding), §3.5 (calibration), §5.1–§5.4 (interface/integration/τ/schema), §7.1, §7.2, §7.4 (acceptance)
**Design:** `.specs/features/system-two-integration/design.md` · **Decision:** `docs/decisions/decoding-strategy.md` (DEC-001)

---

## Problem Statement

The handoff slot `system_two()` is currently a user-supplied stub (B-3, `cookbook-handoff.md`). The SLM must become its **official implementation**: invoked only when the encoder abstains, answering strictly inside the frozen wire contract, with calibrated confidence and a documented τ/retry/fallback policy — while `tests/test_contract_wire.py` remains untouched and green.

## Goals

- [ ] `system_two(state, questions, context)` implemented, exported in the SDK (`tachyone.system_two`) + CLI flag; cookbook example migrated from stub.
- [ ] Default decoding = candidate scoring per §3.4; wire invariants satisfied **by construction**.
- [ ] Temperature scaling fitted per (primitive, language); ECE ≤ 0.030 with Brier + `Conf` published.
- [ ] τ configurable (reference 0.6), max 1 retry, explicit fallback chain; `JSON ok` = 1.000; handoff coverage 100%.
- [ ] Experimental constrained-generation mode available as opt-in.

## Out of Scope

| Item | Reason |
| --- | --- |
| Any change to `/v1/systemone` or its schema | Frozen wire (ADR-0001, §1.4) |
| Modifying the System-1 encoder / handoff thresholds logic | PRD §1.4; τ is *consumed*, not re-tuned here |
| Full KPI benchmark runs (latency/throughput/rows) | Phase 5 |
| Making free generation the default | §3.4 decision (DEC-001) |
| Multi-tenant / remote-only serving | §1.4 |

---

## User Stories

### P1: Official `system_two()` implementation ⭐ MVP

**User Story**: As a SDK/CLI user, I want `system_two()` to be a real implementation so that abstained items get a fast, valid answer without wiring an external LLM myself.

**Why P1**: It is literally the purpose of this PRD — "a especificação da implementação oficial desse slot" (§1.3).

**Acceptance Criteria**:

1. WHEN an item abstains (`assess_response(τ)` reports confidence < τ) THEN `system_two(state, questions, context)` SHALL consume the `HandoffReport` from `tachyone.handoff` and return a **wire-valid** response (§5.2).
2. WHEN composition happens THEN it SHALL be **client-side and additive** (B-3 pattern): **no new field** in `/v1/systemone` (§5.2).
3. WHEN exposed THEN the SDK SHALL export `tachyone.system_two` and the CLI SHALL have the corresponding flag (§5.2).
4. WHEN documentation updates THEN the `docs/cookbook-handoff.md` example SHALL be migrated from stub to the real implementation (§5.2).
5. WHEN the contract suite runs THEN `tests/test_contract_wire.py` SHALL be **unchanged and green** (§1.4, §7.2).

**Independent Test**: SDK import + CLI invocation demo; contract suite diff = empty, result = green.

### P1: Default decoding = candidate scoring

**User Story**: As a consumer of the API, I want answers built by scoring candidates so that the response schema cannot be violated and probabilities are real distributions.

**Why P1**: §3.4 decision (DEC-001) — compliance by construction; B-10 showed free generation failing the contract (0.889) at 46 s per 52-option attempt.

**Acceptance Criteria**:

1. WHEN answering a `choice` question THEN each `criteria` label SHALL be scored as a length-normalized logprob continuation of the shared prefix (shared-prefix batch) → `probabilities = softmax(logprobs)` **summing to 1.0**, `confidence` = modal label mass (§3.4).
2. WHEN answering a `noul` question THEN `noul = sigmoid(ℓ(true) − ℓ(false))` over `criteria.true/false` → a **float in 0..1** (no `ptrue`, no `"false"` string — §5.1).
3. WHEN answering a `score` question THEN `probabilities` SHALL be the softmax over level indices, `score = Σ i·pᵢ` (expected value), `legend` mirrored from the request, `confidence` = modal index mass (§3.4, §5.1).
4. WHEN `options` are numerous (up to 255) THEN cost SHALL remain stable (no per-option free generation, §3.4).
5. WHEN producing `confidence`/`probabilities` THEN they SHALL come from **logits + §3.5 fit — never from generated text** (§3.4 "regra de ouro").

**Independent Test**: per-primitive unit tests: distribution sums, `noul` range, `score` expectation, legend mirror, `answers` ↔ `questions` key parity.

### P1: Wire invariants & contract compliance

**User Story**: As an API consumer, I want every response to satisfy the frozen invariants so that downstream parsers never break.

**Acceptance Criteria**:

1. WHEN any response is returned THEN it SHALL contain the `answers` wrapper; `probabilities` keys SHALL be exactly the option/index keys and sum to 1.0; `noul` SHALL be a float 0..1; `legend` SHALL mirror the score `criteria`; `answers` keys SHALL match `questions` keys (§5.1).
2. WHEN 1,000 items run on each of the two `compare.py` sets THEN `JSON ok` SHALL be **1.000** (§2, §7.1).
3. WHEN a parse/construction fails THEN it SHALL **not** be silently accepted — exactly **1 retry**, then the fallback chain (§5.3).

**Independent Test**: `JSON ok` = 1.000 on both sets; forced-parse-failure test asserts retry + explicit failure path.

### P1: Calibration fit

**User Story**: As a consumer, I want confidence calibrated to reality so that τ routing means something.

**Why P1**: §1.3 — "a confidence that was never fitted to anything" is the central criticism being rejected; ECE ≤ 0.030 is §7.4.

**Acceptance Criteria**:

1. WHEN fitting THEN temperature scaling SHALL use `training/fit_calibration.py` **per (primitive, language)**, grid **0.25–20.00 step 0.05**, on the **train-split validation set — never on eval sets** (§3.5).
2. WHEN reporting THEN **ECE (10-bin) + Brier + `Conf`** SHALL be published together (L-015/L-007 — ECE alone is not a quality metric) (§3.5, §7.4).
3. WHEN a calibration asset is unreadable THEN it SHALL **warn by name** and never degrade silently (B-8 pattern) (§3.5).
4. WHEN measured THEN ECE (fitted) SHALL be **≤ 0.030** (§2, §7.4).

**Independent Test**: fit artifacts per (primitive, language); report triple (ECE/Brier/`Conf`); corrupted-asset test asserts loud warning.

### P1: τ policy, retry and fallback chain

**User Story**: As an operator, I want τ configurable with a documented failure chain so that routing thresholds fit each use case (safety vs automation).

**Acceptance Criteria**:

1. WHEN configuring τ THEN it SHALL be **configurable with no universal default**; documented guidance: ≈0.3 safety · ≈0.5 routing · ≈0.8 automation; benchmark reference **τ = 0.6** (§5.3).
2. WHEN an item abstains THEN coverage SHALL be **100%**: every abstained item receives a wire-valid answer with at most **1 retry** (§2, §7.2).
3. WHEN the SLM fails after retry THEN the documented chain SHALL apply: **SLM local → remote LLM (`llm` backend) → human review**, with the chain **explicit in the diagnostic response** (existing `handoff` object in the CLI) (§5.3).
4. WHEN τ/routing is evaluated on benchmarks THEN the harness SHALL use τ = 0.6 reference (§2, §5.3).

**Independent Test**: τ config surface test; coverage report = 100%; forced-failure test asserts the chain appears in diagnostics.

### P2: Experimental constrained-generation mode

**User Story**: As a researcher, I want an opt-in generation mode (constrained decoding of `answers` values) so that the hard slice can be tested with internal reasoning later.

**Why P2**: §3.4 documents it as *alternativa … modo experimental (Fase 4)* — not the default.

**Acceptance Criteria**:

1. WHEN the experimental mode is enabled THEN values of the `answers` wrapper SHALL be generated under the contract's grammar/JSON Schema (XGrammar/llguidance or vLLM `guided_json`) with the runtime assembling the final JSON (§3.4, §5.4).
2. WHEN the mode emits reasoning THEN a scratchpad **before** the wrapper SHALL be allowed and **discarded by the runtime** (§3.4).
3. WHEN probabilities are needed in this mode THEN they SHALL be produced by rescoring (never asserted from free text) (§3.4).
4. WHEN the mode is off (default) THEN behavior SHALL be pure scoring — zero generated tokens in the default path (`usage.output_tokens = 0`, §5.1).

**Independent Test**: grammar-conformance test on generated values; scratchpad stripped; default path emits 0 output tokens.

### P2: Schema verification & annex

**Acceptance Criteria**:

1. WHEN validating (any mode) THEN the contract grammar/JSON Schema SHALL act as the **final verification** in default mode and as the **source** of constrained decoding in experimental mode (§5.4).
2. WHEN publishing THEN the schema SHALL be an **annex of ADR-0017**, tested against `tests/test_contract_wire.py` (§5.4).

**Independent Test**: schema validation passes over produced responses; contract suite green.

---

## Edge Cases

- WHEN `questions` and `answers` keys diverge THEN the response SHALL be rejected before returning (§5.1 invariant).
- WHEN `probabilities` do not sum to 1.0 (float drift) THEN the response SHALL be normalized or rejected — never returned failing the invariant.
- WHEN τ is missing at call time THEN the caller SHALL receive a clear configuration error (no silent universal default, §5.3).
- WHEN the abstained slice is empty THEN `system_two()` SHALL simply not be invoked and coverage SHALL remain 100% by vacuity (recorded, not guessed).
- WHEN calibration assets are missing for a (primitive, language) pair THEN B-8 behavior: warn **by name**; never degrade silently (§3.5).
- WHEN the remote-LLM fallback also fails THEN the chain SHALL end at human review, explicitly reported (§5.3).

---

## Requirement Traceability

| Requirement ID | Requirement | PRD | KPI / Criterion | Status |
| --- | --- | --- | --- | --- |
| INT-01 | Official `system_two()` consuming `HandoffReport`; SDK export + CLI flag + cookbook migration | §5.2, §1.3 | cobertura handoff → §7.2 | Pending |
| INT-02 | Additive client-side composition; no new wire fields; contract suite untouched & green | §5.2, §1.4 | §7.1, §7.2 | Pending |
| INT-03 | Scoring decoding: `choice` softmax, `noul` sigmoid diff, `score` expectation + legend | §3.4, §5.1 | `JSON ok` → §7.1 | Pending |
| INT-04 | Wire invariants satisfied; `answers` ↔ `questions` parity; `probabilities` = 1.0 | §5.1 | §7.1 | Pending |
| INT-05 | `JSON ok` = 1.000 on both sets | §2 | §7.1 | Pending |
| INT-06 | 100% handoff coverage; ≤ 1 retry; failures never silently accepted | §5.3, §2 | §7.2 | Pending |
| INT-07 | Fallback chain local → remote LLM → human, explicit in diagnostics | §5.3 | §7.2 | Pending |
| INT-08 | τ configurable, no universal default; ref 0.6; cookbook guidance table | §5.3 | §7.2 | Pending |
| INT-09 | Temperature scaling per (primitive, language), grid 0.25–20.00/0.05, fit on train-val only | §3.5 | §7.4 | Pending |
| INT-10 | ECE ≤ 0.030 with Brier + `Conf` published together | §2, §3.5 | §7.4 | Pending |
| INT-11 | Calibration asset failure warns by name (B-8), never silent | §3.5 | §7.4 integrity | Pending |
| INT-12 | Confidence/probabilities from logits + fit — never generated text | §3.4 | §7.1/§7.4 | Pending |
| INT-13 | Experimental constrained-generation mode (opt-in): grammar from contract, scratchpad discarded, rescoring for probabilities | §3.4, §5.4 | §7.1 (mode-on) | Pending |
| INT-14 | Schema as final verification (default) / decoding source (experimental); annex of ADR-0017 | §5.4 | §7.6 | Pending |
| INT-15 | `usage` reported (input_tokens counted, output_tokens 0 in default mode) | §5.1 | contract fidelity | Pending |

**Coverage:** 15 requirements, 0 unmapped.

---

## Verification (Phase 4 exit)

- **Gates:** `ruff check` · `ruff format --check` · `pyright` · `pytest` (incl. **unchanged** `tests/test_contract_wire.py`) · `mkdocs build --strict` (PRD §6).
- **Evidence:** `JSON ok` = 1.000 on both sets; 100% coverage report at τ = 0.6; ECE/Brier/`Conf` table; forced-failure tests (parse fail → retry → chain); B-8 corrupted-asset test.
- **KPI measurement discipline:** latency/throughput/VRAM numbers are **Phase 5** deliverables — Phase 4 verifies behavior, not the perf tables (WS-AD-006: no estimated numbers).

## Success Criteria

- [ ] Abstained items get wire-valid SLM answers 100% of the time (max 1 retry), fallback chain visible on failure.
- [ ] `JSON ok` = 1.000; invariants hold by construction in default mode.
- [ ] ECE ≤ 0.030 (fitted) with Brier + `Conf` alongside.
- [ ] `test_contract_wire.py` diff is empty and green.
