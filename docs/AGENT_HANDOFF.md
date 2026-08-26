# Active checkpoint

`project_state.yaml` is the machine-readable source of truth and
`docs/PARITY_PLAN.md` is the only roadmap. Continue sequentially on
`codex/avp-playable-loop-pivot`; preserve dirty/private worktrees, ignored
evidence, recovery patches, ROMs, captures, and component-scoped user locks.

## Workflow pivot / Preserved evidence work

- Preserve `SALVAGE-00-OLD-BUILD-BASELINE`,
  `USER-01-PLAYER-BASELINE-REVIEW`, V2-2B
  `597f4ed517d4e715d814ff841bd00d3977803f85`, and all accepted component locks.
- REPAIR-11 is accepted at `236eef0` with evidence `35d527e`; its camera/plane
  bridge, attack sequence, class-`0x1F` tracking, and presentation locks remain.
- HW-01 is parked `READY_FOR_PHYSICAL`; physical Saturn remains `UNRUN`.
- USER-09 remains `CHANGES_REQUESTED`; no approval is inferred.

## Current task and next action

Resume the AvP salvage Goal at
`ORACLE-11-ROUND1-REACHABLE-LOGIC-CLOSURE`; it remains active. Actor
scheduler/lifecycle and Predator Warrior locomotion/neutral/facing, melee,
normal jump, directional/airborne actions, interruption cancellation, and
weapon/projectile/resource ownership are source closed. Player nonlethal HIT,
lethal KO, failure/continue, respawn initialization, and return-to-control are
also source closed. The latest checkpoint
reconciles the full-route phase census with input-only counterfactuals: required
phases `0x0400/02/04/06/0a/0c/0e/10` are closed, while unwitnessed
`0x0408/12/14` are explicit `NOT_REQUIRED_FOR_ROUND1`. Natural health pickup,
the source class-`0x0e` temporary-resource grant, interaction completion and
interruption, packed-BCD score award, and player-to-route load/release edges
are now also closed. Every route-observed player phase is mapped. Static and
dynamic evidence corrected `0x0abdd2` from a former audio label to score
authority. Predator Warrior is `SOURCE_CLOSED`, including all 38
player-origin audio trigger edges across 47 state/action/substate contexts.
The accepted player evidence is retained unchanged in
`data/oracle11_predator_player_audio.json` and
`data/oracle11_predator_warrior_authority.json`.

Global gameplay-audio/load/release remains `PARTIAL`. The main-CPU queue drain,
audio-CPU 16-byte shared-command ingress, and guarded QSound write primitive
are source closed in `data/oracle11_global_audio_load_release.json`. The active
experiment is the intervening audio-CPU command dispatcher/handler/table
boundary, followed by the 175 non-player trigger provenance groups and four
route load/release boundaries. Individual low/high/register writes are not
logical sound events; group them by their owning command/handler transaction.
The sole route-segment x authority-family matrix and SPEC-02 zero-gap gate
remain in `data/round1_system_coverage.yaml`.

Continue the same ORACLE-11 card and Goal from
`cde8cea67fe4fed69f6511d0df30a221a4a72b93`. Do not activate SPEC-02
until every completion-route authority is closed or narrowly adapted with
mutation controls. Do not write production runtime, infer USER-09 approval,
activate SALVAGE-08 before explicit USER-10 acceptance, or advance physical
Saturn beyond `UNRUN`.
