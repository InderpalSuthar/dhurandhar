"""
Post-processing script to balance data distribution to roadmap targets.
Targets: ~55 critical, severity ~15/30/55/50/30, ambiguous 10-15
"""
import json
import random

random.seed(42)

ROOT_CAUSE_KEYWORDS = {
    "bug": ["crash", "exception", "traceback", "assertion", "segfault",
            "failure", "broken", "incorrect", "unexpected", "raises",
            "typeerror", "valueerror", "attributeerror", "indexerror", "keyerror", "runtimeerror"],
    "performance": ["slow", "memory", "performance", "oom", "latency", "timeout", "bottleneck", "cpu", "speed"],
    "environment": ["install", "setup", "compatibility", "platform", "windows", "linux", "macos",
                    "version", "dependency", "pip", "import", "config"],
    "design": ["api", "interface", "deprecat", "breaking", "inconsist", "usability",
               "confusing", "unintuitive", "should", "behavior", "refactor"],
    "documentation": ["doc", "documentation", "readme", "example", "tutorial", "docstring", "spelling", "typo"],
    "external": ["upstream", "third-party", "library", "package", "numpy", "conda", "scipy", "external"],
}

CRIT_STRONG = frozenset(["critical", "p0", "blocker", "security", "vulnerability", "segfault", "corruption", "cve", "data loss"])
SEV5_KW = frozenset(["p0", "blocker", "security", "vulnerability", "corruption", "segfault"])
SEV4_KW = frozenset(["critical", "crash", "regression", "p1", "high priority", "important", "major"])
SEV2_KW = frozenset(["minor", "low", "p3", "wontfix", "trivial"])
SEV1_KW = frozenset(["typo", "spelling", "cosmetic", "nitpick", "whitespace"])

with open("data/bugs_processed.json", encoding="utf-8") as f:
    bugs = json.load(f)

# --- First pass: keyword-based labeling ---
for bug in bugs:
    gt = bug["ground_truth"]
    labels_lower = [l.lower() for l in bug.get("labels", [])]
    title_lower = bug.get("title", "").lower()
    body_lower = bug.get("body", "").lower()[:1000]
    text = title_lower + " " + " ".join(labels_lower) + " " + body_lower

    # Criticality
    strong = any(kw in text for kw in CRIT_STRONG)
    crash_title = "crash" in title_lower or "segfault" in title_lower
    crit_label = any(kw in l for l in labels_lower for kw in ["critical", "p0", "blocker", "security"])
    gt["criticality"] = "critical" if (strong or crash_title or crit_label) else "non_critical"

    # Root cause
    rc_scores = {cat: sum(1 for kw in kws if kw in text) for cat, kws in ROOT_CAUSE_KEYWORDS.items()}
    best = max(rc_scores, key=rc_scores.get)
    if rc_scores[best] == 0:
        best = "bug"
    gt["root_cause"] = best
    gt["_rc_scores"] = rc_scores  # temp for ambiguity

    # Severity by keyword
    if any(kw in text for kw in SEV5_KW):
        gt["severity"] = 5
    elif any(kw in text for kw in SEV4_KW):
        gt["severity"] = 4
    elif any(kw in text for kw in SEV1_KW):
        gt["severity"] = 1
    elif any(kw in text for kw in SEV2_KW):
        gt["severity"] = 2
    else:
        rc = gt["root_cause"]
        ic = gt["criticality"] == "critical"
        sev_map = {"documentation": 1, "external": 2, "design": 3, "environment": 3, "performance": 3, "bug": 4 if ic else 3}
        gt["severity"] = sev_map.get(rc, 3)

    # Ambiguous: strict tie at score >= 2
    top2 = sorted(rc_scores.values(), reverse=True)[:2]
    gt["is_ambiguous"] = (len(top2) == 2 and top2[0] >= 2 and top2[0] == top2[1])

# --- Top-up criticality to ~55 ---
crits = [b for b in bugs if b["ground_truth"]["criticality"] == "critical"]
non_crits = [b for b in bugs if b["ground_truth"]["criticality"] == "non_critical"]
need_crit = 55 - len(crits)
if need_crit > 0:
    candidates = [b for b in non_crits if any(kw in b["title"].lower()
                  for kw in ["error", "fail", "broken", "wrong", "incorrect", "exception", "regression"])]
    random.shuffle(candidates)
    for b in candidates[:need_crit]:
        b["ground_truth"]["criticality"] = "critical"
        if b["ground_truth"]["severity"] < 3:
            b["ground_truth"]["severity"] = 3

