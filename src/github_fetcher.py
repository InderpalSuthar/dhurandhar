"""
GitHub data fetcher - Fetches real bug reports from GitHub repos.

Owner: Sumit
Status: Day 1 SKELETON (to be completed in Day 2)

This module handles all interaction with GitHub API.
"""

import os
import json
from typing import List, Dict, Optional
from github import Github
from github.GithubException import GithubException


class GitHubFetcher:
    """Fetches real bug reports from GitHub repositories."""

    def __init__(self, token: str = None):
        """Initialize GitHub API client.

        Args:
            token: GitHub personal access token. If None, reads from GITHUB_TOKEN env var.
        """
        token = token or os.environ.get("GITHUB_TOKEN", "")
        if not token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN env var or pass token parameter.")

        self.github = Github(token)
        self.rate_limit_buffer = 100  # Keep buffer for safety

    def fetch_issues(
        self,
        repo: str,
        max_issues: int = 50,
        state: str = "closed",
        labels: List[str] = None
    ) -> List[Dict]:
        """Fetch issues from a GitHub repository.

        Args:
            repo: Repository in format "owner/repo" (e.g., "pytorch/pytorch")
            max_issues: Maximum number of issues to fetch
            state: "open" or "closed"
            labels: List of label filters (e.g., ["bug", "critical"])

        Returns:
            List of issue dicts with extracted data
        """
        raise NotImplementedError("Implement in Day 2")

    def fetch_contributors(self, repo: str) -> List[Dict]:
        """Fetch top contributors for a repository.

        Args:
            repo: Repository in format "owner/repo"

        Returns:
            List of contributor dicts with name, email (if public), commit count
        """
        raise NotImplementedError("Implement in Day 2")

    def process_raw_to_structured(self, raw_issues: List[Dict]) -> List[Dict]:
        """Convert raw GitHub API responses to our BugReport schema.

        Args:
            raw_issues: Raw issues from GitHub API

        Returns:
            List of dicts matching BugReport schema (without ground_truth)
        """
        raise NotImplementedError("Implement in Day 2")

    def save_to_json(self, data: List[Dict], filepath: str):
        """Save data to JSON file.

        Args:
            data: List of dicts to save
            filepath: Output file path
        """
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Example usage (for reference)
if __name__ == "__main__":
    # This will be filled in during Day 2
    pass
