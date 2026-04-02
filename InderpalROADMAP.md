# INDERPAL's ROADMAP - Bug Report Triage RL Environment

**Role:** Grading Engine + Inference Script + Deployment
**Branch:** `inderpal/graders-inference`
**Deadline:** April 8, 2026 11:59 PM

---

## File Ownership

| File | Status |
|------|--------|
| `src/models.py` | Co-author (Day 1 JOINT) |
| `src/graders.py` | **SOLE OWNER** |
| `src/reward.py` | **SOLE OWNER** |
| `inference.py` | **SOLE OWNER** |
| `Dockerfile` | **SOLE OWNER** |
| `openenv.yaml` | **SOLE OWNER** |
| `requirements.txt` | **SOLE OWNER** (Sumit can suggest additions, you merge) |
| `README.md` | **SOLE OWNER** |

> **RULE:** Never edit Sumit's files (`env.py`, `tasks.py`, `github_fetcher.py`, `utils.py`, `data/*`, `tests/*`). If you find a bug in his code, message him. If you need a stub, write a mock in your own file.

---

## DAY 1 - April 2 (TODAY): Joint Setup + Models Contract

**Time Budget:** 5-6 hours
**Goal:** Lock down the shared interface so both tracks can work independently

### JOINT TASKS (with Sumit) - 2.5 hours

| # | Task | Deliverable | Time |
|---|------|-------------|------|
| 1 | Create repo structure | `mkdir -p src data tests` + all `__init__.py` files | 15 min |
| 2 | Write `src/models.py` together | Complete Pydantic models (see contract below) | 90 min |
| 3 | Write interface stubs | Stub files for `env.py`, `graders.py`, `reward.py`, `tasks.py` with `raise NotImplementedError` | 30 min |
| 4 | Agree on data schema | Exact JSON structure for `bugs_processed.json` | 15 min |
| 5 | Set up `requirements.txt` | Initial deps: `pydantic>=2.0`, `openai`, `requests`, `pytest`, `python-dotenv` | 10 min |
| 6 | Create feature branches | Push `models.py` to `main`, then branch to `inderpal/graders-inference` | 10 min |

### SOLO TASKS (your own) - 3 hours

| # | Task | Deliverable | Time |
|---|------|-------------|------|
| 1 | Implement `grade_criticality()` in `graders.py` | Binary grader: 1.0 if match, 0.0 if not. Fully tested manually | 45 min |
| 2 | Implement `grade_severity()` in `graders.py` | 5-point grader with partial credit: 1.0/0.7/0.4/0.0 | 45 min |
| 3 | Start `grade_root_cause_assignee()` | Scaffold the weighted grader (60% root cause, 40% assignee) | 45 min |
| 4 | Draft `openenv.yaml` skeleton | Basic metadata: name, version, author, task IDs | 30 min |
| 5 | Draft `requirements.txt` (final version) | Pin all deps with exact versions for reproducibility | 15 min |

### Models Contract (MUST AGREE WITH SUMIT)

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

### Day 1 Exit Criteria
- [ ] `python -c "from src.models import BugTriageObservation"` works
- [ ] Both branches created off `main`
- [ ] `grade_criticality()` and `grade_severity()` implemented and returning correct values
- [ ] `openenv.yaml` skeleton committed
- [ ] `requirements.txt` with pinned versions

---

## DAY 2 - April 3: Grading Engine Sprint

**Time Budget:** 7-8 hours
**Goal:** Complete ALL graders + reward calculator. This is your core deliverable.
**Branch:** `inderpal/graders-inference`

### Tasks

| # | Task | Deliverable | Time | Priority |
|---|------|-------------|------|----------|
| 1 | Complete `grade_root_cause_assignee()` | Weighted grader with partial credit for related categories and same-team assignees | 2h | P0 |
| 2 | Define related category mappings | Dict mapping each RootCauseCategory to "related" categories that earn 0.5 partial credit | 30 min | P0 |
| 3 | Define team-based assignee mappings | Dict mapping contributors to teams for 0.6 partial credit | 30 min | P0 |
| 4 | Implement `reward.py` RewardCalculator | Full reward function with all 4 components: base + confidence + reasoning + edge case | 2.5h | P0 |
| 5 | Manual unit testing for all graders | Test with 10+ synthetic inputs per grader, verify exact scores | 1h | P0 |
| 6 | Start `inference.py` skeleton | OpenAI client setup, env var reading, main loop shell | 1h | P1 |

