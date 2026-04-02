# Sumit's Progress Tracker - Bug Report Triage RL Environment

**Role:** Environment Core + Data Pipeline + Tests
**Deadline:** April 8, 2026 11:59 PM
**Current Date:** April 2, 2026
**Days Remaining:** 6

---

## DAY 1 - April 2 (TODAY)

### Status: ✅ COMPLETE

#### JOINT TASKS (with Inderpal)
- [x] Create repo structure (mkdir src/, data/, tests/)
- [x] Write src/models.py - THE SHARED CONTRACT
- [x] Write interface stubs (env.py, graders.py, reward.py, tasks.py)
- [x] Agree on data schema for bugs_processed.json
- [x] Set up requirements.txt with initial deps
- [x] Create feature branches (main branch)

#### SOLO TASKS
- [x] Set up GitHub API auth skeleton
- [x] Identify target repos (pytorch, django, fastapi, numpy, cpython)
- [x] Create src/github_fetcher.py skeleton
- [x] Create src/utils.py skeleton
- [x] Create src/mock_graders.py for dev testing
- [x] Create .env.example and .gitignore

**Day 1 Summary:**
- All files created and tested
- Models contract locked and agreed
- Mock graders ready for development
- Ready for Day 2 parallel work

---

## DAY 2 - April 3

### Status: ⏳ PENDING (Start tomorrow)

**Target:** Fetch 180 bugs, label 80+, complete tasks.py

#### TASKS

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Implement github_fetcher.py | [ ] Pending | Need GitHub API pagination, auth, rate limiting |
| 2 | Set up GitHub authentication | [ ] Pending | Use GITHUB_TOKEN env var |
| 3 | Fetch issues from pytorch/pytorch | [ ] Pending | Target: 30+ issues |
| 4 | Fetch issues from django/django | [ ] Pending | Target: 50+ issues |
| 5 | Fetch issues from fastapi | [ ] Pending | Target: 40+ issues |
| 6 | Fetch issues from numpy | [ ] Pending | Target: 35+ issues |
| 7 | Fetch issues from cpython | [ ] Pending | Target: 25+ issues |
| 8 | Save raw data to bugs_raw.json | [ ] Pending | 180+ issues total |
| 9 | Implement ground truth labeling | [ ] Pending | Criticality, severity, root_cause, assignee |
| 10 | Label first batch of bugs | [ ] Pending | Target: 80 bugs with complete labels |
| 11 | Implement src/tasks.py | [ ] Pending | Define 3 task definitions with metadata |
| 12 | Test data loading | [ ] Pending | Verify JSON schema matches contract |

**Checkpoints:**
- [ ] github_fetcher.py can authenticate and fetch
- [ ] 180+ raw bugs saved to data/bugs_raw.json
- [ ] 80+ bugs with ground truth labels
- [ ] tasks.py complete with all 3 task definitions
- [ ] Push to sumit/env-data branch

**Day 2 Standup (EOD async message to Inderpal):**
```
Yesterday: [N/A - first day]
Today: [tasks]
Blockers: [any issues?]
```

---

## DAY 3 - April 4

### Status: ⏳ PENDING

**Target:** Complete all 180 bugs, env.py working with mock graders

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Finish ground truth labeling | [ ] Pending | All 180 bugs with complete labels |
| 2 | Mark ambiguous bugs | [ ] Pending | 10-15 bugs with is_ambiguous=true |
| 3 | Create contributors.json | [ ] Pending | Team mappings for all 5 repos |
| 4 | Save bugs_processed.json | [ ] Pending | 180 entries, validated schema |
| 5 | Implement env.py reset() | [ ] Pending | Load bugs, create observation |
| 6 | Implement env.py step() | [ ] Pending | Call grader, reward calculator, return results |
| 7 | Implement env.py state() | [ ] Pending | Return episode/step info |
| 8 | Test reset() with mock graders | [ ] Pending | Verify observation structure |
| 9 | Test step() with mock graders | [ ] Pending | Verify reward 0.0-1.0 |
| 10 | Test state() | [ ] Pending | Verify returns correct dict |
| 11 | Verify all 180 bugs load | [ ] Pending | No missing or corrupt entries |
| 12 | Smoke test env end-to-end | [ ] Pending | Run 10 episodes manually |

