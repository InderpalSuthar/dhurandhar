---
title: Bug Triage Env
emoji: "\U0001F41E"
colorFrom: gray
colorTo: yellow
sdk: docker
pinned: false
short_description: "@openenv"
---

# Bug Triage Env

**Meta/PyTorch OpenEnv Hackathon — Round 1 | Team Dhurandhar**

An OpenEnv-compliant RL environment for training and evaluating AI agents on real-world GitHub bug report triage. Agents learn to classify bugs across 3 tasks of increasing difficulty using 530 real bug reports from 15 popular open-source repositories.

---

## Quick Evaluation (For Judges)

### Requirements

- Python 3.11+
- A HuggingFace token with **"Make calls to Inference Providers"** permission
  - Get one at: `huggingface.co/settings/tokens` (fine-grained token)

### Setup

```bash
git clone https://github.com/Inderpal004/dhurandhar.git
cd dhurandhar
pip install -r requirements.txt
```

### Security & Environment Variables

For local development, create a `.env` file. For **Hugging Face Spaces**, use **Secrets** in the settings menu to store your `HF_TOKEN`.

```env
HF_TOKEN=hf_your_token_here
API_BASE_URL=https://router.huggingface.co/v1
MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
```

### Run Inference

```bash
# Default — 15 episodes per task, all repos
python inference.py

# Specific repos only
python inference.py --repos "pytorch/pytorch,pallets/flask"

# Custom episode count + specific repos
python inference.py --episodes 10 --repos "pytorch/pytorch,pallets/flask"

# Advanced visibility (Expert Mode)
python inference.py --verbose --show-gt --show-details
```

**Advanced Inference Flags:**

| Flag             | Description                                                   |
| ---------------- | ------------------------------------------------------------- |
| `--verbose`      | Shows the full **Mind of the AI** reasoning for every bug.    |
| `--show-gt`      | Displays the **Ground Truth** (correct answer) for comparison. |
| `--show-details` | Shows the detailed **Reward Breakdown** (bonuses/penalties).  |

**Why the defaults are safe for the 20-minute limit:**

| Factor                                 | Value        |
| -------------------------------------- | ------------ |
| Episodes per task                      | 15           |
| Tasks                                  | 3            |
| Total LLM calls                        | 45           |
| Avg time per call (4 parallel workers) | 5–10s        |
| Estimated runtime                      | ~3–4 minutes |
| Buffer before 20-min kill switch       | 15+ minutes  |

Use `--repos` to filter to specific repositories and `--episodes` to reduce the number of bugs evaluated per task.

Expected output format:

```
[START] task=task_criticality env=bug-triage model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=classify('critical') reward=1.00 done=true error=null
[END] success=true steps=1 score=1.000 rewards=1.00
[START] task=task_criticality env=bug-triage model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=classify('non_critical') reward=0.00 done=false error=null
[END] success=false steps=1 score=0.000 rewards=0.00
...
```

### Run Tests

```bash
pytest tests/ -v
```

### Validate OpenEnv Compliance

```bash
openenv validate
```

### Docker Build

```bash
docker build -t bug-triage-env .
docker run \
  -e HF_TOKEN=hf_your_token \
  -e API_BASE_URL=https://router.huggingface.co/v1 \
  -e MODEL_NAME=Qwen/Qwen2.5-72B-Instruct \
  bug-triage-env
```

---

## The Problem

Open-source maintainers are drowning in bug reports. A project like PyTorch or CPython receives hundreds of issues per week. Each needs to be:

1. **Triaged for criticality** — Is this a production crash or a cosmetic issue?
2. **Scored for severity** — How urgently does this need attention?
3. **Categorized and assigned** — What is the root cause, and who should fix it?

This manual process takes experienced engineers hours per day. Bug Triage Env provides the training ground for agents that can do this automatically, accurately, and at scale.

---

## Tasks

| #   | Task                  | Difficulty | Description                                         |
| --- | --------------------- | ---------- | --------------------------------------------------- |
| 1   | Criticality Detection | Easy       | Binary: `critical` or `non_critical`                |
| 2   | Severity Scoring      | Medium     | 5-point scale: 1 (trivial) to 5 (crash/outage)      |
| 3   | Root Cause + Assignee | Hard       | Category + pick best assignee from contributor list |

### Grading

**Task 1 — Criticality**

- 1.0 correct, 0.0 wrong

**Task 2 — Severity**

- 1.0 exact, 0.7 off-by-1, 0.4 off-by-2, 0.0 off-by-3+

**Task 3 — Root Cause + Assignee**

- `(0.6 × root_cause_score) + (0.4 × assignee_score)`
- Root cause: 1.0 exact, 0.5 related category, 0.0 wrong
- Assignee: 1.0 exact, 0.6 same team, 0.0 wrong

---

## Reward Function

Rewards go beyond accuracy. Agents are rewarded for calibrated confidence and quality reasoning:

