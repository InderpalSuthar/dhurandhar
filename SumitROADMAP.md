# SUMIT's ROADMAP - Bug Report Triage RL Environment

**Role:** Environment Core + Data Pipeline + Tests
**Branch:** `sumit/env-data`
**Deadline:** April 8, 2026 11:59 PM

---

## File Ownership

| File | Status |
|------|--------|
| `src/models.py` | Co-author (Day 1 JOINT) |
| `src/env.py` | **SOLE OWNER** |
| `src/tasks.py` | **SOLE OWNER** |
| `src/github_fetcher.py` | **SOLE OWNER** |
| `src/utils.py` | **SOLE OWNER** |
| `src/__init__.py` | **SOLE OWNER** |
| `data/bugs_processed.json` | **SOLE OWNER** |
| `data/contributors.json` | **SOLE OWNER** |
| `tests/test_env.py` | **SOLE OWNER** |
| `tests/test_graders.py` | **SOLE OWNER** |
| `tests/test_inference.py` | **SOLE OWNER** |

> **RULE:** Never edit Inderpal's files (`graders.py`, `reward.py`, `inference.py`, `Dockerfile`, `openenv.yaml`, `README.md`). If you find a bug in his code, message him. If you need a stub, write a mock in your own file.

---

## DAY 1 - April 2 (TODAY): Joint Setup + Models Contract

**Time Budget:** 5-6 hours
**Goal:** Lock down the shared interface so both tracks can work independently

### JOINT TASKS (with Inderpal) - 2.5 hours

| # | Task | Deliverable | Time |
|---|------|-------------|------|
| 1 | Create repo structure | `mkdir -p src data tests` + all `__init__.py` files | 15 min |
| 2 | Write `src/models.py` together | Complete Pydantic models (see contract below) | 90 min |
| 3 | Write interface stubs | Stub files for `env.py`, `graders.py`, `reward.py`, `tasks.py` with `raise NotImplementedError` | 30 min |
| 4 | Agree on data schema | Exact JSON structure for `bugs_processed.json` | 15 min |
| 5 | Set up `requirements.txt` | Initial deps: `pydantic>=2.0`, `openai`, `requests`, `pytest`, `python-dotenv` | 10 min |
| 6 | Create feature branches | Push `models.py` to `main`, then branch to `sumit/env-data` | 10 min |

### SOLO TASKS (your own) - 3 hours

| # | Task | Deliverable | Time |
|---|------|-------------|------|
| 1 | Set up GitHub API auth | Create `github_fetcher.py` skeleton with personal access token auth, rate limit handling | 45 min |
| 2 | Identify target repos | Research and list 5-6 repos with good bug data: `pytorch/pytorch`, `django/django`, `tiangolo/fastapi`, `numpy/numpy`, `python/cpython` | 30 min |
| 3 | Start first data fetch | Begin fetching issues from first 2 repos (can run overnight) | 45 min |
| 4 | Write `src/utils.py` | Helper functions: JSON loading, text truncation, bug filtering | 30 min |
| 5 | Write mock graders | Local mocks so you can test `env.py` without Inderpal's code | 30 min |

### Models Contract (MUST AGREE WITH INDERPAL)

```python
# src/models.py - THE SHARED CONTRACT

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class CriticalityLabel(str, Enum):
    CRITICAL = "critical"
    NON_CRITICAL = "non_critical"

class SeverityLevel(int, Enum):
    TRIVIAL = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5

class RootCauseCategory(str, Enum):
    BUG = "bug"
    DESIGN = "design"
    ENVIRONMENT = "environment"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    EXTERNAL = "external"

class BugReport(BaseModel):
    bug_id: str
    title: str
    body: str
    labels: List[str] = []
    created_at: str
    repo: str
    comments_text: List[str] = []
    author: str
    is_pull_request: bool = False

class BugTriageObservation(BaseModel):
    task_id: str
    bug_report: BugReport
    available_assignees: List[str] = []
    step: int
    max_steps: int
    done: bool = False

class BugTriageAction(BaseModel):
    task_id: str
    bug_id: str
    criticality: Optional[CriticalityLabel] = None
    severity: Optional[SeverityLevel] = None
    root_cause: Optional[RootCauseCategory] = None
    assignee: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    reasoning: str = ""

class BugTriageReward(BaseModel):
    base_score: float = Field(ge=0.0, le=1.0)
    confidence_bonus: float = 0.0
    reasoning_bonus: float = 0.0
    edge_case_bonus: float = 0.0
    total: float = Field(ge=0.0, le=1.0)

class BugGroundTruth(BaseModel):
    bug_id: str
    criticality: CriticalityLabel
    severity: SeverityLevel
    root_cause: RootCauseCategory
    assignee: str
    is_ambiguous: bool = False
```

