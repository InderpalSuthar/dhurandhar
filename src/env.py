"""
Bug Triage RL Environment - Main class.

Owner: Sumit
Status: STUB (to be implemented)
"""

from src.models import BugTriageObservation, BugTriageAction, BugTriageReward


class BugTriageEnv:
    """OpenEnv-compliant Bug Triage environment."""

    def __init__(self, data_path: str = "data/bugs_processed.json", task_type: str = "all"):
        """Initialize environment.

        Args:
            data_path: Path to bugs_processed.json
            task_type: "all" or specific task ID
        """
        raise NotImplementedError("Implement in Day 3")

    def reset(self, task_id: str = None) -> BugTriageObservation:
        """Start a new episode.

        Args:
            task_id: Task to run ("task_criticality", "task_severity", "task_root_cause_assignee")

        Returns:
            BugTriageObservation for the first bug
        """
        raise NotImplementedError("Implement in Day 3")

    def step(self, action: BugTriageAction) -> tuple:
        """Process agent's action.

        Args:
            action: BugTriageAction from agent

        Returns:
            (observation, reward, done, info) tuple
        """
        raise NotImplementedError("Implement in Day 3")

    def state(self) -> dict:
        """Return current environment state."""
        raise NotImplementedError("Implement in Day 3")
