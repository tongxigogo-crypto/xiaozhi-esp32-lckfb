# Changelog

## Purpose

Record accepted project changes in a concise audit trail tied to tasks, affected artifacts, and acceptance authority.

## Filling Rules

- This log is append-only. Add a new Entry ID; never rewrite accepted history.
- Use ISO-8601 timestamps with a timezone, for example `2026-08-09T14:30:00+08:00`.
- The Recording Actor identifies who wrote the entry; the Acceptance Owner identifies who accepted the change.
- The SOL records accepted changes only after acceptance is established through parseable Acceptance Evidence; an Acceptance Owner declaration alone is insufficient.
- List affected files and assets precisely and link the originating Task ID.
- Link the applicable review and decision records. Use an explicit `not_applicable` only when no such record is required.

## Usage Notes

- copying this template into a project requires explicit initialization.
- if project already has `.agent`, Do not overwrite or merge without explicit user approval.
- project `.agent` records should be committed to Git unless they contain secrets.
- placeholders are not evidence.

## Blank Entry

```yaml
Entry ID:
Task ID:
Recording Actor: SOL
Summary:
Affected Files/Assets: []
Acceptance Owner:
Accepted At:
Acceptance Evidence: []
Related Review ID:
Related Decision ID:
Timestamp:
```


## CHANGE-NET-INIT-FW-20261108

{
  "Entry ID": "CHANGE-NET-INIT-FW-20261108",
  "Task ID": "NET-INIT-FW-20261108",
  "Recording Actor": "SOL",
  "Summary": "Authorizedmissingrecords initialization accepted; originalfirmwarerecords untouched",
  "Affected Files/Assets": [
    "new.agent records only; exactlist inhandoffV2"
  ],
  "Acceptance Owner": "SOL",
  "Accepted At": "2026-11-08T19:40:21+08:00",
  "Acceptance Evidence": [
    "REVIEW-NET-INIT-20261108-R2",
    "QA chunk75b62c"
  ],
  "Related Review ID": "REVIEW-NET-INIT-20261108-R2",
  "Related Decision ID": "DEC-NET-INIT-FW-20261108",
  "Timestamp": "2026-11-08T19:40:21+08:00"
}


## CHANGE-NET-FW-20261109

{
  "Entry ID": "CHANGE-NET-FW-20261109",
  "Task ID": "NET-FIX-FW-20261108",
  "Recording Actor": "SOL",
  "Summary": "Accepted software candidate 986aabd: finite auto/realtime session recovery, safe cancellable network-task ownership, source/epoch isolation and preserved MQTT controls; cloud build and independent artifacts verified",
  "Affected Files/Assets": [
    ".github/workflows/build-lckfb.yml",
    "main/CMakeLists.txt",
    "main/application.cc",
    "main/application.h",
    "main/protocols/connection_recovery.cc",
    "main/protocols/connection_recovery.h",
    "main/protocols/mqtt_protocol.cc",
    "main/protocols/mqtt_protocol.h",
    "main/protocols/protocol.cc",
    "main/protocols/protocol.h",
    "main/protocols/websocket_protocol.cc",
    "main/protocols/websocket_protocol.h",
    "scripts/tests/test_connection_recovery_controls.py",
    "scripts/tests/test_connection_recovery_dispatch.py",
    "scripts/tests/test_connection_recovery_lifecycle.py",
    "scripts/tests/test_connection_recovery_policy.cc",
    "scripts/tests/test_connection_recovery_policy_runner.py",
    "scripts/tests/test_connection_recovery_wiring.py"
  ],
  "Acceptance Owner": "SOL",
  "Accepted At": "2026-11-09T01:55:25.498288+08:00",
  "Acceptance Evidence": [
    "REVIEW-NET-INTEGRATION-20261109-R4",
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/fw-r2-qa-summary.json",
    "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/artifact-qa-summary.json",
    "Actions42506218869 success"
  ],
  "Related Review ID": "REVIEW-NET-INTEGRATION-20261109-R4",
  "Related Decision ID": "DEC-NET-FW-R2-20261109",
  "Known Gaps": [
    "no physical acceptance or release authorization; update bundle excludes cold-flash support images"
  ],
  "Timestamp": "2026-11-09T01:55:25.498288+08:00"
}
