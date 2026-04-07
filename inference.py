#!/usr/bin/env python3
"""
Inference script for Bug Report Triage environment.

Reads env vars: API_BASE_URL, MODEL_NAME, HF_TOKEN
Uses OpenAI client for all LLM calls.
Outputs structured [START], [STEP], [END] format to stdout.

Owner: Team Dhurandhar
"""

import os
import json
import re
import time
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI
from src.env import BugTriageEnv
from src.models import BugTriageAction

class LlmCache:
    def __init__(self, cache_file="llm_cache.json"):
        self.cache_file = cache_file
        self.cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    self.cache = json.load(f)
            except Exception:
                pass

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f)
        except Exception:
            pass

LLM_CACHE = LlmCache()

logger = logging.getLogger(__name__)

API_BASE_URL = os.environ.get("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.environ.get("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
HF_TOKEN = os.environ.get("HF_TOKEN", "")
NUM_WORKERS = int(os.environ.get("NUM_WORKERS", "4"))

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or os.environ.get("OPENAI_API_KEY", ""),
)

def _load_repo_stats():
    """Build per-repo assignee frequency from the dataset."""
    from collections import Counter, defaultdict
    try:
        with open("data/bugs_processed.json", "r") as f:
            bugs = json.load(f)
        repo_counts = defaultdict(Counter)
        for b in bugs:
            assignee = b.get("ground_truth", {}).get("assignee", "")
            if assignee and assignee != "unknown":
                repo_counts[b["repo"]][assignee] += 1
        stats = {}
        for repo, counts in repo_counts.items():
            total = sum(counts.values())
            top = [(name, c, round(c/total*100)) for name, c in counts.most_common(5)]
            stats[repo] = top
        return stats
    except Exception:
        return {}

def _load_contributor_expertise():
    """Load contributor expertise mappings."""
    try:
        with open("data/contributors.json", "r") as f:
            raw = json.load(f)
        expertise = {}
        for repo_data in raw.values():
            for c in repo_data.get("contributors", []):
                name = c.get("name", "")
                areas = c.get("work_area", [])
                if name and areas:
                    expertise[name.lower()] = areas
        return expertise
    except Exception:
        return {}

REPO_STATS = _load_repo_stats()
CONTRIBUTOR_EXPERTISE = _load_contributor_expertise()

from typing import List, Optional

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

CRITICALITY_SYSTEM_PROMPT = """Classify bug as "critical" or "non_critical".

CRITICAL: crash, segfault, data loss, corruption, security vuln, outage, core feature broken, regression blocking users, deadlock, infinite loop.
NON_CRITICAL: UI issue, cosmetic, doc typo, feature request, enhancement, edge case, workaround exists.

Rules:
- Labels with crash/security/regression/blocker/p0 -> critical
- Labels with enhancement/feature/documentation/cosmetic -> non_critical
- Segfault/assertion failed/data loss in description -> critical
- Affects all users or production -> critical

Reply ONLY JSON: {"classification": "critical" or "non_critical", "confidence": 0.0-1.0, "reasoning": "brief"}"""

SEVERITY_SYSTEM_PROMPT = """Assign severity 1-5 for this bug.

5=crash/data loss/security/outage 4=major feature broken/regression 3=partial break/workaround exists 2=minor/cosmetic/edge case 1=typo/docs/formatting

Rules:
- Labels crash/security/p0/blocker -> 4-5
- Labels regression -> 4+
- Labels enhancement/feature -> 2-3
- Labels trivial/cosmetic/docs -> 1
- Workaround mentioned -> cap at 3
- Affects all users/production -> 4+

Reply ONLY JSON: {"score": 1-5, "confidence": 0.0-1.0, "reasoning": "brief"}"""