### Data Schema Contract (bugs_processed.json)

Each entry must look like this:
```json
{
    "bug_id": "pytorch/pytorch#12345",
    "title": "RuntimeError when using torch.compile with custom autograd",
    "body": "Full issue description text...",
    "labels": ["bug", "high priority", "module: autograd"],
    "created_at": "2024-01-15T10:30:00Z",
    "repo": "pytorch/pytorch",
    "comments_text": ["Comment 1 from maintainer...", "Comment 2..."],
    "author": "user123",
    "is_pull_request": false,
    "ground_truth": {
        "criticality": "critical",
        "severity": 4,
        "root_cause": "bug",
        "assignee": "dev_abc",
        "is_ambiguous": false
    }
}
```

### Day 1 Exit Criteria
- [ ] `python -c "from src.models import BugTriageObservation"` works
- [ ] Both branches created off `main`
- [ ] GitHub fetcher can authenticate and pull issues
- [ ] Mock graders return 0.5 for any input
- [ ] Data schema documented and agreed

---

## DAY 2 - April 3: Data Pipeline Sprint

**Time Budget:** 7-8 hours
**Goal:** Fetch all 180 bugs, clean them, start labeling ground truth
**Branch:** `sumit/env-data`

### Tasks

| # | Task | Deliverable | Time | Priority |
|---|------|-------------|------|----------|
| 1 | Complete `github_fetcher.py` | Full-featured fetcher: pagination, rate-limit retry, filter closed issues with labels, extract comments, cache results locally | 3h | P0 |
| 2 | Fetch bugs from all 5 repos | Target per repo: Django (50), FastAPI (40), NumPy (35), PyTorch (30), CPython (25) = 180 total. Filter for issues labeled "bug" that have been closed and resolved | 1.5h | P0 |
| 3 | Ground truth labeling pipeline | Script/process to assign `criticality`, `severity`, `root_cause`, `assignee`, `is_ambiguous` to each bug. Strategy: use GitHub labels + PR history for automated labeling, then manual review | 2h | P0 |
| 4 | Label first batch | Label at least 80 bugs (automated + spot-check) | 1.5h | P0 |
| 5 | Implement `tasks.py` | Task definitions with metadata: ID, name, difficulty, description, which grader function to call | 1h | P1 |

### github_fetcher.py Requirements

```python
class GitHubFetcher:
    """Fetches real bug reports from GitHub repos."""

    def __init__(self, token: str = None):
        # Auth with personal access token
        # Rate limit: 5000 req/hr with auth

    def fetch_issues(self, repo: str, max_issues: int = 50,
                     state: str = "closed", labels: list = ["bug"]) -> list:
        # Paginate through issues
        # Extract: title, body, labels, created_at, author, comments
        # Filter: only real bugs (not feature requests, not PRs)
        # Return list of dicts matching BugReport schema

    def fetch_contributors(self, repo: str) -> list:
        # Get top contributors with their commit areas
        # Used for assignee ground truth in Task 3

    def process_raw_to_structured(self, raw_issues: list) -> list:
        # Convert raw GitHub API response to our schema
        # Truncate body to 5000 chars
        # Extract meaningful comments (skip bot comments)
```

### Ground Truth Labeling Strategy

| Field | Source | Automation Level |
|-------|--------|------------------|
| `criticality` | GitHub labels: "critical", "P0", "blocker", "crash", "security" = critical; else non_critical | 90% automated |
| `severity` | GitHub labels mapped: P0/blocker=5, P1/high=4, P2/medium=3, P3/low=2, trivial/docs=1 | 80% automated |
| `root_cause` | Infer from labels + title keywords: "crash"/"error"=bug, "slow"/"memory"=performance, "config"/"env"=environment, "refactor"/"design"=design, "docs"=documentation, "upstream"/"dependency"=external | 70% automated, 30% manual review |
| `assignee` | Person who merged the fixing PR (from git history / linked PR) | 85% automated |
| `is_ambiguous` | Flag if multiple categories could apply, or labels conflict | Manual review |

