"""
Task definitions for Bug Triage environment.

Owner: Sumit
Status: STUB (to be implemented)

Each task defines an objective with metadata.
"""

TASK_DEFINITIONS = {
    "task_criticality": {
        "name": "Criticality Detection",
        "difficulty": "easy",
        "description": "Determine if a bug report is critical or non-critical",
        "grader_fn": "grade_criticality",
        "required_action_fields": ["criticality"],
    },
    "task_severity": {
        "name": "Severity Scoring",
        "difficulty": "medium",
        "description": "Assign severity score 1-5 to a bug report",
        "grader_fn": "grade_severity",
        "required_action_fields": ["severity"],
    },
    "task_root_cause_assignee": {
        "name": "Root Cause & Assignee",
        "difficulty": "hard",
        "description": "Identify root cause category and recommend assignee",
        "grader_fn": "grade_root_cause_assignee",
        "required_action_fields": ["root_cause", "assignee"],
    },
}

# Implementation: To be added in Day 2
