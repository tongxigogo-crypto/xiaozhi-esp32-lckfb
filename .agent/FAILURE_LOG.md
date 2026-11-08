# Failure Log

## Purpose

Preserve failed approaches and their causes so agents do not repeat known-invalid work without justified new evidence.

## Filling Rules

- This log is append-only. Never alter or remove an existing failure entry.
- Use ISO-8601 timestamps with a timezone, for example `2026-08-09T14:30:00+08:00`.
- Do not repeat a Prohibited Repeat Attempt unless genuinely new evidence changes the underlying conditions.
- A repeat requires SOL or user approval and must cite that new evidence.
- Every prohibition and repeat decision must link to a Decision ID in the Decision Log.
- Record the authorization as a linked Decision ID.
- Describe the observable outcome and root cause separately; do not substitute speculation for evidence.

## Usage Notes

- copying this template into a project requires explicit initialization.
- if project already has `.agent`, Do not overwrite or merge without explicit user approval.
- project `.agent` records should be committed to Git unless they contain secrets.
- placeholders are not evidence.

## Blank Entry

```yaml
Failure ID:
Task ID:
Failed Approach:
Outcome:
Root Cause:
Prohibited Repeat Attempt:
Decision Reference:
Owner:
Timestamp:
```
