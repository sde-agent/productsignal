# Results — October 6, 2026

Recorded local development experiments, not independent test performance.

| Size / samples / selection | Groups | Failures retained / 730 | Search retained / 15 | Promo freeze retained / 25 | Failure purity |
|---|---:|---:|---:|---:|---:|
| 10/5/eom | 42 | 669 | 2 | 8 | 98.5% |
| 15/5/eom | 31 | 601 | 2 | 7 | 98.5% |
| 5/2/eom | 95 | 680 | 9 | 21 | 99.1% |
| 5/5/eom | 74 | 680 | 2 | 8 | 98.5% |
| 10/5/eom | 42 | 669 | 2 | 8 | 98.5% |
| 5/5/eom | 74 | 680 | 2 | 8 | 98.5% |
| 5/5/leaf | 78 | 634 | 0 | 8 | 98.7% |

## Candidate evidence inspection

Size 5 / samples 2 / EOM: search cluster 73 contains 9 outage reports and no other labels; six outage cases are noise. Promo clusters 11, 29, and 31 contain five clean cases each. Two promo cases join address cases in cluster 0; four join cart-emptying cases in cluster 32; four are noise. Thus clean promo coverage is 15/25 (60%), not assigned coverage 21/25 (84%).

Compared with size 10 / samples 5, the candidate retains 11 additional failures overall (680 vs 669), but shifts coverage between behaviors and produces 95 groups instead of 42. Relative to size 5 / samples 5, retained failures stay at 680 while small-issue preservation improves. Aggregate scores conceal this redistribution.

## Severity extension

Qwen2.5:14b: v1 4/6, v2 6/6, v3 9/12 human-reference label agreement. All are development/rubric checks. V3 downgrades search outage with browsing, delayed reset while signed in, and checkout failure repaired by refresh from Medium to Low. Correct quotes and valid JSON do not imply policy-faithful reasoning. No held-out severity performance or alert readiness is claimed.

## Conclusion

A local pipeline can expose some distinct small behaviors, with substantial template-driven fragmentation and remaining misses/mixing. Candidate is suitable for further feasibility evaluation, not accepted for deployment. Emergence, review time, unique affected customers, investigation benefit, and time to fix remain unmeasured.

## Recorded sources

- [10/5/eom](../results/milestone1_20261006T152743185113Z/size_10/metrics.json)
- [15/5/eom](../results/milestone1_20261006T152743185113Z/size_15/metrics.json)
- [5/2/eom](../results/milestone1_density_20261006T153720775313Z/size_5_samples_2/metrics.json)
- [5/5/eom](../results/milestone1_density_20261006T153720775313Z/size_5_samples_5/metrics.json)
- [10/5/eom](../results/milestone1_small_issue_20261006T153157708250Z/size_10_eom/metrics.json)
- [5/5/eom](../results/milestone1_small_issue_20261006T153157708250Z/size_5_eom/metrics.json)
- [5/5/leaf](../results/milestone1_small_issue_20261006T153157708250Z/size_5_leaf/metrics.json)
