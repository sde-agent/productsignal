# Evaluation contract

- **Overall coverage:** assigned cases / all cases.
- **Reported-failure coverage:** assigned failure cases / all failure cases. Escaping noise is not successful behavior discovery.
- **Known-topic coverage:** assignment across failures, how-to, requests, and intended behavior; excludes ambiguous labels.
- **Assigned purity:** sum of each cluster's largest golden-label count / assigned cases. An ambiguous-only cluster can appear perfectly pure.
- **Failure-only purity:** the same calculation restricted to failure records. It ignores nonfailure contamination and large categories dominate it.
- **Fragmentation:** number of assigned clusters containing a behavior. Also report largest fragment / total behavior cases so misses remain visible.
- **Clean case coverage:** cases assigned to clusters containing only that golden behavior / all cases of the behavior. Strictly excludes any cross-behavior contamination, including nonfailures. Diagnostic only: no minimum evidence threshold or human usefulness judgment is implied. Ambiguous-only groups can be label-pure but not actionable.
- **Confusion-pair merge rate:** coassigned cross-behavior pairs / all possible pairs for the two behaviors. Noise is never treated as a shared cluster. Zero can mean both behaviors were discarded. Pair rates alone do not give the proportion of minority cases absorbed.
- **Small issues:** report search outage (15 cases) and promo freeze (25) individually, including clean, mixed, and rejected counts. Do not replace these with an aggregate accuracy number.

No precision/recall of incident discovery or acceptance rate is established: a discovered-incident matching contract and human review set would be needed. Pair coassignment is an over-merging diagnostic, not incident precision. There is no time-to-detection measurement.

All current examples are development data. Independently worded reserved examples are outstanding. Do not interpret these scores as expected production performance or evidence of an achieved time-to-fix target.