### graders.py Full Implementation

```python
# src/graders.py

from src.models import BugTriageAction, BugGroundTruth, CriticalityLabel, RootCauseCategory

# ============================================================
# GRADER 1: Criticality Detection (EASY)
# ============================================================
def grade_criticality(action: BugTriageAction, ground_truth: BugGroundTruth) -> float:
    """Binary classification grader.

    Returns:
        1.0 if action.criticality matches ground_truth.criticality
        0.0 otherwise

    Example:
        action.criticality = "critical", gt.criticality = "critical" -> 1.0
        action.criticality = "critical", gt.criticality = "non_critical" -> 0.0
    """
    if action.criticality is None:
        return 0.0
    return 1.0 if action.criticality == ground_truth.criticality else 0.0


# ============================================================
# GRADER 2: Severity Scoring (MEDIUM)
# ============================================================
def grade_severity(action: BugTriageAction, ground_truth: BugGroundTruth) -> float:
    """5-point scale grader with partial credit.

    Returns:
        1.0 if exact match
        0.7 if off by 1
        0.4 if off by 2
        0.0 if off by 3+

    Example:
        predicted=4, actual=4 -> 1.0
        predicted=3, actual=4 -> 0.7
        predicted=2, actual=4 -> 0.4
        predicted=1, actual=4 -> 0.0
    """
    if action.severity is None:
        return 0.0
    diff = abs(action.severity.value - ground_truth.severity.value)
    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.7
    elif diff == 2:
        return 0.4
    else:
        return 0.0


# ============================================================
# GRADER 3: Root Cause + Assignee (HARD)
# ============================================================

# Related categories for partial credit (0.5 instead of 0.0)
RELATED_CATEGORIES = {
    RootCauseCategory.BUG: [RootCauseCategory.DESIGN],
    RootCauseCategory.DESIGN: [RootCauseCategory.BUG, RootCauseCategory.PERFORMANCE],
    RootCauseCategory.ENVIRONMENT: [RootCauseCategory.EXTERNAL],
    RootCauseCategory.PERFORMANCE: [RootCauseCategory.BUG, RootCauseCategory.DESIGN],
    RootCauseCategory.DOCUMENTATION: [],
    RootCauseCategory.EXTERNAL: [RootCauseCategory.ENVIRONMENT],
}

def grade_root_cause_assignee(
    action: BugTriageAction,
    ground_truth: BugGroundTruth,
    contributor_teams: dict = None
) -> float:
    """Weighted multi-criterion grader.

    Formula: (0.6 * root_cause_score) + (0.4 * assignee_score)

    Root cause scoring:
        1.0 = exact match
        0.5 = related category
        0.0 = completely wrong

    Assignee scoring:
        1.0 = exact match
        0.6 = same team
        0.0 = completely wrong
    """
    # Root cause score
    if action.root_cause is None:
        root_cause_score = 0.0
    elif action.root_cause == ground_truth.root_cause:
        root_cause_score = 1.0
    elif action.root_cause in RELATED_CATEGORIES.get(ground_truth.root_cause, []):
        root_cause_score = 0.5
    else:
        root_cause_score = 0.0

    # Assignee score
    if action.assignee is None or not action.assignee.strip():
        assignee_score = 0.0
    elif action.assignee.lower() == ground_truth.assignee.lower():
        assignee_score = 1.0
    elif contributor_teams and _same_team(action.assignee, ground_truth.assignee, contributor_teams):
        assignee_score = 0.6
    else:
        assignee_score = 0.0

    return (0.6 * root_cause_score) + (0.4 * assignee_score)


def _same_team(predicted: str, actual: str, contributor_teams: dict) -> bool:
    """Check if two contributors are on the same team."""
    predicted_team = contributor_teams.get(predicted.lower())
    actual_team = contributor_teams.get(actual.lower())
    if predicted_team and actual_team:
        return predicted_team == actual_team
    return False
```

### reward.py Full Implementation

