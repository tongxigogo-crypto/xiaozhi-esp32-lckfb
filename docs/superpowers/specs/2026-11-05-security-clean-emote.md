# 2.5.5 security and clean-emote setup

User requested all access protections enabled while retaining protected Mac control, plus fixing missing status-icon resources. Continue the same Mac checkout from 4a8964aaee1df6e4c1a77ec0c497a2dad200703a; preserve the installed2.5.4 package and other agents' status commits. Codex develops/configures; Gemini3.8Flash independently reviews. New firmware is prepared, not flashed before explicit device handoff/authorization.

Design:
- Strict private per-device credential for WebSocket, stored in existing device NVS websocket.token and private server policy; never compile secrets into open-source firmware or commit them.
- Remove MAC allowlist token bypass. Public OTA returns public connection/version metadata only and never issues device credentials. An identity header alone is not authentication.
- Serve trusted HTTPS/WSS from VPS and close plaintext public backend paths after migration is verified. Use public-IP certificate if no domain is configured, with automatic renewal and restart reload checks.
- Preserve existing fixed signing key for vision and per-camera token refresh; unknown battery remains hidden.
- Keep Mac control enabled only behind successfully authenticated device sessions, retaining operation confirmation guards.
- Clean emote layout has no status-icon widgets. Stop obsolete icon requests in the owning event adapter; use existing expressions and mode/state overlay, no fake icons/extra binaries.

Execution:
1. Back up live private configuration and current device NVS; inspect official NVS parser/generator to preserve every existing logical key when provisioning. Device read/write waits for ownership answer.
2. Reproduce anonymous/forged/expired/white-list-bypass cases, add tests, implement server policy and public OTA metadata contract.
3. Independently fix missing-icon event handling with tests against pinned expression1.0.2.
4. Set up TLS candidate endpoints/renewal, validate certificate, WSS, strict auth negative cases and device-owned positive case before switching defaults or closing old routes.
5. Prepare version2.5.5 if firmware changes required. Gemini reviews committed diffs/tests; cloud compile and exact artifact hashes match source.
6. Deploy only authorized configuration steps and device provisioning after confirmed handoff; preserve rollback. Sync Agent/Obsidian and distinguish code/endpoint/device evidence.

Acceptance: anonymous/forged/missing credentials denied including allowed MAC; OTA cannot mint credentials from spoofed IDs; valid paired device works over verified TLS; actual Mac controls retain confirmation; no missing icon/listen errors in clean display path; no secrets in Git/logs. Pending external gates are recorded precisely.

## WorkBuddy v1 handoff accepted 2026-11-05T21:23:28+0800

Stable complete report: /Users/tong/Desktop/网页设计/机器人diy/00-现行基线/派工单-2.5.4-真机问题-v1.0-2026-11-05.md; SHA256 cd14139174c5d320d7e98a800c59d1ed9b11319170225fd06438b40bc2e760b7. Add boundedstream gate parsing fornormal+direct_answer, syncpluginoffload/boundednoteslookup, timeoutfallback and exactlyoneLAST. Reportlen4hypothesis notconfirmed: oldcodealreadybufferedleadingbracket; direct_answer bypass reproduced. Resource-onlydeletion advice contradictsexistingcleanlayout andpinnedengineorder. Newfirmware2.5.5 mustenableTLSdatecheck +coldbootSNTP beforeassets/OTA, fixserver-timeUTCoffsetbug. Userexplicitlyauthorizeddeviceconfigwrites andhandedoverserial; freshNVSbackupmadeandvalidated. Firmwareapplicationwrite stillpreparedforfinalreview ratherthanreuseold2.5.4package.
