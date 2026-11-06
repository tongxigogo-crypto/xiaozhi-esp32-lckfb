# Project execution learnings

## 2026-11-06 - Superseded candidate identities must leave the current report

- Context: 2.5.6 candidate33d7bdf was rejected; c46a91d replaced it.
- Signal: A final notice was appended but the current report body retained the rejected app hash; the acceptance page also embedded an initial QA identity snapshot.
- Rule: Generate current identity fields from latest-release.json only after hashing actual artifacts. Archive the original report byte-for-byte with an explicit rejected-candidate name; keep one current report. Do not present historical identity snapshots as current validation data.
- Scope: Xiaofeiyu firmware release documents and browser acceptance page.
- Action: Compare actual Mac/Windows files, checksum file, manifest, current report, PR and structured page identity. Search for superseded app hashes in every current-facing document and expanded evidence. Keep raw historical QA immutable. Documentation commits do not change the firmware build identity or authorize flashing.
