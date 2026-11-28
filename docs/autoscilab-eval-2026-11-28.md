# `autoscilab` Benchmark Validation Log (2026-11-28)

Compact provenance record for evaluating `skills/autoscilab` (`v2.0.0`) against external black-box benchmarks without storing benchmark source code, task adapters, or recovered mechanisms in tracked Git history.

## 1. Architecture & Contamination Controls

- **Reusable skill (`skills/autoscilab/`, tracked):** Domain-free closed-loop discovery engine (`autoscilab_engine.py`, `model_fitting.py`, `experiment_design.py`), `autoscilab-env/1` specification (`references/environment-spec.md`), agent-authored hypothesis module protocol (`references/model-modules.md`), and offline toy unit tests (`tests/`). Contains zero benchmark-specific equations, motifs, constants, or representation backends.
- **Task environment & raw runs (`evals/autoscilab/`, git-ignored):** External `autoscilab-env/1` oracle adapter, shuffled task registry (`seed = 20261127`, `registry_sha256 = 24aa99646f701131ffbcf77bfd9f1dd5aebb196c2eeca83b71758524b179802f`), append-only query ledgers, and per-task workspaces are stored locally under git-ignored `evals/autoscilab/` so future agents in this repository cannot read prior benchmark trajectories.
- **Upstream benchmark source:** `https://github.com/scientific-discovery/LLM-AutoSciLab` at commit `467fa184ba537d26b2228ee3f3a8c052d9bfca58` (*LLM-AutoSciLab: Closed-Loop Scientific Discovery via Active Experimentation with LLMs*, `arXiv:2605.24043`), evaluated with `grammar_mode="none"` and `noise_level=0.0` under standard budgets ($B = 60$ on `ActiveSciBench-Chem`, $B = 20$ on `ActiveSciBench-GRN`).

## 2. Frozen Skill Manifest (`v2.0.0`)

All 16 files in `skills/autoscilab/` were SHA-256 frozen prior to evaluation and verified unchanged post-run:

| File | SHA-256 |
| :--- | :--- |
| `SKILL.md` | `b108a2388a5cdef8af11177319a1f5ca8a7ddcc660e3a06f1c21473f5bc0bdee` |
| `agents/openai.yaml` | `4dd53668970bbf481d522e49d0bf5b47f302197c86e56070c6fa894082709e78` |
| `contract.json` | `7b8556e25f41ff52d77e44ef227a792d260b61285b5077dbc09aaeb88e7c6134` |
| `references/cli-reference.md` | `b92389284dda32ebb08972d32d1703c50609182f64d72aeb1ec0459c736479f2` |
| `references/environment-spec.md` | `0efcd0373b22bf75c4954e4e3b6aad6aaac739212a7c360f1eb3836202639bb4` |
| `references/model-modules.md` | `d56ed7f49f0d8a272f92554cdefeb0b442e5160fa8792419dc6d3f2ad4edcb07` |
| `scripts/autoscilab_engine.py` | `7fee98c97fe79d3cc81a247d61dabf02cc93ad460c20420c0de97998033d2ce0` |
| `scripts/experiment_design.py` | `87c38b963c02e5e5e8ff2d52d302103e671c87426886de454329ce2ee9a2fae2` |
| `scripts/model_fitting.py` | `dc4698f5406c73fb7e731b4da3532a893a9b43a7a8f8f0e2921a2cba7127915e` |
| `tests/test_autoscilab_engine.py` | `87995793ea6c9c3df75e556ea1a91d78ebff9fd9cc630007a0053557dc272f40` |

## 3. Untouched Benchmark Results Summary

Evaluated strictly on untouched stratified tasks (`0` prior oracle queries; `100%` server-side ledger match; `100%` protocol `audit.passed`; `0` out-of-bounds transcript accesses):

| Benchmark | Configuration | Exact Recovery | Secondary Metrics | Audit & Ledger |
| :--- | :--- | :---: | :---: | :---: |
| **`ActiveSciBench-Chem`** ($B=60$) | **`autoscilab` v2.0.0 split (`n=3`: 1E/1M/1H)** | **`100.0%`** (`RMSLE < 0.05`) | `100.0%` Full-Sim SA*, `0.0%` Primary SA*, `0.017` RMSLE | `3/3` PASS |
| | Pre-split clean skill (`n=14`: 2E/7M/5H) | `100.0%` (`RMSLE < 0.05`) | `92.9%` Full-Sim SA*, `0.0%` Primary SA*, `0.013` RMSLE | `14/14` PASS |
| | Paper `LLM-AutoSciLab` (GPT-4o-mini, `n=57`) | `50.9%` | `35.1%` Primary SA, `0.189` RMSLE | — |
| | Paper `LLM-AutoSciLab` (Qwen3-32B, `n=57`) | `52.8%` | `25.6%` Primary SA, `0.082` RMSLE | — |
| **`ActiveSciBench-GRN`** ($B=20$) | **`autoscilab` v2.0.0 split (`n=3`: 1E/1M/1H)** | **`100.0%` Exact Graph** | `100.0%` Edge F1, `100.0%` Sign Acc. | `3/3` PASS |
| | Pre-split clean skill (`n=6`: 2E/2M/2H) | `100.0%` Exact Graph | `100.0%` Edge F1, `100.0%` Sign Acc. | `6/6` PASS |
| | Paper `LLM-AutoSciLab` (GPT-4o-mini, `n=45`) | `31.1%` Exact Graph | `72.5%` Edge F1, `98.2%` Sign Acc. | — |
| | Paper `LLM-AutoSciLab` (Qwen3-32B, `n=45`) | `25.9%` Exact Graph | `62.7%` Edge F1, `98.7%` Sign Acc. | — |

*\*Evaluator note (`ActiveSciBench-Chem` Symbolic Accuracy):* `ChemBenchOracle.run()` multiplies noiseless measurements by a ±5% background temperature/pH factor (`_secondary_effects`), whereas `evaluate_law`'s primary ground-truth formula omits that factor. With zero scorer-aware stripping heuristics, agents recover the exact full simulator equation (`100.0%` Full-Sim SA on `v2.0.0`, `92.9%` on `v1.0.0`, judged with the verbatim upstream `SYMBOLIC_EQUIVALENCE_JUDGE_PROMPT`), producing `0.0%` against the primary-only string and `100.0%` `Exact` (`RMSLE < 0.05`).

## 4. Offline Verification Commands

```bash
python3 -B -m unittest discover -s skills/autoscilab/tests -v
python3 -B skills/skill-contract/scripts/check_contracts.py skills
pytest tests/test_link_skills.py
```
