import hashlib
import importlib.metadata
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import hdbscan
import numpy as np
import pandas as pd


ROOT = Path("data/milestone1")


def read_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(root="data/milestone1", settings_list=None, output_root="experiments"):
    ROOT = Path(root)
    if settings_list is None:
        settings_list = [{"min_cluster_size": 10, "min_samples": settings["min_samples"],
            "cluster_selection_method": settings["cluster_selection_method"], "metric": "euclidean", "cluster_selection_method": "eom"}]
    pointer = json.loads(
        (ROOT / "processed/latest_embedding.json").read_text()
    )
    embedding_dir = Path(pointer["path"])
    if not embedding_dir.is_absolute():
        embedding_dir = ROOT.resolve().parent.parent / embedding_dir
    manifest = json.loads(
        (embedding_dir / "manifest.json").read_text()
    )

    if manifest["status"] != "complete":
        raise ValueError("Embedding run is incomplete.")
    if sha256(ROOT / "raw/support_cases.jsonl") != manifest["raw_sha256"]:
        raise ValueError("Raw cases changed since embedding.")
    if sha256(embedding_dir / "embeddings.npy") != manifest["embeddings_sha256"]:
        raise ValueError("Embedding file changed.")

    if manifest.get("cases_sha256") and sha256(embedding_dir / "cases.jsonl") != manifest["cases_sha256"]:
        raise ValueError("Case trace changed since embedding.")
    cases = pd.DataFrame(read_jsonl(embedding_dir / "cases.jsonl"))
    vectors = np.load(embedding_dir / "embeddings.npy")

    if len(cases) != len(vectors) or not cases["case_id"].is_unique:
        raise ValueError("Invalid case-to-vector alignment.")

    raw = read_jsonl(ROOT / "raw/support_cases.jsonl")
    if len(raw) != len(cases) or any(
        c["case_id"] != r["case_id"] or c["original_text"] != r["text"]
        for c, r in zip(cases.to_dict("records"), raw)
    ):
        raise ValueError("Case trace does not match raw case order/text.")
    if not np.isfinite(vectors).all() or vectors.ndim != 2:
        raise ValueError("Invalid embeddings.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    experiment = Path(output_root) / f"milestone1_{timestamp}"
    experiment.mkdir(parents=True, exist_ok=False)

    # Discovery uses only embeddings and case IDs.
    discovered = []
    for settings in settings_list:
        size = settings["min_cluster_size"]
        samples = settings["min_samples"]
        selection = settings["cluster_selection_method"]
        clusterer = hdbscan.HDBSCAN(**settings).fit(vectors)

        run_dir = experiment / f"size_{size}_samples_{samples}_{selection}"
        run_dir.mkdir()

        assignments = pd.DataFrame({
            "case_id": cases["case_id"],
            "cluster": clusterer.labels_,
            "membership_strength": clusterer.probabilities_,
            "outlier_score": clusterer.outlier_scores_,
        })
        assignments.to_csv(run_dir / "assignments.csv", index=False)
        clusterer.condensed_tree_.to_pandas().to_csv(
            run_dir / "condensed_tree.csv", index=False
        )
        np.save(
            run_dir / "cluster_persistence.npy",
            clusterer.cluster_persistence_,
        )

        provenance = {
            "settings": settings,
            "embedding_run": str(embedding_dir),
            "embedding_manifest": manifest,
            "versions": {
                package: importlib.metadata.version(package)
                for package in ["hdbscan", "numpy", "pandas", "scikit-learn"]
            },
            "trace_notes": [
                "membership_strength is not probability of a real defect",
                "outlier_score is a density-based score, not issue severity",
            ],
        }
        (run_dir / "provenance.json").write_text(
            json.dumps(provenance, indent=2) + "\n"
        )
        discovered.append((settings, run_dir, assignments))

    # Golden labels enter only after both clustering runs finish.
    golden_path = ROOT / "golden/labels.jsonl"
    golden = pd.DataFrame(read_jsonl(golden_path))
    dataset_manifest = json.loads(
        (ROOT / "golden/manifest.json").read_text()
    )

    if not golden["case_id"].is_unique:
        raise ValueError("Duplicate golden IDs.")
    if set(golden["case_id"]) != set(cases["case_id"]):
        raise ValueError("Golden IDs do not match embedded cases.")

    summaries = []

    for settings, run_dir, assignments in discovered:
        size = settings["min_cluster_size"]
        result = (
            cases.merge(assignments, on="case_id", validate="one_to_one")
            .merge(golden, on="case_id", validate="one_to_one")
        )
        result.to_json(
            run_dir / "evaluation_cases.jsonl",
            orient="records",
            lines=True,
            force_ascii=False,
        )

        assigned = result["cluster"] != -1
        failures = result["evidence_type"] == "reported_failure"
        topics = result["evidence_type"].isin(
            ["reported_failure", "how_to", "feature_request", "intended_behavior"]
        )

        composition = pd.crosstab(
            result.loc[assigned, "cluster"],
            result.loc[assigned, "behavior"],
        )
        composition.to_csv(run_dir / "composition.csv")

        failure_composition = pd.crosstab(
            result.loc[assigned & failures, "cluster"],
            result.loc[assigned & failures, "behavior"],
        )

        # Purity across ALL cases can reward ambiguous-only clusters.
        all_purity = (
            float(composition.max(axis=1).sum() / assigned.sum())
            if assigned.any() else None
        )
        retained_failures = int((assigned & failures).sum())
        failure_purity = (
            float(failure_composition.max(axis=1).sum() / retained_failures)
            if retained_failures else None
        )
        mixed_failure_clusters = (
            int((failure_composition.gt(0).sum(axis=1) > 1).sum())
            if not failure_composition.empty else 0
        )

        behavior_rows = []
        for behavior, group in result.groupby("behavior"):
            retained = group[group["cluster"] != -1]
            counts = retained["cluster"].value_counts()
            behavior_rows.append({
                "behavior": behavior,
                "evidence_type": group["evidence_type"].iloc[0],
                "total": len(group),
                "retained": len(retained),
                "coverage": len(retained) / len(group),
                "fragments": len(counts),
                "largest_fragment_share_of_total": (
                    int(counts.max()) / len(group) if len(counts) else 0.0
                ),
            })
        from .metrics import clean_behavior_metrics
        clean = clean_behavior_metrics(result)
        for row in behavior_rows:
            row.update(clean[row["behavior"]])
        behaviors = pd.DataFrame(behavior_rows)
        behaviors.to_csv(run_dir / "behavior_metrics.csv", index=False)

        pair_rows = []
        for behavior_a, behavior_b in dataset_manifest["confusion_pairs"]:
            a = result[result["behavior"] == behavior_a]
            b = result[result["behavior"] == behavior_b]
            counts_a = Counter(a.loc[a["cluster"] != -1, "cluster"])
            counts_b = Counter(b.loc[b["cluster"] != -1, "cluster"])
            shared = sorted(set(counts_a) & set(counts_b))
            coassigned_pairs = sum(
                counts_a[cluster] * counts_b[cluster]
                for cluster in shared
            )
            pair_rows.append({
                "behavior_a": behavior_a,
                "behavior_b": behavior_b,
                "shared_clusters": shared,
                "cross_behavior_pair_merge_rate": (
                    coassigned_pairs / (len(a) * len(b))
                ),
                "a_cases_in_shared_clusters": sum(
                    counts_a[cluster] for cluster in shared
                ),
                "b_cases_in_shared_clusters": sum(
                    counts_b[cluster] for cluster in shared
                ),
            })
        (run_dir / "confusion_pairs.json").write_text(
            json.dumps(pair_rows, indent=2) + "\n"
        )

        assigned_by_type = {
            kind: {
                "assigned": int((group["cluster"] != -1).sum()),
                "total": len(group),
            }
            for kind, group in result.groupby("evidence_type")
        }

        metrics = {
            "min_cluster_size": size,
            "min_samples": settings["min_samples"],
            "cluster_selection_method": settings["cluster_selection_method"],
            "clusters": len(composition),
            "overall_coverage": float(assigned.mean()),
            "reported_failure_coverage": float(assigned[failures].mean()),
            "known_topic_coverage": float(assigned[topics].mean()),
            "all_assigned_purity": all_purity,
            "failure_only_purity": failure_purity,
            "clusters_mixing_failure_behaviors": mixed_failure_clusters,
            "assigned_by_evidence_type": assigned_by_type,
            "golden_sha256": sha256(golden_path),
        }
        (run_dir / "metrics.json").write_text(
            json.dumps(metrics, indent=2) + "\n"
        )
        summaries.append(metrics)

        print(f"\n=== {settings} ===")
        print(f"Clusters: {metrics['clusters']}")
        print(f"Reported-failure coverage: {metrics['reported_failure_coverage']:.1%}")
        print(f"Known-topic coverage: {metrics['known_topic_coverage']:.1%}")
        if failure_purity is not None:
            print(f"Failure-only purity: {failure_purity:.1%}")
        else:
            print("Failure-only purity: undefined")
        print(f"Clusters mixing failure behaviors: {mixed_failure_clusters}")

        print("\nPER-BEHAVIOR RESULTS")
        print(behaviors.to_string(index=False))

        print("\nIMPORTANT CONFUSION PAIRS")
        for pair in pair_rows:
            print(
                f"{pair['behavior_a']} <-> {pair['behavior_b']}: "
                f"shared clusters={pair['shared_clusters']}; "
                f"pair merge rate={pair['cross_behavior_pair_merge_rate']:.1%}"
            )

        print("\nASSIGNMENT BY EVIDENCE TYPE")
        for kind, counts in assigned_by_type.items():
            print(f"{kind}: {counts['assigned']}/{counts['total']}")

    (experiment / "summary.json").write_text(
        json.dumps(summaries, indent=2) + "\n"
    )
    print(f"\nAll results and traces saved to: {experiment}")


if __name__ == "__main__":
    main()
