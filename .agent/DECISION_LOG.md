# Decision Log

## Purpose

Record durable decisions, their rationale, considered alternatives, and links to related tasks and failures.

## Filling Rules

- This log is append-only. Add a new decision instead of rewriting decision history.
- Use a unique Decision ID and ISO-8601 timestamps with a timezone, for example `2026-08-09T14:30:00+08:00`.
- Link every affected Task ID and Failure ID; use empty lists only when none apply.
- State alternatives fairly and make the Final Choice explicit.
- The Owner must be the actor authorized to make or record the decision.

## Usage Notes

- copying this template into a project requires explicit initialization.
- if project already has `.agent`, Do not overwrite or merge without explicit user approval.
- project `.agent` records should be committed to Git unless they contain secrets.
- placeholders are not evidence.

## Blank Entry

```yaml
Decision ID:
Related Task IDs: []
Related Failure IDs: []
Decision:
Reason:
Alternatives: []
Final Choice:
Owner:
Timestamp:
```


## DEC-NET-INIT-FW-20261108

{
  "Decision ID": "DEC-NET-INIT-FW-20261108",
  "Related Task IDs": [
    "NET-INIT-FW-20261108",
    "NET-DIAG-FW-20261108"
  ],
  "Related Failure IDs": [],
  "Decision": "User explicitly authorized both agent-directory repair/initialization; preserve all existing files; no deployment/restart/flash",
  "Reason": "Partial firmware records and absent server records blocked engineering; user approved in chat",
  "Alternatives": [
    "read-only inspection only",
    "replace existing files (rejected)"
  ],
  "Final Choice": "backup + per-file comparison + add missing only, then controlled diagnosis/repair/review",
  "Owner": "SOL",
  "Timestamp": "2026-11-08T19:31:40+08:00",
  "Evidence": "/Users/tong/CodexWorkspace/AgentBackups/xiaofeiyu/20261108T193104+0800/comparison-and-added-files.json"
}


## DEC-NET-INIT-AUDIT-FW-20261108

{
  "Decision ID": "DEC-NET-INIT-AUDIT-FW-20261108",
  "Related Task IDs": [
    "NET-INIT-FW-20261108"
  ],
  "Related Failure IDs": [],
  "Decision": "Append superseding precise handoff after independent Reviewer requested evidence details",
  "Reason": "Initial handoff lacked exact command/counts/changed filenames",
  "Alternatives": [
    "editoldhistory (rejected)",
    "appendsupersedingrecord"
  ],
  "Final Choice": "appendonly correction with executableverification",
  "Owner": "SOL",
  "Timestamp": "2026-11-08T19:35:03+08:00"
}


## DEC-WS-DESIGN-FW-20261108

{
  "Decision ID": "DEC-WS-DESIGN-FW-20261108",
  "Related Task IDs": [
    "NET-FIX-FW-20261108"
  ],
  "Related Failure IDs": [],
  "Decision": "UserapprovedcandidateWSkeepalive/telemetry+boundedcontinuous-listeningrecovery; tests/build/review only",
  "Reason": "Verifiedrecoverygap; unknownrecvrootcause keptseparate",
  "Alternatives": [
    "serverkeepaliveonly",
    "firmwarerecoveryonly",
    "approvedcombinedcandidate"
  ],
  "Final Choice": "combinedcandidate; manual/stop/upgrade excluded; no oldaudio/greeting; no productionactions",
  "Owner": "SOL",
  "Timestamp": "2026-11-08T19:40:21+08:00"
}


## DEC-NET-BUILD-AUTH-20261108

{
  "Decision ID": "DEC-NET-BUILD-AUTH-20261108",
  "Related Task IDs": [
    "NET-FIX-FW-20261108"
  ],
  "Related Failure IDs": [
    "FAIL-NET-MAC-PUSH-20261108"
  ],
  "Decision": "Use Windows authenticatedgh/git + temporarybundle relay for candidatebuild; never transfer credentials toMac",
  "Reason": "Mac dry-run push lacksnoninteractivecredential; Windowsalready authenticated workflow account; userapprovedcandidatecompilation",
  "Alternatives": [
    "retryMacunchanged rejected",
    "copytokens rejected",
    "Windowscredentialhelper +bundle chosen"
  ],
  "Final Choice": "Windowsgittemporarybare repository andbundle preservingexactSHAs; artifact-onlyworkflow",
  "Owner": "SOL",
  "Timestamp": "2026-11-08T19:45:51+08:00"
}


## DEC-NET-REMOTE-BASE-20261108

{
  "Decision ID": "DEC-NET-REMOTE-BASE-20261108",
  "Related Task IDs": [
    "NET-FIX-FW-20261108"
  ],
  "Related Failure IDs": [
    "FAIL-NET-REMOTE-REF-20261108"
  ],
  "Decision": "Fetchadvertisedforkbranch50a1be5 ratherthanlocal-only468971c; buildbundleagainstverifiedcommonancestor",
  "Reason": "GitHubAPIbranchlistingadvertises50a1be5; upload-packrejectslocal-onlydocscommit468971c",
  "Alternatives": [
    "retryunadvertisedSHA rejected",
    "fetchverifiedremoteheads chosen"
  ],
  "Final Choice": "fetchfeat/2.5.8-touch-wo2 currentremoteSHA, preservealllocalcandidatecommitsinbundle",
  "Owner": "SOL",
  "Timestamp": "2026-11-08T19:46:37+08:00"
}