**Checkpoints:**
- [ ] data/bugs_processed.json has 180 complete entries
- [ ] data/contributors.json has team mappings
- [ ] env.py reset/step/state all work
- [ ] Reward always in [0.0, 1.0]
- [ ] Mock graders integrated and working
- [ ] Push to sumit/env-data branch

**Day 3 Sync Call with Inderpal (15 min):**
- [ ] Demo env.py working with mock graders
- [ ] Review data schema
- [ ] Check for interface mismatches
- [ ] Confirm ready for Day 4 merge

---

## DAY 4 - April 5

### Status: ⏳ PENDING

**Target:** Integration complete, all tests pass

#### JOINT TASKS (first 2 hours with Inderpal)
| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Merge sumit/env-data to main | [ ] Pending | Handle any conflicts |
| 2 | Merge inderpal branch to main | [ ] Pending | Handle any conflicts |
| 3 | Remove all mock implementations | [ ] Pending | Wire real graders/reward |
| 4 | Smoke test end-to-end | [ ] Pending | python inference.py on 5 bugs |
| 5 | Debug integration issues | [ ] Pending | Fix type errors, import errors |

#### SOLO TASKS (after integration - 6 hours)
| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Write test_env.py | [ ] Pending | 15+ test cases for reset/step/state |
| 2 | Write test_graders.py | [ ] Pending | 20+ test cases for all graders |
| 3 | Write test_inference.py | [ ] Pending | 8+ test cases for stdout format |
| 4 | Run pytest tests | [ ] Pending | All tests must pass |
| 5 | Fix any test failures | [ ] Pending | Debug and resolve issues |
| 6 | Verify no import errors | [ ] Pending | Clean Python imports |
| 7 | Test with all 180 bugs | [ ] Pending | Full dataset integration |

**Test Coverage Targets:**
- [ ] test_env.py: 15+ cases covering all reset/step/state scenarios
- [ ] test_graders.py: 20+ cases covering grading logic
- [ ] test_inference.py: 8+ cases covering stdout format
- [ ] Overall: All tests passing

**Checkpoints:**
- [ ] Full end-to-end inference runs successfully
- [ ] All tests pass: pytest tests/ -v
- [ ] No import errors or type mismatches
- [ ] Docker builds: docker build -t bugtriage .

---

## DAY 5 - April 6

### Status: ⏳ PENDING

**Target:** Data hardened, openenv validate passing, Docker verified

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Data quality audit | [ ] Pending | Check all 180 bugs for accuracy |
| 2 | Verify data distribution | [ ] Pending | 30% critical, 70% non-critical |
| 3 | Check severity distribution | [ ] Pending | Spread across all 5 levels |
| 4 | Verify root causes spread | [ ] Pending | All 6 categories represented |
| 5 | Verify edge cases | [ ] Pending | 10-15 bugs marked ambiguous |
| 6 | Fix any labeling errors | [ ] Pending | Correct misclassified bugs |
| 7 | Harden env.py error handling | [ ] Pending | Never crash, handle bad input |
| 8 | Test edge cases in env | [ ] Pending | Malformed actions, missing fields |
| 9 | Performance profiling | [ ] Pending | Measure full inference runtime |
| 10 | Optimize if needed | [ ] Pending | Target: < 15 min total |
| 11 | Run openenv validate | [ ] Pending | Must pass all checks |
| 12 | Fix validation errors | [ ] Pending | Address any failures |
| 13 | Increase test coverage | [ ] Pending | Target: >90% on core files |
| 14 | Print data report | [ ] Pending | Bugs per repo, severity hist, etc |

