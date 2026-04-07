"""
Graders for Bug Triage tasks.

Each grader function takes an agent's action and the ground truth,
then returns a float score in [0.0, 1.0].

Scoring philosophy:
  - Exact match = 1.0
  - Partial credit for "close" answers (off-by-one severity, related root cause, same team)
  - Complete miss = 0.0

Owner: Team Dhurandhar
"""

import logging
from src.models import BugTriageAction, BugGroundTruth, RootCauseCategory

logger = logging.getLogger(__name__)

__all__ = ["grade_criticality", "grade_severity", "grade_root_cause_assignee"]

# Related categories for partial credit (0.5 instead of 0.0)
RELATED_CATEGORIES = {
    RootCauseCategory.BUG: [RootCauseCategory.DESIGN],
    RootCauseCategory.DESIGN: [RootCauseCategory.BUG, RootCauseCategory.PERFORMANCE],
    RootCauseCategory.ENVIRONMENT: [RootCauseCategory.EXTERNAL],
    RootCauseCategory.PERFORMANCE: [RootCauseCategory.BUG, RootCauseCategory.DESIGN],
    RootCauseCategory.DOCUMENTATION: [],
    RootCauseCategory.EXTERNAL: [RootCauseCategory.ENVIRONMENT],
}


def grade_criticality(action: BugTriageAction, ground_truth: BugGroundTruth) -> float:
    """Binary classification grader for criticality detection.

    Args:
        action: Agent's action containing criticality prediction.
        ground_truth: The true criticality label.

    Returns:
        1.0 if match, 0.0 otherwise.
    """
    if action.criticality is None:
        return 0.0
    return 1.0 if action.criticality == ground_truth.criticality else 0.0


def grade_severity(action: BugTriageAction, ground_truth: BugGroundTruth) -> float:
    """5-point scale grader with partial credit for near-misses.

    Scoring:
        Exact match:  1.0
        Off by 1:     0.7
        Off by 2:     0.4
        Off by 3+:    0.0

    Args:
        action: Agent's action containing severity prediction.
        ground_truth: The true severity level.

    Returns:
        Float score in [0.0, 1.0].
    """
    if action.severity is None:
        return 0.0
    diff = abs(action.severity.value - ground_truth.severity.value)
    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.7
    elif diff == 2:
        return 0.4
    else:
        return 0.0


def grade_root_cause_assignee(
    action: BugTriageAction,
    ground_truth: BugGroundTruth,
    contributor_teams: dict = None
) -> float:
    """Weighted multi-criterion grader for root cause + assignee.

    Formula: (0.6 × root_cause_score) + (0.4 × assignee_score)

    Root cause scoring:
        Exact match:      1.0
        Related category:  0.5
        Wrong:             0.0

    Assignee scoring:
        Exact match:      1.0
        Same team:        0.6
        Wrong:            0.0

    Args:
        action: Agent's action with root_cause and assignee predictions.
        ground_truth: The true root cause and assignee.
        contributor_teams: Optional dict mapping contributor name to team.

    Returns:
        Float score in [0.0, 1.0].
    """
    # Root cause score
    if action.root_cause is None:
        root_cause_score = 0.0
    elif action.root_cause == ground_truth.root_cause:
        root_cause_score = 1.0
    elif action.root_cause in RELATED_CATEGORIES.get(ground_truth.root_cause, []):
        root_cause_score = 0.5
    else:
        root_cause_score = 0.0

    # Assignee score
    if action.assignee is None or not action.assignee.strip():
        assignee_score = 0.0
    elif action.assignee.lower() == ground_truth.assignee.lower():
        assignee_score = 1.0
    elif contributor_teams and _same_team(action.assignee, ground_truth.assignee, contributor_teams):
        assignee_score = 0.6
    else:
        assignee_score = 0.0

    return (0.6 * root_cause_score) + (0.4 * assignee_score)


def _same_team(predicted: str, actual: str, contributor_teams: dict) -> bool:
    """Check if two contributors belong to the same team.

    Args:
        predicted: The agent's predicted assignee name.
        actual: The ground-truth assignee name.
        contributor_teams: Dict mapping lowercase contributor name to team string.

    Returns:
        True if both are on the same team, False otherwise.
    """
    predicted_team = contributor_teams.get(predicted.lower())
    actual_team = contributor_teams.get(actual.lower())
    if predicted_team and actual_team:
        return predicted_team == actual_team
    return False
