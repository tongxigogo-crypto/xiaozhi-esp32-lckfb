# Task Queue

## Purpose

Track task ownership, lifecycle, outputs, and verifiable completion evidence for the agent system.

## Filling Rules

- Append exactly one Task Definition for each Task ID. Never overwrite, duplicate, or reuse a Task ID.
- Record every lifecycle transition as a new append-only Status Event. Never edit or delete a prior event.
- The current task status is derived from the `To Status` of the last valid Status Event for that Task ID; the `Status` in the Task Definition is only the initial status.
- Use ISO-8601 timestamps with a timezone, for example `2026-08-09T14:30:00+08:00`.
- Priority must be `P0`, `P1`, `P2`, or `P3`: `P0` is urgent/critical, `P1` is high, `P2` is normal, and `P3` is low/deferred.
- Allowed statuses are `pending`, `running`, `blocked`, `ready_for_review`, `completed`, and `cancelled`.
- An executing agent must not self-approve its task.
- QA and Reviewer record evidence only; they do not complete or cancel a task.
- Only the SOL records `completed` or `cancelled` after checking the required evidence or authorization.
- Only SOL records completed or cancelled.
- Claims, placeholders, summaries, and status labels are not evidence. Evidence Links must resolve to inspectable artifacts or records.
- For literal policy matching: claims are not evidence.

## Status Migration Table

| From | To | Who Records It | Required Basis |
|---|---|---|---|
| new | `pending` | SOL | Task scope, owner, inputs, outputs, and verification method are defined. |
| `pending` | `running` | Assigned Worker or SOL | Start timestamp and accepted assignment are recorded. |
| `pending` | `cancelled` | SOL only | Cancellation reason and impact are recorded, with user direction when applicable. |
| `running` | `blocked` | Assigned Agent or SOL | Concrete blocker, attempted checks, and required next action are recorded. |
| `running` | `ready_for_review` | Assigned Agent | Handoff, changed files, verification evidence, and known gaps are recorded. |
| `running` | `cancelled` | SOL only | Cancellation reason and impact are recorded, with user direction when applicable. |
| `blocked` | `running` | SOL only | Blocker resolution or new evidence is recorded. |
| `blocked` | `cancelled` | SOL only | Cancellation reason and impact are recorded, with user direction when applicable. |
| `ready_for_review` | `running` | SOL only | Reviewer `NEED FIX` or QA failure is recorded, with the review or QA record and a bounded revision scope. |
| `ready_for_review` | `completed` | SOL only | Reviewer `PASS` and all required QA are recorded, with review evidence, QA evidence, and an acceptance timestamp. |
| `ready_for_review` | `cancelled` | SOL only | Cancellation reason and impact are recorded, with user direction when applicable. |
| `completed` | no transition | none | Terminal state; create a new task for further work. |
| `cancelled` | no transition | none | Terminal state; create a new task to restart work. |

All transitions not listed above are prohibited. Each permitted transition must be represented by a complete Status Event whose Actor and Evidence satisfy this table.

## Usage Notes

- copying this template into a project requires explicit initialization.
- if project already has `.agent`, Do not overwrite or merge without explicit user approval.
- project `.agent` records should be committed to Git unless they contain secrets.
- placeholders are not evidence.

## Blank Entries

### Task Definition

```yaml
Task ID:
Priority: P2
Assigned Agent:
Inputs: []
Outputs: []
Verification Method:
Status: pending
Evidence Links: []
Record Owner:
Created At:
Started At: null
Updated At:
Completed At: null
```

`Started At`, `Updated At`, `Completed At`, and additional `Evidence Links` are lifecycle projection fields retained in the definition schema. Do not rewrite the Task Definition to update them; derive their current values from the append-only Status Events.

### Status Event

```yaml
Event ID:
Task ID:
From Status:
To Status:
Actor:
Evidence: []
Blocker/Attempted Checks/Next Action:
  Blocker:
  Attempted Checks: []
  Next Action:
Review or QA Record: []
Cancellation Reason/Impact:
  Cancellation Reason:
  Impact:
Acceptance Timestamp:
Timestamp:
```


## Task Definition NET-INIT-FW-20261108