**Data Distribution Verification:**
- [ ] Criticality: ~55 critical (30%), ~125 non-critical (70%)
- [ ] Severity: ~15 L1, ~30 L2, ~55 L3, ~50 L4, ~30 L5
- [ ] Root Cause: ~50 bug, ~30 design, ~25 environment, ~30 performance, ~20 docs, ~25 external
- [ ] Ambiguous: 10-15 bugs flagged
- [ ] Repos: Django 50, FastAPI 40, NumPy 35, PyTorch 30, CPython 25

**Checkpoints:**
- [ ] openenv validate passes
- [ ] Data distribution verified and balanced
- [ ] env.py handles all edge cases
- [ ] Full inference completes in < 15 min
- [ ] Test coverage > 90% on core files

---

## DAY 6 - April 7

### Status: ⏳ PENDING

**Target:** Code cleanup, cross-review complete, ready to submit

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Fix test failures from Day 5 | [ ] Pending | All tests must be green |
| 2 | Data rebalancing if needed | [ ] Pending | Adjust counts if distribution off |
| 3 | Verify contributors.json | [ ] Pending | Team mappings are sensible |
| 4 | Code cleanup | [ ] Pending | Remove debug prints, unused imports |
| 5 | Add docstrings | [ ] Pending | Document all public methods |
| 6 | Add type hints | [ ] Pending | Where possible |
| 7 | Cross-review Inderpal's code | [ ] Pending | Check graders, reward, inference |
| 8 | Full test suite run | [ ] Pending | pytest tests/ -v - all green |
| 9 | Final code review | [ ] Pending | No TODOs, no debug code |
| 10 | Ensure no hardcoded paths | [ ] Pending | Works in Docker container |

**Code Review Checklist (your files):**
- [ ] env.py: reset/step/state work correctly
- [ ] env.py: handles all action validation
- [ ] env.py: calls correct grader per task
- [ ] tasks.py: all 3 task definitions complete
- [ ] github_fetcher.py: handles API errors gracefully
- [ ] data/bugs_processed.json: valid schema, no corruption
- [ ] data/contributors.json: team mappings sensible
- [ ] All tests pass without warnings
- [ ] No hardcoded paths (relative paths OK)

**Cross-Review of Inderpal's Code:**
- [ ] grade_criticality(): 1.0/0.0 correct
- [ ] grade_severity(): 1.0/0.7/0.4/0.0 correct
- [ ] grade_root_cause_assignee(): weighted 0.6/0.4
- [ ] RewardCalculator: bonuses computed correctly
- [ ] RewardCalculator: total clamped to [0.0, 1.0]
- [ ] inference.py: uses OpenAI client
- [ ] inference.py: stdout format exact [START]/[STEP]/[END]
- [ ] inference.py: < 20 min runtime
- [ ] Dockerfile: builds and runs
- [ ] README: complete and clear

**Checkpoints:**
- [ ] All tests passing
- [ ] All code reviewed by both developers
- [ ] No TODOs or debug code remaining
- [ ] Data is clean and verified
- [ ] Ready for submission

---

## DAY 7 - April 8 (SUBMISSION DAY)

### Status: ⏳ PENDING

**Target:** Final validation and submit

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Final openenv validate | [ ] Pending | MUST PASS |
| 2 | Final test suite run | [ ] Pending | All tests green |
| 3 | Final Docker test | [ ] Pending | Build + run locally |
| 4 | Verify no import errors | [ ] Pending | Clean imports throughout |
| 5 | Final data verification | [ ] Pending | 180 bugs present and valid |
| 6 | Submission checklist | [ ] Pending | All items confirmed |

**Pre-Submission Checklist (YOUR half):**
- [ ] data/bugs_processed.json has 180 complete entries
- [ ] data/contributors.json has team mappings
- [ ] env.py reset/step/state all working
- [ ] All tests passing (pytest tests/ -v)
- [ ] No import errors anywhere
- [ ] Ground truth labels accurate
- [ ] Data distribution balanced
- [ ] Edge case bugs flagged

