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
