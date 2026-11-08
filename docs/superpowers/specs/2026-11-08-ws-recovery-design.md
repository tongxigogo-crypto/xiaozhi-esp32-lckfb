# WebSocket resilience candidate — approved design

User approved implementation in chat on 2026-11-08 Asia/Shanghai. No deployment, restart, flashing, production configuration edit, OTA publication or main-branch merge is authorized.

## Evidence and scope
- Serial /tmp/xfy-serial-ts2.csv: handshake/listening19:19:55, recv -76 at19:20:30, idle through last19:20:59 event.
- -76 means receive failure; no packet-level RST proof. Preserve this distinction in all delivery records.
- VPS nginx WS read/send timeout3600s; frps/frpc available logs do not identify the data-stream failure.
- Server39f36a4 explicitly disables periodicPing. Actual websockets14.2 supports keepalive.
- Firmware317748c main/ equals checked-out468971c main/. Boot starts continuous listening, but unexpectedclose onlyentersidle.
- Actual device mode was realtime; auto is also continuous, selected byAEC. manual mustnotautorecover.

## Approved behavior
1. Preserve a distinct continuous-listening intent. Unexpected transportloss while auto/realtime intent remainsvalid triggers finite exponentialbackoff (target five attempts, delays1/2/4/8/16sec); successfulhandshake restores exactpriorlistenmode once.
2. manual, explicitstop/BOOTstop, upgrade, reset orsuperseding sessioncancel retryintent. Repeatedclose/latecallbacks cannotcreateparallelopens ormutatenewsession.
3. Recovery opensnetwork/hello andsendlisten/start only. Never invokewakeword greeting/detect, proactive_speak/TTS, replayoldmic packets oroldassistantframes. No authentication/TLS weakening; no NVS/schema/board-pin/assets changes.
4. Network callbacks onlysignal events. Don'tdestroy/reconnect fromTLSreceive callback. A potentially10-second hello wait mustnotblockmain/audio; use boundedlifecycle-safe worker ownership/cancellation.
5. Server configurableWebSocketpinginterval15sec, timeout20sec as candidate defaults, with explicitdisable support andvalidatedfinitepositivevalues; no liveconfigchanges. VerifyexistingESPclientPonglineage/build dependency andlocalprotocolcompatibility. Treatheartbeat as resilience/observation, notprovenfixforthe35secrootcause.
6. Addsafeconnection-close telemetry for normaliteratorcompletion andabnormalConnectionClosed: correlation/sessionID, monotonicage, received/sentclosecodes andorder, exceptiontype/numericerrno. Neverlogheaders/tokens/payloads/arbitraryclosereason/exceptiontext.
7. Preserveexisting120sec business-idle semantics insharedProtocol/MQTT; serverPing isnotbusinessdata. Documentandtestboundary ratherthan silently changing it.
8. Deliveredcode is a reviewablecandidate. Integration/evidence gaps mustbeexplicit; cloudbuild producesartifacts only, neverflash/deploy.

## Validation
Hostdeterministicpolicy/adaptertests cover auto/realtime/manual, intentionalclose, finitebackoff/retryexhaustion, cancellation/stalegeneration, duplicatecallbacks, hello/openfailure, Wifidown, successfulrestore andnooldaudio/greeting. Tests should proveactualapplication/protocolwiring, notsolelyhelperbehavior.
Server localrealwebsockets tests covernormal1000close,1011close, abruptTCPabort andping/pong; telemetryexcludesarbitraryreason/secrets andisexactlyonce. Existingsecurity/autonomy/memoryregressions remain.
Compileactuallichuang-dev usingexistingESP-IDF6.1workflow/boardconfiguration andrecordcommit, logs andhashes. Do not claimdevicebehaviorfrombuildsuccess. IndependentReviewer + separateQA evidence required beforeSOL acceptance; final deployment/flash waitsuserconfirmation.
