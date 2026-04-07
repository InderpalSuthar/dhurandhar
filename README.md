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

**Meta/PyTorch OpenEnv Hackathon - Round 1 | Team Dhurandhar**

An OpenEnv-compliant reinforcement learning environment that trains and evaluates AI agents on real-world GitHub bug report triage. Built on real bug reports from popular open-source projects, Bug Triage Env turns the tedious, error-prone job of bug triage into a structured RL benchmark. The dataset is fully customizable — add your own repositories and run the data pipeline to generate a fresh dataset.

---

## The Problem

Open-source maintainers are drowning. A project like CPython or PyTorch receives hundreds of bug reports per week. Each one needs to be:

1. **Triaged for criticality** — Is this a production crash or a cosmetic issue?
2. **Scored for severity** — How urgently does this need attention?
3. **Categorized and assigned** — What's the root cause, and who should fix it?

This manual process takes experienced engineers hours per day. Mistakes are costly: a mis-triaged critical bug can sit unnoticed while a minor UI tweak gets escalated. Dhurandhar provides the training ground for agents that can do this automatically, accurately, and at scale.

## Why Dhurandhar is Different

| Feature                | Bug Triage Env                                                                                  | Typical Bug Classifiers           |
| ---------------------- | ----------------------------------------------------------------------------------------------- | --------------------------------- |
| **Real data**          | Real bugs from top repos (PyTorch, NumPy, Flask, etc.) — dataset size configurable               | Synthetic or single-repo datasets |
| **Multi-task**         | 3 tasks with increasing difficulty                                                              | Single classification task        |
| **Rich reward signal** | Base score + confidence calibration + reasoning quality + edge case bonuses                     | Binary correct/incorrect          |
| **Partial credit**     | Off-by-one severity, related root cause categories, same-team assignees all earn partial credit | Exact match only                  |
| **RL-native**          | OpenEnv-compliant reset/step API, works with any RL framework                                   | Static train/test splits          |
| **Any LLM backend**    | OpenAI, Groq, Ollama (local), or any OpenAI-compatible API                                      | Locked to one provider            |
| **Parallel inference** | Concurrent LLM calls with thread pool for fast evaluation                                       | Sequential only                   |

## Who Is This For?

- **RL Researchers** — A real-world, multi-task benchmark for language-agent training with a rich, multi-component reward signal
- **MLOps / DevOps Teams** — Evaluate LLMs on your actual triage workflow before deploying automation
- **Open-Source Maintainers** — Test how well AI can handle your bug triage backlog
- **AI Engineering Students** — A hands-on project that connects RL concepts to a tangible software engineering problem

---

## Tasks

### Task 1: Criticality Detection `easy`

Binary classification: is the bug **critical** (crash, data loss, security vulnerability, production outage) or **non_critical** (cosmetic, documentation, feature request, edge case)?

- **Grading:** 1.0 for correct, 0.0 for incorrect

### Task 2: Severity Scoring `medium`

5-point scale: Trivial (1) / Low (2) / Medium (3) / High (4) / Critical (5)

- **Grading:** 1.0 exact match, 0.7 off-by-1, 0.4 off-by-2, 0.0 off-by-3+

### Task 3: Root Cause + Assignee Recommendation `hard`

Identify the root cause category (bug / design / environment / performance / documentation / external) and recommend the best assignee from a list of real contributors.

- **Grading:** `(0.6 x root_cause_score) + (0.4 x assignee_score)`
- Root cause: 1.0 exact, 0.5 related category, 0.0 wrong
- Assignee: 1.0 exact match, 0.6 same team, 0.0 wrong

---

## Reward Function

The reward goes beyond simple accuracy. It encourages agents to be well-calibrated, thoughtful, and robust on ambiguous cases:

```
total = base_score + confidence_bonus + reasoning_bonus + edge_case_bonus
```

| Component              | Condition                                               | Bonus |
| ---------------------- | ------------------------------------------------------- | ----- |
| Confidence calibration | Confidence within 0.15 of actual accuracy               | +0.08 |
| Confidence calibration | Within 0.30                                             | +0.02 |
| Confidence calibration | Off by > 0.30                                           | -0.05 |
| Reasoning quality      | Detailed reasoning (>50 chars) on correct answer (>0.7) | +0.05 |
| Reasoning quality      | Long reasoning (>100 chars) on incorrect answer (<0.5)  | +0.02 |
| Edge case handling     | Correct on ambiguous bug                                | +0.10 |

Total reward is clamped to [0.0, 1.0].

---

## Dataset