### tasks.py Structure

```python
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
```

### Day 2 Exit Criteria
- [ ] `github_fetcher.py` fetches from all 5 repos successfully
- [ ] 180+ raw bugs saved to `data/bugs_raw.json`
- [ ] 80+ bugs have ground truth labels
- [ ] `tasks.py` complete with 3 task definitions
- [ ] Push to `sumit/env-data` branch

### Day 2 Sync with Inderpal (EOD, async message)
Report: "Fetched N bugs, labeled M. tasks.py done. Starting env.py tomorrow."
Ask: "Are graders ready? I'll need the function signatures to wire up env.py."

---

## DAY 3 - April 4: Environment Core Sprint

**Time Budget:** 7-8 hours
**Goal:** Complete env.py with full reset/step/state, finish ALL data labeling
**Branch:** `sumit/env-data`

### Tasks

| # | Task | Deliverable | Time | Priority |
|---|------|-------------|------|----------|
| 1 | Finish ground truth labeling | All 180 bugs labeled. Mark 10-15 as `is_ambiguous: true` | 2h | P0 |
| 2 | Create `data/contributors.json` | Map of 15-20 contributors with team assignments per repo | 1h | P0 |
| 3 | Implement `env.py` BugTriageEnv | Full environment class with reset(), step(), state() | 3.5h | P0 |
| 4 | Create mock graders for dev testing | Mock graders that return predictable scores for known inputs | 30 min | P1 |
| 5 | Smoke test env locally | Run through 10 episodes manually, verify observation/reward/done flow | 1h | P1 |

### env.py Implementation Details

```python
class BugTriageEnv:
    """OpenEnv-compliant Bug Triage RL Environment."""

    def __init__(self, data_path: str = "data/bugs_processed.json",
                 task_type: str = "all"):
        # Load dataset
        # Initialize episode counter
        # Set up graders + reward calculator
        # Shuffle dataset with seed for reproducibility

    def reset(self, task_id: str = None) -> BugTriageObservation:
        """Start new episode.

        - Pick next bug from dataset (sequential, wrapping)
        - If task_id specified, use that task; else cycle through all 3
        - Build BugTriageObservation with bug data
        - Store ground truth internally (hidden from agent)
        - Return observation
        """

    def step(self, action: BugTriageAction) -> tuple:
        """Agent makes one classification.

        - Validate action matches current task
        - Call appropriate grader: grade_criticality / grade_severity / grade_root_cause_assignee
        - Call RewardCalculator.compute(base_score, action, ground_truth)
        - Build info dict with ground truth (for analysis)
        - Episode ends after one step (done=True)
        - Return (next_observation, reward, done, info)
        """

    def state(self) -> dict:
        """Return current environment state.

        Returns:
            {
                "current_task_id": str,
                "current_bug_id": str,
                "episode_number": int,
                "step_count": int,
                "total_bugs": int,
                "tasks_available": ["task_criticality", "task_severity", "task_root_cause_assignee"]
            }
        """
```

### Mock Graders (for dev testing without Inderpal's code)

```python
# In env.py during development:
try:
    from src.graders import grade_criticality, grade_severity, grade_root_cause_assignee
    from src.reward import RewardCalculator
except ImportError:
    def grade_criticality(action, gt):
        return 1.0 if action.criticality == gt.criticality else 0.0
    def grade_severity(action, gt):
        return 1.0 if action.severity and action.severity.value == gt.severity.value else 0.5
    def grade_root_cause_assignee(action, gt):
        return 0.5
    class RewardCalculator:
        def compute(self, base_score, action, gt):
            from src.models import BugTriageReward
            return BugTriageReward(base_score=base_score, total=base_score)
```

### contributors.json Structure

