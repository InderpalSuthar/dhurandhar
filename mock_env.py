"""Temporary mock environment for testing inference.py without Sumit's env.py.
Delete after integration on Day 4.
"""

from src.models import (
    BugTriageObservation,
    BugReport,
    BugTriageAction,
    BugTriageReward,
    BugGroundTruth,
    CriticalityLabel,
    SeverityLevel,
    RootCauseCategory,
)
from src.graders import grade_criticality, grade_severity, grade_root_cause_assignee
from src.reward import RewardCalculator

MOCK_BUGS = [
    BugReport(
        bug_id="mock/repo#1",
        title="App crashes on startup with segfault",
        body="When launching the app on Ubuntu 22.04, it immediately crashes with a segmentation fault. Stack trace points to null pointer dereference in the auth module. This affects all users.",
        labels=["bug", "critical", "crash"],
        created_at="2024-01-15T10:00:00Z",
        repo="mock/repo",
        author="mockuser",
    ),
    BugReport(
        bug_id="mock/repo#2",
        title="Typo in README installation instructions",
        body="Step 3 says 'pip install -r requrements.txt' but the file is named 'requirements.txt'. Minor typo.",
        labels=["documentation", "good-first-issue"],
        created_at="2024-01-16T10:00:00Z",
        repo="mock/repo",
        author="contributor1",
    ),
    BugReport(
        bug_id="mock/repo#3",
        title="API response time increased 10x after v2.3 release",
        body="Since the v2.3 release, average API response time went from 50ms to 500ms. Profiling shows the new ORM queries are not using indexes. Affects all API endpoints.",
        labels=["performance", "regression", "high-priority"],
        created_at="2024-01-17T10:00:00Z",
        repo="mock/repo",
        author="devops-lead",
    ),
]

MOCK_GROUND_TRUTHS = {
    "mock/repo#1": BugGroundTruth(
        bug_id="mock/repo#1", criticality=CriticalityLabel.CRITICAL,
        severity=SeverityLevel.CRITICAL, root_cause=RootCauseCategory.BUG, assignee="alice",
    ),
    "mock/repo#2": BugGroundTruth(
        bug_id="mock/repo#2", criticality=CriticalityLabel.NON_CRITICAL,
        severity=SeverityLevel.TRIVIAL, root_cause=RootCauseCategory.DOCUMENTATION, assignee="charlie",
    ),
    "mock/repo#3": BugGroundTruth(
        bug_id="mock/repo#3", criticality=CriticalityLabel.CRITICAL,
        severity=SeverityLevel.HIGH, root_cause=RootCauseCategory.PERFORMANCE, assignee="bob",
    ),
}

MOCK_TEAMS = {"alice": "frontend", "bob": "backend", "charlie": "docs"}


class MockBugTriageEnv:
    def __init__(self):
        self.episode = 0
        self.current_bug = None
        self.current_task = None
        self.reward_calc = RewardCalculator()

    def reset(self, task_id="task_criticality"):
        bug = MOCK_BUGS[self.episode % len(MOCK_BUGS)]
        self.current_bug = bug
        self.current_task = task_id
        self.episode += 1
        return BugTriageObservation(
            task_id=task_id,
            bug_report=bug,
            available_assignees=["alice", "bob", "charlie"],
            step=0,
            max_steps=1,
        )

    def step(self, action: BugTriageAction):
        gt = MOCK_GROUND_TRUTHS[self.current_bug.bug_id]

        if self.current_task == "task_criticality":
            base = grade_criticality(action, gt)
        elif self.current_task == "task_severity":
            base = grade_severity(action, gt)
        else:
            base = grade_root_cause_assignee(action, gt, MOCK_TEAMS)

        reward = self.reward_calc.compute(base, action, gt)
        return None, reward, True, {"ground_truth": gt.model_dump()}

    def state(self):
        return {"episode": self.episode, "task": self.current_task}