**Submit by:** April 8, 6:00 PM (safe 6-hour buffer before 11:59 PM deadline)

---

## DAILY SUMMARY LOG

### April 2 (Day 1)
**Status:** ✅ COMPLETE
- Created project structure
- Locked models.py contract
- Created all stubs and skeletons
- Ready for parallel development

**Time Spent:** 6 hours
**Blockers:** None
**Next:** Start github_fetcher.py Day 2

---

### April 3 (Day 2)
**Status:** ⏳ PENDING
**Planned Time:** 7-8 hours
**Target Deliverable:** 80+ bugs labeled, tasks.py complete

**Date:** _____
**Time Spent:** _____ hours
**Completed:**
- [ ] github_fetcher.py implemented
- [ ] Issues fetched from all 5 repos
- [ ] 80+ bugs labeled
- [ ] tasks.py complete
- [ ] Push to branch

**Blockers:** _____________________
**Notes:** _____________________

---

### April 4 (Day 3)
**Status:** ⏳ PENDING
**Planned Time:** 7-8 hours
**Target Deliverable:** env.py complete, all 180 bugs labeled

**Date:** _____
**Time Spent:** _____ hours
**Completed:**
- [ ] All 180 bugs labeled
- [ ] contributors.json created
- [ ] env.py reset() implemented
- [ ] env.py step() implemented
- [ ] env.py state() implemented
- [ ] All integration tests pass
- [ ] Push to branch

**Blockers:** _____________________
**Notes:** _____________________

---

### April 5 (Day 4)
**Status:** ⏳ PENDING
**Planned Time:** 8 hours
**Target Deliverable:** Integration complete, tests written

**Date:** _____
**Time Spent:** _____ hours
**Completed:**
- [ ] Merged to main branch
- [ ] Removed mock implementations
- [ ] test_env.py written (15+ cases)
- [ ] test_graders.py written (20+ cases)
- [ ] test_inference.py written (8+ cases)
- [ ] All tests passing
- [ ] Docker builds successfully

**Integration Issues Found & Fixed:**
1. _____________________
2. _____________________
3. _____________________

**Blockers:** _____________________
**Notes:** _____________________

---

### April 6 (Day 5)
**Status:** ⏳ PENDING
**Planned Time:** 7-8 hours
**Target Deliverable:** Data hardened, openenv validate pass

**Date:** _____
**Time Spent:** _____ hours
**Completed:**
- [ ] Data quality audit complete
- [ ] Data distribution verified
- [ ] env.py error handling hardened
- [ ] openenv validate PASSES
- [ ] Test coverage > 90%
- [ ] Runtime < 15 min verified

**Data Distribution Report:**
- Criticality: Critical ____ (target 55), Non-critical ____ (target 125)
- Severity: L1 ____, L2 ____, L3 ____, L4 ____, L5 ____
- Root Causes: Bug ____, Design ____, Env ____, Perf ____, Docs ____, Ext ____
- Ambiguous: ____

**Blockers:** _____________________
**Notes:** _____________________

---

### April 7 (Day 6)
**Status:** ⏳ PENDING
**Planned Time:** 5-6 hours
**Target Deliverable:** Code cleanup, cross-review complete

**Date:** _____
**Time Spent:** _____ hours
**Completed:**
- [ ] All tests passing
- [ ] Code cleanup done
- [ ] Docstrings added
- [ ] Type hints added
- [ ] Inderpal's code cross-reviewed
- [ ] No TODOs remaining
- [ ] Ready for submission

**Cross-Review Issues Found:**
1. _____________________
2. _____________________

**Blockers:** _____________________
**Notes:** _____________________

---

### April 8 (Day 7 - SUBMISSION)
**Status:** ⏳ PENDING
**Planned Time:** 3-4 hours
**Target:** SUBMIT