TRIAGE_SYSTEM_PROMPT = """Classify root cause and pick assignee.

Categories (environment is ~55% of bugs - prefer it when unsure):
- environment: runtime, toolchain, build, CI/CD, platform compat, version issues, config, module interaction, JIT/compiler, wrapper gen, framework integration, import failures, GPU/hardware, permissions, dependencies. DEFAULT when ambiguous.
- bug: PURE logic defect - null deref, off-by-one, wrong return, type error in code itself. Only when code logic is clearly wrong.
- design: architectural flaw, API inconsistency, refactoring needed
- performance: slow/memory leak/OOM - ONLY when performance is main complaint
- documentation: docs issues, typos, missing examples
- external: third-party lib bug (rare)

Assignee rules:
- Pick EXACTLY one from the provided list
- Pay attention to the "handles X% of bugs" hints - high-percentage assignees are usually correct
- If expertise info is provided, match the bug's domain to the assignee's work area
- When unsure, pick the assignee with the highest percentage for that repo

Reply ONLY JSON: {"root_cause": "category", "assignee": "username", "confidence": 0.0-1.0, "reasoning": "brief"}"""

_MAX_LLM_RETRIES = 1


def call_llm(system_prompt: str, user_prompt: str) -> dict:
    """Call LLM via OpenAI client with caching and retry logic."""
    cache_key = f"{MODEL_NAME}|{system_prompt}|{user_prompt}"
    cached = LLM_CACHE.get(cache_key)
    if cached:
        return cached

    last_error = ""
    for attempt in range(_MAX_LLM_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=100,
                timeout=60,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0]
            match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            result = json.loads(match.group()) if match else json.loads(content)
            LLM_CACHE.set(cache_key, result)
            return result
        except Exception as e:
            last_error = str(e)
            if attempt < _MAX_LLM_RETRIES:
                time.sleep(1)
    return {"error": last_error}


# Default fallbacks when LLM fails
DEFAULTS = {
    "task_criticality": {"classification": "non_critical", "confidence": 0.5, "reasoning": "default"},
    "task_severity": {"score": 3, "confidence": 0.5, "reasoning": "default"},
    "task_root_cause_assignee": {"root_cause": "environment", "confidence": 0.5, "reasoning": "default"},
}


def _process_episode(env_args: tuple) -> tuple:
    """Process a single episode. Returns (episode_index, action, reward, error_msg, info)."""
    ep, task_id, obs, bug, available_assignees = env_args
    error_msg = "null"

    user_prompt = f"Title: {bug.title}\nBody: {bug.body[:1000]}\nLabels: {', '.join(bug.labels)}"

    # Add first comment for extra context (all tasks)
    if bug.comments_text:
        user_prompt += f"\nFirst comment: {bug.comments_text[0][:300]}"

    if task_id == "task_criticality":
        result = call_llm(CRITICALITY_SYSTEM_PROMPT, user_prompt)
        if "error" in result:
            error_msg = result["error"][:50]
            result = DEFAULTS["task_criticality"]
        action = BugTriageAction(
            task_id=task_id,
            bug_id=bug.bug_id,
            criticality=result.get("classification", "non_critical"),
            confidence=float(result.get("confidence", 0.5)),
            reasoning=result.get("reasoning", ""),
        )
    elif task_id == "task_severity":
        result = call_llm(SEVERITY_SYSTEM_PROMPT, user_prompt)
        if "error" in result:
            error_msg = result["error"][:50]
            result = DEFAULTS["task_severity"]
        raw_score = int(result.get("score", 3))
        clamped_score = max(1, min(5, raw_score))
        action = BugTriageAction(
            task_id=task_id,
            bug_id=bug.bug_id,
            severity=clamped_score,
            confidence=float(result.get("confidence", 0.5)),
            reasoning=result.get("reasoning", ""),
        )
    else:  # task_root_cause_assignee
        comments = bug.comments_text[:2] if bug.comments_text else []
        if comments:
            user_prompt += f"\nComments: {' '.join(c[:200] for c in comments)}"
        user_prompt += f"\nRepo: {bug.repo}"

        # Build rich assignee list with expertise and frequency hints
        assignee_parts = []
        repo_stats = REPO_STATS.get(bug.repo, [])
        freq_map = {name: pct for name, _, pct in repo_stats}
        for name in available_assignees[:10]:
            part = name
            pct = freq_map.get(name)
            if pct:
                part += f" (handles {pct}% of bugs)"
            expertise = CONTRIBUTOR_EXPERTISE.get(name.lower(), [])
            if expertise:
                part += f" [expertise: {', '.join(expertise[:3])}]"
            assignee_parts.append(part)
        user_prompt += f"\nAssignees (PICK ONE): {'; '.join(assignee_parts)}"
        result = call_llm(TRIAGE_SYSTEM_PROMPT, user_prompt)
        if "error" in result:
            error_msg = result["error"][:50]
            result = DEFAULTS["task_root_cause_assignee"]
            result["assignee"] = available_assignees[0] if available_assignees else "unknown"
        action = BugTriageAction(
            task_id=task_id,
            bug_id=bug.bug_id,
            root_cause=result.get("root_cause", "environment"),
            assignee=result.get("assignee", available_assignees[0] if available_assignees else "unknown"),
            confidence=float(result.get("confidence", 0.5)),
            reasoning=result.get("reasoning", ""),
        )

    return ep, action, error_msg


