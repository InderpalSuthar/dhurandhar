"""
GitHub data fetcher - Fetches real bug reports from GitHub repos.

Owner: Sumit
Status: Day 2 COMPLETE
"""

import os
import json
import time
import re
from typing import List, Dict, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

REPO_CONFIGS = {
    "pytorch/pytorch": {"max_issues": 35},
    "django/django": {"max_issues": 55},
    "tiangolo/fastapi": {"max_issues": 45},
    "numpy/numpy": {"max_issues": 40},
    "python/cpython": {"max_issues": 30},
}

CRITICAL_KEYWORDS = frozenset([
    "critical", "p0", "blocker", "crash", "security", "vulnerability",
    "segfault", "data loss", "regression", "corruption", "dataloss"
])

SEVERITY_LABEL_MAP = {
    5: frozenset(["p0", "blocker", "critical", "crash", "security", "segfault"]),
    4: frozenset(["p1", "high", "important", "regression", "major"]),
    3: frozenset(["p2", "medium", "normal", "moderate"]),
    2: frozenset(["p3", "low", "minor"]),
    1: frozenset(["trivial", "cosmetic", "typo", "nitpick"]),
}

ROOT_CAUSE_KEYWORDS = {
    "bug": ["crash", "error", "exception", "traceback", "assertion", "segfault",
            "failure", "broken", "incorrect", "wrong", "unexpected", "raises", "typeerror",
            "valueerror", "attributeerror", "indexerror", "keyerror", "runtimeerror"],
    "performance": ["slow", "memory", "performance", "leak", "speed", "latency",
                    "timeout", "resource", "cpu", "oom", "optimization", "bottleneck"],
    "environment": ["config", "install", "setup", "environment", "compatibility",
                    "platform", "version", "windows", "linux", "macos", "import", "pip"],
    "design": ["refactor", "design", "api", "interface", "deprecat", "breaking",
               "inconsist", "behavior", "usability", "confusing", "unintuitive"],
    "documentation": ["doc", "documentation", "typo", "readme", "example",
                      "tutorial", "docstring", "spelling", "misleading"],
    "external": ["upstream", "dependency", "third-party", "external", "vendor",
                 "library", "package", "conda", "numpy", "scipy"],
}

TEAM_MAP = {
    "pytorch/pytorch": ["autograd", "distributed", "jit", "quantization", "mobile", "onnx", "cuda"],
    "django/django": ["orm", "admin", "forms", "middleware", "security", "http", "template"],
    "tiangolo/fastapi": ["routing", "dependencies", "security", "websockets", "openapi", "middleware"],
    "numpy/numpy": ["core", "linalg", "fft", "random", "ma", "testing", "io"],
    "python/cpython": ["stdlib", "interpreter", "gc", "typing", "asyncio", "io", "ssl"],
}