```
total = base_score + confidence_bonus + reasoning_bonus + edge_case_bonus
```

| Component              | Condition                            | Bonus |
| ---------------------- | ------------------------------------ | ----- |
| Confidence calibration | Within 0.15 of actual accuracy       | +0.08 |
| Confidence calibration | Within 0.30                          | +0.02 |
| Confidence calibration | Off by > 0.30                        | -0.05 |
| Reasoning quality      | Detailed reasoning on correct answer | +0.05 |
| Reasoning quality      | Long reasoning on incorrect answer   | +0.02 |
| Edge case handling     | Correct on ambiguous bug             | +0.10 |

Total reward clamped to [0.0, 1.0].

---

## Dataset

530 real bug reports fetched from the GitHub API across 15 repositories:

| Repository                  | Bugs | Domain                |
| --------------------------- | ---- | --------------------- |
| `tiangolo/fastapi`          | 45   | Web Framework         |
| `numpy/numpy`               | 40   | Scientific Computing  |
| `pandas-dev/pandas`         | 40   | Data Analysis         |
| `huggingface/transformers`  | 40   | Machine Learning      |
| `pytorch/pytorch`           | 35   | Deep Learning         |
| `pallets/flask`             | 35   | Web Framework         |
| `scikit-learn/scikit-learn` | 35   | Machine Learning      |
| `matplotlib/matplotlib`     | 35   | Visualization         |
| `home-assistant/core`       | 35   | IoT / Home Automation |
| `google/jax`                | 35   | Scientific Computing  |
| `ansible/ansible`           | 35   | DevOps                |
| `python/cpython`            | 30   | Language Runtime      |
| `pydantic/pydantic`         | 30   | Data Validation       |
| `scipy/scipy`               | 30   | Scientific Computing  |
| `aws/aws-cli`               | 30   | Cloud CLI             |

225 real contributors with team and expertise mappings used for partial-credit assignee scoring.

**Root Cause Distribution:**

| Category      | Count | %   |
| ------------- | ----- | --- |
| Environment   | 301   | 57% |
| Bug           | 154   | 29% |
| Documentation | 41    | 8%  |
| Performance   | 19    | 4%  |
| Design        | 13    | 2%  |
| External      | 2     | <1% |

---

## Environment API

```python
from src.env import BugTriageEnv

env = BugTriageEnv()

# Reset starts a new episode
obs = env.reset(task_id="task_criticality")
print(obs.bug_report.title)
print(obs.bug_report.body)

# Step with an action
from src.models import BugTriageAction
action = BugTriageAction(
    task_id="task_criticality",
    bug_id=obs.bug_report.bug_id,
    criticality="critical",
    confidence=0.9,
    reasoning="Contains segfault in title",
)
obs, reward, done, info = env.step(action)
print(f"Reward: {reward}")  # 0.0 to 1.0
```

### Observation Fields

| Field                 | Type        | Description                         |
| --------------------- | ----------- | ----------------------------------- |
| `task_id`             | `str`       | Active task                         |
| `bug_report`          | `BugReport` | Title, body, labels, repo, comments |
| `available_assignees` | `List[str]` | Candidate assignees (Task 3 only)   |
| `done`                | `bool`      | Episode complete flag               |

### Action Fields

| Field         | Type                                                                                   | Tasks  |
| ------------- | -------------------------------------------------------------------------------------- | ------ |
| `criticality` | `"critical"` or `"non_critical"`                                                       | Task 1 |
| `severity`    | `1–5`                                                                                  | Task 2 |
| `root_cause`  | `"bug"`, `"environment"`, `"design"`, `"performance"`, `"documentation"`, `"external"` | Task 3 |
| `assignee`    | `str`                                                                                  | Task 3 |
| `confidence`  | `0.0–1.0`                                                                              | All    |
| `reasoning`   | `str`                                                                                  | All    |

---

## Environment Variables

| Variable       | Description                       | Default                            |
| -------------- | --------------------------------- | ---------------------------------- |
| `HF_TOKEN`     | HuggingFace token for inference   | —                                  |
| `API_BASE_URL` | LLM API endpoint                  | `https://router.huggingface.co/v1` |
| `MODEL_NAME`   | Model identifier                  | `Qwen/Qwen2.5-72B-Instruct`        |
| `NUM_WORKERS`  | Parallel LLM threads              | `4`                                |
| `GITHUB_TOKEN` | GitHub token (data pipeline only) | —                                  |

---

## Project Structure

