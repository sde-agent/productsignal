import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import requests


ROOT = Path("data/milestone1")
MODEL = "nomic-embed-text:latest"
HOST = "http://localhost:11434"
PREFIX = "search_document: "
BATCH_SIZE = 32


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def preprocess(text):
    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[EMAIL]",
        text,
    )
    return re.sub(r"\s+", " ", text).strip()


def main():
    raw_path = ROOT / "raw/support_cases.jsonl"
    raw_bytes = raw_path.read_bytes()
    cases = [
        json.loads(line)
        for line in raw_bytes.decode("utf-8").splitlines()
        if line.strip()
    ]

    ids = [case["case_id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case IDs.")
    if not all(
        set(case) == {"case_id", "created_at", "text"}
        for case in cases
    ):
        raise ValueError("Unexpected raw fields; check for label leakage.")

    processed = []
    for case in cases:
        text = preprocess(case["text"])
        if not text:
            raise ValueError(f"Empty text: {case['case_id']}")
        processed.append({
            "case_id": case["case_id"],
            "created_at": case["created_at"],
            "original_text": case["text"],
            "sanitized_text": text,
            "embedding_input_sha256": sha256(
                (PREFIX + text).encode("utf-8")
            ),
        })

    # Record the installed model identity before embedding.
    response = requests.get(f"{HOST}/api/tags", timeout=30)
    response.raise_for_status()
    model = next(
        (
            item
            for item in response.json()["models"]
            if item.get("name") == MODEL
            or item.get("model") == MODEL
        ),
        None,
    )
    if model is None:
        raise RuntimeError(f"{MODEL} is not available in Ollama.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "processed" / f"embedding_{timestamp}"
    output.mkdir(parents=True, exist_ok=False)

    manifest = {
        "status": "started",
        "model": MODEL,
        "model_digest": model["digest"],
        "raw_sha256": sha256(raw_bytes),
        "case_count": len(cases),
        "prefix": PREFIX,
        "preprocessing_version": "1",
        "preprocessing": ["mask emails", "normalize whitespace"],
        "batch_size": BATCH_SIZE,
        "created_at_utc": timestamp,
    }
    manifest_path = output / "manifest.json"

    def save_manifest():
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )

    save_manifest()

    with (output / "cases.jsonl").open("w", encoding="utf-8") as handle:
        for case in processed:
            handle.write(json.dumps(case, ensure_ascii=False) + "\n")

    batches = []
    try:
        for start in range(0, len(processed), BATCH_SIZE):
            batch = processed[start:start + BATCH_SIZE]
            response = requests.post(
                f"{HOST}/api/embed",
                json={
                    "model": MODEL,
                    "input": [
                        PREFIX + case["sanitized_text"]
                        for case in batch
                    ],
                    "truncate": False,
                },
                timeout=180,
            )
            response.raise_for_status()
            vectors = np.asarray(
                response.json()["embeddings"],
                dtype=np.float64,
            )

            if vectors.ndim != 2 or len(vectors) != len(batch):
                raise ValueError("Unexpected embedding response shape.")
            if not np.isfinite(vectors).all():
                raise ValueError("Embeddings contain non-finite values.")
            if batches and vectors.shape[1] != batches[0].shape[1]:
                raise ValueError("Embedding dimensions changed between batches.")

            # Preserve completed batches if a later request fails.
            np.save(output / f"batch_{start:04d}.npy", vectors)
            batches.append(vectors)
            print(f"Embedded {start + len(batch)}/{len(processed)}")

        embeddings = np.vstack(batches)
        norms = np.linalg.norm(embeddings, axis=1)
        if np.any(norms == 0):
            raise ValueError("Found a zero-length embedding.")

        # Explicit normalization makes vector-distance comparisons consistent.
        embeddings = embeddings / norms[:, None]
        vector_path = output / "embeddings.npy"
        np.save(vector_path, embeddings)

        manifest.update({
            "status": "complete",
            "dimensions": embeddings.shape[1],
            "l2_normalized": True,
            "embeddings_sha256": sha256(vector_path.read_bytes()),
        })
        save_manifest()

        # Update this pointer only after successful completion.
        (ROOT / "processed/latest_embedding.json").write_text(
            json.dumps({"path": str(output)}, indent=2) + "\n",
            encoding="utf-8",
        )

        print(f"\nSaved complete embedding run: {output}")
        print(f"Embedding matrix: {embeddings.shape}")
        print("Golden labels were not read.")

    except Exception as error:
        manifest.update({
            "status": "failed",
            "error": str(error),
            "completed_cases": sum(len(batch) for batch in batches),
        })
        save_manifest()
        raise


if __name__ == "__main__":
    main()