class GitHubFetcher:
    """Fetches real bug reports from GitHub repositories using REST API."""

    def __init__(self, token: str = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.session = requests.Session()
        if self.token:
            self.session.headers["Authorization"] = f"token {self.token}"
        self.session.headers["Accept"] = "application/vnd.github.v3+json"
        self.session.headers["User-Agent"] = "BugTriageEnv/1.0"

    def _api_get(self, url: str, params: dict = None) -> Optional[requests.Response]:
        for attempt in range(3):
            try:
                resp = self.session.get(url, params=params, timeout=30)
                if resp.status_code == 200:
                    return resp
                elif resp.status_code == 403:
                    reset = int(resp.headers.get("X-RateLimit-Reset", 0))
                    wait = max(5, reset - time.time() + 2)
                    print(f"  Rate limited. Waiting {wait:.0f}s...")
                    time.sleep(wait)
                elif resp.status_code == 422:
                    print(f"  Validation error for {url}, trying without labels...")
                    return None
                else:
                    print(f"  HTTP {resp.status_code} for {url}")
                    time.sleep(2 ** attempt)
            except requests.RequestException as e:
                print(f"  Request error (attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)
        return None

    def fetch_issues(self, repo: str, max_issues: int = 50,
                     state: str = "closed", labels: List[str] = None) -> List[Dict]:
        all_issues = []
        page = 1
        base_url = f"https://api.github.com/repos/{repo}/issues"
        while len(all_issues) < max_issues:
            params = {"state": state, "per_page": 100, "page": page,
                      "sort": "updated", "direction": "desc"}
            if labels:
                params["labels"] = ",".join(labels)
            resp = self._api_get(base_url, params)
            if not resp:
                break
            issues = resp.json()
            if not isinstance(issues, list) or not issues:
                break
            for issue in issues:
                if issue.get("pull_request"):
                    continue
                all_issues.append(issue)
                if len(all_issues) >= max_issues:
                    break
            page += 1
            time.sleep(0.3)
        print(f"  Fetched {len(all_issues)} raw issues from {repo}")
        return all_issues

    def fetch_issue_comments(self, repo: str, issue_number: int, max_comments: int = 3) -> List[str]:
        url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
        resp = self._api_get(url, {"per_page": max_comments})
        if not resp:
            return []
        comments = []
        for c in resp.json()[:max_comments]:
            body = (c.get("body") or "").strip()
            user = (c.get("user") or {}).get("login", "")
            if any(b in user.lower() for b in ["bot", "github-actions", "codecov", "dependabot"]):
                continue
            if body and len(body) > 20:
                comments.append(body[:2000])
        return comments

    def fetch_contributors(self, repo: str, max_n: int = 15) -> List[Dict]:
        url = f"https://api.github.com/repos/{repo}/contributors"
        resp = self._api_get(url, {"per_page": max_n})
        if not resp:
            return []
        return [{"name": c.get("login", "unknown"), "contributions": c.get("contributions", 0)}
                for c in resp.json()[:max_n]]

    def _is_bug_issue(self, issue: Dict) -> bool:
        labels = [l.get("name", "").lower() for l in issue.get("labels", [])]
        title = (issue.get("title") or "").lower()
        body = (issue.get("body") or "").lower()[:500]
        bug_label = any("bug" in l for l in labels) or any("defect" in l for l in labels)
        skip = any(kw in l for l in labels for kw in
                   ["feature", "enhancement", "question", "discussion", "rfc", "proposal", "wontfix"])
        title_bug = any(kw in title for kw in
                        ["error", "bug", "crash", "fail", "broken", "incorrect", "wrong",
                         "exception", "traceback", "segfault", "regression", "fix"])
        body_bug = any(kw in body for kw in ["traceback", "error", "exception", "crash"])
        has_body = len(issue.get("body") or "") > 50
        return (bug_label or title_bug or body_bug) and not skip and has_body

    def process_raw_to_structured(self, raw_issues: List[Dict], repo: str) -> List[Dict]:
        structured = []
        for issue in raw_issues:
            if not self._is_bug_issue(issue):
                continue
            body = (issue.get("body") or "")[:5000]
            labels = [l.get("name", "") for l in issue.get("labels", [])]
            closed_by = ""
            if issue.get("closed_by") and isinstance(issue["closed_by"], dict):
                closed_by = issue["closed_by"].get("login", "")
            structured.append({
                "bug_id": f"{repo}#{issue['number']}",
                "title": issue.get("title", ""),
                "body": body,
                "labels": labels,
                "created_at": issue.get("created_at", ""),
                "repo": repo,
                "comments_text": [],
                "author": (issue.get("user") or {}).get("login", "unknown"),
                "is_pull_request": False,
                "_closed_by": closed_by,
            })
        return structured

    def label_ground_truth(self, bugs: List[Dict]) -> List[Dict]:
        for bug in bugs:
            labels_lower = [l.lower() for l in bug.get("labels", [])]
            title_lower = bug.get("title", "").lower()
            body_lower = bug.get("body", "").lower()[:1000]
            text = f"{title_lower} {' '.join(labels_lower)} {body_lower}"

            # Criticality
            crit = "non_critical"
            crit_hits = sum(1 for kw in CRITICAL_KEYWORDS if kw in text)
            if crit_hits > 0:
                crit = "critical"

            # Severity
            sev = 3
            for level in [5, 4, 3, 2, 1]:
                if any(kw in text for kw in SEVERITY_LABEL_MAP[level]):
                    sev = level
                    break
            if crit == "critical" and sev < 4:
                sev = 4

            # Root cause
            scores = {cat: sum(1 for kw in kws if kw in text)
                      for cat, kws in ROOT_CAUSE_KEYWORDS.items()}
            rc = max(scores, key=scores.get) if max(scores.values()) > 0 else "bug"

            # Assignee
            assignee = bug.get("_closed_by") or bug.get("author", "unknown")

            # Ambiguous
            top = sorted(scores.values(), reverse=True)
            is_amb = (len(top) >= 2 and top[0] > 0 and top[0] == top[1]) or crit_hits == 1

            bug["ground_truth"] = {
                "criticality": crit,
                "severity": sev,
                "root_cause": rc,
                "assignee": assignee,
                "is_ambiguous": is_amb,
            }
            bug.pop("_closed_by", None)
        return bugs

    def save_to_json(self, data, filepath: str):
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(data) if isinstance(data, list) else 'dict'} to {filepath}")

    def run_full_pipeline(self, repos: Dict = None, fetch_comments: bool = True):
        repos = repos or REPO_CONFIGS
        print("=" * 60)
        print("BUG TRIAGE DATA PIPELINE")
        print("=" * 60)

        all_raw, all_structured = [], []
        contributors_data = {}

        for repo, config in repos.items():
            print(f"\n--- {repo} ---")
            target = config.get("max_issues", 50)
            raw = self.fetch_issues(repo, max_issues=target * 3, state="closed")
            all_raw.extend(raw)
            structured = self.process_raw_to_structured(raw, repo)[:target]

            if fetch_comments and self.token:
                print(f"  Fetching comments for {len(structured)} issues...")
                for i, bug in enumerate(structured):
                    num = int(bug["bug_id"].split("#")[1])
                    bug["comments_text"] = self.fetch_issue_comments(repo, num)
                    if (i + 1) % 10 == 0:
                        print(f"    Progress: {i+1}/{len(structured)}")
                    time.sleep(0.25)

            all_structured.extend(structured)
            contribs = self.fetch_contributors(repo)
            contributors_data[repo] = {
                "contributors": contribs,
                "teams": TEAM_MAP.get(repo, ["general"]),
            }
            print(f"  Got {len(structured)} bugs from {repo}")

        self.save_to_json(all_raw, "data/bugs_raw.json")
        labeled = self.label_ground_truth(all_structured)
        self.save_to_json(labeled, "data/bugs_processed.json")
        self.save_to_json(contributors_data, "data/contributors.json")
        self._print_summary(labeled)
        return labeled

    def _print_summary(self, bugs: List[Dict]):
        print("\n" + "=" * 60)
        print(f"TOTAL BUGS: {len(bugs)}")
        repos = {}
        for b in bugs:
            repos[b["repo"]] = repos.get(b["repo"], 0) + 1
        for r, c in sorted(repos.items()):
            print(f"  {r}: {c}")
        crit = sum(1 for b in bugs if b["ground_truth"]["criticality"] == "critical")
        print(f"Critical: {crit} ({crit*100//max(len(bugs),1)}%) | Non-critical: {len(bugs)-crit}")
        for lvl in range(1, 6):
            n = sum(1 for b in bugs if b["ground_truth"]["severity"] == lvl)
            print(f"  Severity {lvl}: {n}")
        rc = {}
        for b in bugs:
            k = b["ground_truth"]["root_cause"]
            rc[k] = rc.get(k, 0) + 1
        for k, v in sorted(rc.items()):
            print(f"  {k}: {v}")
        amb = sum(1 for b in bugs if b["ground_truth"]["is_ambiguous"])
        print(f"Ambiguous: {amb}")


if __name__ == "__main__":
    fetcher = GitHubFetcher()
    fetcher.run_full_pipeline()
