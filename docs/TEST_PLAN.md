# Active test plan

Tests retire one claim at one evidence tier. They do not promote themselves.

## T0: identity and provenance

- Verify MAME executable version/hash.
- Run `mame.exe -rompath . -verifyroms avspu`.
- Parse list XML and compare set/parent/display/ROM inventory with the source ledger.
- Reject any generated artifact missing set, ROM hashes, source address space/offset, extractor pin/parameters, output hash, schema, consumer lifetime, tier, or exclusions.

Acceptance: exact identity, deterministic manifests, and non-vacuous wrong-set/wrong-hash controls.

## T1: focused host tests

Run the narrowest test for the changed subsystem first. Preserve strict C90/warnings-as-errors for portable runtime models. Every behavioral test needs at least one mutation/negative control that would fail if the asserted rule were removed or perturbed.

Key retained areas: actor fields, animation walk, table-set/class attribution, collision predicate, object emission, tile archive, CRAM bounds, scene parser/runtime, disc guard, palette coverage, scene census, residency calculations, VDP1 command model.

Acceptance: RED is recorded before a behavior correction; GREEN and negative control both pass afterward.

## T2: complete host/generator regression

`test.ps1` regenerates tracked evidence. Run it only in the assigned clean implementation worktree when all outputs are owned, or in an isolated shadow copy. Record Python and WSL GCC versions, exact command, exit code, and generated diffs.

Acceptance: exit 0, no weakened assertions, deterministic regeneration, and explicit review of every changed manifest.

## T3: unified MAME gameplay oracle

From cold boot with fixed config/NVRAM/input, record cadence-1:

- input and frame;
- actor class/type/state/substate/action/animation record;
- positions, velocities, facing, health;
- object list and palette;
- collision/hit/damage/KO events;
- camera and stage state;
- scroll registers, layer order, line/row scroll, and palette writes;
- QSound commands/events;
- final-frame hash.

Run twice from cold boot. A one-frame input perturbation must change the expected downstream state. Raw private traces stay ignored; committed manifests contain schemas, hashes, counts, and bounded evidence only.

Acceptance: two byte-identical ledgers, complete required fields, non-vacuous control, exact tool/ROM/config provenance.

## T4: target build and bounded emulator checks

- Build the assigned diagnostic profile only after T0-T3.
- Read back compile profile, ISO members, and artifact hashes.
- Compare semantic state first, then VDP1 command/texture/palette, VDP2 register/VRAM/CRAM, and final scanout.
- One emulator remains `ONE_EMULATOR`; use a second independent emulator only when the claim benefits from it.

Acceptance: no adapted fallback in the accepted slice and no mismatch hidden by screenshot plausibility.

## T5: normal release

Run `.\build.ps1 -Clean -Release` in the clean implementation worktree. Require `release-normal-release` and a manifest that identifies every phase asset/audio member. Re-run the complete emulator semantic and final-scanout route on this exact ISO.

Acceptance: normal profile, deterministic rebuild/hash or documented build nondeterminism, no diagnostic-only fixtures/markers, and zero required semantic mismatches.

## T6: physical Saturn

Follow `docs/HARDWARE_TEST.md`. First run the render/transfer budget probe; later run the integrated capability slice. Record console/cart/loader, ISO hash, input device, capture method, draw-end/timer/high-water counters, audio, latency, final scanout, and soak.

Acceptance: only the hardware checklist can produce `PHYSICAL_SATURN` evidence.

## Stop rules

Stop the tranche and return evidence when:

- target/tool/input identity cannot be pinned;
- the oracle is nondeterministic or lacks a required semantic field;
- executed control flow remains unresolved beyond the tranche threshold;
- a physical draw/transfer deadline fails;
- memory/audio ownership overlaps or canaries fail;
- continuing requires a different architecture, new authority, unavailable private evidence, or user physical interaction.

Do not “fix” a stop by expanding into a general engine or weakening acceptance.
