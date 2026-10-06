# ProductSignal — Milestone 1

An AI PM feasibility study: can a local system discover distinct customer-observed support problems, including small issues, without receiving their golden behavior labels?

**Status:** Milestone 1 experiment complete; packaged runner validated against the saved local embeddings. This is a synthetic-data study, not a production-quality or early-detection claim.

## Product priorities

1. Preserve meaningful small behaviors rather than discard them as noise.
2. Avoid merging materially different failures.
3. Tolerate fragmentation before over-merging.

Repeated how-to topics remain discoverable as possible usability friction. A candidate cluster is not automatically a defect, an incident, or a notification.

## What we learned

The leading candidate is HDBSCAN EOM with `min_cluster_size=5`, `min_samples=2`. On 1,000 synthetic cases, it retains 680/730 reported-failure cases. It discovers one clean search-outage group containing 9/15 outage cases, and three clean promo-freeze groups containing 15/25 cases. Another six promo-freeze cases are mixed with different failures; four are rejected.

Size 10 / samples 5 remains the comparison baseline. See [the results](docs/results.md), [metrics definitions](docs/evaluation.md), and [product decisions](docs/decisions.md).

## Mac setup

Python 3.11+ and Ollama are required. The original experiments used Python 3.14 on a Mac Studio. Run commands from this repository's root.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
ollama pull nomic-embed-text:latest
ollama list
```

Make sure Ollama is running. The default endpoint is local: `http://localhost:11434`. The package does not require an API key or a cloud model.

If integrating into the existing project, reuse its `.venv`. The file `requirements-observed.txt` records the actual five principal library versions used; it is not a full environment lock. New environments may resolve different compatible versions. Every experiment records installed versions.

## Reproduce the study

The revised 1,000-case dataset is included. **Skip generation if using the supplied dataset.** To generate into a new folder, change `dataset_root` in a copy of the config, then run `generate`. Generation refuses to overwrite an existing dataset.

```bash
productsignal --config configs/milestone1.json embed
productsignal --config configs/milestone1.json run
```

`embed` creates versioned traces and vectors. `run` uses the latest completed embedding run and compares the two settings in the config; it does not call Ollama. To create review cards, use the printed experiment directory and its candidate subdirectory:

```bash
productsignal cards --run experiments/EXPERIMENT_DIRECTORY/size_5_samples_2_eom
```

Equivalent command without installation, using existing dependencies:

```bash
PYTHONPATH=src python -m productsignal --config configs/milestone1.json run
```

On the original Mac, the existing `data/milestone1/processed/latest_embedding.json` enables immediate reuse of the completed embeddings. Fresh clones need `embed`. Recorded model digests identify the original artifact; a future `latest` tag may resolve to a different artifact. Clustering labels are run-specific and are not stable issue identities.

## Layout

```text
configs/                 Experiment parameters
src/productsignal/       Configurable generator, embedding, clustering/evaluation, cards
 data/milestone1/raw/     Synthetic cases: IDs, timestamps, text only
 data/milestone1/golden/  Evaluation-only behavior labels and manifest
results/                 Recorded measurements, assignments, evaluation traces
research/original_scripts/  Original chronological learning scripts
 docs/                   Brief, architecture, decisions, results, limitations
 tests/                  Evaluation and data-contract invariants
```

Generated embeddings and exploratory run directories are ignored by Git. Selected historical results are retained in `results/`; original experiments are preserved locally. Provenance paths in historical files reflect the original repo and are not portable execution pointers.

## Verify

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

These checks verify deterministic generation, label isolation, symptom-preserving preprocessing, and clean-coverage arithmetic. They do not establish model quality.

## Boundaries and next milestone

The generator uses repeated templates. Labels were authored alongside generation, not independently adjudicated. There is no reserved clustering test set; settings were selected on these development cases. Duplicate-like phrasing may exaggerate quality. Counts represent reports, not unique customers. Random timestamps cannot establish emergence, detection delay, or reduced time to investigation/fix.

Severity was a separate exploratory extension. Qwen v3 matched 9/12 development judgments and systematically downgraded some functional failures. It remains advisory and human-reviewed; it is not connected to alerts or the discovery runner.

Next: permissioned historical incident data and chronological replay against recognition/investigation baselines, plus independently worded discovery examples. No software license has been selected yet; standard copyright applies until the author chooses one.