```json
{
    "pytorch/pytorch": {
        "contributors": [
            {"name": "user1", "team": "autograd", "commits": 150},
            {"name": "user2", "team": "distributed", "commits": 120}
        ],
        "teams": ["autograd", "distributed", "jit", "quantization", "mobile"]
    },
    "django/django": {
        "contributors": [
            {"name": "user3", "team": "orm", "commits": 200}
        ],
        "teams": ["orm", "admin", "forms", "middleware", "security"]
    }
}
```

### Day 3 Exit Criteria
- [ ] `data/bugs_processed.json` has 180 bugs with complete ground truth
- [ ] `data/contributors.json` has team mappings for all 5 repos
- [ ] `env.py` passes: `env = BugTriageEnv(); obs = env.reset(); print(obs)`
- [ ] `env.step(action)` returns valid (obs, reward, done, info) tuple
- [ ] `env.state()` returns correct dict
- [ ] Push to `sumit/env-data` branch

### Day 3 Sync with Inderpal (15-min call or async)
Report: "env.py works with mock graders. 180 bugs labeled. Ready for integration."
Ask: "Can you share grader function signatures? Any changes to the contract?"
Plan: "Merging tomorrow morning. I'll be at my machine by 9 AM."

---

## DAY 4 - April 5: Integration Day

**Time Budget:** 8 hours
**Goal:** Merge both tracks, wire real graders into env, run end-to-end

### JOINT TASKS (with Inderpal, first 2 hours)

| # | Task | Time |
|---|------|------|
| 1 | Merge `sumit/env-data` into `main` | 20 min |
| 2 | Merge `inderpal/graders-inference` into `main` | 20 min |
| 3 | Resolve any conflicts (likely: `requirements.txt`, maybe `models.py`) | 20 min |
| 4 | Remove all mock implementations, wire real imports | 15 min |
| 5 | Smoke test: `python -c "from src.env import BugTriageEnv; env = BugTriageEnv(); obs = env.reset('task_criticality'); print(obs)"` | 15 min |
| 6 | Smoke test: `python inference.py` (short run, 5 bugs) | 30 min |

### SOLO TASKS (after integration) - 6 hours

| # | Task | Deliverable | Time | Priority |
|---|------|-------------|------|----------|
| 1 | Write `tests/test_env.py` | 15+ test cases covering reset(), step(), state(), edge cases, validation | 2.5h | P0 |
| 2 | Write `tests/test_graders.py` | 20+ test cases: exact match, partial credit, edge cases, determinism checks | 2h | P0 |
| 3 | Write `tests/test_inference.py` | 8+ test cases: stdout format, env var handling, graceful errors | 1h | P1 |
| 4 | Run full test suite: `pytest tests/ -v` | All tests green | 30 min | P0 |

### test_env.py Test Cases

```python
# Must test:
# 1. reset() returns BugTriageObservation with correct fields
# 2. reset("task_criticality") returns observation with task_id="task_criticality"
# 3. reset("task_severity") returns observation with task_id="task_severity"
# 4. reset("task_root_cause_assignee") returns observation with available_assignees populated
# 5. step() with correct action returns reward > 0
# 6. step() with wrong action returns reward = 0 or low
# 7. step() returns done=True (single-step episodes)
# 8. state() returns dict with all required keys
# 9. Episode counter increments on each reset()
# 10. Invalid action raises validation error (confidence > 1.0)
# 11. Mismatched task_id in action vs observation raises error
# 12. All 180 bugs can be iterated through
# 13. Reward is always in [0.0, 1.0]
# 14. info dict contains ground_truth
# 15. Reproducibility: same seed = same episode sequence
```

### test_graders.py Test Cases

```python
# Must test:
# 1. grade_criticality: correct = 1.0
# 2. grade_criticality: incorrect = 0.0
# 3. grade_severity: exact match = 1.0
# 4. grade_severity: off-by-one = 0.7
# 5. grade_severity: off-by-two = 0.4
# 6. grade_severity: off-by-three+ = 0.0
# 7. grade_root_cause_assignee: both correct = 1.0
# 8. grade_root_cause_assignee: root_cause correct, assignee wrong = 0.6*1.0 + 0.4*0.6 = 0.84
# 9. grade_root_cause_assignee: both wrong = 0.6*0.5 + 0.4*0.6 = 0.54
# 10. Confidence calibration: well-calibrated gets +0.08
# 11. Confidence calibration: overconfident gets -0.05
# 12. Reasoning bonus: good reasoning + correct = +0.05
# 13. Edge case bonus: ambiguous + perfect = +0.1
# 14. Total reward always clamped to [0.0, 1.0]
# 15. Determinism: same inputs always produce same output
# 16-20. Boundary conditions for each grader
```

