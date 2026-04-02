"""
Graders for Bug Triage tasks.

Owner: Inderpal
Status: STUB (to be implemented)

Grader functions must return float scores in [0.0, 1.0]
"""

from src.models import BugTriageAction, BugGroundTruth


def grade_criticality(action: BugTriageAction, ground_truth: BugGroundTruth) -> float:
    """Grade Task 1: Criticality Detection.

    Returns:
        1.0 if action.criticality matches ground_truth.criticality
        0.0 otherwise
    """
    raise NotImplementedError("Implement in Day 2")


def grade_severity(action: BugTriageAction, ground_truth: BugGroundTruth) -> float:
    """Grade Task 2: Severity Scoring.

    Returns:
        1.0 if exact match
        0.7 if off by 1
        0.4 if off by 2
        0.0 if off by 3+
    """
    raise NotImplementedError("Implement in Day 2")


def grade_root_cause_assignee(
    action: BugTriageAction,
    ground_truth: BugGroundTruth,
    contributor_teams: dict = None
) -> float:
    """Grade Task 3: Root Cause + Assignee.

    Formula: (0.6 * root_cause_score) + (0.4 * assignee_score)

    Returns:
        Combined weighted score in [0.0, 1.0]
    """
    raise NotImplementedError("Implement in Day 2")
