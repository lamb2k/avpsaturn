# Next implementor prompt: RP6 semantic scene manifest

## Invocation request

Continue implementation in:

`C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest`

Execute the bounded RP6 body below. RP4 passed interim review at `671eca8`
(offline reconstruction exact, live contract proven, fixture isolated); Codex
ratification of that acceptance is still pending and may reopen it.

Use the `port-cps2-to-sega-saturn` skill. Read completely, in order:

1. `AGENTS.md`;
2. `docs/GOAL.md`;
3. `docs/AGENT_HANDOFF.md`;
4. `docs/PARITY_PLAN.md`;
5. `docs/ROUND1_EXECUTION_PLAN.md`;
6. `docs/ARCHITECTURE.md`;
7. `docs/TEST_PLAN.md`;
8. this file.

Then run from this independent repository:

```powershell
git status --short --branch
git log --oneline -10
Get-Process mame,yabasanshiro* -ErrorAction SilentlyContinue
```

Expected branch is `codex/avp-master-plan`. Preserve all unrelated dirty and
untracked work. Do not reset, clean, stash, switch branch, or bulk-stage.

## Scope lock: RP6 only

Use RP2's grouped full route (`data/round1_route_census.json`, 122 groups over
frames 1..18000, plus the private cadence-1 capture) to produce the
authoritative semantic scene manifest. For every group record:

- source state/frame range (from the census, MEASURED);
- provisional bit-15 ID (from the census);
- final stable ID: content-addressed from the group signature so it survives
  re-capture and re-grouping, not order-derived;
- input dependency: whether and when the composite input schedule was active
  during the group (census `input_word_runs`);
- layer/object composition: layer bases, video control, object count range,
  scroll spans, row-scroll usage;
- audio events: QSound change count (audio payloads stay private);
- transition target: the next group's final stable ID plus the boundary
  reason.

Semantic labels are evidence-bound: label a scene only from measured anchors
(prior committed measurements or reviewed private screenshots); every other
group keeps `label: null` with a review flag. Unknown IDs remain hard
diagnostic errors in the runtime; do not coerce or skip.

Deliverables:

1. `tools/gen_avsp_scene_manifest.py` — deterministic generator from the
   tracked census (private capture optional for enrichment);
2. `data/avsp_scene_manifest.json` — tracked manifest (hashes, counts, ranges
   and labels only; no ROM bytes, no payloads);
3. `tools/verify_scene_manifest.py` — structural gate: complete route tiling,
   unique stable IDs, consistent transition chain, census cross-check, and
   negative controls; wire into `test.ps1`;
4. handoff update with evidence and label coverage.

## Do not

- Do not implement RP5 residency, RP7, or content batches in this body.
- Do not advance Capability Gate counts.
- Do not commit ROMs, captures, screenshots, audio, or payload bytes.
- Do not invent semantic labels without measured evidence.

## After RP6

RP5 (pessimistic G0/CDDA residency measurement) is the next dependency-ready
package, then RP7 per `docs/ROUND1_EXECUTION_PLAN.md`.
