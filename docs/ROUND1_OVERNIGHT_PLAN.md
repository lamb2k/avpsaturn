# Round 1 overnight sequence: census-first closure to a playable round

Owner directive, 2026-08-31. Motivation: the runtime is stalled at source
frame 5566 because that is exactly where accepted ORACLE-10/11 authority
ends (`oracle11_round1_encounter_route_authority.json` scope is "Coffee
Shop entry through exit stabilization", frames 1972-5566). Every future
body would re-pay a capture round-trip at its own frontier. Extend the
evidence frontier across all of Round 1 first, then close bodies against
it without waiting. This sequences existing accepted work; it rotates no
plan, reopens no lock, and changes no evidence standard.

## Phase order (strict)

**P0 - finish in-flight closure.** Complete the Coffee Shop exit
controller (route edges 5453/5524/5562, load boundaries 5565/5566) with
accepted evidence or the smallest fixture amendment; checkpoint.

**P1 - capture-lane integration.** Execute `docs/EMULATOR_MCP_CAPTURE.md`
in full (package, re-pin, negative controls A/B, MCP visual-QA mode).
Burst PNGs and manifests live under `generated/mcp_captures/<scene>/`
(ignored); commit only manifest SHA-256 values and analysis reports.

**P2 - evidence frontier extension (the overnight bulk).** Extend the
deterministic source route and ORACLE-10/11 census from source frame 5566
to Round 1 clear stabilization (round-end results, the Round1->2 seam that
USER-10 labels ADAPTED). Same schema, same ceremony as the 1972-5566
census: paired byte-identical cold captures (cs50a/cs50b discipline),
per-frame character-identity gates, perturbation and counterfactual
controls. Deliverables, committed per segment as they complete:
- route-authority extension: segments, route_state_transitions,
  camera_lock_runs, load/release boundaries, audio events;
- scene census delta: class_type_inventory additions with selectors,
  actor lifetimes, health writes, pool scans;
- table-demand delta vs the accepted 152-table cart archive - report any
  table the memory plan does not bind; do not squeeze or re-plan memory.

**P3 - batched SPEC-02 completion.** For every new class/program family in
the P2 census: whole-routine bodies decoded offline from the decrypted
opcode image, validated against retained ledgers, a5-relative globals
fixture rows, ceremony once per body (2026-08-30 amendment). Live capture
only where retained ledgers cannot witness a behaviour.

**P4 - scene-order closure.** REIMPLEMENT-13 implements bodies in the
order the extended route demands them. Per closed transition: focused
mutation lanes plus a burst visual gate (cadence-1 contact sheet over the
transition window from the MCP lane; ONE_EMULATOR tier; scenes stay RED
until accepted criteria pass; WGC only for USER packages).

## Autonomy rules for the unattended run

- Attempt cap: a body that resists three focused attempts gets its blocker
  recorded on the card, then move to the next body in scene order. Never
  rotate the plan, self-accept, invent states ahead of the owning program,
  or reopen accepted locks.
- Checkpoint commit+push after every closed body, every completed census
  segment, and every phase boundary. Stage explicit paths only; never
  touch `data/avsp_anim_records.json` or `history.txt`.
- Emulator hygiene: capture runs set `Video\VideoCore=1` and
  `Sound\SoundCore=0` and restore `4`/`1` after; kill stray emulator
  processes between runs; never commit ROMs, ISOs, PNGs, or dumps.
- Morning report (in the handoff plus card notes): phases reached, census
  segments completed with hashes, bodies closed vs RED with one-line
  blockers, and the exact resume point.
