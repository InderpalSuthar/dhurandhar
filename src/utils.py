"""
Utility functions for Bug Triage environment.

Owner: Sumit
Status: Day 1 SKELETON (to be completed in Day 2)
"""

import json
import os
from typing import List, Dict, Optional


def load_json(filepath: str) -> Dict:
    """Load data from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        Loaded data
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, filepath: str):
    """Save data to JSON file.

    Args:
        data: Data to save
        filepath: Output file path
    """
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def truncate_text(text: str, max_chars: int = 5000) -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_chars: Maximum characters

    Returns:
        Truncated text
    """
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


def filter_bugs_by_difficulty(bugs: List[Dict], difficulty: str) -> List[Dict]:
    """Filter bugs by difficulty level.

    Args:
        bugs: List of bugs with ground_truth
        difficulty: "easy", "medium", or "hard"

    Returns:
        Filtered list
    """
    raise NotImplementedError("Implement in Day 2")


def get_bug_by_id(bugs: List[Dict], bug_id: str) -> Optional[Dict]:
    """Get a single bug by ID.

    Args:
        bugs: List of bugs
        bug_id: Bug ID to find

    Returns:
        Bug dict or None if not found
    """
    for bug in bugs:
        if bug.get("bug_id") == bug_id:
            return bug
    return None
