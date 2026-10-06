# Packaging validation

Validated on October 6, 2026, using the original Mac Studio's existing Python environment and saved 1,000-case embedding run. No new Ollama calls or parameter search were performed during packaging.

- Three invariant tests passed: deterministic generation and isolated golden fields, clean coverage excluding mixed/noise cases, and preprocessing preserving symptom contrasts.
- Configurable runner reproduced the historical size 10/samples 5 and size 5/samples 2 measurements exactly: cluster count, failure coverage, failure-only purity, mixing counts, assignment counts by evidence type, and every case's cluster assignment.
- Derived clean coverage confirmed baseline 0 search/0 promo clean cases; candidate 9 search/15 promo clean cases.
- Review-card stage generated 95 cards from raw-derived evidence and saved assignments.
- Installer preview validated the existing target layout and found no conflicting dataset bytes. The user applied the installer and all three checks passed in the installed repo.

The network embedding stage was refactored from the user's successfully executed script; a fresh Ollama embedding call was not repeated during packaging. New environment installation and external GitHub publication have not been tested/performed. Historical hashes and model/library provenance remain available in results.