{
  "Task ID": "NET-INIT-FW-20261108",
  "Priority": "P1",
  "Assigned Agent": "SOL",
  "Inputs": [
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/comparison-and-added-files.json",
    "/tmp/xfy-serial-ts2.csv"
  ],
  "Outputs": [
    "versioned evidence and reviewable candidate"
  ],
  "Verification Method": "independent Reviewer + QA; production pointer unchanged",
  "Status": "pending",
  "Record Owner": "SOL",
  "Created At": "2026-11-08T19:31:40+08:00",
  "Scope": "Coordination records initialized; existing firmware files preserved byte for byte"
}


## Status Event NET-INIT-FW-20261108-START

{
  "Event ID": "NET-INIT-FW-20261108-START",
  "Task ID": "NET-INIT-FW-20261108",
  "From Status": "pending",
  "To Status": "running",
  "Actor": "SOL",
  "Reason": "Authorized repair/diagnosis started",
  "Evidence": [
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/comparison-and-added-files.json",
    "DEC-NET-INIT-FW-20261108"
  ],
  "Timestamp": "2026-11-08T19:31:40+08:00"
}


## Task Definition NET-DIAG-FW-20261108

{
  "Task ID": "NET-DIAG-FW-20261108",
  "Priority": "P1",
  "Assigned Agent": "generic worker exploration (not DeepSeek runtime)",
  "Inputs": [
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/comparison-and-added-files.json",
    "/tmp/xfy-serial-ts2.csv"
  ],
  "Outputs": [
    "versioned evidence and reviewable candidate"
  ],
  "Verification Method": "independent Reviewer + QA; production pointer unchanged",
  "Status": "pending",
  "Record Owner": "SOL",
  "Created At": "2026-11-08T19:31:40+08:00",
  "Scope": "Investigate WS receive failure and missing session recovery; evidence before fix; no live changes"
}


## Status Event NET-DIAG-FW-20261108-START

{
  "Event ID": "NET-DIAG-FW-20261108-START",
  "Task ID": "NET-DIAG-FW-20261108",
  "From Status": "pending",
  "To Status": "running",
  "Actor": "SOL",
  "Reason": "Authorized repair/diagnosis started",
  "Evidence": [
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/comparison-and-added-files.json",
    "DEC-NET-INIT-FW-20261108"
  ],
  "Timestamp": "2026-11-08T19:31:40+08:00"
}


## NET-INIT-FW-20261108-READY

{
  "Event ID": "NET-INIT-FW-20261108-READY",
  "Task ID": "NET-INIT-FW-20261108",
  "From Status": "running",
  "To Status": "ready_for_review",
  "Actor": "SOL",
  "Reason": "Directoryrepair executed and hashverified; independent review/QA requested",
  "Evidence": [
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/comparison-and-added-files.json",
    "HANDOFF-NET-INIT-FW-20261108"
  ],
  "Timestamp": "2026-11-08T19:32:42+08:00"
}


## NET-INIT-FW-20261108-AUDIT-REVISION

{
  "Event ID": "NET-INIT-FW-20261108-AUDIT-REVISION",
  "Task ID": "NET-INIT-FW-20261108",
  "From Status": "ready_for_review",
  "To Status": "running",
  "Actor": "SOL",
  "Reason": "Reviewer NEED FIX: imprecise handoff evidence; bounded documentation revision",
  "Evidence": [
    "DEC-NET-INIT-AUDIT-FW-20261108"
  ],
  "Timestamp": "2026-11-08T19:35:03+08:00"
}


## NET-INIT-FW-20261108-AUDIT-READY

{
  "Event ID": "NET-INIT-FW-20261108-AUDIT-READY",
  "Task ID": "NET-INIT-FW-20261108",
  "From Status": "running",
  "To Status": "ready_for_review",
  "Actor": "SOL",
  "Reason": "Append-only handoff precision corrected; executableverificationpassed",
  "Evidence": [
    "HANDOFF-NET-INIT-FW-20261108-V2",
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/verify_initialization.py"
  ],
  "Timestamp": "2026-11-08T19:35:03+08:00"
}


## NET-INIT-FW-20261108-ACCEPT