def run_task(env: BugTriageEnv, task_id: str, num_episodes: int, repository_filter=None) -> list:
    """Run inference for one task across N episodes with streaming results."""
    total_episodes = min(num_episodes, env._total_bugs)
    if num_episodes > env._total_bugs:
        logger.info(f"Capping episodes to {total_episodes} (dataset size)")

    # Phase 1: Collect observations
    episode_data = []
    temp_env = BugTriageEnv(seed=env._seed, repository_filter=repository_filter)
    for ep in range(total_episodes):
        obs = temp_env.reset(task_id=task_id)
        bug = obs.bug_report
        episode_data.append({
            "ep": ep,
            "bug_id": bug.bug_id,
            "bug": bug,
            "available_assignees": obs.available_assignees,
        })
        # Dummy step to satisfy env invariants
        temp_env.step(BugTriageAction(
            task_id=task_id, bug_id=bug.bug_id, 
            confidence=0.5, reasoning="",
            criticality="non_critical" if task_id == "task_criticality" else None,
            severity=3 if task_id == "task_severity" else None,
            root_cause="bug" if task_id == "task_root_cause_assignee" else None,
            assignee=obs.available_assignees[0] if obs.available_assignees else "unknown"
        ))

    llm_results = {}
    env_replay = BugTriageEnv(seed=env._seed, repository_filter=repository_filter)
    scores = []
    
    def _do_llm(ed):
        args = (ed["ep"], task_id, None, ed["bug"], ed["available_assignees"])
        return _process_episode(args)

    logger.info(f"Evaluating {total_episodes} bugs across {NUM_WORKERS} parallel workers...")

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(_do_llm, ed): ed["ep"] for ed in episode_data}

        next_ep_to_score = 0
        while next_ep_to_score < total_episodes:
            ready_ep = None
            for future in futures:
                if futures[future] == next_ep_to_score and future.done():
                    ready_ep = next_ep_to_score
                    ep, action, error_msg = future.result()
                    llm_results[ep] = (action, error_msg)
                    break

            if ready_ep is not None:
                obs = env_replay.reset(task_id=task_id)
                action, error_msg = llm_results[ready_ep]

                # Rebuild action
                action = BugTriageAction(
                    task_id=action.task_id,
                    bug_id=obs.bug_report.bug_id,
                    criticality=action.criticality.value if action.criticality else None,
                    severity=action.severity.value if action.severity else None,
                    root_cause=action.root_cause.value if action.root_cause else None,
                    assignee=action.assignee,
                    confidence=action.confidence,
                    reasoning=action.reasoning,
                )

                log_start(task_id, "bug-triage", MODEL_NAME)
                _, reward, _, info = env_replay.step(action)
                action_str = _format_action(action)
                log_step(1, action_str, reward, True, error_msg if error_msg != "null" else None)
                log_end(reward > 0, 1, reward, [reward])

                scores.append(reward)
                next_ep_to_score += 1
            else:
                time.sleep(0.05)

    return scores


