#!/usr/bin/env python3
"""Baseline inference script for Bug Report Triage environment.

Reads env vars: API_BASE_URL, MODEL_NAME, HF_TOKEN
Uses OpenAI client for all LLM calls.
Outputs structured [START], [STEP], [END] format to stdout.
"""

import os
import json
from openai import OpenAI
from src.env import BugTriageEnv
from src.models import BugTriageAction

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
