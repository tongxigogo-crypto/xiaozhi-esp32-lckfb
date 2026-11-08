# Project execution learnings

## 2026-11-06 - Superseded candidate identities must leave the current report

- Context: 2.5.6 candidate33d7bdf was rejected; c46a91d replaced it.
- Signal: A final notice was appended but the current report body retained the rejected app hash; the acceptance page also embedded an initial QA identity snapshot.
- Rule: Generate current identity fields from latest-release.json only after hashing actual artifacts. Archive the original report byte-for-byte with an explicit rejected-candidate name; keep one current report. Do not present historical identity snapshots as current validation data.
- Scope: Xiaofeiyu firmware release documents and browser acceptance page.
- Action: Compare actual Mac/Windows files, checksum file, manifest, current report, PR and structured page identity. Search for superseded app hashes in every current-facing document and expanded evidence. Keep raw historical QA immutable. Documentation commits do not change the firmware build identity or authorize flashing.

## 2026-11-09 - 构建身份与受限审计交付

- Context: WebSocket 修复已独立审查、云编译并核验，后续仅追加审计记录。
- Signal: 可选的最终审计远端推送被执行工具自动审批拒绝，返回 blocked by policy，未给出细因。
- Rule: 分开记录实际编译提交与审计 HEAD；审批拒绝后不得通过拆命令、换工具绕过同一被拒动作。已完成的代码/产物可用本地报告交付。
- Scope: 本机器人固件的候选构建与交付。
- Action: manifest 保留 firmware_source_commit 和 firmware_audit_commit；记录失败与决策，保持本地审计提交，导出只读报告，生产部署/烧录仍等待用户确认。