```python
# src/reward.py

from src.models import BugTriageAction, BugGroundTruth, BugTriageReward

class RewardCalculator:
    """Computes sophisticated reward with bonuses beyond base grader score."""

    def compute(
        self,
        base_score: float,
        action: BugTriageAction,
        ground_truth: BugGroundTruth
    ) -> BugTriageReward:
        """
        Reward = base_score + confidence_bonus + reasoning_bonus + edge_case_bonus
        Clamped to [0.0, 1.0]
        """

        # 1. Confidence calibration bonus
        confidence_diff = abs(action.confidence - base_score)
        if confidence_diff < 0.15:
            confidence_bonus = 0.08   # Well calibrated
        elif confidence_diff < 0.3:
            confidence_bonus = 0.02   # Okay calibration
        else:
            confidence_bonus = -0.05  # Poorly calibrated

        # 2. Reasoning quality bonus
        reasoning_len = len(action.reasoning.strip())
        if reasoning_len > 50 and base_score > 0.7:
            reasoning_bonus = 0.05    # Good explanation for correct answer
        elif reasoning_len > 100 and base_score < 0.5:
            reasoning_bonus = 0.02    # Attempted explanation for wrong answer
        else:
            reasoning_bonus = 0.0

        # 3. Edge case bonus
        if ground_truth.is_ambiguous and base_score == 1.0:
            edge_case_bonus = 0.1     # Nailed a tricky case
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
```

### Day 2 Exit Criteria
- [ ] All 3 graders implemented and producing correct scores
- [ ] `RewardCalculator` computes all 4 bonus components correctly
- [ ] Total reward always in [0.0, 1.0]
- [ ] Related category mappings defined
- [ ] Team-based assignee mappings defined
- [ ] `inference.py` skeleton started
- [ ] Push to `inderpal/graders-inference` branch

### Day 2 Sync with Sumit (EOD, async message)
Report: "All 3 graders done. Reward calculator done. Starting inference.py tomorrow."
Ask: "How many bugs fetched? Any data schema changes?"

---

## DAY 3 - April 4: Inference + Deployment Prep Sprint

**Time Budget:** 7-8 hours
**Goal:** Complete inference.py with correct stdout format, Dockerfile ready
**Branch:** `inderpal/graders-inference`

### Tasks

| # | Task | Deliverable | Time | Priority |
|---|------|-------------|------|----------|
| 1 | Complete `inference.py` | Full baseline script using OpenAI client | 4h | P0 |
| 2 | Implement stdout format | `[START]`, `[STEP]`, `[END]` markers exactly as spec | 30 min | P0 |
| 3 | Write prompt templates for 3 tasks | System + user prompts with few-shot examples per task | 1.5h | P0 |
| 4 | Write `Dockerfile` | Python 3.11-slim, 2 vCPU / 8GB RAM compatible | 45 min | P1 |
| 5 | Complete `openenv.yaml` | All required fields filled | 30 min | P1 |
| 6 | Write mock env for testing | Synthetic BugTriageEnv that returns fake observations | 30 min | P1 |

### inference.py Full Implementation