**Date:** _____
**Submitted at:** _____ (time)
**Final Checklist:**
- [ ] openenv validate PASSED
- [ ] All tests PASSED
- [ ] Docker builds successfully
- [ ] 180 bugs present and valid
- [ ] All deliverables complete
- [ ] README complete
- [ ] Submission confirmed

**Final Notes:** _____________________

---

## OVERALL PROGRESS

| Day | Status | % Complete | Hours Used | Notes |
|-----|--------|-----------|-----------|-------|
| 1 | ✅ Complete | 100% | 6h | Models locked, ready for parallel |
| 2 | ⏳ Pending | 0% | -- | Start tomorrow |
| 3 | ⏳ Pending | 0% | -- | Continue github/data |
| 4 | ⏳ Pending | 0% | -- | Integration day |
| 5 | ⏳ Pending | 0% | -- | Hardening/validate |
| 6 | ⏳ Pending | 0% | -- | Polish/review |
| 7 | ⏳ Pending | 0% | -- | Submit |
| **Total** | **10% (1/7 days)** | **10%** | **6h** | **On track** |

---

## KEY METRICS TO TRACK

### Data Metrics
- Bugs fetched: ____ / 180
- Bugs labeled: ____ / 180
- Repos covered: ____ / 5
- Ambiguous flagged: ____ / 10-15

### Code Metrics
- env.py lines: ____
- test_env.py test cases: ____ (target: 15+)
- test_graders.py test cases: ____ (target: 20+)
- Test coverage: ____% (target: >90%)

### Performance Metrics
- Full inference runtime: ____ min (target: <20)
- Docker image size: ____ MB
- Memory usage: ____ MB (target: <8GB)
- CPU usage: ____ % (target: <200% on 2vCPU)

### Quality Metrics
- All tests passing: [ ] Yes / [ ] No
- openenv validate: [ ] Pass / [ ] Fail
- No import errors: [ ] Yes / [ ] No
- No hardcoded paths: [ ] Yes / [ ] No
- Data corruption: [ ] None / [ ] Found: ____

---

## NOTES & OBSERVATIONS

```
Day 1 (Apr 2):
- Project structure complete
- Models contract locked
- Ready for parallel work with Inderpal
- Next: Start github_fetcher.py

Day 2 (Apr 3):
[Update after execution]

Day 3 (Apr 4):
[Update after execution]

Day 4 (Apr 5):
[Update after execution]

Day 5 (Apr 6):
[Update after execution]

Day 6 (Apr 7):
[Update after execution]

Day 7 (Apr 8):
[Update after execution]

SUBMISSION:
[Final status and timestamp]
```

---

## EMERGENCY PROTOCOLS

**If GitHub API rate-limited:**
- [ ] Use personal access token (5000 req/hr)
- [ ] Cache responses locally in bugs_raw.json
- [ ] Use second account if needed
- [ ] Fall back to web scraping

**If not enough bugs (< 150):**
- [ ] Expand to more repos
- [ ] Include non-"bug" labeled issues
- [ ] Generate synthetic examples (mark as synthetic)

**If env.py integration fails:**
- [ ] Check grader signatures match
- [ ] Check Pydantic field names match
- [ ] Check data schema matches
- [ ] Pair-debug with Inderpal

**If tests fail:**
- [ ] Fix immediately - don't push broken tests
- [ ] If grader logic wrong: contact Inderpal
- [ ] If env logic wrong: fix it
- [ ] If data wrong: fix specific entries

**If behind schedule:**
- Day 3: Cut data to 120 bugs
- Day 4: Skip test_inference.py
- Day 5: Skip data audit
- Day 6: Skip code cleanup
- Day 7: Submit what works

---

**Last Updated:** April 2, 2026 @ completion of Day 1
**Next Update:** April 3, 2026 end of Day 2
**Status:** ON TRACK - Ready for execution