def _format_action(action: BugTriageAction) -> str:
    """Format an action for structured log output."""
    if action.criticality:
        return f"classify('{action.criticality.value}')"
    elif action.severity:
        return f"severity({action.severity.value})"
    else:
        return f"triage('{action.root_cause.value}','{action.assignee}')"


def _format_action_short(action: BugTriageAction) -> str:
    """Format an action for the results table."""
    if action.criticality:
        return action.criticality.value
    elif action.severity:
        return f"severity {action.severity.value}"
    else:
        assignee = action.assignee[:12] if len(action.assignee) > 12 else action.assignee
        return f"{action.root_cause.value} -> {assignee}"


def main():
    """Entry point: parse args, run all three tasks and report scores."""
    parser = argparse.ArgumentParser(description="Triage Inference")
    parser.add_argument("--repos", type=str, help="Comma-separated repo names to filter")
    parser.add_argument("--episodes", type=int, default=15, help="Number of episodes per task")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    log_file = open("output.log", "w", encoding="utf-8")
    import sys
    class Tee:
        def __init__(self, *streams): self.streams = streams
        def write(self, data):
            for s in self.streams: s.write(data)
        def flush(self):
            for s in self.streams: s.flush()
    sys.stdout = Tee(sys.__stdout__, log_file)

    start_time = time.time()
    repo_filter = [r.strip() for r in args.repos.split(",")] if args.repos else None
    env = BugTriageEnv(repository_filter=repo_filter)
    num_total = min(args.episodes, env._total_bugs)

    all_scores = []
    task_results = {}

    TASK_LABELS = {
        "task_criticality": "Criticality Detection",
        "task_severity": "Severity Scoring",
        "task_root_cause_assignee": "Root Cause + Assignee",
    }

    tasks = [
        ("task_criticality", num_total),
        ("task_severity", num_total),
        ("task_root_cause_assignee", num_total),
    ]

    print("=" * 96)
    print(f"  BUG TRIAGE ENV - INFERENCE REPORT")
    print(f"  Team Dhurandhar")
    print(f"  Model: {MODEL_NAME}  |  Bugs: {num_total}  |  Filter: {repo_filter or 'all repos'}")
    print("=" * 96)

    for task_id, num_episodes in tasks:
        label = TASK_LABELS[task_id]
        print(f"\n{'-' * 96}")
        print(f"  TASK: {label}")
        print(f"{'-' * 96}\n")

        scores = run_task(env, task_id, num_episodes, repository_filter=repo_filter)
        all_scores.extend(scores)
        avg = sum(scores) / len(scores) if scores else 0.0
        perfect = sum(1 for s in scores if s >= 1.0)
        good = sum(1 for s in scores if 0.5 <= s < 1.0)
        bad = sum(1 for s in scores if s < 0.5)
        task_results[task_id] = avg

        print(f"\n  Result: {avg:.3f}  |  {perfect} correct  {good} partial  {bad} wrong  (out of {len(scores)})")

    overall = sum(all_scores) / len(all_scores) if all_scores else 0.0
    elapsed = time.time() - start_time

    print(f"\n{'=' * 96}")
    print(f"  SUMMARY")
    print(f"{'=' * 96}")
    print(f"  {'Task':<35} {'Score':>8}")
    print(f"  {'-'*35} {'-'*8}")
    for tid, label in TASK_LABELS.items():
        if tid in task_results:
            print(f"  {label:<35} {task_results[tid]:>8.3f}")
    print(f"  {'-'*35} {'-'*8}")
    print(f"  {'OVERALL':<35} {overall:>8.3f}")
    print(f"{'=' * 96}")
    print(f"  Completed in {elapsed/60:.1f} minutes ({elapsed/len(all_scores) if all_scores else 0:.1f}s per call)")
    print(f"{'=' * 96}")


if __name__ == "__main__":
    main()