```python
#!/usr/bin/env python3
"""Baseline inference script for Bug Report Triage environment.

Reads env vars: API_BASE_URL, MODEL_NAME, HF_TOKEN
Uses OpenAI client for all LLM calls.
Outputs structured [START], [STEP], [END] format to stdout.
"""

import os
import sys
import json
import time
from openai import OpenAI
from src.env import BugTriageEnv
from src.models import BugTriageAction, CriticalityLabel, SeverityLevel, RootCauseCategory

# ============================================================
# CONFIG FROM ENV VARS
# ============================================================
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or os.environ.get("OPENAI_API_KEY", ""),
)

# ============================================================
# PROMPT TEMPLATES
# ============================================================
CRITICALITY_SYSTEM_PROMPT = """You are a senior software engineer triaging bug reports.
Determine if this bug is CRITICAL or NON-CRITICAL.

CRITICAL means: system crash, data loss, security vulnerability, production outage, core feature broken.
NON-CRITICAL means: everything else (minor UI issue, docs, feature request, enhancement).

Respond with ONLY a JSON object:
{"classification": "critical" or "non_critical", "confidence": 0.0-1.0, "reasoning": "brief explanation"}"""

SEVERITY_SYSTEM_PROMPT = """You are a senior software engineer triaging bug reports.
Assign a severity score from 1-5:
5 = Critical (system down, data loss, security)
4 = High (major feature broken, hard workaround)
3 = Medium (feature partially broken, clear workaround)
2 = Low (minor issue, cosmetic, non-essential)
1 = Trivial (docs, typo, edge case)

Respond with ONLY a JSON object:
{"score": 1-5, "confidence": 0.0-1.0, "reasoning": "brief explanation"}"""

TRIAGE_SYSTEM_PROMPT = """You are a senior software engineer triaging bug reports.
1. Identify the root cause category: bug, design, environment, performance, documentation, external
2. Recommend the best assignee from the available list.

Root cause definitions:
- bug: code defect, logic error
- design: architectural issue, needs refactoring
- environment: dependency/config/version issue
- performance: optimization needed, memory leak
- documentation: misleading/missing docs
- external: third-party/upstream issue

Respond with ONLY a JSON object:
{"root_cause": "category", "assignee": "username", "confidence": 0.0-1.0, "reasoning": "brief explanation"}"""


# ============================================================
# INFERENCE FUNCTIONS
# ============================================================
def call_llm(system_prompt: str, user_prompt: str) -> dict:
    """Call LLM via OpenAI client and parse JSON response."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        content = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0]
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}


def run_task(env, task_id: str, num_episodes: int):
    """Run inference for one task across N episodes."""
    scores = []

    for ep in range(num_episodes):
        obs = env.reset(task_id=task_id)
        bug = obs.bug_report

        user_prompt = f"Title: {bug.title}\nDescription: {bug.body[:2000]}\nLabels: {', '.join(bug.labels)}"

        if task_id == "task_criticality":
            result = call_llm(CRITICALITY_SYSTEM_PROMPT, user_prompt)
            action = BugTriageAction(
                task_id=task_id,
                bug_id=bug.bug_id,
                criticality=result.get("classification", "non_critical"),
                confidence=float(result.get("confidence", 0.5)),
                reasoning=result.get("reasoning", ""),
            )
        elif task_id == "task_severity":
            result = call_llm(SEVERITY_SYSTEM_PROMPT, user_prompt)
            action = BugTriageAction(
                task_id=task_id,
                bug_id=bug.bug_id,
                severity=int(result.get("score", 3)),
                confidence=float(result.get("confidence", 0.5)),
                reasoning=result.get("reasoning", ""),
            )
        else:  # task_root_cause_assignee
            assignee_list = ", ".join(obs.available_assignees[:10])
            user_prompt += f"\n\nAvailable assignees: {assignee_list}"
            result = call_llm(TRIAGE_SYSTEM_PROMPT, user_prompt)
            action = BugTriageAction(
                task_id=task_id,
                bug_id=bug.bug_id,
                root_cause=result.get("root_cause", "bug"),
                assignee=result.get("assignee", obs.available_assignees[0] if obs.available_assignees else "unknown"),
                confidence=float(result.get("confidence", 0.5)),
                reasoning=result.get("reasoning", ""),
            )

        obs_next, reward, done, info = env.step(action)

        # STRUCTURED STDOUT - [STEP] format
        print(f"[STEP] step={ep+1} action={_format_action(action)} reward={reward.total:.2f} done={str(done).lower()} error=null")
        scores.append(reward.total)

    return scores


def _format_action(action):
    if action.criticality:
        return f"classify('{action.criticality.value}')"
    elif action.severity:
        return f"severity({action.severity.value})"
    else:
        return f"triage('{action.root_cause.value}','{action.assignee}')"


# ============================================================
# MAIN
# ============================================================
def main():
    env = BugTriageEnv()
    all_scores = []

    tasks = [
        ("task_criticality", 60),
        ("task_severity", 60),
        ("task_root_cause_assignee", 60),
    ]

    for task_id, num_episodes in tasks:
        # [START] format
        print(f"[START] task={task_id} env=bug-triage model={MODEL_NAME}")

        scores = run_task(env, task_id, num_episodes)
        all_scores.extend(scores)
        avg = sum(scores) / len(scores) if scores else 0.0

        # [END] format
        rewards_str = ",".join(f"{s:.2f}" for s in scores)
        print(f"[END] success=true steps={len(scores)} score={avg:.3f} rewards={rewards_str}")

    overall = sum(all_scores) / len(all_scores) if all_scores else 0.0
    print(f"\nOverall score: {overall:.3f}")


if __name__ == "__main__":
    main()
```

