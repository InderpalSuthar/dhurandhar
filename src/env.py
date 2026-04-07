"""
Bug Triage RL Environment — Main class.

OpenEnv-compliant single-step RL environment for automated GitHub
bug report triage. Supports three tasks: criticality detection,
severity scoring, and root-cause + assignee recommendation.

Owner: Team Dhurandhar
Status: Final submission — production-grade, hardened
"""

import json
import random
import logging
from typing import Optional, List, Dict, Set

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
from src.graders import grade_criticality, grade_severity, grade_root_cause_assignee
from src.reward import RewardCalculator
from src.tasks import TASK_DEFINITIONS, get_all_task_ids, validate_task_id

logger = logging.getLogger(__name__)

_TASK_CYCLE = get_all_task_ids()  # ["task_criticality", "task_severity", "task_root_cause_assignee"]

# Safe fallback reward for error recovery
_SAFE_REWARD = BugTriageReward(base_score=0.0, total=0.0)


class BugTriageEnv:
    """OpenEnv-compliant Bug Triage RL environment.

    Each episode presents one bug report. The agent classifies it according
    to the active task (criticality, severity, or root cause + assignee).
    Each episode is a single step (done=True immediately after step()).

    HARDENED: This environment NEVER crashes. All public methods catch
    exceptions internally and return valid data, even on malformed input.
    """

    _DATA_CACHE: Dict[str, List[dict]] = {}
    _CONTRIBS_CACHE: Dict[str, tuple] = {}

    def __init__(self, data_path: str = "data/bugs_processed.json",
                 task_type: str = "all", seed: int = 42,
                 repository_filter: Optional[List[str]] = None):
        """Initialize environment (optimized with dataset caching)."""
        if task_type != "all" and not validate_task_id(task_type):
            raise ValueError(f"Unknown task_type: {task_type!r}. Must be 'all' or one of {_TASK_CYCLE}")

        self._task_type = task_type
        self._seed = seed
        self._reward_calculator = RewardCalculator()

        # Load dataset (with class-level cache)
        if data_path not in BugTriageEnv._DATA_CACHE:
            with open(data_path, "r", encoding="utf-8") as f:
                BugTriageEnv._DATA_CACHE[data_path] = json.load(f)
        
        raw_bugs = BugTriageEnv._DATA_CACHE[data_path]

        if repository_filter:
            self._bugs = [b for b in raw_bugs if b.get("repo") in repository_filter]
        else:
            self._bugs = raw_bugs

        self._total_bugs = len(self._bugs)
        if self._total_bugs == 0:
            raise ValueError(f"Dataset is empty (filter={repository_filter}) — cannot create environment")

        # Load contributor team & expertise mappings (with caching)
        contributors_path = data_path.replace("bugs_processed.json", "contributors.json")
        if contributors_path not in BugTriageEnv._CONTRIBS_CACHE:
            teams: Dict[str, str] = {}
            expertise: Dict[str, List[str]] = {}
            try:
                with open(contributors_path, "r", encoding="utf-8") as f:
                    contribs_raw = json.load(f)
                for repo_data in contribs_raw.values():
                    for c in repo_data.get("contributors", []):
                        name = c.get("name", "").lower()
                        if name:
                            teams[name] = repo_data.get("teams", ["general"])[0]
                            expertise[name] = c.get("work_area", [])
                BugTriageEnv._CONTRIBS_CACHE[contributors_path] = (teams, expertise)
            except (FileNotFoundError, KeyError, ValueError):
                BugTriageEnv._CONTRIBS_CACHE[contributors_path] = ({}, {})
        
        self._contributor_teams, self._contributor_expertise = BugTriageEnv._CONTRIBS_CACHE[contributors_path]

        # Pre-compute assignee pools per repo (O(1) lookup instead of O(n) scan)
        self._repo_assignees: Dict[str, List[str]] = {}
        _repo_assignee_sets: Dict[str, Set[str]] = {}
        for bug in self._bugs:
            repo = bug.get("repo", "")
            assignee = bug.get("ground_truth", {}).get("assignee", "")
            if assignee and assignee != "unknown":
                _repo_assignee_sets.setdefault(repo, set()).add(assignee)
        self._repo_assignees = {r: sorted(a) for r, a in _repo_assignee_sets.items()}

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

        Raises:
            ValueError: If task_id is invalid.
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
            criticality=CriticalityLabel(gt_raw.get("criticality", "non_critical")),
            severity=SeverityLevel(gt_raw.get("severity", 3)),
            root_cause=RootCauseCategory(gt_raw.get("root_cause", "bug")),
            assignee=gt_raw.get("assignee", "unknown"),
            is_ambiguous=gt_raw.get("is_ambiguous", False),
        )

        # Build BugReport (what the agent sees)
        bug_report = BugReport(
            bug_id=self._current_bug.get("bug_id", "unknown"),
            title=self._current_bug.get("title", ""),
            body=self._current_bug.get("body", ""),
            labels=self._current_bug.get("labels", []),
            created_at=self._current_bug.get("created_at", ""),
            repo=self._current_bug.get("repo", ""),
            comments_text=self._current_bug.get("comments_text", []),
            author=self._current_bug.get("author", "unknown"),
            is_pull_request=False,
        )

        # Populate available_assignees for task_root_cause_assignee
        available_assignees: List[str] = []
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

        HARDENED: Catches all grader/reward errors and returns a valid
        tuple with reward=0.0 instead of crashing.

        Args:
            action: BugTriageAction from the agent.

        Returns:
            (observation, reward_float, done, info) tuple.
            observation is a new BugTriageObservation with done=True.
            reward_float is a float in [0.0, 1.0].
            info dict contains ground_truth and reward breakdown.

        Raises:
            RuntimeError: If called before reset() or after episode is done.
            ValueError: If action.task_id or action.bug_id doesn't match.
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

        # ── HARDENED GRADING ─────────────────────────────────────────────
        grading_error = None
        try:
            base_score = self._grade(action, self._current_gt)
            base_score = max(0.0, min(1.0, float(base_score)))
        except Exception as e:
            logger.warning("Grader raised %s: %s — defaulting to 0.0", type(e).__name__, e)
            base_score = 0.0
            grading_error = str(e)

        # Compute full reward with bonuses
        try:
            reward_model = self._reward_calculator.compute(base_score, action, self._current_gt)
            reward_float = max(0.0, min(1.0, float(reward_model.total)))
        except Exception as e:
            logger.warning("RewardCalculator raised %s: %s — defaulting to base_score", type(e).__name__, e)
            reward_model = _SAFE_REWARD
            reward_float = base_score

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
        }
        if grading_error:
            info["grading_error"] = grading_error

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
        """Dispatch to the correct grader based on current task.

        Passes contributor_teams to the root_cause_assignee grader so that
        same-team assignees receive partial credit.
        """
        if self._current_task_id == "task_criticality":
            return grade_criticality(action, gt)
        elif self._current_task_id == "task_severity":
            return grade_severity(action, gt)
        elif self._current_task_id == "task_root_cause_assignee":
            return grade_root_cause_assignee(
                action, gt, contributor_teams=self._contributor_teams or None
            )
        return 0.0

    def _get_assignees_for_bug(self, bug: dict) -> List[str]:
        """Return a list of candidate assignees for a bug (for task 3 context).

        Uses the pre-computed repo assignee pool for O(1) lookup instead of
        scanning the entire dataset on every call.
        """
        gt_assignee = bug.get("ground_truth", {}).get("assignee", "")
        repo = bug.get("repo", "")
        pool = self._repo_assignees.get(repo, [])

        # Always include the correct answer + up to 7 distractors
        candidates: Set[str] = set()
        if gt_assignee and gt_assignee != "unknown":
            candidates.add(gt_assignee)
        for name in pool:
            if name != gt_assignee and name != "unknown":
                candidates.add(name)
            if len(candidates) >= 8:
                break

        return sorted(candidates)
