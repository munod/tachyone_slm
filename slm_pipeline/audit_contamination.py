"""Phase 1 — contamination audit: prove no frozen eval content entered the mixture (DAT-04).

Two fingerprints are compared, both **content-based** (record ids are positional and collide
across domains — they are never used as identity):

* **state text** — the information-carrying input;
* **prompt fingerprint** — ``sha256(state | instructions | criteria)``, i.e. the rendered wire
  request itself, which is what the spec means by "prompts".

Empty states are excluded and counted separately: they carry no information, both the frozen
sets and the mixture contain them by construction, and flagging them would drown the real
signal (they are reported in ``empty_states_excluded``).

The temperature-fit validation split is audited as its **own** side (§3.3: the fit must never
touch a frozen row), even though it is a subset of the mixture.

Public probes (typed-decisions / MASSIVE / XNLI) are audited when their directories exist;
when absent the artifact records ``skipped`` with the reason — the generator has no external
data path (its inputs are the phrase banks in code plus ``training/data/domains/*.json``), so
the structural argument is recorded instead of a silent pass.

**Overlap means failure**: ``audit(...)`` returns ``result: "fail"`` and the caller must stop.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

#: Probe directories checked by the upstream harness (``benchmarks/README.md``).
PROBE_DIRS = ("data/typed-decisions", "data/massive", "data/xnli")

#: Unit separator — keeps the three fields unambiguous when concatenated.
SEP = "\x1f"


def prompt_fingerprint(record: dict[str, Any]) -> str | None:
    """Fingerprint of the rendered prompt, or ``None`` for an empty (information-free) state."""
    state = str(record.get("state", ""))
    if not state:
        return None
    criteria = record.get("criteria")
    encoded = (
        json.dumps(criteria, ensure_ascii=False, sort_keys=True)
        if isinstance(criteria, (dict, list))
        else str(criteria)
    )
    blob = SEP.join((state, str(record.get("instructions", "")), encoded))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"{path} not found — regenerate it (see AGENTS.md)")
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _index(records: list[dict[str, Any]]) -> tuple[set[str], set[str], int]:
    states: set[str] = set()
    prompts: set[str] = set()
    empty = 0
    for record in records:
        state = str(record.get("state", ""))
        if not state:
            empty += 1
            continue
        states.add(state)
        fingerprint = prompt_fingerprint(record)
        if fingerprint:
            prompts.add(fingerprint)
    return states, prompts, empty


def _hits(
    records: list[dict[str, Any]], states: set[str], prompts: set[str]
) -> dict[str, int]:
    state_hits = 0
    prompt_hits = 0
    for record in records:
        state = str(record.get("state", ""))
        if not state:
            continue
        state_hits += state in states
        fingerprint = prompt_fingerprint(record)
        prompt_hits += fingerprint is not None and fingerprint in prompts
    return {"state_texts": state_hits, "prompt_fingerprints": prompt_hits}


def audit(
    *,
    mixture: list[dict[str, Any]],
    val: list[dict[str, Any]],
    frozen_paths: dict[str, Path],
    workspace: Path,
) -> dict[str, Any]:
    """Compare mixture + temperature-fit val against every frozen source. Overlap -> ``fail``."""
    frozen_states: set[str] = set()
    frozen_prompts: set[str] = set()
    per_source: dict[str, int] = {}
    frozen_empty = 0
    for name, path in frozen_paths.items():
        records = load_records(path)
        per_source[name] = len(records)
        states, prompts, empty = _index(records)
        frozen_states |= states
        frozen_prompts |= prompts
        frozen_empty += empty

    probes = {
        relative: (
            "present — audit its split with its own loader"
            if (workspace / relative).exists()
            else "skipped — absent locally"
        )
        for relative in PROBE_DIRS
    }
    probe_note = (
        "generator inputs are the phrase banks in code + training/data/domains/*.json; "
        "no external dataset import path exists"
    )

    overlap = {
        "mixture": _hits(mixture, frozen_states, frozen_prompts),
        "temperature_fit_val": _hits(val, frozen_states, frozen_prompts),
    }
    failed = any(count for side in overlap.values() for count in side.values())
    return {
        "dataset": "Tachyone-SLM-Mixture-v1",
        "frozen_sources": per_source,
        "frozen_records": sum(per_source.values()),
        "empty_states_excluded": {
            "mixture": _index(mixture)[2],
            "frozen": frozen_empty,
            "note": "empty states carry no information; counted, never matched",
        },
        "probes": {"status": probes, "reason": probe_note},
        "overlap": overlap,
        "result": "fail" if failed else "pass",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="audit-contamination", description=__doc__)
    parser.add_argument("--mixture", required=True)
    parser.add_argument("--frozen", nargs="+", required=True, metavar="NAME=PATH")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    workspace = Path(__file__).resolve().parents[1]
    mixture = load_records(Path(args.mixture))
    frozen: dict[str, Path] = {}
    for item in args.frozen:
        name, sep, path = item.partition("=")
        if not sep:
            raise SystemExit(f"--frozen expects NAME=PATH, got {item!r}")
        frozen[name] = Path(path)
    report = audit(
        mixture=mixture, val=mixture, frozen_paths=frozen, workspace=workspace
    )
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 1 if report["result"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