### Stdout Format Specification (MUST MATCH EXACTLY)

```
[START] task=task_criticality env=bug-triage model=gpt-4
[STEP] step=1 action=classify('critical') reward=1.00 done=true error=null
[STEP] step=2 action=classify('non_critical') reward=1.00 done=true error=null
...
[END] success=true steps=60 score=0.842 rewards=1.00,1.00,0.95,...

[START] task=task_severity env=bug-triage model=gpt-4
[STEP] step=1 action=severity(4) reward=1.00 done=true error=null
...
[END] success=true steps=60 score=0.710 rewards=1.00,0.70,1.00,...

[START] task=task_root_cause_assignee env=bug-triage model=gpt-4
[STEP] step=1 action=triage('bug','alice') reward=0.84 done=true error=null
...
[END] success=true steps=60 score=0.580 rewards=0.84,1.00,0.54,...
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Environment variables (set at runtime)
ENV API_BASE_URL=""
ENV MODEL_NAME=""
ENV HF_TOKEN=""

# Expose port for HF Spaces
EXPOSE 7860

# Default command
CMD ["python", "inference.py"]
```

### openenv.yaml

```yaml
name: bug-triage
version: "1.0"
description: "RL environment for automated GitHub bug report triage"
author: "Team Dhurandhar"

environment:
  entry_point: "src.env"
  class_name: "BugTriageEnv"
  
  observation_model: "src.models.BugTriageObservation"
  action_model: "src.models.BugTriageAction"
  reward_model: "src.models.BugTriageReward"

tasks:
  - id: "task_criticality"
    name: "Criticality Detection"
    difficulty: "easy"
    description: "Determine if a bug report is critical or non-critical"
    grader: "src.graders.grade_criticality"
    
  - id: "task_severity"
    name: "Severity Scoring"  
    difficulty: "medium"
    description: "Assign a severity score (1-5) to a bug report"
    grader: "src.graders.grade_severity"
    
  - id: "task_root_cause_assignee"
    name: "Root Cause & Assignee"
    difficulty: "hard"
    description: "Identify root cause category and recommend the best assignee"
    grader: "src.graders.grade_root_cause_assignee"

inference:
  script: "inference.py"
  env_vars:
    - API_BASE_URL
    - MODEL_NAME
    - HF_TOKEN

deployment:
  platform: "huggingface-spaces"
  docker: true
  tags:
    - "openenv"
```

### Mock Env (for testing inference.py without Sumit's code)

```python
# mock_env.py (temporary, delete after integration)
from src.models import *

class MockBugTriageEnv:
    def __init__(self):
        self.episode = 0

    def reset(self, task_id="task_criticality"):
        self.episode += 1
        return BugTriageObservation(
            task_id=task_id,
            bug_report=BugReport(
                bug_id=f"mock/repo#{self.episode}",
                title="Mock bug: App crashes on startup",
                body="When I click the button, the app crashes with a segfault...",
                labels=["bug", "critical"],
                created_at="2024-01-15T10:00:00Z",
                repo="mock/repo",
                author="mockuser",
            ),
            available_assignees=["alice", "bob", "charlie"],
            step=0,
            max_steps=1,
        )

    def step(self, action):
        reward = BugTriageReward(base_score=0.75, total=0.80)
        return None, reward, True, {"ground_truth": "mock"}

    def state(self):
        return {"episode": self.episode, "task": "mock"}
```

### Day 3 Exit Criteria
- [ ] `inference.py` runs end-to-end with mock env
- [ ] Stdout format matches spec exactly (`[START]`, `[STEP]`, `[END]`)
- [ ] All 3 task prompts produce parseable JSON from LLM
- [ ] `Dockerfile` builds locally: `docker build -t bugtriage .`
- [ ] `openenv.yaml` has all required fields
- [ ] Push to `inderpal/graders-inference` branch

### Day 3 Sync with Sumit (15-min call or async)
Report: "inference.py works with mock env. Docker builds. Ready for integration."
Ask: "Is env.py ready? How many bugs in the dataset?"
Plan: "Merging tomorrow morning. I'll be at my machine by 9 AM."

