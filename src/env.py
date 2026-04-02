"""
Bug Triage RL Environment - Main class.

Owner: Sumit
Status: Day 3 COMPLETE
"""

import json
import random
from typing import Optional, List

from src.models import (
    BugReport,
    BugTriageObservation,
    BugTriageAction,
    BugTriageReward,
    BugGroundTruth,
    CriticalityLabel,
    SeverityLevel,
    RootCauseCategory,
)
from src.tasks import TASK_DEFINITIONS, get_all_task_ids, validate_task_id

# Try real graders; fall back to mocks if not yet implemented
try:
    from src.graders import grade_criticality as _gc, grade_severity as _gs, grade_root_cause_assignee as _grc
    from src.reward import RewardCalculator as _RC
    # Probe: raise if still stubs
    _probe_action = BugTriageAction(task_id="task_criticality", bug_id="probe",
                                    criticality=CriticalityLabel.CRITICAL, confidence=0.5)
    _probe_gt = BugGroundTruth(bug_id="probe", criticality=CriticalityLabel.CRITICAL,
                               severity=SeverityLevel.MEDIUM, root_cause=RootCauseCategory.BUG,
                               assignee="probe")
    _gc(_probe_action, _probe_gt)
    grade_criticality = _gc
    grade_severity = _gs
    grade_root_cause_assignee = _grc
    RewardCalculator = _RC
    _USING_MOCK_GRADERS = False
except (ImportError, NotImplementedError):
    _USING_MOCK_GRADERS = True

    def grade_criticality(action: BugTriageAction, gt: BugGroundTruth) -> float:
        return 1.0 if action.criticality == gt.criticality else 0.0

    def grade_severity(action: BugTriageAction, gt: BugGroundTruth) -> float:
        if action.severity is None:
            return 0.0
        diff = abs(action.severity.value - gt.severity.value)
        return {0: 1.0, 1: 0.7, 2: 0.4}.get(diff, 0.0)

    def grade_root_cause_assignee(action: BugTriageAction, gt: BugGroundTruth) -> float:
        rc_score = 1.0 if action.root_cause == gt.root_cause else 0.5
        assignee_score = 1.0 if action.assignee == gt.assignee else 0.6
        return 0.6 * rc_score + 0.4 * assignee_score

    class RewardCalculator:
        def compute(self, base_score: float, _action: BugTriageAction, _gt: BugGroundTruth) -> BugTriageReward:
            return BugTriageReward(base_score=base_score, total=min(1.0, base_score))


_TASK_CYCLE = get_all_task_ids()  # ["task_criticality", "task_severity", "task_root_cause_assignee"]