### Day 4 Exit Criteria
- [ ] Both branches merged to `main` with no conflicts
- [ ] `python inference.py` runs end-to-end on real data with real graders
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No import errors, no type mismatches
- [ ] Docker builds: `docker build -t bugtriage .` (quick test)

### Day 4 Sync with Inderpal
Throughout the day - pair-debug integration issues as they come up.

---

## DAY 5 - April 6: Hardening + Validation

**Time Budget:** 7-8 hours
**Goal:** Bulletproof the environment, pass openenv validate, verify Docker

### Tasks

| # | Task | Deliverable | Time | Priority |
|---|------|-------------|------|----------|
| 1 | Data quality audit | Review all 180 bugs for labeling accuracy. Check distribution: ~30% critical vs 70% non-critical. Severity spread across all 5 levels. Root causes across all 6 categories. Fix any errors | 2h | P0 |
| 2 | Edge case verification | Verify 10-15 bugs have `is_ambiguous: true`. These enable the +0.1 edge case bonus. If too few, add more | 45 min | P0 |
| 3 | Harden env.py | Add error handling: malformed actions, missing fields, out-of-range values. Env must NEVER crash. Always return valid observation + reward, even on bad input | 2h | P0 |
| 4 | Performance profiling | Run full inference, measure wall-clock time. Target: < 15 min. If slow, profile and optimize (likely: data loading, prompt construction) | 1h | P1 |
| 5 | Run `openenv validate` | Fix any failures. Common issues: missing yaml fields, wrong method signatures, type mismatches | 1h | P0 |
| 6 | Increase test coverage | Add edge case tests. Target: >90% line coverage on env.py. Run `pytest --cov=src tests/` | 1h | P1 |
| 7 | Data distribution report | Print and verify: bugs per repo, criticality split, severity histogram, root cause distribution | 30 min | P2 |

### Data Distribution Targets

```
Criticality: ~55 critical (30%), ~125 non-critical (70%)
Severity:    ~15 level-1, ~30 level-2, ~55 level-3, ~50 level-4, ~30 level-5
Root Cause:  ~50 bug, ~30 design, ~25 environment, ~30 performance, ~20 documentation, ~25 external
Ambiguous:   10-15 bugs flagged
Repos:       Django 50, FastAPI 40, NumPy 35, PyTorch 30, CPython 25
```

### Day 5 Exit Criteria
- [ ] `openenv validate` passes
- [ ] Data distribution is balanced and verified
- [ ] env.py handles all edge cases without crashing
- [ ] Full inference completes in < 15 min
- [ ] Test coverage > 90% on core files
- [ ] Docker build + run verified locally

---

## DAY 6 - April 7: Polish + Cross-Review

**Time Budget:** 5-6 hours
**Goal:** Code cleanup, review Inderpal's code, verify everything works

### Tasks

| # | Task | Deliverable | Time | Priority |
|---|------|-------------|------|----------|
| 1 | Fix any test failures from Day 5 | All tests green | 1h | P0 |
| 2 | Data rebalancing (if needed) | Adjust bug counts per category if distribution is off | 1h | P1 |
| 3 | Final contributors.json review | Verify team mappings make sense for assignee partial credit | 30 min | P1 |
| 4 | Code cleanup | Remove debug prints, unused imports. Add docstrings to all public methods. Type hints everywhere | 1h | P1 |
| 5 | Cross-review Inderpal's code | Review `graders.py`, `reward.py`, `inference.py` for correctness. Check: grading formulas match spec, reward bonuses correct, stdout format matches requirement | 1.5h | P0 |
| 6 | Final full test run | `pytest tests/ -v --tb=long` - all green | 30 min | P0 |

