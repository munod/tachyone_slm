"""Phase 1 tests — golden idempotence, stable split, rendering, contamination audit (DAT-03…06).

Run from this workspace (the clone provides ``tachyone`` + ``training``):

    PYTHONPATH="$TACHYONE_REPO" uv run --project "$TACHYONE_REPO" pytest tests/ -q

Small fixtures are generated in-test (fast); tests that need the full 50k dataset or the
frozen eval sets skip with a reason when those artifacts are absent.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest

from slm_pipeline.audit_contamination import audit, load_records
from slm_pipeline.prepare_sft import CLEAN, side
from slm_pipeline.render_sft import (
    candidate_labels,
    gold_target,
    render_pair,
    render_prompt,
)

WS = Path(__file__).resolve().parents[1]
CLONE = Path(os.environ.get("TACHYONE_REPO", "/tmp/opencode/tachyone"))
FROZEN_DIR = CLONE / "data"
CONFIG = WS / "training" / "configs" / "data_sft_slm.json"
MANIFEST = WS / "artifacts" / "slm-mixture-v1" / "manifest.json"

FROZEN_SETS = (
    "eval_en.jsonl",
    "eval_multi.jsonl",
    "eval_en_domains.jsonl",
    "eval_multi_domains.jsonl",
)


def _small_config(per_type: int = 4) -> dict[str, Any]:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    config["per_type"] = per_type
    return config


def _generate(config: dict[str, Any], path: Path) -> bytes:
    from training.generate_data import DataConfig, generate  # upstream pipeline

    generate(DataConfig(**config), path)
    return path.read_bytes()


def _first(path: Path, kind: str | None = None) -> dict[str, Any]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if kind is None or record["type"] == kind:
            return record
    raise AssertionError(f"no {kind or 'record'} found in {path}")


def _frozen_paths() -> dict[str, Path]:
    """Frozen sets that exist locally (empty dict when none — callers just skip)."""
    paths = {name.removesuffix(".jsonl"): FROZEN_DIR / name for name in FROZEN_SETS}
    return {name: path for name, path in paths.items() if path.exists()}


# ---------------------------------------------------------------- idempotence (DAT-03)
def test_raw_generation_is_byte_idempotent(tmp_path: Path) -> None:
    """Same config + seed twice → byte-identical output (golden-hash premise)."""
    config = _small_config()
    first = _generate(config, tmp_path / "a.jsonl")
    second = _generate(config, tmp_path / "b.jsonl")
    assert first == second
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(second).hexdigest()


def test_config_and_generation_match_committed_manifest(tmp_path: Path) -> None:
    """The committed manifest describes *this* config — a silent config edit must fail here."""
    if not MANIFEST.exists():
        pytest.skip("manifest absent — run slm_pipeline.generate_mixture first")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["config_sha256"] == hashlib.sha256(CONFIG.read_bytes()).hexdigest()

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    payload = _generate(config, tmp_path / "raw.jsonl")
    assert hashlib.sha256(payload).hexdigest() == manifest["mixture_sha256"]
    assert manifest["records"] == config["per_type"] * 3 * len(config["domains"])


# ---------------------------------------------------------------- split (DAT-03)
def test_side_is_a_pure_function_of_record_bytes() -> None:
    line = json.dumps({"state": "hello", "type": "noul"}, sort_keys=True)
    assert side(line) == side(line)
    assert side(line) in {"train", "val"}


def test_split_is_deterministic_and_covers_both_sides(tmp_path: Path) -> None:
    """Same records → same sides, and a hash of the bytes keeps membership independent of order."""
    config = _small_config(per_type=300)
    payload = _generate(config, tmp_path / "raw.jsonl")
    lines = [line for line in payload.decode("utf-8").splitlines() if line.strip()]

    shuffled = list(reversed(lines))
    assignment = {line: side(line) for line in lines}
    assert all(assignment[line] == side(line) for line in shuffled)

    values = set(assignment.values())
    assert values == {"train", "val"}
    val_share = sum(1 for line in lines if side(line) == "val") / len(lines)
    assert 0.05 < val_share < 0.15  # ~10% by construction


def test_committed_split_is_stable() -> None:
    """The published split files reproduce from the clean mixture, byte for byte."""
    if not (CLEAN.exists() and (WS / "data" / f"{CLEAN.stem}.val.jsonl").exists()):
        pytest.skip("split absent — run slm_pipeline.prepare_sft first")
    clean = [
        line for line in CLEAN.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    val = [
        line
        for line in (WS / "data" / f"{CLEAN.stem}.val.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    expected = [line for line in clean if side(line) == "val"]
    assert val == expected
    assert 0.05 < len(val) / len(clean) < 0.15


# ---------------------------------------------------------------- rendering (DAT-05/06)
def test_prompt_is_the_wire_request_and_parses() -> None:
    from tachyone.wire import parse_request  # contract authority

    if not CLEAN.exists():
        pytest.skip("clean mixture absent")
    for kind in ("choice", "score", "noul"):
        record = _first(CLEAN, kind)
        prompt = render_prompt(record)
        request = parse_request(json.loads(prompt.removesuffix("Answer:")))
        assert set(request.questions) == {"q"}
        assert request.questions["q"].type == kind


@pytest.mark.parametrize("kind", ["choice", "score", "noul"])
def test_gold_target_is_in_the_candidate_set(kind: str) -> None:
    if not CLEAN.exists():
        pytest.skip("clean mixture absent")
    record = _first(CLEAN, kind)
    labels = candidate_labels(record)
    assert labels is not None
    target = gold_target(record)
    assert target is not None and target in labels


def test_render_rejects_a_target_outside_the_candidates() -> None:
    record = {
        "state": "please refund this",
        "type": "choice",
        "instructions": "Which team?",
        "criteria": {"billing": None, "technical": None},
        "target": "sales",  # not a key of criteria
        "lang": "en",
    }
    pair, reason = render_pair(record)
    assert pair is None
    assert reason == "target_not_in_candidates"


def test_render_rejects_malformed_criteria() -> None:
    record = {
        "state": "hello",
        "type": "noul",
        "instructions": "Is it a request?",
        "criteria": {"yes": "a", "no": "b"},  # missing true/false
        "target": 1,
        "lang": "en",
    }
    pair, reason = render_pair(record)
    assert pair is None
    assert reason == "malformed_criteria"


def test_invalid_pairs_are_dropped_with_a_count_in_the_report() -> None:
    report_path = WS / "artifacts" / "slm-mixture-v1" / "split_render.json"
    if not report_path.exists():
        pytest.skip("report absent — run slm_pipeline.prepare_sft first")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["pairs"] + sum(report["dropped_pairs"].values()) == report["records"]


# ---------------------------------------------------------------- contamination (DAT-04)
def test_audit_passes_on_the_published_dataset() -> None:
    if not CLEAN.exists() or not _frozen_paths():
        pytest.skip("clean mixture or frozen sets absent")
    val_lines = [
        line
        for line in (WS / "data" / f"{CLEAN.stem}.val.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    report = audit(
        mixture=load_records(CLEAN),
        val=[json.loads(line) for line in val_lines],
        frozen_paths=_frozen_paths(),
        workspace=WS,
    )
    assert report["result"] == "pass"
    assert report["overlap"]["mixture"]["state_texts"] == 0
    assert report["overlap"]["mixture"]["prompt_fingerprints"] == 0
    assert report["overlap"]["temperature_fit_val"]["state_texts"] == 0
    assert report["frozen_records"] >= 18_000


def test_audit_fails_on_a_seeded_overlap() -> None:
    """The audit must be able to fail (DAT-04 AC2) — a frozen row injected into the mixture."""
    frozen = _frozen_paths()
    seed_path = frozen.get("eval_en")
    if seed_path is None:
        pytest.skip("eval_en absent locally")
    seed_record = next(
        (record for record in load_records(seed_path) if record.get("state")),
        None,
    )
    assert seed_record is not None, "eval_en has no non-empty state to seed with"
    report = audit(mixture=[seed_record], val=[], frozen_paths=frozen, workspace=WS)
    assert report["result"] == "fail"
    assert report["overlap"]["mixture"]["state_texts"] == 1


# ---------------------------------------------------------------- cells (DAT-07)
def test_all_language_domain_cells_are_present() -> None:
    if not CLEAN.exists():
        pytest.skip("clean mixture absent")
    cells: dict[str, set[str]] = {}
    for line in CLEAN.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        cells.setdefault(str(record.get("lang", "?")), set()).add(
            str(record.get("domain", "support"))
        )
    assert set(cells) == {"en", "pt", "es", "fr", "de", "it", "nl"}
    assert all(
        domains == {"support", "ecommerce", "agent_tools", "documents", "voice"}
        for domains in cells.values()
    )


def test_pairs_carry_every_primitive_and_split() -> None:
    pairs_path = WS / "data" / f"{CLEAN.stem}.pairs.jsonl"
    if not pairs_path.exists():
        pytest.skip("pairs absent — run slm_pipeline.prepare_sft first")
    kinds: set[str] = set()
    splits: set[str] = set()
    for line in pairs_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        pair = json.loads(line)
        kinds.add(pair["type"])
        splits.add(pair["split"])
    assert kinds == {"choice", "score", "noul"}
    assert splits == {"train", "val"}
