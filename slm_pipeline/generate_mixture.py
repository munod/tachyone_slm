"""Phase 1 — generate `Tachyone-SLM-Mixture-v1` from one committed config (DAT-01, DAT-03).

The config file is the single source of truth: the run reads
``training/configs/data_sft_slm.json`` and builds the upstream ``DataConfig`` from it, so the
JSON and the run can never drift (no duplicated CLI flags). Generation itself is the
**existing** upstream pipeline (``training/generate_data.py``) — this workspace adds no new
label logic, which is what keeps ADR-0014/ADR-0015 binding (§3.3).

Sizing: ``raw = per_type × 3 primitives × len(domains)`` — with ``per_type = 5700`` and 5
domains that is **85,500 raw** records; the 7 languages cycle inside each ``per_type`` block
(``language = languages[index % 7]``). **41.3% of raw records collide with a frozen eval
set** (the phrase-bank pools are shared — measured 2026-10-03), so
``slm_pipeline.prepare_sft`` drops them and lands the clean dataset at **≈ 50,180 ≈ 50,000**
records. The raw file is therefore written as ``*.raw.jsonl`` — the canonical
``tachyone_slm_mixture_v1.jsonl`` name belongs to the **clean** dataset only.

Seed **20261003** is deliberately outside {1 (train), 2 (eval), 42 (default)} so no record
draw can coincide with a frozen eval split by construction (contamination guard, DAT-04).

Outputs (big files stay out of git, see ``.gitignore``):

* ``data/tachyone_slm_mixture_v1.raw.jsonl`` — raw generation (contains frozen overlaps)
* ``artifacts/slm-mixture-v1/manifest.json`` — sha256 + counts + per-cell table

Run (this workspace is the cwd; the clone provides the upstream packages):

    cd <workspace> && PYTHONPATH="$TACHYONE_REPO" uv run --project "$TACHYONE_REPO" \
        python -m slm_pipeline.generate_mixture --config training/configs/data_sft_slm.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parents[1]


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    unknown = set(config) - {
        "seed",
        "per_type",
        "languages",
        "domains",
        "per_domain",
        "source",
        "noise_rate",
    }
    if unknown:
        raise SystemExit(f"{path}: unknown config keys {sorted(unknown)}")
    return config


def per_cell(records_path: Path) -> dict[str, dict[str, int]]:
    """language → domain → records (DAT-07: Phase 2 gates on the worst cell)."""
    cells: dict[str, Counter[str]] = {}
    with records_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            lang = str(record.get("lang", "?"))
            domain = str(record.get("domain", "support"))
            cells.setdefault(lang, Counter())[domain] += 1
    return {
        lang: dict(sorted(counts.items())) for lang, counts in sorted(cells.items())
    }


def run(config_path: Path, out_path: Path) -> dict[str, Any]:
    from training.generate_data import (  # upstream pipeline (PYTHONPATH=.)
        DataConfig,
        generate,
    )

    config = DataConfig(**load_config(config_path))
    written = generate(config, out_path)

    digest = hashlib.sha256(out_path.read_bytes()).hexdigest()
    kinds: Counter[str] = Counter()
    langs: Counter[str] = Counter()
    with out_path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            kinds[str(record["type"])] += 1
            langs[str(record.get("lang", "?"))] += 1

    expected = config.per_type * 3 * len(config.domains)
    if written != expected:
        raise SystemExit(
            f"expected {expected} records, wrote {written} — config/pipeline drift"
        )

    manifest: dict[str, Any] = {
        "dataset": "Tachyone-SLM-Mixture-v1",
        "config": str(config_path.relative_to(WORKSPACE)),
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "seed": config.seed,
        "per_type": config.per_type,
        "languages": list(config.languages),
        "domains": list(config.domains),
        "noise_rate": config.noise_rate,
        "records": written,
        "by_primitive": dict(sorted(kinds.items())),
        "by_language": dict(sorted(langs.items())),
        "per_cell_language_x_domain": per_cell(out_path),
        "mixture_sha256": digest,
        "generator": "training/generate_data.py (upstream pipeline, unmodified)",
    }
    manifest_path = WORKSPACE / "artifacts" / "slm-mixture-v1" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in ("records", "mixture_sha256", "by_primitive", "by_language")
            },
            indent=2,
        )
    )
    print(f"wrote {out_path} and {manifest_path}")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="generate-mixture", description=__doc__)
    parser.add_argument(
        "--config", default=str(WORKSPACE / "training/configs/data_sft_slm.json")
    )
    parser.add_argument(
        "--out",
        default=str(WORKSPACE / "data/tachyone_slm_mixture_v1.raw.jsonl"),
        help="RAW output — contamination dedup happens in slm_pipeline.prepare_sft",
    )
    args = parser.parse_args(argv)
    run(Path(args.config), Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
