"""
Reward calculator for Bug Triage environment.

Owner: Inderpal

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
        """Reward = base_score + confidence_bonus + reasoning_bonus + edge_case_bonus
        Clamped to [0.0, 1.0]
        """
        # 1. Confidence calibration bonus
        confidence_diff = abs(action.confidence - base_score)
        if confidence_diff < 0.15:
            confidence_bonus = 0.08
        elif confidence_diff < 0.3:
            confidence_bonus = 0.02
        else:
            confidence_bonus = -0.05

        # 2. Reasoning quality bonus
        reasoning_len = len(action.reasoning.strip())
        if reasoning_len > 50 and base_score > 0.7:
            reasoning_bonus = 0.05
        elif reasoning_len > 100 and base_score < 0.5:
            reasoning_bonus = 0.02
        else:
            reasoning_bonus = 0.0

        # 3. Edge case bonus
        if ground_truth.is_ambiguous and base_score == 1.0:
            edge_case_bonus = 0.1
        else:
            edge_case_bonus = 0.0

        # Combine and clamp
        total = base_score + confidence_bonus + reasoning_bonus + edge_case_bonus
        total = max(0.0, min(1.0, total))

        return BugTriageReward(
            base_score=base_score,
            confidence_bonus=confidence_bonus,
            reasoning_bonus=reasoning_bonus,
            edge_case_bonus=edge_case_bonus,
            total=total,
        )
