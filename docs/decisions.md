# Decisions and unresolved work

1. Prioritize retention of meaningful emerging behaviors, then distinctness, then reduced fragmentation. No automatic signal/alert threshold was chosen.
2. Preserve the completed 500-case prototype as historical context. New raw cases physically exclude golden fields. Original prototype used different data and embedding preparation: comparisons across datasets do not isolate a clustering change.
3. Keep how-to topics discoverable as possible usability friction. Topic coherence alone does not establish a defect.
4. Candidate: EOM size 5, samples 2. Comparison baseline: EOM size 10, samples 5. Candidate gains clean small-issue groups but adds fragments, assigned ambiguity, and losses in other behaviors. Additional review burden is hypothesized from group counts, not timed or measured.
5. Stop severity prompt iteration for this milestone. V1 High includes reported financial harm or unresolved purchase/account block; Medium includes identified functional failures, including successful recovery; Low includes cosmetic friction/preference requests; Unknown means insufficient impact context. Qwen suggestions remain advisory. A hybrid fact-extraction/deterministic-policy approach was proposed but is not implemented.
6. Conclude Milestone 1 as feasibility evidence with limitations, not a production acceptance decision. Model weights were not fine-tuned.

## Next milestone
Acquire permissioned incident-labeled real data. Record report timestamps, incident identity, recognition, investigation, and resolution times. Replay chronologically without future evidence; assess detection delay, meaningful misses, distinctness, false candidates, and reviewer usefulness. Keep reduced MTTR as a broader hypothesis, not a demonstrated outcome. Decide pilot acceptance thresholds after this evidence.
