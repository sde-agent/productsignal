# Product brief and phase boundary

## User and decision
A PM needs to notice distinct customer problems buried in individual support cases and decide whether to begin investigating.

## Outcome hypothesis
Evidence-backed recognition can shorten the interval from first customer report to investigation. Time to fix is a broader outcome affected by diagnosis, engineering capacity, and resolution work; ProductSignal does not control all of it.

## Milestone 1 question
Can messy cases yield useful behavior groups without predetermined labels entering discovery? Establish coverage, mixing, fragmentation, small-issue preservation, and inspectable evidence. Stop when the experiment and limitations are reproducible and documented, rather than require every failure to disappear.

## Ownership
PM owns the outcome, error priorities, operational burden, severity policy, and pilot acceptance decisions. ML/DS owns diagnosing failures, selecting bounded experiments, technical implementation, and reporting achievable tradeoffs. Thresholds for deployment remain unset; exploratory configuration choices are not acceptance thresholds.

## Draft requirements informed by evidence
A surfaced candidate must preserve supporting IDs and specific customer-observed symptoms. Do not collapse materially different failures into one confident explanation. Report found evidence counts without implying exhaustive incident counts. How-to requests can be usability topics; they are not automatically defects. Potential severity needs evidence-backed reasoning and unknowns, and remains advisory until validated.

## Non-goals here
Emergence detection, ranking, notification automation, root-cause determination, production PII guarantees, tenant isolation, vector databases, and model training/fine-tuning. Ordinary email masking is a limited demonstration, not full de-identification.