## DEC-NET-PROTOCOL-EPOCH-20261108

{
  "Decision ID": "DEC-NET-PROTOCOL-EPOCH-20261108",
  "Related Task IDs": [
    "NET-FIX-FW-20261108"
  ],
  "Related Failure IDs": [],
  "Decision": "AllowadditiveProtocolepoch/cancelinterfaces neededtosafelyownbackgroundOpen lifecycle",
  "Reason": "Oldcallbacksandinflightopensmustnot affectnewsession; narrowsharedinterface supportdirectlyimplementsapproveddesign",
  "Alternatives": [
    "unsafeapplicationrawpointerconcurrency rejected",
    "additivecompatibilityinterface chosen"
  ],
  "Final Choice": "allowprotocol.h/.cc onlyneededadditions; retainlegacycallbacks/MQTTsemantics and120sbusinessidle; testbothcallbackcontracts",
  "Owner": "SOL",
  "Timestamp": "2026-11-08T20:10:53+08:00"
}


## DEC-NET-ASYNC-OWNERSHIP-20261108

{
  "Decision ID": "DEC-NET-ASYNC-OWNERSHIP-20261108",
  "Related Task IDs": [
    "NET-FIX-FW-20261108",
    "NET-EXPERT-FW-20261108"
  ],
  "Related Failure IDs": [],
  "Decision": "Adoptexpertmain-ownedtimer/jobretirementpattern withinapprovedrecoverybehavior",
  "Reason": "Separateintentcancellationfromoldworkerdrain; avoidFreeRTOSC++destructorleak,pendingmanualstarvation,cancel-before-openresurrection,andstaleeventrelabelling",
  "Alternatives": [
    "pollingsleepoccupiesworkerslot",
    "cancellableone-shottimer +singleidentifiednetworkjob"
  ],
  "Final Choice": "mainownsintent,timer,jobslot; workerownsprotocolsharedlifetime only; immutableopenidentityreservedbeforedispatch; sourceidentity/epochcheckedonconsumption",
  "Owner": "SOL",
  "Timestamp": "2026-11-08T20:35:40+08:00"
}


## DEC-NET-FW-EXPERT-TAKEOVER-20261108

{
  "Decision ID": "DEC-NET-FW-EXPERT-TAKEOVER-20261108",
  "Related Task IDs": [
    "NET-FIX-FW-20261108",
    "NET-EXPERT-FW-20261108"
  ],
  "Related Failure IDs": [],
  "Decision": "TransferexclusiveFWimplementationownershipfrompausedLUNA tologicalTERRAexpert forhigh-riskasynccompletion",
  "Reason": "LUNAcheckpointconfirmsreservation API/applicationwiring, sourceepochdeliveryandmain-ownedjobretirementstillincomplete; exceptionalcross-threadTLS/FreeRTOSlifetimejudgmentrequired",
  "Alternatives": [
    "continueunboundedLUNA推演 rejected",
    "rewritewholecontroller rejected",
    "expertfinishminimalexistingcandidate chosen"
  ],
  "Final Choice": "ws_async_lifecycle_expertsoleFWauthor; existing100mscancellablebackoffmayremain ifjobidentity/retirementandmanualresponsivenessproven; userbehaviorunchanged; separateReviewer/QAacceptance",
  "Supersedes In Part": "DEC-NET-ASYNC-OWNERSHIP-20261108 timerimplementationpreferenceonly",
  "Owner": "SOL",
  "Timestamp": "2026-11-08T20:45:26+08:00"
}


## DEC-NET-FW-R1-20261109

{
  "Decision ID": "DEC-NET-FW-R1-20261109",
  "Related Task IDs": [
    "NET-FIX-FW-20261108"
  ],
  "Related Failure IDs": [],
  "Decision": "FreshTERRAauthor ws_fw_finish exclusivelyownsbounded4findingrevision; otherspaused",
  "Reason": "Reviewfoundactualbranchregressionsnotcoveredbyinitialhostlifecyclefixture",
  "Alternatives": [
    "compilebrokenfreeze rejected",
    "narrowactualbranchred-green revision chosen"
  ],
  "Final Choice": "separatecancelretryfromlivechannelinvalidation; explicitstopidle; manualpreserve/reopenvalidsession; AEC/upgradeteardownexactlyonce; atomic.load",
  "Owner": "SOL",
  "Timestamp": "2026-11-09T01:23:49+08:00"
}


## DEC-NET-FW-RESUME-20261109

{
  "Decision ID": "DEC-NET-FW-RESUME-20261109",
  "Related Task IDs": [
    "NET-FIX-FW-20261108",
    "NET-QA-FW-20261108",
    "NET-REVIEW-FW-20261108"
  ],
  "Related Failure IDs": [],
  "Decision": "ResumeR1withfreshindependentactors afterusercontinueandprioragentusageinterruptions",
  "Reason": "Existingcandidate/sourcebranchunchanged,SVhashesverified; FW4consolidatedfindingrevisionstillrequired",
  "Alternatives": [
    "reuseinterruptedunavailableagents",
    "freshboundedexpert+separateQA/Reviewer chosen"
  ],
  "Final Choice": "ws_fw_finish exclusiveauthor; ws_fw_final_qa evidenceonly; ws_fw_final_review independent; no productionactions",
  "Owner": "SOL",
  "Timestamp": "2026-11-09T01:26:25+08:00"
}
