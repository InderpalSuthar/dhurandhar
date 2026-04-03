# Bug Report Triage - OpenEnv RL Environment

**Meta/PyTorch OpenEnv Hackathon - Round 1**
**Team Dhurandhar**

An OpenEnv-compliant reinforcement learning environment for training and evaluating autonomous agents on real-world GitHub bug report triage tasks.

## Overview

Bug triage is a critical but time-consuming task in software development. This environment presents agents with real GitHub bug reports and evaluates their ability to:

1. Detect whether a bug is critical (production impact) or non-critical
2. Assign an appropriate severity score on a 1-5 scale
3. Identify the root cause category and recommend the best assignee

The environment uses real bug reports fetched from popular open-source repositories, with ground truth labels for objective evaluation.

## Tasks

### Task 1: Criticality Detection (Easy)
Binary classification: is the bug **critical** (crash, data loss, security, outage) or **non_critical** (cosmetic, docs, enhancement)?

- **Grading:** 1.0 for correct, 0.0 for incorrect

### Task 2: Severity Scoring (Medium)
5-point scale: Trivial (1) / Low (2) / Medium (3) / High (4) / Critical (5)

- **Grading:** 1.0 exact match, 0.7 off-by-1, 0.4 off-by-2, 0.0 off-by-3+

### Task 3: Root Cause & Assignee (Hard)
Identify root cause category (bug/design/environment/performance/documentation/external) and recommend the best assignee from a list of contributors.

- **Grading:** (0.6 x root_cause_score) + (0.4 x assignee_score)
- Root cause: 1.0 exact, 0.5 related category, 0.0 wrong
- Assignee: 1.0 exact, 0.6 same team, 0.0 wrong

## Action & Observation Spaces

**Observation** (`BugTriageObservation`):
- `task_id` - which task to perform
- `bug_report` - title, body, labels, repo, author, comments
- `available_assignees` - list of contributors (Task 3)
- `step`, `max_steps`, `done`

**Action** (`BugTriageAction`):
- `criticality` - "critical" or "non_critical" (Task 1)
- `severity` - 1-5 (Task 2)
- `root_cause` - category string (Task 3)
- `assignee` - username (Task 3)
- `confidence` - 0.0-1.0
- `reasoning` - explanation string

## Reward Function

`total = base_score + confidence_bonus + reasoning_bonus + edge_case_bonus` (clamped to [0.0, 1.0])

| Component | Condition | Value |
|-----------|-----------|-------|
| Confidence bonus | Well calibrated (diff < 0.15) | +0.08 |
| Confidence bonus | Okay (diff < 0.3) | +0.02 |
| Confidence bonus | Poor (diff >= 0.3) | -0.05 |
| Reasoning bonus | Good explanation + correct (len > 50, score > 0.7) | +0.05 |
| Reasoning bonus | Attempted explanation + wrong (len > 100, score < 0.5) | +0.02 |
| Edge case bonus | Ambiguous bug, perfect score | +0.10 |

## Setup

### Local
```bash
pip install -r requirements.txt
cp .env.example .env  # Configure API keys
python inference.py
```

### Docker
```bash
docker build -t bugtriage .
docker run --cpus=2 --memory=8g \
  -e API_BASE_URL="your-api-url" \
  -e MODEL_NAME="gpt-4" \
  -e HF_TOKEN="your-token" \
  bugtriage
```

### Environment Variables
| Variable | Description |
|----------|-------------|
| `API_BASE_URL` | LLM API endpoint |
| `MODEL_NAME` | Model identifier |
| `HF_TOKEN` | HuggingFace token |

## Baseline Scores

| Task | Score |
|------|-------|
| Criticality Detection | TBD |
| Severity Scoring | TBD |
| Root Cause & Assignee | TBD |
| **Overall** | **TBD** |

## Architecture

```
dhurandhar/
├── src/
│   ├── models.py          # Shared Pydantic contract
│   ├── env.py             # BugTriageEnv (Sumit)
│   ├── graders.py         # 3 grader functions (Inderpal)
│   ├── reward.py          # RewardCalculator (Inderpal)
│   ├── tasks.py           # Task definitions (Sumit)
│   ├── github_fetcher.py  # Data pipeline (Sumit)
│   └── utils.py           # Utilities (Sumit)
├── data/                  # Processed bug data
├── tests/                 # Test suite
├── inference.py           # Baseline inference script
├── Dockerfile             # Container config
├── openenv.yaml           # OpenEnv metadata
└── requirements.txt       # Pinned dependencies
```

## Team
- **Sumit** - Environment Core, Data Pipeline, Tests
- **Inderpal** - Grading Engine, Inference, Deployment
