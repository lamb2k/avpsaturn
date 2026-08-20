# Next implementor prompt: RP8 Batch A frontend scene programs

## Invocation request

Continue implementation in:

`C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest`

Execute the bounded RP8 body below. RP4-RP7 passed interim review (see
`docs/ROUND1_EXECUTION_PLAN.md` status tables and `docs/AGENT_HANDOFF.md`);
Codex ratification of those acceptances is pending and may reopen them.

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

## Scope lock: RP8 Batch A only

Convert the frontend presentation scenes into ROM-derived scene programs
driven through the RP3 scene player and the RP6 manifest:

- legal/warning, EPA, QSound, and Capcom screens;
- opening earth, opening demo, and story panels;
- title wait and Start transition;
- character select and confirmation (including the six line-scroll scenes
  classified at SP10: 0x8012, 0x8013, 0x8015, 0x8016, 0x8019, 0x801a);
- Round 1 title.

Requirements:

- scene content comes from ROM translation (tilemaps, palettes, scripts),
  not from captured RLE holds; captures remain regression oracles;
- scenes are addressed by RP6 stable IDs; unknown IDs stay hard errors;
- the six line-scroll scenes get a measured Saturn line-scroll (or bounded
  ADAPTED equivalent) proven against source frames;
- controller-driven route: legal through Round 1 title with real input,
  proven against the capture at held frames;
- respect the residency ledger: the encounter profile has only 320 bytes
  of work-RAM headroom - new unconditional BSS must be paid for first;
- all reads honour the disc guard; new phase loads declare measured
  windows.

Work in bounded slices (one scene family per commit), each with offline
proof, negative controls, live readback where the contract requires it,
and a handoff update.

## Do not

- Do not advance Capability Gate counts.
- Do not commit ROMs, captures, screenshots, audio, or payload bytes.
- Do not replace ROM translation with capture-derived runtime payloads.

## After RP8

RP9 (Batch B: street and interior presentation) then RP10 (Batch C) per
`docs/ROUND1_EXECUTION_PLAN.md`.