class BugTriageEnv:
    """OpenEnv-compliant Bug Triage RL environment.

    Each episode presents one bug report. The agent classifies it according
    to the active task (criticality, severity, or root cause + assignee).
    Each episode is a single step (done=True immediately after step()).
    """

    def __init__(self, data_path: str = "data/bugs_processed.json",
                 task_type: str = "all", seed: int = 42):
        """Initialize environment.

        Args:
            data_path: Path to bugs_processed.json
            task_type: "all" to cycle through tasks, or a specific task ID
            seed: Random seed for reproducible episode ordering
        """
        if task_type != "all" and not validate_task_id(task_type):
            raise ValueError(f"Unknown task_type: {task_type!r}. Must be 'all' or one of {_TASK_CYCLE}")

        self._task_type = task_type
        self._seed = seed
        self._reward_calculator = RewardCalculator()

        # Load dataset
        with open(data_path, "r", encoding="utf-8") as f:
            raw_bugs = json.load(f)

        self._bugs: List[dict] = raw_bugs
        self._total_bugs = len(self._bugs)

        # Shuffle with fixed seed for reproducibility
        rng = random.Random(seed)
        self._bug_order: List[int] = list(range(self._total_bugs))
        rng.shuffle(self._bug_order)

        # Episode state
        self._episode_number: int = 0
        self._bug_cursor: int = 0        # index into _bug_order
        self._task_cursor: int = 0       # index into _TASK_CYCLE
        self._current_task_id: Optional[str] = None
        self._current_bug: Optional[dict] = None
        self._current_gt: Optional[BugGroundTruth] = None
        self._current_obs: Optional[BugTriageObservation] = None
        self._step_count: int = 0
        self._waiting_for_step: bool = False  # True after reset, before step

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self, task_id: str = None) -> BugTriageObservation:
        """Start a new episode.

        Args:
            task_id: Force a specific task; None cycles through all three.

        Returns:
            BugTriageObservation for the next bug in the queue.
        """
        # Determine task for this episode
        if task_id is not None:
            if not validate_task_id(task_id):
                raise ValueError(f"Unknown task_id: {task_id!r}")
            self._current_task_id = task_id
        elif self._task_type != "all":
            self._current_task_id = self._task_type
        else:
            self._current_task_id = _TASK_CYCLE[self._task_cursor % len(_TASK_CYCLE)]
            self._task_cursor += 1

        # Advance bug cursor (wrap around)
        bug_idx = self._bug_order[self._bug_cursor % self._total_bugs]
        self._bug_cursor += 1
        self._current_bug = self._bugs[bug_idx]

        # Parse ground truth (hidden from agent)
        gt_raw = self._current_bug.get("ground_truth", {})
        self._current_gt = BugGroundTruth(
            bug_id=self._current_bug["bug_id"],
            criticality=CriticalityLabel(gt_raw["criticality"]),
            severity=SeverityLevel(gt_raw["severity"]),
            root_cause=RootCauseCategory(gt_raw["root_cause"]),
            assignee=gt_raw.get("assignee", "unknown"),
            is_ambiguous=gt_raw.get("is_ambiguous", False),
        )

        # Build BugReport (what the agent sees)
        bug_report = BugReport(
            bug_id=self._current_bug["bug_id"],
            title=self._current_bug["title"],
            body=self._current_bug["body"],
            labels=self._current_bug.get("labels", []),
            created_at=self._current_bug["created_at"],
            repo=self._current_bug["repo"],
            comments_text=self._current_bug.get("comments_text", []),
            author=self._current_bug["author"],
            is_pull_request=False,
        )

        # Populate available_assignees for task_root_cause_assignee
        available_assignees = []
        if self._current_task_id == "task_root_cause_assignee":
            available_assignees = self._get_assignees_for_bug(self._current_bug)

        task_def = TASK_DEFINITIONS[self._current_task_id]
        self._current_obs = BugTriageObservation(
            task_id=self._current_task_id,
            bug_report=bug_report,
            available_assignees=available_assignees,
            step=0,
            max_steps=task_def["max_steps"],
            done=False,
        )

        self._episode_number += 1
        self._step_count = 0
        self._waiting_for_step = True
        return self._current_obs

    def step(self, action: BugTriageAction) -> tuple:
        """Process agent's classification action.

        Args:
            action: BugTriageAction from the agent.

        Returns:
            (observation, reward_float, done, info) tuple.
            observation is a new BugTriageObservation with done=True.
            reward_float is a float in [0.0, 1.0].
            info dict contains ground_truth and reward breakdown.
        """
        if not self._waiting_for_step:
            raise RuntimeError("Call reset() before step().")
        if self._current_obs is None or self._current_gt is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        # Validate task_id matches
        if action.task_id != self._current_task_id:
            raise ValueError(
                f"Action task_id {action.task_id!r} does not match current task {self._current_task_id!r}"
            )

        # Validate bug_id matches
        if action.bug_id != self._current_gt.bug_id:
            raise ValueError(
                f"Action bug_id {action.bug_id!r} does not match current bug {self._current_gt.bug_id!r}"
            )

        # Grade the action
        base_score = self._grade(action, self._current_gt)

        # Compute full reward with bonuses
        reward_model = self._reward_calculator.compute(base_score, action, self._current_gt)
        reward_float = float(reward_model.total)

        # Build terminal observation
        terminal_obs = BugTriageObservation(
            task_id=self._current_task_id,
            bug_report=self._current_obs.bug_report,
            available_assignees=self._current_obs.available_assignees,
            step=1,
            max_steps=self._current_obs.max_steps,
            done=True,
        )

        info = {
            "ground_truth": {
                "criticality": self._current_gt.criticality.value,
                "severity": self._current_gt.severity.value,
                "root_cause": self._current_gt.root_cause.value,
                "assignee": self._current_gt.assignee,
                "is_ambiguous": self._current_gt.is_ambiguous,
            },
            "reward_breakdown": {
                "base_score": reward_model.base_score,
                "confidence_bonus": reward_model.confidence_bonus,
                "reasoning_bonus": reward_model.reasoning_bonus,
                "edge_case_bonus": reward_model.edge_case_bonus,
                "total": reward_model.total,
            },
            "episode_number": self._episode_number,
            "using_mock_graders": _USING_MOCK_GRADERS,
        }

        self._step_count += 1
        self._waiting_for_step = False
        return terminal_obs, reward_float, True, info

    def state(self) -> dict:
        """Return current environment state.

        Returns:
            Dict with episode metadata (no bug content, safe to log).
        """
        return {
            "current_task_id": self._current_task_id,
            "current_bug_id": self._current_bug["bug_id"] if self._current_bug else None,
            "episode_number": self._episode_number,
            "step_count": self._step_count,
            "total_bugs": self._total_bugs,
            "tasks_available": _TASK_CYCLE,
            "waiting_for_step": self._waiting_for_step,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _grade(self, action: BugTriageAction, gt: BugGroundTruth) -> float:
        """Dispatch to the correct grader based on current task."""
        if self._current_task_id == "task_criticality":
            return grade_criticality(action, gt)
        elif self._current_task_id == "task_severity":
            return grade_severity(action, gt)
        elif self._current_task_id == "task_root_cause_assignee":
            return grade_root_cause_assignee(action, gt)
        return 0.0

    def _get_assignees_for_bug(self, bug: dict) -> List[str]:
        """Return a list of candidate assignees for a bug (for task 3 context)."""
        assignees = set()
        gt_assignee = bug.get("ground_truth", {}).get("assignee", "")
        if gt_assignee:
            assignees.add(gt_assignee)
        # Add a few distractors from the same repo's bugs
        repo = bug.get("repo", "")
        for other in self._bugs:
            if other["repo"] == repo and other["bug_id"] != bug["bug_id"]:
                other_assignee = other.get("ground_truth", {}).get("assignee", "")
                if other_assignee and other_assignee != "unknown":
                    assignees.add(other_assignee)
            if len(assignees) >= 8:
                break
        return sorted(assignees)
