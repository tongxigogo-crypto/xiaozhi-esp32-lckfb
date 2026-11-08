# Asset Registry

## Purpose

Track versioned assets, provenance, integrity, approvals, and synchronization across Web and Mini surfaces, including conditional 3D metadata.

## Filling Rules

- This registry is append-only. Do not overwrite an existing asset version; create a new Asset ID or Asset Version entry.
- Use ISO-8601 timestamps with a timezone, for example `2026-08-09T14:30:00+08:00`.
- Placeholders, descriptions, and visual claims are not evidence. Record SHA-256 and link render or screenshot verification.
- For literal policy matching: placeholders are not evidence.
- Approval State must be one of `draft`, `ready_for_review`, `approved`, `rejected`, or `superseded`.
- Synchronization State must be one of `not_applicable`, `not_started`, `web_only`, `mini_only`, `pending_verification`, or `verified_synced`.
- Follow the lifecycle: `analysis -> versioned asset -> render/screenshot verification -> human confirmation -> Web/Mini synchronization`.
- Human confirmation is required before `approved` and before claiming final Web/Mini synchronization.
- For 3D assets, inspect and change in this order: `geometry -> hierarchy -> pivot -> material -> lighting`.
- Complete GLB Version, Node Hierarchy, Material Changes, Blender Source, and Blender Version when the asset is 3D; otherwise record `not_applicable`.
- Use Web/Mini synchronization states only when those delivery surfaces apply; otherwise record `not_applicable`.
- Link the Related Task and Related Decision that authorize the asset or its change.

## Usage Notes

- copying this template into a project requires explicit initialization.
- if project already has `.agent`, Do not overwrite or merge without explicit user approval.
- project `.agent` records should be committed to Git unless they contain secrets.
- placeholders are not evidence.

## Blank Entry

```yaml
Asset ID:
Asset Version:
SHA-256:
Source:
Tool/Source Version:
Purpose:
Reason for Change:
GLB Version:
Node Hierarchy: []
Material Changes: []
Blender Source:
Blender Version:
Approval State: draft
Synchronization State: not_started
Related Task:
Related Decision:
Owner:
Timestamp:
```