---

## DAY 4 - April 5: Integration Day

**Time Budget:** 8 hours
**Goal:** Merge both tracks, wire everything together, tune prompts

### JOINT TASKS (with Sumit, first 2 hours)

| # | Task | Time |
|---|------|------|
| 1 | Merge `inderpal/graders-inference` into `main` | 20 min |
| 2 | Merge `sumit/env-data` into `main` | 20 min |
| 3 | Resolve conflicts (likely: `requirements.txt`) | 20 min |
| 4 | Remove all mock implementations (mock env, mock graders) | 15 min |
| 5 | Smoke test: `python -c "from src.env import BugTriageEnv; env = BugTriageEnv(); obs = env.reset('task_criticality'); print(obs)"` | 15 min |
| 6 | Smoke test: `python inference.py` (short run, 5 bugs per task) | 30 min |

### SOLO TASKS (after integration) - 6 hours

| # | Task | Deliverable | Time | Priority |
|---|------|-------------|------|----------|
| 1 | Tune criticality prompt | Run on 20 bugs, measure accuracy. Iterate on prompt to improve. Target: > 80% accuracy | 1.5h | P0 |
| 2 | Tune severity prompt | Run on 20 bugs, measure accuracy. Add few-shot examples if needed. Target: > 65% accuracy | 1.5h | P0 |
| 3 | Tune root cause + assignee prompt | Run on 20 bugs. This is the hardest task. Target: > 50% accuracy | 1.5h | P0 |
| 4 | Optimize runtime | Ensure full inference (180 bugs x 3 tasks) completes in < 20 min. Add timeouts per LLM call (30s). Consider reducing to 50 bugs per task if needed | 1h | P0 |
| 5 | Write README.md | Complete documentation: env description, task definitions, action/observation spaces, setup instructions, Docker usage, baseline scores placeholder | 1h | P1 |

### Prompt Tuning Strategy

**Criticality (target: 80%+):**
- Keywords that signal critical: "crash", "segfault", "data loss", "security", "production", "outage", "broken"
- Keywords that signal non-critical: "feature request", "enhancement", "typo", "docs", "minor", "cosmetic"
- Add 2-3 few-shot examples if accuracy < 75%

**Severity (target: 65%+):**
- Biggest error: confusing 3 vs 4 (medium vs high)
- Add explicit criteria: "affects all users" = 4+, "workaround exists" = 3, "edge case" = 2
- Few-shot with borderline examples

**Root Cause + Assignee (target: 50%+):**
- Root cause: look for code paths mentioned, error types, stack traces
- Assignee: use available_assignees list, match expertise areas from bug content
- This task is genuinely hard - 50% is a good baseline

### README.md Structure

```markdown
# Bug Report Triage - OpenEnv RL Environment

## Overview
[2-3 paragraphs: what, why, real-world impact]

## Tasks
### Task 1: Criticality Detection (Easy)
### Task 2: Severity Scoring (Medium)  
### Task 3: Root Cause & Assignee (Hard)

## Action & Observation Spaces
[Pydantic model definitions]

## Reward Function
[Explanation of base + bonuses]

## Setup
### Local
### Docker
### Environment Variables

## Baseline Scores
[Table: task, accuracy, final score]

## Dataset
[Source repos, size, ground truth method]

## Architecture
[Project structure tree]
```

### Day 4 Exit Criteria
- [ ] `python inference.py` runs end-to-end with real data and real graders
- [ ] Baseline scores recorded for all 3 tasks
- [ ] Runtime < 20 min verified
- [ ] README.md complete
- [ ] No import errors, no crashes

---

## DAY 5 - April 6: Deployment + HF Spaces

**Time Budget:** 7-8 hours
**Goal:** Docker working under constraints, HF Space live and tagged

### Tasks