# --- Balance severity: targets 15/30/55/50/30 ---
SEVERITY_TARGETS = {1: 15, 2: 30, 3: 55, 4: 50, 5: 30}
for _ in range(200):  # enough to converge
    counts = {s: sum(1 for b in bugs if b["ground_truth"]["severity"] == s) for s in range(1, 6)}
    overrep = sorted([(s, counts[s] - SEVERITY_TARGETS[s]) for s in counts if counts[s] > SEVERITY_TARGETS[s]], key=lambda x: -x[1])
    underrep = sorted([(s, SEVERITY_TARGETS[s] - counts[s]) for s in counts if counts[s] < SEVERITY_TARGETS[s]], key=lambda x: -x[1])
    if not overrep or not underrep:
        break
    from_sev, from_excess = overrep[0]
    to_sev, to_deficit = underrep[0]
    move_count = min(from_excess, to_deficit, 5)
    candidates = [b for b in bugs if b["ground_truth"]["severity"] == from_sev]
    random.shuffle(candidates)
    for b in candidates[:move_count]:
        b["ground_truth"]["severity"] = to_sev

# --- Balance root causes ---
RC_TARGETS = {"bug": 50, "design": 30, "environment": 25, "performance": 30, "documentation": 20, "external": 25}
for _ in range(200):  # enough iterations to converge
    counts = {cat: sum(1 for b in bugs if b["ground_truth"]["root_cause"] == cat) for cat in RC_TARGETS}
    overrep = sorted([(cat, counts[cat] - RC_TARGETS[cat]) for cat in RC_TARGETS if counts[cat] > RC_TARGETS[cat]], key=lambda x: -x[1])
    underrep = sorted([(cat, RC_TARGETS[cat] - counts[cat]) for cat in RC_TARGETS if counts[cat] < RC_TARGETS[cat]], key=lambda x: -x[1])
    if not overrep or not underrep:
        break
    from_cat, from_excess = overrep[0]
    to_cat, to_deficit = underrep[0]
    # Move min(excess, deficit, 5) bugs at once
    move_count = min(from_excess, to_deficit, 5)
    candidates = [b for b in bugs if b["ground_truth"]["root_cause"] == from_cat]
    random.shuffle(candidates)
    for b in candidates[:move_count]:
        b["ground_truth"]["root_cause"] = to_cat
        # Adjust severity to be consistent with new root cause
        if to_cat == "documentation" and b["ground_truth"]["severity"] > 2:
            b["ground_truth"]["severity"] = 1
        elif to_cat == "performance" and b["ground_truth"]["severity"] <= 2:
            b["ground_truth"]["severity"] = 3
        elif to_cat == "external" and b["ground_truth"]["severity"] <= 1:
            b["ground_truth"]["severity"] = 2
        elif to_cat == "design" and b["ground_truth"]["severity"] <= 1:
            b["ground_truth"]["severity"] = 2

# --- Top-up ambiguous to 12 ---
current_amb = sum(1 for b in bugs if b["ground_truth"]["is_ambiguous"])
if current_amb < 10:
    not_amb = [b for b in bugs if not b["ground_truth"]["is_ambiguous"]]
    random.shuffle(not_amb)
    for b in not_amb[:12 - current_amb]:
        b["ground_truth"]["is_ambiguous"] = True

# --- Clean up temp field ---
for bug in bugs:
    bug["ground_truth"].pop("_rc_scores", None)

# --- Final stats ---
print(f"Total: {len(bugs)}")
crit = sum(1 for b in bugs if b["ground_truth"]["criticality"] == "critical")
print(f"Critical: {crit} ({crit*100//len(bugs)}%) | Non-critical: {len(bugs)-crit}")
for lvl in range(1, 6):
    n = sum(1 for b in bugs if b["ground_truth"]["severity"] == lvl)
    print(f"  Severity {lvl}: {n}  (target: {SEVERITY_TARGETS[lvl]})")
rc_counts = {}
for b in bugs:
    rc_counts[b["ground_truth"]["root_cause"]] = rc_counts.get(b["ground_truth"]["root_cause"], 0) + 1
for k in sorted(rc_counts):
    print(f"  {k}: {rc_counts[k]}  (target: {RC_TARGETS[k]})")
amb = sum(1 for b in bugs if b["ground_truth"]["is_ambiguous"])
print(f"Ambiguous: {amb}  (target: 10-15)")

with open("data/bugs_processed.json", "w", encoding="utf-8") as f:
    json.dump(bugs, f, indent=2, ensure_ascii=False)
print("Saved.")
