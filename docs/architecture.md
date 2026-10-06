# Milestone 1 architecture

Synthetic raw cases → whitespace/email preprocessing → prefixed Ollama/nomic embeddings → L2 normalization → HDBSCAN → assignments and hierarchy → separate golden-label evaluation → raw-evidence review cards.

The configurable runner replaces source-rewriting wrappers. Config sets dataset/output paths, Ollama endpoint/model, batch size, and a list of clustering settings. `generate`, `embed`, `run`, and `cards` are explicit separate stages.

Discovery reads IDs and embeddings. Only after all configured clustering fits finish does evaluation read golden labels. Cards read raw-derived evidence and assignments, not golden data or evaluation cases.

Embedding manifests record raw hash, input hashes, model digest, prefix, dimensions, completion status, vector hash, and (for newly generated runs) case-trace hash. Batch traces survive failures; automatic batch resume is not implemented. The latest pointer changes only on success. Historical embeddings predate case-trace hashing; their raw-derived traces are checked against the raw cases during packaged-run validation.

Runs save parameters, library versions, memberships, outlier scores, hierarchy, persistence, full evaluation joins, per-behavior metrics, confusion pairs, and summaries. Membership is not probability of a defect; outlier score is not severity. These diagnose the geometric grouping, not a technical root cause.

There is no automatic synthesis or severity in the packaged pipeline. Review cards use central and weaker-fitting examples and retain every assigned case ID. Evidence samples can miss contradictions: a reviewer can inspect the complete assignments/raw cases. Cluster numbers have no meaning across runs.
