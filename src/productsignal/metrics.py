"""Evaluation helpers; golden behavior labels never enter discovery."""

def clean_behavior_metrics(frame):
    """Strict clean coverage: all cases in a cluster share the behavior.

    This is a diagnostic, not an incident-detection success threshold. Even a
    pure group can consist of duplicates, and ambiguous is not an issue label.
    """
    assigned = frame[frame['cluster'] != -1]
    distinct = assigned.groupby('cluster')['behavior'].nunique()
    clean_ids = set(distinct[distinct == 1].index)
    answer = {}
    for behavior, group in frame.groupby('behavior'):
        clean = group[group['cluster'].isin(clean_ids)]
        mixed = group[(group['cluster'] != -1) & ~group['cluster'].isin(clean_ids)]
        answer[behavior] = {
            'clean_cases': len(clean),
            'clean_case_coverage': len(clean) / len(group),
            'clean_fragments': clean['cluster'].nunique(),
            'cases_in_mixed_clusters': len(mixed),
            'noise_cases': int((group['cluster'] == -1).sum()),
        }
    return answer