Real bug reports fetched from the GitHub API. The default configuration includes 15 repositories (configurable via `src/keywords.py`):

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
| `ansible/ansible`           | 35   | DevOps / Automation   |
| `python/cpython`            | 30   | Language Runtime      |
| `pydantic/pydantic`         | 30   | Data Validation       |
| `scipy/scipy`               | 30   | Scientific Computing  |
| `aws/aws-cli`               | 30   | Cloud CLI             |

**225 real contributors** with team and expertise mappings for assignee evaluation.

Ground truth labels are generated using a keyword-based heuristic pipeline from issue metadata, labels, and content analysis.

### Root Cause Distribution

| Category      | Count | Percentage |
| ------------- | ----- | ---------- |
| Environment   | 287   | 54%        |
| Bug           | 167   | 32%        |
| Documentation | 45    | 8%         |
| Performance   | 16    | 3%         |
| Design        | 13    | 2%         |
| External      | 2     | <1%        |

---

## Quick Start

### Prerequisites

- Python 3.11+
- An LLM backend (Ollama for local, or an API key for Groq/OpenAI)

### Installation

```bash
git clone https://github.com/Inderpal004/dhurandhar.git
cd dhurandhar
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Configure your environment:

```bash
cp .env.example .env
# Edit .env with your API keys and preferred LLM provider
```

### Option A: Run Locally with Ollama (Free, No Rate Limits)

```bash
# Install Ollama (macOS)
brew install ollama

# Pull a model
ollama pull llama3.1:8b

# Start the server
ollama serve
```

Update `.env`:

```env
API_BASE_URL=http://localhost:11434/v1
MODEL_NAME=llama3.1:8b
OPENAI_API_KEY=ollama
```

```bash
python inference.py
```

### Option B: Run with Groq (Free Tier)

Sign up at [console.groq.com](https://console.groq.com) and get an API key.

```env
API_BASE_URL=https://api.groq.com/openai/v1
MODEL_NAME=llama-3.1-8b-instant
OPENAI_API_KEY=your_groq_api_key
```

> Note: Groq's free tier has rate limits (~30 req/min). The script automatically handles retries.

### Option C: Run with OpenAI (Pay-as-you-go)

```env
API_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
OPENAI_API_KEY=your_openai_api_key
```

> A full run costs approximately $0.06 with `gpt-4o-mini` (for the default dataset).

### Run Inference

```bash
python inference.py
```

Output is printed to stdout and automatically saved to `output.log`.

### Understanding the Output

The inference script produces a clean evaluation report. Each task shows a table of predictions vs ground truth:

```
================================================================================================
  BUG TRIAGE ENV — INFERENCE REPORT
  Team Dhurandhar
  Model: llama3.1:8b  |  Bugs: 35  |  Filter: all repos
================================================================================================

────────────────────────────────────────────────────────────────────────────────────────────────
  TASK: Criticality Detection
────────────────────────────────────────────────────────────────────────────────────────────────

  #     Bug ID                              Predicted              Expected               Score
  ───── ─────────────────────────────────── ────────────────────── ────────────────────── ──────
  1     pytorch/pytorch#176667              critical               non_critical            0.00 [-]
  2     pytorch/pytorch#179391              non_critical           non_critical            1.00 [+]
  3     pytorch/pytorch#179026              critical               critical                1.00 [+]

  Result: 0.657  |  23 correct  0 partial  12 wrong  (out of 35)
```

Scores are marked: `[+]` correct (>=0.8), `[~]` partial (>=0.5), `[-]` wrong (<0.5).

Each run ends with a summary table:

```
================================================================================================
  SUMMARY
================================================================================================
  Task                                   Score
  ─────────────────────────────────── ────────
  Criticality Detection                  0.657
  Severity Scoring                       0.782
  Root Cause + Assignee                  0.579
  ─────────────────────────────────── ────────
  OVERALL                                0.673
================================================================================================
  Completed in 8.9 minutes (5.1s per call)