{
  "Event ID": "NET-INIT-FW-20261108-ACCEPT",
  "Task ID": "NET-INIT-FW-20261108",
  "From Status": "ready_for_review",
  "To Status": "completed",
  "Actor": "SOL",
  "Reason": "Independent ReviewerPASS andseparateQAhashpreservation evidence accepted",
  "Evidence": [
    "REVIEW-NET-INIT-20261108-R2",
    "HANDOFF-NET-INIT-FW-20261108-V2"
  ],
  "Acceptance Timestamp": "2026-11-08T19:40:21+08:00",
  "Timestamp": "2026-11-08T19:40:21+08:00"
}


## entry

{
  "Task ID": "NET-FIX-FW-20261108",
  "Priority": "P1",
  "Assigned Agent": "LUNA FW worker",
  "Inputs": [
    "docs/superpowers/specs/2026-11-08-ws-recovery-design.md",
    "docs/superpowers/plans/2026-11-08-ws-recovery.md"
  ],
  "Outputs": [
    "testedreviewablecandidate"
  ],
  "Verification Method": "test-first, independentReviewer+QA, artifact-onlyfirmwarecompile",
  "Status": "pending",
  "Record Owner": "SOL",
  "Created At": "2026-11-08T19:40:21+08:00"
}


## NET-DIAG-FW-20261108-READY

{
  "Event ID": "NET-DIAG-FW-20261108-READY",
  "Task ID": "NET-DIAG-FW-20261108",
  "From Status": "running",
  "To Status": "ready_for_review",
  "Actor": "SOL",
  "Reason": "Workerdiagnosisreturned; approvedrepairdesignprepared; independentreviewduringcandidateacceptance",
  "Evidence": [
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/diagnostic-evidence.json",
    "HANDOFF-NET-DIAG-FW-20261108"
  ],
  "Timestamp": "2026-11-08T19:42:10+08:00"
}


## NET-FIX-FW-20261108-START

{
  "Event ID": "NET-FIX-FW-20261108-START",
  "Task ID": "NET-FIX-FW-20261108",
  "From Status": "pending",
  "To Status": "running",
  "Actor": "SOL",
  "Reason": "Userapproveddesign andindependentspec/plan advisoryPASS; delegatedLUNAimplementation",
  "Evidence": [
    "docs/superpowers/specs/2026-11-08-ws-recovery-design.md",
    "docs/superpowers/plans/2026-11-08-ws-recovery.md",
    "ws_plan_review advisoryPASS"
  ],
  "Timestamp": "2026-11-08T19:43:23+08:00"
}


## NET-QA-FW-20261108

{
  "Task ID": "NET-QA-FW-20261108",
  "Priority": "P1",
  "Assigned Agent": "ws_candidate_qa independentQA",
  "Inputs": [
    "approveddesign/plan",
    "upcomingLUNAcandidate"
  ],
  "Outputs": [
    "reproducibleisolatedtest evidence"
  ],
  "Verification Method": "preparefixturesnow; runsuitesonlyafterSOLready; separateReviewer",
  "Status": "pending",
  "Record Owner": "SOL",
  "Created At": "2026-11-08T19:51:21+08:00"
}


## NET-QA-FW-20261108-START

{
  "Event ID": "NET-QA-FW-20261108-START",
  "Task ID": "NET-QA-FW-20261108",
  "From Status": "pending",
  "To Status": "running",
  "Actor": "SOL",
  "Reason": "IndependentQA preparesisolatedtestharness concurrently; implementationnotreadyforruns",
  "Evidence": [
    "docs/superpowers/plans/2026-11-08-ws-recovery.md"
  ],
  "Timestamp": "2026-11-08T19:51:21+08:00"
}


## NET-REVIEW-FW-20261108

{
  "Task ID": "NET-REVIEW-FW-20261108",
  "Priority": "P1",
  "Assigned Agent": "ws_candidate_review independentReviewer",
  "Inputs": [
    "approvedspec/plan",
    "upcomingfrozencandidate"
  ],
  "Outputs": [
    "speccompliance+codequalityPASS/NEEDFIX"
  ],
  "Verification Method": "preparebaselinechecklist now; inspectfrozendiffandQA evidenceafterhandoff",
  "Status": "pending",
  "Record Owner": "SOL",
  "Created At": "2026-11-08T20:06:55+08:00"
}


## NET-REVIEW-FW-20261108-START