### Code Review Checklist (for Inderpal's code)
- [ ] `grade_criticality()`: Returns exactly 1.0 or 0.0
- [ ] `grade_severity()`: Returns 1.0/0.7/0.4/0.0 based on distance
- [ ] `grade_root_cause_assignee()`: Weighted 60/40 correctly
- [ ] `RewardCalculator`: Confidence bonus thresholds correct (0.15, 0.3)
- [ ] `RewardCalculator`: Total clamped to [0.0, 1.0]
- [ ] `inference.py`: Uses `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN` env vars
- [ ] `inference.py`: Uses OpenAI client (not Anthropic)
- [ ] `inference.py`: Stdout format: `[START]`, `[STEP]`, `[END]` exactly as spec
- [ ] `inference.py`: Runs on all 3 tasks
- [ ] `inference.py`: Completes in < 20 min

### Day 6 Exit Criteria
- [ ] All code reviewed by both developers
- [ ] All tests pass
- [ ] No TODOs or debug code remaining
- [ ] Code is clean and documented

---

## DAY 7 - April 8: SUBMISSION DAY (Buffer)

**Time Budget:** 3-4 hours (morning only, submit by afternoon)
**Goal:** Final validation, submit with confidence

### Tasks

| # | Task | Deliverable | Time |
|---|------|-------------|------|
| 1 | Run `openenv validate` one final time | PASS | 15 min |
| 2 | Run full test suite | All green | 15 min |
| 3 | Run `docker build && docker run` locally | Works, output correct | 30 min |
| 4 | Verify HF Space is live | Responds to reset() | 15 min |
| 5 | Run `python inference.py` end-to-end | Completes < 20 min, scores documented | 20 min |
| 6 | Final submission checklist walkthrough (with Inderpal) | All items checked | 30 min |
| 7 | SUBMIT | Done before 6 PM (safe buffer) | -- |

### Pre-Submission Checklist (YOUR half)

- [ ] `data/bugs_processed.json` has 180 complete entries
- [ ] `data/contributors.json` has team mappings for all repos
- [ ] `env.py` reset/step/state all work correctly
- [ ] All tests pass (`pytest tests/ -v`)
- [ ] No import errors anywhere
- [ ] Ground truth labels are accurate
- [ ] Data distribution is balanced
- [ ] Edge case bugs are flagged

---

## EMERGENCY PROTOCOLS

### If GitHub API is rate-limited (Day 2)
1. Use a personal access token (5000 req/hr)
2. Cache all responses locally in `data/bugs_raw.json`
3. If still blocked: use a second GitHub account, or fall back to web scraping

### If not enough bugs from GitHub (Day 2-3)
1. Expand repos: add `huggingface/transformers`, `pallets/flask`, `psf/requests`
2. Lower quality bar: include issues without "bug" label but with clear bug descriptions
3. Last resort: generate 20-30 synthetic bugs using GPT-4, clearly mark them as synthetic

### If env.py integration fails (Day 4)
1. Check: are grader function signatures matching the contract?
2. Check: are Pydantic model fields matching between action and ground truth?
3. Check: is data schema matching what env.py expects?
4. Pair-debug with Inderpal for max 1 hour, then escalate

### If tests fail on Day 5+
1. Fix immediately - don't push broken tests
2. If grader logic is wrong: message Inderpal, he owns graders
3. If env logic is wrong: fix it yourself
4. If data is wrong: fix the specific entries, re-run labeling

### If we're behind schedule
- **Day 3 behind:** Cut data to 120 bugs (still sufficient). Skip contributors.json complexity
- **Day 4 behind:** Skip test_inference.py. Focus on test_env.py only
- **Day 5 behind:** Skip data audit. Focus on openenv validate + Docker
- **Day 6 behind:** Skip code cleanup. Submit what works

---

## KEY REMINDERS

1. **NEVER edit Inderpal's files.** Message him if something needs changing.
2. **Push to your branch daily.** Never have code only on your laptop.
3. **Mock graders exist for a reason.** Don't wait for Inderpal to test your env.
4. **180 bugs is the target, not the minimum.** If you have 150 quality bugs, that's fine.
5. **Ground truth accuracy > quantity.** 150 well-labeled bugs beats 200 sloppy ones.
6. **Test as you code.** Don't write 400 lines of env.py then test.
7. **The deadline is April 8 11:59 PM.** Submit by April 8 afternoon. No last-minute rushes.

---

**Last Updated:** April 2, 2026
**Status:** EXECUTE NOW