================================================================================================
```

The `contributors.json` file provides team and expertise mappings — when the agent picks the wrong assignee but someone from the same team, it still earns partial credit (0.6 instead of 0.0).

### Customizing Repositories

By default, Bug Triage Env evaluates on 15 popular open-source repos. To use your own repositories:

**Step 1:** Add your repos to `src/keywords.py`:

```python
REPO_CONFIGS["your-org/your-repo"] = {"max_issues": 40}
```

**Step 2:** Set your GitHub token and run the data pipeline:

```bash
export GITHUB_TOKEN=your_token
python scripts/run_pipeline.py
```

This fetches real bug reports from your repos, auto-generates ground truth labels using keyword heuristics, builds contributor team/expertise mappings into `data/contributors.json`, and writes the processed dataset to `data/bugs_processed.json`.

**Step 3:** Run inference on your custom dataset:

```bash
python inference.py
```

The environment automatically picks up the new data. You can evaluate how well different LLMs triage bugs specific to your project.

### Docker

```bash
docker build -t bug-triage-env .
docker run --cpus=2 --memory=8g \
  -e API_BASE_URL="http://host.docker.internal:11434/v1" \
  -e MODEL_NAME="llama3.1:8b" \
  -e OPENAI_API_KEY="ollama" \
  bug-triage-env
```

---

## Environment Variables

| Variable         | Description                           | Default                     |
| ---------------- | ------------------------------------- | --------------------------- |
| `API_BASE_URL`   | LLM API endpoint                      | `http://localhost:11434/v1` |
| `MODEL_NAME`     | Model identifier                      | `llama3.1:8b`               |
| `OPENAI_API_KEY` | API key (or `ollama` for local)       | —                           |
| `NUM_WORKERS`    | Parallel LLM call threads             | `4`                         |
| `GITHUB_TOKEN`   | GitHub token (only for data pipeline) | —                           |
| `HF_TOKEN`       | HuggingFace token (for deployment)    | —                           |

---

## Action and Observation Spaces

### Observation (`BugTriageObservation`)

| Field                 | Type        | Description                                     |
| --------------------- | ----------- | ----------------------------------------------- |
| `task_id`             | `str`       | Which task to perform                           |
| `bug_report`          | `BugReport` | Title, body, labels, repo, author, comments     |
| `available_assignees` | `List[str]` | Candidate assignees (Task 3 only)               |
| `step`                | `int`       | Current step (always 0 at start)                |
| `max_steps`           | `int`       | Maximum steps (always 1 — single-step episodes) |
| `done`                | `bool`      | Whether episode is complete                     |

### Action (`BugTriageAction`)

| Field         | Type                                                                                   | Used In   |
| ------------- | -------------------------------------------------------------------------------------- | --------- |
| `criticality` | `"critical"` or `"non_critical"`                                                       | Task 1    |
| `severity`    | `1-5`                                                                                  | Task 2    |
| `root_cause`  | `"bug"`, `"design"`, `"environment"`, `"performance"`, `"documentation"`, `"external"` | Task 3    |
| `assignee`    | `str` (username)                                                                       | Task 3    |
| `confidence`  | `0.0-1.0`                                                                              | All tasks |
| `reasoning`   | `str`                                                                                  | All tasks |

---

## Scores

### Inference Baseline (zero-shot prompting via `inference.py`)

| Model | Criticality | Severity | Root Cause + Assignee | Overall |
| ----- | ----------- | -------- | --------------------- | ------- |
| `llama3.1:8b` (Ollama) | 0.657 | 0.782 | 0.579 | **0.673** |

### RL Training Results (fine-tuned via `train_rl.py`)

| Model | Task | Before | After | Change |
| ----- | ---- | ------ | ----- | ------ |
| `SmolLM2-135M-Instruct` | Criticality | 0.530 | 0.530 | +0.000 |

> The RL training pipeline uses GRPO with LoRA adapters. Larger models and more epochs yield better improvements — the 135M model serves as a minimal proof-of-concept that the training loop runs end-to-end. See `models/bug-triage-rl/training_report.json` for full results.

> The environment's multi-component reward signal (base score + confidence calibration + reasoning quality) provides a richer learning signal than binary accuracy, enabling RL agents to learn nuanced triage behavior.

---

## Architecture

```
dhurandhar/
├── src/
│   ├── models.py          # Pydantic data contracts (observations, actions, rewards)
│   ├── env.py             # BugTriageEnv — OpenEnv-compliant RL environment
│   ├── graders.py         # Task-specific grading functions with partial credit
│   ├── reward.py          # Multi-component reward calculator
│   ├── tasks.py           # Task definitions and metadata
│   ├── keywords.py        # Keyword taxonomy for ground truth labeling
│   ├── github_fetcher.py  # Data pipeline — fetches real bugs from GitHub API
│   └── utils.py           # Shared utilities
├── data/
│   ├── bugs_processed.json    # Labeled bug reports (generated by pipeline)
│   ├── bugs_raw.json          # Raw fetched data
│   └── contributors.json      # 225 contributors with team/expertise mappings
├── tests/
│   ├── test_env.py            # Environment tests
│   ├── test_graders.py        # Grader tests
│   ├── test_inference.py      # Inference pipeline tests
│   └── test_tasks_utils.py    # Task/utility tests
├── scripts/
│   ├── run_pipeline.py        # Full data pipeline runner
│   ├── generate_labels.py     # Ground truth label generation
│   └── check_token.py         # GitHub token validation
├── Assets/                    # Architecture diagrams (SVG + Mermaid)
├── inference.py               # Baseline inference with parallel LLM calls
├── train_rl.py                # RL training with PPO (fine-tunes LLM using env rewards)
├── openenv.yaml               # OpenEnv metadata
├── Dockerfile                 # Container deployment
├── requirements.txt           # Python dependencies
└── .env.example               # Environment variable template
```