| # | Task | Deliverable | Time | Priority |
|---|------|-------------|------|----------|
| 1 | Docker resource-constrained test | `docker run --cpus=2 --memory=8g bugtriage python inference.py` - must complete successfully | 2h | P0 |
| 2 | Fix any Docker issues | Missing deps, path issues, env var passing | 1h | P0 |
| 3 | Create HF Space | New Space, tag "openenv", push Docker config | 1h | P0 |
| 4 | Configure HF Space secrets | Set API_BASE_URL, MODEL_NAME, HF_TOKEN in Space settings | 30 min | P0 |
| 5 | Verify HF Space is live | Space builds, responds to reset(), runs inference | 1h | P0 |
| 6 | Run `openenv validate` | Fix any validation failures | 1h | P0 |
| 7 | README: add baseline scores | Fill in actual scores from Day 4 runs | 30 min | P1 |
| 8 | `requirements.txt` final audit | Remove unused deps, pin all versions, verify clean install in fresh venv | 30 min | P1 |

### Docker Troubleshooting Checklist

| Issue | Fix |
|-------|-----|
| Module not found | Check COPY paths in Dockerfile, verify src/ is copied |
| API key not found | Pass env vars: `docker run -e API_BASE_URL=... -e MODEL_NAME=... -e HF_TOKEN=...` |
| Out of memory | Reduce batch size, process bugs sequentially |
| Timeout | Add per-call timeouts, reduce total bugs if needed |
| Port issues | Expose 7860, map with `-p 7860:7860` |

### HF Spaces Deployment Steps

