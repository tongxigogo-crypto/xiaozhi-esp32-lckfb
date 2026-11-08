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


## HANDOFF-NET-DIAG-FW-20261108

{
  "Handoff ID": "HANDOFF-NET-DIAG-FW-20261108",
  "Task ID": "NET-DIAG-FW-20261108",
  "Executing Agent": "ws_firmware_diagnosis (genericworker, notDeepSeekruntime)",
  "Completed Work": [
    "readonlycode/log/configdiagnosis; boundedcandidateproposal"
  ],
  "Changed Files": [],
  "Verification": {
    "Command": "git diff --stat317748c..468971c --main (FW); SSHreadonlyselectednginx/log/configchecks (SV); exactfindings inevidencefile",
    "Exit Status": 0,
    "Relevant Counts": {
      "functionaltests": 0
    },
    "Timestamp": "2026-11-08T19:42:10+08:00",
    "Known Gaps": [
      "recvrootcauseunproven",
      "nophysicalrecoverytests"
    ]
  },
  "Evidence": [
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/diagnostic-evidence.json"
  ],
  "Findings": [
    "confirmedcontinuous-listeningrecoverygap",
    "nginx3600stimeoutcontradicts35sconfigurationhypothesis"
  ],
  "Timestamp": "2026-11-08T19:42:10+08:00"
}


## HANDOFF-NET-EXPERT-FW-20261108

{
  "Handoff ID": "HANDOFF-NET-EXPERT-FW-20261108",
  "Task ID": "NET-EXPERT-FW-20261108",
  "Executing Agent": "ws_async_lifecycle_expert (logicalTERRA, default runtime)",
  "Completed Work": [
    "bounded5-sectionasynclifecycleassessment;5proofsequencesprovided"
  ],
  "Changed Files": [],
  "Verification": {
    "Command": "readonlycurrentApplication/Protocol sourceinspection viaSSH",
    "Exit Status": 0,
    "Relevant Counts": {
      "testsexecuted": 0,
      "proofsequencesrecommended": 5
    },
    "Timestamp": "2026-11-08T20:35:40+08:00",
    "Known Gaps": [
      "implementationandtestsremainLUNAresponsibility",
      "finalindependentreviewandQApending"
    ]
  },
  "Evidence": [
    "DEC-NET-ASYNC-OWNERSHIP-20261108",
    "expertfinal5-sectionreportinchat"
  ],
  "Timestamp": "2026-11-08T20:35:40+08:00"
}


## HANDOFF-NET-FIX-FW-20261108-LUNA-CHECKPOINT

{
  "Handoff ID": "HANDOFF-NET-FIX-FW-20261108-LUNA-CHECKPOINT",
  "Task ID": "NET-FIX-FW-20261108",
  "Executing Agent": "ws_firmware_implementation LUNA",
  "Completed Work": [
    "policyandpreliminaryapp/protocolcandidate",
    "additivereservation/sourceepochinterfaces"
  ],
  "Changed Files": [
    "main/application.h/.cc",
    "main/protocols/protocol.h/.cc",
    "main/protocols/websocket_protocol.h/.cc",
    "main/protocols/mqtt_protocol.h/.cc",
    "main/protocols/connection_recovery.h/.cc",
    "main/CMakeLists.txt",
    "scripts/tests/test_connection_recovery_policy.cc",
    "scripts/tests/test_connection_recovery_policy_runner.py",
    "scripts/tests/test_connection_recovery_wiring.py"
  ],
  "Verification": {
    "Command": "policyandwiringrunners (authorcheckpoint; exactlatestAPIrerunpending)",
    "Exit Status": 0,
    "Relevant Counts": {
      "policytest_passed": 1,
      "wiringtests_passed": 5
    },
    "Timestamp": "2026-11-08T20:45:26+08:00",
    "Known Gaps": [
      "latestprotocolAPIeditsnotrerun",
      "Applicationreservation/sourceepoch/jobretirementnotfinished",
      "cloudcompile/hardwarepending",
      "initialredoutputnotretained"
    ]
  },
  "Next Recommendation": "boundedexpertcompletion; noacceptanceyet",
  "Timestamp": "2026-11-08T20:45:26+08:00"
}


## HANDOFF-NET-FIX-FW-20261109-R1

{
  "Handoff ID": "HANDOFF-NET-FIX-FW-20261109-R1",
  "Task ID": "NET-FIX-FW-20261108",
  "Executing Agent": "TERRA ws_fw_finish",
  "Completed Work": [
    "atomicload",
    "explicitstopidle",
    "manualvalidchannel/reopen",
    "AEC/upgradeteardownonce"
  ],
  "Changed Files": [
    "main/application.cc",
    "main/application.h",
    "scripts/tests/test_connection_recovery_lifecycle.py",
    "scripts/tests/test_connection_recovery_wiring.py",
    "scripts/tests/test_connection_recovery_controls.py"
  ],
  "Verification": {
    "Command": "python3 -m unittest discover -s scripts/tests -p test_connection_recovery*.py -v",
    "Exit Status": 0,
    "Relevant Counts": {
      "newtests": 15,
      "regressiontests": 10,
      "skipped": 0
    },
    "Timestamp": "2026-11-09T01:31:33+08:00",
    "Known Gaps": [
      "independentQA/review andESP-IDFcompilepending",
      "hardwarepending"
    ]
  },
  "Evidence": [
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/ws-fw-r1-green.log",
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/ws-fw-r1-red-controls.log"
  ],
  "Timestamp": "2026-11-09T01:31:33+08:00"
}
