# Capcom Saturn historical-fidelity standard

The authoritative pilot scorecard is
`data/mshvsf_fidelity_scorecard.json`. It intentionally has no composite number:
an average can hide a gameplay failure behind presentation strengths.

## Classification

Use one relationship per claim:

- `MATCH`: same observed behavior within a declared tolerance.
- `EQUIVALENT`: different implementation, same observed result.
- `PLATFORM ADAPTATION`: Saturn-specific implementation required by hardware or
  media form.
- `OPTIMIZATION`: internal change with no accepted behavioral or presentation
  loss.
- `REDUCTION`: measured content, frame, effect, or functionality loss.
- `ALTERATION`: intentional observable change not explained by reduction.
- `ADDITION`: home-version behavior or content absent from the arcade source.
- `BUG`: reproducible unintended difference.
- `UNRESOLVED`: evidence is incomplete or competing explanations remain.

Confidence is independent. `HIGH` needs multiple independent evidence forms;
`MEDIUM` allows strong behavior with incomplete structure; `LOW` is a lead and
cannot become a team standard.

## Dimension gates

### Gameplay

Measure state order, input latency, movement, collision, damage, hitstop,
reactions, projectiles, meter, supers, tags, AI, RNG, and recovery. Compare the
same attack and initial state. A visually similar move is not gameplay proof.

### Animation

Measure script states, source-frame durations, rendered poses, pivots, flip,
loops, and transition boundaries. Report missing or merged poses separately from
changes to collision or action timing.

### Graphics

Normalize resolution, crop, coordinates, and aspect before comparing sprites,
effects, palettes, priority, clipping, backgrounds, HUD, and transitions. Include
representative and worst-case scenes.

### Content

Audit roster, moves, stages, modes, endings, options, regional/revision changes,
home additions, and known bugs. One shared route cannot prove content parity.

### Audio

Map event, command frame, source asset, transport, voice/slot, audible onset,
duration, retrigger, mix, music transition, and loading interaction.

### Performance

Measure frame deadlines, pacing, CPU ownership, VDP1 draw completion, VDP/SCSP
RAM peaks, DMA, CD stalls, and loading on worst-case routes. Emulator completion
is not physical-hardware performance proof.

## Evidence record

Every non-`UNRESOLVED` scorecard claim must include the claim, both-system
evidence, normalization, test, falsification attempt, tolerance, confidence,
uncertainty, and reusable lesson. The relationship returns to `UNRESOLVED` when
a wider route contradicts it.

## Acceptance

Release-level fidelity requires all six dimensions to have complete mandatory
route coverage, accepted tolerances, measured worst cases, no silent unresolved
deviations, and physical target validation. A focused slice may graduate as a
training checkpoint but cannot stand in for full-title acceptance.
