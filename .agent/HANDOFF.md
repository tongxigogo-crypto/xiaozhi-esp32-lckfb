# Handoff

## Purpose

Transfer completed execution context and inspectable evidence from an executing agent to the next responsible actor.

## Filling Rules

- This log is append-only. Add one entry per handoff and never edit prior entries.
- Do not replace another task entry. Use a unique Handoff ID tied to exactly one Task ID.
- Use ISO-8601 timestamps with a timezone, for example `2026-08-09T14:30:00+08:00`.
- Verification evidence must include the command, exit status, relevant counts, timestamp, and known gaps.
- List changed files precisely; do not claim files that were not inspected.
- If records or handoffs conflict, stop and escalate the conflict to the SOL rather than choosing one silently.
- In short: escalate to SOL.

## Usage Notes

- copying this template into a project requires explicit initialization.
- if project already has `.agent`, Do not overwrite or merge without explicit user approval.
- project `.agent` records should be committed to Git unless they contain secrets.
- placeholders are not evidence.

## Blank Entry

```yaml
Handoff ID:
Task ID:
Executing Agent:
Completed Work: []
Changed Files: []
Verification:
  Command:
  Exit Status:
  Relevant Counts: {}
  Timestamp:
  Known Gaps: []
Findings: []
Risks: []
Next Recommendation:
Timestamp:
```


## HANDOFF-NET-INIT-FW-20261108

{
  "Handoff ID": "HANDOFF-NET-INIT-FW-20261108",
  "Task ID": "NET-INIT-FW-20261108",
  "Executing Agent": "SOL",
  "Completed Work": [
    "backup existing firmware.agent and compare every original file",
    "copy onlymissingtemplatefiles; initialize absent server.agent"
  ],
  "Changed Files": [
    ".agent/ missing records only; existing firmware records untouched"
  ],
  "Verification": {
    "Command": "SHA256 and byte-for-byte original/backup/new comparisons",
    "Exit Status": 0,
    "Timestamp": "2026-11-08T19:32:42+08:00",
    "Known Gaps": [
      "independent Reviewer/QA pending"
    ]
  },
  "Evidence": [
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/comparison-and-added-files.json"
  ],
  "Timestamp": "2026-11-08T19:32:42+08:00"
}


## HANDOFF-NET-INIT-FW-20261108-V2

{
  "Handoff ID": "HANDOFF-NET-INIT-FW-20261108-V2",
  "Supersedes": "HANDOFF-NET-INIT-FW-20261108",
  "Task ID": "NET-INIT-FW-20261108",
  "Executing Agent": "SOL",
  "Completed Work": [
    "firmware: preserved8originalrecords and added7missing only"
  ],
  "Changed Files": [
    ".agent/HANDOFF.md",
    ".agent/FAILURE_LOG.md",
    ".agent/DECISION_LOG.md",
    ".agent/TASK_QUEUE.md",
    ".agent/REVIEW_REPORT.md",
    ".agent/CHANGELOG.md",
    ".agent/ASSET_REGISTRY.md"
  ],
  "Verification": {
    "Command": "ssh -o BatchMode=yes codex-mac-tong python3 /Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/verify_initialization.py",
    "Exit Status": 0,
    "Relevant Counts": {
      "original_firmware_preserved": 8,
      "firmware_added": 7,
      "server_added": 8,
      "failed": 0
    },
    "Timestamp": "2026-11-08T19:35:03+08:00",
    "Known Gaps": [
      "functionalrepairnotstarted",
      "independentrevieweracceptancepending"
    ]
  },
  "Evidence": [
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/comparison-and-added-files.json",
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/verify_initialization.py",
    "QA chunk75b62c at2026-11-08T19:33:38.088488+08:00 exit0"
  ],
  "Timestamp": "2026-11-08T19:35:03+08:00"
}
