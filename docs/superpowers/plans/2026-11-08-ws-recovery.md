# WebSocket resilience implementation plan

> For agentic workers: use superpowers:subagent-driven-development and test-driven-development. Implement only the approved design in the adjacent specification.

Goal: repair lost continuous-listening recovery and provide bounded keepalive plus safe disconnect evidence.
Architecture: small host-testable firmware recovery policy with application-owned lifecycle; independent server transport configuration/telemetry helpers.
Tech stack: ESP-IDF6.1 C++ firmware, Python3.10 websockets14.2.

## Task FW: NET-FIX-FW-20261108, LUNA firmware worker
Ownership: main/application.h/.cc; main/protocols/websocket_protocol.h/.cc only where required for connectionepoch/callback evidence; new main/protocols/connection_recovery.h or equivalent focusedmodule; scripts/tests/ recovery tests/runner; narrowlyrequiredCItestentry. No board/assets/NVS/generated/vendor changes. SOL owns .agent and thisplan.
- [ ] Readrequiredrecords/repoAGENTS andcurrentowningimplementations.
- [ ] Writeactual-policy/adapterregressions andrunred with clang++ -std=c++17 -Wall -Wextra -Werror via Pythonrunner.
- [ ] Implementminimumcontinuous-intent/retryepochpolicy andactualappconnectioncallbacks, preservemanualstop andexistingwakepaths.
- [ ] Runnewtests green plus existingrelevanthostsuite, verifycancel/openneverblocks main/audio.
- [ ] Provideexactchangedfiles/red-greencommands/counts/gaps andhandoff; do notselfapprove/commit/push unlessSOLinstructs.

## Task SV: NET-FIX-SV-20261108, LUNA server worker
Ownership: core/websocket_server.py, core/connection.py minimalwiring; new core/utils/connection_telemetry.py/helper ifuseful; config.yaml onlydocumentedcandidatekeys; new test_websocket_recovery.py. SOL ownscoorddocs.
- [ ] Readrecords; writefailingvalidation/telemetry/localrealwebsockettests first. Useisolatedlogging/state; noprivatememory.
- [ ] Implementvalidatedconfigurablekeepalive15/20/disable andexactlyoncesafecloseevents normal/abnormalpaths.
- [ ] Runlocalreal1000/1011/TCPabort/pingpongtests plusactualwrapperforwarding; verify auth/TLS/securitynotweakened andnofreeformdata.
- [ ] Runappropriateregression; handoffexactevidence/gaps. No productionstate/restart/deploy, no commitswithoutSOL.

## Integration, SOL + independentReviewer/QA
- [ ] Reviewerreadactualdiff includingrace/lifecycles/closing whileopening; returnPASS/NEEDFIX.
- [ ] QA rerunmeaningfulnewtestsandrequiredregression inisolatedtemporarydirs, recordexactcommands/exits/counts/times.
- [ ] Compilefirmwarecandidate withexistingartifact-onlyworkflow, preserveoriginalrollbackartifacts; verifyactualdependencyPongimplementation andflashpartitions/hashes.
- [ ] SOLacceptscompletedonlyafterReviewPASS+QA; committrackedcandidate andappendhistory. Userconfirmationbeforeanyproductionaction.
