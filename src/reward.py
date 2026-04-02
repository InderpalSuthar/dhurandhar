"""
Reward calculator for Bug Triage environment.

Owner: Inderpal
Status: STUB (to be implemented)

Combines base grader score with bonuses:
- Confidence calibration
- Reasoning quality
- Edge case handling
"""

from src.models import BugTriageAction, BugGroundTruth, BugTriageReward


class RewardCalculator:
    """Computes sophisticated rewards beyond raw grader scores."""

    def compute(
        self,
        base_score: float,
        action: BugTriageAction,
        ground_truth: BugGroundTruth
    ) -> BugTriageReward:
        """Compute reward with all bonuses.

        Args:
            base_score: Raw grader score (0.0-1.0)
            action: Agent's action
            ground_truth: Ground truth labels

        Returns:
            BugTriageReward with total clamped to [0.0, 1.0]
        """
        raise NotImplementedError("Implement in Day 2")