1. Go to huggingface.co/new-space
2. Create Space named `bug-triage-env` (or `team-dhurandhar-bug-triage`)
3. Select "Docker" as SDK
4. Tag with "openenv"
5. Push code:
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/bug-triage-env
   git push hf main
   ```
6. Add secrets in Space settings:
   - `API_BASE_URL` = your API endpoint
   - `MODEL_NAME` = `gpt-4` (or whatever model)
   - `HF_TOKEN` = your HF token
7. Wait for build (3-5 min)
8. Check logs for errors
9. Test: ping Space URL, verify 200 response

### Day 5 Exit Criteria
- [ ] Docker builds and runs under 2 vCPU / 8GB constraint
- [ ] HF Space is live, tagged "openenv"
- [ ] HF Space responds to API calls
- [ ] `openenv validate` passes
- [ ] `requirements.txt` pinned and clean
- [ ] Baseline scores in README

---

## DAY 6 - April 7: Polish + Final Optimization

**Time Budget:** 5-6 hours
**Goal:** Maximize baseline scores, polish everything

### Tasks

| # | Task | Deliverable | Time | Priority |
|---|------|-------------|------|----------|
| 1 | Baseline optimization | Run full inference on all 180 bugs. Iterate prompts to maximize average score. Try: better few-shot examples, chain-of-thought, explicit rubric in prompt | 2.5h | P0 |
| 2 | Fix any HF Spaces issues | Ensure Space is stable, no timeouts, no crashes | 1h | P0 |
| 3 | Cross-review Sumit's code | Review `env.py`, `tasks.py`, data pipeline. Check: reset() produces clean state, step() validates actions, state() returns correct dict | 1h | P0 |
| 4 | Final README update | Add final baseline scores, polish writing, add badges | 30 min | P1 |
| 5 | Code cleanup in your files | Remove dead code, add docstrings, check type hints | 30 min | P1 |

### Code Review Checklist (for Sumit's code)
- [ ] `env.py` reset() returns valid BugTriageObservation for all 3 tasks
- [ ] `env.py` step() validates action.task_id matches current task
- [ ] `env.py` step() calls correct grader based on task
- [ ] `env.py` state() includes all required fields
- [ ] `data/bugs_processed.json` has 180 entries with valid ground truth
- [ ] `data/contributors.json` has team mappings
- [ ] No hardcoded paths (works in Docker container)
- [ ] No debug prints in production code

### Baseline Score Targets

| Task | Minimum | Target | Stretch |
|------|---------|--------|---------|
| Criticality | 0.75 | 0.82 | 0.88 |
| Severity | 0.60 | 0.71 | 0.78 |
| Root Cause + Assignee | 0.45 | 0.58 | 0.65 |
| Overall | 0.60 | 0.70 | 0.77 |

### Day 6 Exit Criteria
- [ ] Baseline scores optimized and documented
- [ ] All code reviewed by both developers
- [ ] HF Space stable
- [ ] README polished and complete
- [ ] No TODOs or debug code remaining

---

## DAY 7 - April 8: SUBMISSION DAY (Buffer)

**Time Budget:** 3-4 hours (morning only, submit by afternoon)
**Goal:** Final validation and submission

### Tasks

| # | Task | Deliverable | Time |
|---|------|-------------|------|
| 1 | Final Docker build + run test | Works under constraints | 30 min |
| 2 | Final HF Space check | Live, responding, no errors in logs | 15 min |
| 3 | Run `openenv validate` one last time | PASS | 15 min |
| 4 | Run `python inference.py` end-to-end | Completes, scores match documented values | 20 min |
| 5 | Final submission checklist (with Sumit) | All items checked | 30 min |
| 6 | SUBMIT | Before 6 PM (safe 6-hour buffer) | -- |

### Pre-Submission Checklist (YOUR half)

- [ ] `graders.py`: All 3 graders deterministic, scores 0.0-1.0
- [ ] `reward.py`: Bonuses correct, total clamped
- [ ] `inference.py`: Uses OpenAI client, correct env vars, stdout format matches
- [ ] `Dockerfile`: Builds, runs under resource constraints
- [ ] `openenv.yaml`: All fields present and correct
- [ ] `requirements.txt`: Pinned, clean, no unused deps
- [ ] `README.md`: Complete with setup, tasks, baseline scores
- [ ] HF Space: Live, tagged "openenv", responds to API calls
- [ ] Runtime: < 20 minutes for full inference

---

## EMERGENCY PROTOCOLS

### If LLM returns unparseable responses (Day 3-4)
1. Add robust JSON parsing with fallbacks
2. Strip markdown code fences before parsing
3. If JSON fails: regex extract key fields
4. Last resort: return default values (non_critical, severity=3, root_cause=bug)

### If Docker doesn't build (Day 5)
1. Check: are all source files being COPY'd?
2. Check: is requirements.txt complete?
3. Check: any OS-level deps needed? (unlikely for pure Python)
4. Simplify: use `python:3.11` instead of `python:3.11-slim`
5. Test locally first: `pip install -r requirements.txt` in clean venv

### If HF Space fails (Day 5)
1. Check Space logs in HF dashboard
2. Common issues: env vars not set, port not exposed, build timeout
3. Try: rebuild Space from scratch
4. Backup: submit Docker-only (without live Space), explain in README

### If inference is too slow (Day 4-5)
1. Reduce bugs per task: 60 -> 40 (120 total, still sufficient)
2. Add async LLM calls (parallel requests)
3. Reduce max_tokens: 200 -> 150
4. Use faster model: `gpt-4o-mini` instead of `gpt-4`
5. Add 30-second timeout per call, return defaults on timeout

### If baseline scores are too low (Day 6)
1. Don't panic - working submission > high scores
2. Try: add more few-shot examples (3-5 per task)
3. Try: add chain-of-thought ("Think step by step...")
4. Try: temperature 0.3 instead of 0.7 (more deterministic)
5. Submit what you have - scores are only 10% of grading

### If we're behind schedule
- **Day 3 behind:** Simplify Dockerfile (no multi-stage). Skip openenv.yaml polish
- **Day 4 behind:** Skip prompt tuning. Use default prompts. Focus on integration
- **Day 5 behind:** Skip HF Space (deploy Day 7 morning). Focus on Docker + validate
- **Day 6 behind:** Skip code review. Submit what works. README can be minimal

---

## KEY REMINDERS

1. **NEVER edit Sumit's files.** Message him if something needs changing.
2. **Push to your branch daily.** Never have code only on your laptop.
3. **Mock env exists for a reason.** Don't wait for Sumit to test inference.py.
4. **Stdout format is SACRED.** `[START]`, `[STEP]`, `[END]` must be exact. Any deviation = incorrect evaluation scoring.
5. **OpenAI client is MANDATORY.** No Anthropic SDK, no raw HTTP. Must use `from openai import OpenAI`.
6. **Env vars are MANDATORY.** `API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN` must be read from environment.
7. **Runtime < 20 min.** Test this repeatedly. Add timeouts.
8. **Docker must work on 2 vCPU / 8GB.** Test with `--cpus=2 --memory=8g`.
9. **The deadline is April 8 11:59 PM.** Submit by April 8 afternoon. NO LAST-MINUTE RUSHES.

---

**Last Updated:** April 2, 2026
**Status:** EXECUTE NOW
