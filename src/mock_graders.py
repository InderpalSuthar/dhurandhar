"""
Mock graders for development and testing.

Owner: Sumit
Status: Day 1 (for use during Days 2-3)

These mocks return predictable scores so env.py can be tested without Inderpal's real graders.
Delete this file after Day 3 integration.
"""

from src.models import BugTriageAction, BugGroundTruth


def mock_grade_criticality(action: BugTriageAction, ground_truth: BugGroundTruth) -> float:
    """Mock criticality grader - returns 0.5 for everything.

    In production: 1.0 if correct, 0.0 if wrong
    """
    if action.criticality is None:
        return 0.0
    return 1.0 if action.criticality == ground_truth.criticality else 0.0


def mock_grade_severity(action: BugTriageAction, ground_truth: BugGroundTruth) -> float:
    """Mock severity grader - returns 0.5 for everything.

    In production: 1.0 exact, 0.7 off-by-one, 0.4 off-by-two, 0.0 else
    """
    if action.severity is None:
        return 0.0
    diff = abs(action.severity.value - ground_truth.severity.value)
    return {0: 1.0, 1: 0.7, 2: 0.4}.get(diff, 0.0)


def mock_grade_root_cause_assignee(
    action: BugTriageAction,
    ground_truth: BugGroundTruth,
    contributor_teams: dict = None
) -> float:
    """Mock root cause + assignee grader - returns 0.5 for everything.

    In production: (0.6 * root_cause_score) + (0.4 * assignee_score)
    """
    root_cause_score = 1.0 if action.root_cause == ground_truth.root_cause else 0.5
    assignee_score = 1.0 if action.assignee and action.assignee.lower() == ground_truth.assignee.lower() else 0.6
    return (0.6 * root_cause_score) + (0.4 * assignee_score)
