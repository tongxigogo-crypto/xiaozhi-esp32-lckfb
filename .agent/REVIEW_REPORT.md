# Review Report

## Purpose

Capture an independent, evidence-based review of a task's diff, files, tests, findings, and disposition.

## Filling Rules

- This report is append-only. Add a unique Review ID for each review pass.
- Use ISO-8601 timestamps with a timezone, for example `2026-08-09T14:30:00+08:00`.
- Record evidence only: inspected diffs, files, tests, commands, results, and reproducible findings.
- Use `PASS` or `NEED FIX` as the review disposition; leave the other field false.
- A Review Report does not complete a task. Only the SOL may record task completion in the Task Queue.
- Classify findings as Critical, Warning, or Suggestion without inflating severity.

## Usage Notes

- copying this template into a project requires explicit initialization.
- if project already has `.agent`, Do not overwrite or merge without explicit user approval.
- project `.agent` records should be committed to Git unless they contain secrets.
- placeholders are not evidence.

## Blank Entry

```yaml
Review ID:
Task ID:
Reviewer:
Scope:
Diff Inspected: []
Files Inspected: []
Tests Inspected: []
Critical: []
Warning: []
Suggestion: []
PASS: false
NEED FIX: false
Evidence: []
Timestamp:
```


## REVIEW-NET-INIT-20261108-R1

{
  "Review ID": "REVIEW-NET-INIT-20261108-R1",
  "Task ID": "NET-INIT-FW-20261108",
  "Reviewer": "ws_agent_init_review",
  "Scope": "coordination initialization only",
  "PASS": false,
  "NEED FIX": true,
  "Critical": [
    "handoff command/counts/files insufficiently precise"
  ],
  "Evidence": [
    "reviewerchat R1; superseded byR2"
  ],
  "Timestamp": "2026-11-08T19:40:21+08:00"
}


## REVIEW-NET-INIT-20261108-R2

{
  "Review ID": "REVIEW-NET-INIT-20261108-R2",
  "Supersedes": "REVIEW-NET-INIT-20261108-R1",
  "Task ID": "NET-INIT-FW-20261108",
  "Reviewer": "ws_agent_init_review",
  "Scope": "coordination initialization only",
  "PASS": true,
  "NEED FIX": false,
  "Evidence": [
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/verify_initialization.py",
    "Reviewer exit0 at2026-11-08T19:35:38.126074+08:00; preserved8 addedFW7 addedSV8 failed0",
    "QA independentworker chunk75b62c exit0 at2026-11-08T19:33:38.088488+08:00"
  ],
  "Timestamp": "2026-11-08T19:40:21+08:00"
}


## REVIEW-NET-FW-20261109-R1

{
  "Review ID": "REVIEW-NET-FW-20261109-R1",
  "Task ID": "NET-FIX-FW-20261108",
  "Reviewer": "ws_candidate_review independentReviewer",
  "Scope": "FWfullsource+CI",
  "PASS": false,
  "NEED FIX": true,
  "Critical": [
    "atomiccopycompilefailure",
    "Togglelisteningneveridle",
    "speaking->manualinvalidatescurrentchannel",
    "AEC/Upgradeepochinvalidationpreventsclose"
  ],
  "Evidence": [
    "ReviewerformalR1chat",
    "actualsourcebranches; isolatedclangatomiccopyexit1"
  ],
  "Timestamp": "2026-11-09T01:23:49+08:00"
}
