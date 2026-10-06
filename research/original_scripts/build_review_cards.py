import json
from pathlib import Path

import numpy as np
import pandas as pd


RUN = Path(
    "experiments/milestone1_density_20261006T153720775313Z/"
    "size_5_samples_2"
)


def read_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main():
    provenance = json.loads(
        (RUN / "provenance.json").read_text()
    )
    embedding_dir = Path(provenance["embedding_run"])

    # Only raw-derived text, embeddings, and assignments enter the cards.
    cases = pd.DataFrame(
        read_jsonl(embedding_dir / "cases.jsonl")
    )
    cases["vector_row"] = np.arange(len(cases))

    assignments = pd.read_csv(RUN / "assignments.csv")
    vectors = np.load(embedding_dir / "embeddings.npy")

    if len(cases) != len(vectors):
        raise ValueError("Case and embedding counts differ.")
    if set(cases["case_id"]) != set(assignments["case_id"]):
        raise ValueError("Assignment IDs differ from embedded case IDs.")

    df = cases.merge(
        assignments, on="case_id", validate="one_to_one"
    )
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    output = RUN / "review_cards"
    output.mkdir(exist_ok=True)
    cards = []

    for cluster_id, group in df[df["cluster"] != -1].groupby("cluster"):
        positions = group["vector_row"].to_numpy()
        local_vectors = vectors[positions]

        center = local_vectors.mean(axis=0)
        center_norm = np.linalg.norm(center)
        centrality = (
            local_vectors @ (center / center_norm)
            if center_norm > 0
            else np.zeros(len(group))
        )

        ranked = group.assign(centrality=centrality).sort_values(
            "centrality", ascending=False
        )

        # Include central examples and weaker-fitting examples.
        selected = ranked.head(3).copy()
        remaining = group[
            ~group["case_id"].isin(selected["case_id"])
        ].sort_values("membership_strength")
        selected = pd.concat([selected, remaining.head(2)])

        evidence = [
            {
                "case_id": row["case_id"],
                "text": row["sanitized_text"],
                "membership_strength": float(row["membership_strength"]),
            }
            for _, row in selected.iterrows()
        ]

        card = {
            "candidate_id": f"cluster-{int(cluster_id)}",
            "supporting_reports": len(group),
            "all_case_ids": group["case_id"].tolist(),
            "evidence_sample": evidence,
            "status": "unreviewed",
            "limitations": [
                "Grouping does not establish a defect or common root cause.",
                "Report count may omit related cases assigned elsewhere.",
                "Multiple reports may repeat the same synthetic wording.",
                "No emergence, severity, or notification decision has been made.",
            ],
        }
        cards.append(card)

        lines = [
            f"# Candidate group {int(cluster_id)}",
            "",
            f"**Supporting reports in this group:** {len(group)}",
            "",
            "## Evidence sample",
            "",
        ]
        for item in evidence:
            lines.extend([
                f"**{item['case_id']}**",
                "",
                item["text"],
                "",
            ])

        lines.extend([
            "## PM review",
            "",
            "- What customer-observed problem, if any, does this describe?",
            "- Does the evidence describe one behavior or multiple behaviors?",
            "- Is it a reported failure, usability question, request, or unclear?",
            "- Is there enough information to start an investigation?",
            "",
            "## Limitations",
            "",
        ])
        lines.extend(f"- {note}" for note in card["limitations"])

        (output / f"cluster_{int(cluster_id)}.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

    (output / "cards.json").write_text(
        json.dumps(cards, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Created {len(cards)} candidate review cards in:\n{output}")
    print("Golden labels were not read.")

    # These IDs come from our previous diagnostic review.
    # This preview is deliberately selected, not a representative quality sample.
    for cluster_id in [73, 11, 32]:
        path = output / f"cluster_{cluster_id}.md"
        print("\n" + "=" * 60)
        print(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