### Data Flow

```
GitHub API  -->  github_fetcher.py  -->  bugs_raw.json
                                              |
                                    generate_labels.py
                                              |
                                     bugs_processed.json  -->  BugTriageEnv
                                                                    |
                                                          reset() / step()
                                                                    |
                                                          Agent (inference.py)
```

### RL Loop

```
Agent                           Environment
  |                                  |
  |  <-- observation (bug report) -- | reset()
  |                                  |
  |  -- action (classification) -->  | step()
  |                                  |
  |  <-- reward + done ------------- |
```

Each episode is a single step: the agent sees one bug report and makes one decision. The environment returns a reward based on correctness, confidence calibration, reasoning quality, and edge case handling.

---

## Refreshing the Dataset

To fetch fresh bug reports from GitHub (requires a GitHub personal access token):

```bash
export GITHUB_TOKEN=your_token
python scripts/run_pipeline.py
```

This pipeline:

1. Fetches the latest issues from all configured repositories via the GitHub REST API
2. Extracts comments, labels, and metadata for each bug report
3. Generates ground truth labels (criticality, severity, root cause) using keyword heuristics from `src/keywords.py`
4. Builds `data/contributors.json` — maps 225 contributors to teams and expertise areas, used for same-team partial credit in assignee scoring
5. Writes the final dataset to `data/bugs_processed.json`

---

## Running Tests

```bash
pytest tests/ -v
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Performance Optimization

The inference script supports parallel LLM calls for faster evaluation:

| Configuration                   | Time (per task, 35 bugs) | Notes                   |
| ------------------------------- | ------------------------ | ----------------------- |
| Ollama `llama3.1:8b`, 4 workers | ~3 min                   | Parallel, Apple Silicon |
| Groq `llama-3.1-8b-instant`     | ~1 min                   | Cloud API, rate limited |
| OpenAI `gpt-4o-mini`            | ~30s                     | Cloud API               |

Tune `NUM_WORKERS` in `.env` based on your hardware. For Apple Silicon Macs, 4-6 workers is a good starting point.

---

## RL Training with GRPO

### Why `train_rl.py` exists

`inference.py` uses a **pre-trained LLM as-is** — it classifies bugs through prompting alone. The model has never seen our specific labeling scheme, reward signals, or dataset. It's guessing based on general knowledge.

`train_rl.py` closes this gap. It uses **Group Relative Policy Optimization (GRPO)** to fine-tune a language model using the reward signals from BugTriageEnv. This is the core value proposition of the project:

```
                    inference.py (baseline)
                    ┌─────────────────────┐
Bug Report ──────> │  Pre-trained LLM     │ ──> Classification
                    │  (zero-shot)        │      (baseline score)
                    └─────────────────────┘

                    train_rl.py (RL-trained)
                    ┌─────────────────────┐
Bug Report ──────> │  Fine-tuned LLM      │ ──> Classification
                    │  (learned from       │      (improved score)
                    │   env rewards)       │
                    └─────────────────────┘
                           ▲
                           │ GRPO policy update
                           │
                    BugTriageEnv rewards
```

The environment teaches the model:

- Which bugs are actually critical vs non-critical in real-world projects
- How severity maps to specific patterns in bug reports
- Which root cause categories match which types of issues
- How to calibrate its own confidence (rewarded via confidence bonus)

### How it works

```
┌──────────┐    prompt     ┌──────────┐    action     ┌──────────────┐
│          │ ────────────> │          │ ────────────> │              │
│  Dataset │               │  Model   │               │ BugTriageEnv │
│  (bugs)  │               │  (LoRA)  │               │  (grader)    │
│          │ <──────────── │          │ <──────────── │              │
└──────────┘  GRPO update  └──────────┘    reward     └──────────────┘
```

Each training step:

1. Environment presents a bug report
2. Model generates multiple completions (GRPO's group sampling)
3. Environment grades each completion and returns rewards (0.0 - 1.0)
4. GRPO computes relative advantages within the group and updates model weights
5. Repeat — the model learns which triage patterns earn higher rewards

### Quick start

```bash
# Install training dependencies
pip install torch transformers trl peft accelerate