{
  "Event ID": "NET-REVIEW-FW-20261108-START",
  "Task ID": "NET-REVIEW-FW-20261108",
  "From Status": "pending",
  "To Status": "running",
  "Actor": "SOL",
  "Reason": "FreshindependentReviewer preparesbaselinecontext whileLUNAimplements; no interimselfapproval",
  "Evidence": [
    "docs/superpowers/plans/2026-11-08-ws-recovery.md"
  ],
  "Timestamp": "2026-11-08T20:06:55+08:00"
}


## NET-EXPERT-FW-20261108

{
  "Task ID": "NET-EXPERT-FW-20261108",
  "Priority": "P1",
  "Assigned Agent": "ws_async_lifecycle_expert (logicalTERRA; independentdefault runtime)",
  "Inputs": [
    "currentApplication recoveryworker/timer code",
    "approvedspec/plan"
  ],
  "Outputs": [
    "boundedasynclifetimeadvice; noimplementation"
  ],
  "Verification Method": "evidence-basedreview ofFreeRTOScontextdestruction, cancellablebackoff, pendingownerstate; finalcodeReview+QAvalidateadoption",
  "Status": "pending",
  "Record Owner": "SOL",
  "Created At": "2026-11-08T20:30:07+08:00"
}


## NET-EXPERT-FW-20261108-START

{
  "Event ID": "NET-EXPERT-FW-20261108-START",
  "Task ID": "NET-EXPERT-FW-20261108",
  "From Status": "pending",
  "To Status": "running",
  "Actor": "SOL",
  "Reason": "Exceptionalcross-threadresourceownership risks identified; boundedexpertjudgment needed; LUNAretainscodeownership",
  "Evidence": [
    "StartRecoveryTask/HandleRecoveryWorkerDone currentpreliminaryinspection",
    "userapprovednonblockingcancellationdesign"
  ],
  "Timestamp": "2026-11-08T20:30:07+08:00"
}


## NET-EXPERT-FW-20261108-READY

{
  "Event ID": "NET-EXPERT-FW-20261108-READY",
  "Task ID": "NET-EXPERT-FW-20261108",
  "From Status": "running",
  "To Status": "ready_for_review",
  "Actor": "SOL",
  "Reason": "Boundedexpertadvice delivered; adoptionwillbereviewedwithcandidate",
  "Evidence": [
    "HANDOFF-NET-EXPERT-FW-20261108"
  ],
  "Timestamp": "2026-11-08T20:35:40+08:00"
}


## NET-FIX-FW-20261108-R0-READY

{
  "Event ID": "NET-FIX-FW-20261108-R0-READY",
  "Task ID": "NET-FIX-FW-20261108",
  "From Status": "running",
  "To Status": "ready_for_review",
  "Actor": "SOL",
  "Reason": "PriorTERRA sourcefrozen forindependentreview andQA",
  "Evidence": [
    "author2026-11-08T20:53:30+08:00handoff",
    "qa-summary-fw-initial.json"
  ],
  "Timestamp": "2026-11-09T01:23:49+08:00"
}


## NET-FIX-FW-20261108-R1-REVISION

{
  "Event ID": "NET-FIX-FW-20261108-R1-REVISION",
  "Task ID": "NET-FIX-FW-20261108",
  "From Status": "ready_for_review",
  "To Status": "running",
  "Actor": "SOL",
  "Reason": "IndependentReviewerNEEDFIX;bounded4findingrevision",
  "Evidence": [
    "REVIEW-NET-FW-20261109-R1",
    "DEC-NET-FW-R1-20261109"
  ],
  "Timestamp": "2026-11-09T01:23:49+08:00"
}


## NET-FIX-FW-20261108-R1-READY

{
  "Event ID": "NET-FIX-FW-20261108-R1-READY",
  "Task ID": "NET-FIX-FW-20261108",
  "From Status": "running",
  "To Status": "ready_for_review",
  "Actor": "SOL",
  "Reason": "AuthorR1frozen; draftsourcecommitforindependentQA/review/compile; notacceptedcompleted",
  "Evidence": [
    "HANDOFF-NET-FIX-FW-20261109-R1"
  ],
  "Timestamp": "2026-11-09T01:31:33+08:00"
}