```
dhurandhar/
├── inference.py               # Baseline inference — produces [START]/[STEP]/[END] logs
├── train_rl.py                # RL training with GRPO + LoRA
├── openenv.yaml               # OpenEnv spec
├── Dockerfile
├── requirements.txt
├── src/
│   ├── env.py                 # BugTriageEnv — reset/step/state
│   ├── models.py              # Pydantic: Action, Observation, Reward, GroundTruth
│   ├── graders.py             # Task graders with partial credit logic
│   ├── reward.py              # Multi-component reward calculator
│   ├── tasks.py               # Task definitions
│   ├── keywords.py            # Keyword taxonomy + repo config
│   └── github_fetcher.py      # Data pipeline (GitHub REST API)
├── data/
│   ├── bugs_processed.json    # 530 labeled bug reports
│   ├── bugs_raw.json          # Raw GitHub API responses
│   └── contributors.json      # 225 contributors with expertise mappings
└── tests/
    ├── test_env.py
    ├── test_graders.py
    ├── test_inference.py
    └── test_tasks_utils.py
```

---

## RL Training

`train_rl.py` fine-tunes a language model using GRPO on the environment's reward signal. This is the core demonstration that Bug Triage Env is a functional RL benchmark — not just an evaluation harness.

```bash
# Train on the easiest task
python train_rl.py --task task_criticality --epochs 2

# Train all tasks
python train_rl.py --task all --epochs 2

# Custom model
python train_rl.py --model HuggingFaceTB/SmolLM2-135M-Instruct
```

The training loop:

1. Environment presents a bug report
2. Model generates multiple completions (GRPO group sampling)
3. Environment grades each completion → reward (0.0–1.0)
4. GRPO updates model weights based on relative advantages
5. Repeat

LoRA adapters are saved to `models/bug-triage-rl/`.

---

## Refreshing the Dataset

To fetch fresh bugs from GitHub:

```bash
export GITHUB_TOKEN=your_token
python -m src.github_fetcher
```

### Customizing Repositories

All repo configuration lives in `src/keywords.py`. Open it and edit `REPO_CONFIGS`:

```python
# src/keywords.py

REPO_CONFIGS: Dict[str, dict] = {
    "pytorch/pytorch":        {"max_issues": 35},
    "pallets/flask":          {"max_issues": 35},
    # Add your own repo:
    "your-org/your-repo":     {"max_issues": 40},
    # Remove any repo by commenting it out or deleting the line
}
```

- `max_issues` controls how many bugs to fetch per repo (fetcher pulls `max_issues × 5` raw issues, then filters for real bugs)
- Any public GitHub repo works
- After editing, re-run the data pipeline to regenerate the dataset:

```bash
export GITHUB_TOKEN=your_token
python -m src.github_fetcher
```

### Customizing Keywords

`src/keywords.py` also controls how ground-truth labels are generated. You can tune the keyword lists to match your domain:

**`CRITICAL_KEYWORDS`** — words that mark a bug as critical:

```python
CRITICAL_KEYWORDS: FrozenSet[str] = frozenset([
    "crash", "segfault", "data loss", "security", "deadlock",
    # add your own:
    "your-critical-keyword",
])
```

**`SEVERITY_LABEL_MAP`** — maps severity levels (1–5) to keywords:

```python
SEVERITY_LABEL_MAP: Dict[int, FrozenSet[str]] = {
    5: frozenset(["p0", "blocker", "critical", "crash"]),
    4: frozenset(["p1", "high", "regression"]),
    3: frozenset(["p2", "medium", "normal"]),
    2: frozenset(["p3", "low", "minor"]),
    1: frozenset(["trivial", "typo", "docs"]),
}
```

**`ROOT_CAUSE_KEYWORDS`** — maps root cause categories to keywords:

```python
ROOT_CAUSE_KEYWORDS: Dict[str, List[str]] = {
    "bug":           ["crash", "error", "wrong", "incorrect"],
    "environment":   ["config", "install", "platform", "version"],
    "performance":   ["slow", "memory", "leak", "timeout"],
    "design":        ["refactor", "api", "interface"],
    "documentation": ["doc", "typo", "readme"],
    "external":      ["upstream", "dependency"],
}
```

**`TEAM_MAP`** — maps repos to team area tags (used to build contributor expertise profiles):

```python
TEAM_MAP: Dict[str, List[str]] = {
    "pytorch/pytorch": ["autograd", "distributed", "jit", "cuda"],
    "your-org/your-repo": ["frontend", "backend", "infra"],
}
```

After changing any keyword list, re-run the pipeline to regenerate ground truth labels with the new taxonomy:

```bash
python -m src.github_fetcher
```

---

## Built With

- [OpenEnv](https://github.com/pytorch/openenv) — RL environment standard by Meta/HuggingFace
- [Pydantic](https://docs.pydantic.dev/) — Data contracts
- [OpenAI Python SDK](https://github.com/openai/openai-python) — Universal LLM client
- [TRL](https://github.com/huggingface/trl) — GRPO training
- [PEFT](https://github.com/huggingface/peft) — LoRA fine-tuning
- [GitHub REST API](https://docs.github.com/en/rest) — Real bug data

---

## Team

**Team Dhurandhar** — Built by **Sumit** and **Inderpal** for the Meta/PyTorch OpenEnv Hackathon.