# Train on criticality detection (easiest task, fastest to see results)
python train_rl.py --task task_criticality --epochs 2

# Train on all tasks
python train_rl.py --task all --epochs 2

# Use a specific model
python train_rl.py --model HuggingFaceTB/SmolLM2-135M-Instruct

# Custom training parameters
python train_rl.py --task task_severity --epochs 3 --batch_size 4 --lr 1e-5
```

### Recommended models

| Model                                | Size | VRAM Needed | Best For                          |
| ------------------------------------ | ---- | ----------- | --------------------------------- |
| `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | 1.1B | ~4 GB       | Quick experiments, CPU/laptop     |
| `microsoft/phi-2`                    | 2.7B | ~8 GB       | Good balance of speed and quality |
| `meta-llama/Llama-3.2-3B-Instruct`   | 3B   | ~8 GB       | Best quality for small models     |
| `mistralai/Mistral-7B-Instruct-v0.3` | 7B   | ~16 GB      | High quality, needs GPU           |

### CLI options

| Flag               | Default                                    | Description                                     |
| ------------------ | ------------------------------------------ | ----------------------------------------------- |
| `--model`          | `TinyLlama/TinyLlama-1.1B-Chat-v1.0`       | HuggingFace model name                          |
| `--task`           | `all`                                      | Task to train on (`all` for all three)          |
| `--epochs`         | `2`                                        | Training epochs per task                        |
| `--batch_size`     | `4`                                        | Batch size per device                           |
| `--lr`             | `1e-5`                                     | Learning rate                                   |
| `--lora_r`         | `8`                                        | LoRA rank (higher = more capacity, more memory) |
| `--eval_episodes`  | `20`                                       | Episodes per evaluation run                     |
| `--num_samples`    | `100`                                      | Training samples per task                       |
| `--output_dir`     | `models/bug-triage-rl`                     | Where to save trained model                     |

### Training output

The script saves checkpoints and a JSON report:

| File                                        | Description                          |
| ------------------------------------------- | ------------------------------------ |
| `models/bug-triage-rl/<task>/`              | Per-task LoRA adapter checkpoints    |
| `models/bug-triage-rl/<task>_final/`        | Final model after all training       |
| `models/bug-triage-rl/training_report.json` | Full report with before/after scores |

### What the training demonstrates

1. The environment provides a **structured reward signal** compatible with standard RL training frameworks (TRL/GRPO)
2. The full pipeline works end-to-end: dataset loading, prompt formatting, reward calculation, and policy updates
3. The environment is a **valid RL benchmark** — agents can be trained and evaluated on the same reward function
4. LoRA adapters keep training lightweight — even a 135M parameter model can run on consumer hardware (Apple MPS)

The trained LoRA adapters are saved to `models/bug-triage-rl/` and can be loaded for inference or further training.

---

## Extending the Environment

### Adding a new task

1. Define the task in `src/tasks.py`
2. Add a grading function in `src/graders.py`
3. Add the action fields in `src/models.py`
4. Register it in `openenv.yaml`

### Using a different LLM

Any OpenAI-compatible API works. Just change `API_BASE_URL` and `MODEL_NAME` in `.env`. Tested with:

- Ollama (llama3.1, phi3, mistral, gemma2)
- Groq (llama-3.1-8b-instant)
- OpenAI (gpt-4o-mini, gpt-4o)
- Together AI, Cerebras, Google Gemini

---

## Built With

- [OpenEnv](https://github.com/pytorch/openenv) — RL environment standard
- [Pydantic](https://docs.pydantic.dev/) — Data validation and contracts
- [OpenAI Python SDK](https://github.com/openai/openai-python) — Universal LLM client
- [TRL](https://github.com/huggingface/trl) — PPO training for language models
- [PEFT](https://github.com/huggingface/peft) — Parameter-efficient fine-tuning (LoRA)
- [Ollama](https://ollama.com) — Local model inference
- [GitHub REST API](https://docs.github.com/en/rest) — Real bug report data

---

## Team

**Team Dhurandhar** — Built by **Sumit** and **Inderpal** for the Meta/PyTorch OpenEnv Hackathon.

---

## License

This project is released for the OpenEnv Hackathon. See the repository for license details.
