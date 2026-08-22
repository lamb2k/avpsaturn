# ADR 0008: Presentation scenes do not own gameplay

## Status

Accepted for staged implementation.

## Context

`AvspSceneDef` already expresses useful layer, palette, object, patch, audio,
and transition operations. Expanding it into a gameplay language would couple
AI, damage, collision, and route completion to presentation again.

## Decision

Retain scenes for logos, attract, title, character select, round/story panels,
continue, game over, endings, credits, and noninteractive transitions. Enemy
AI, collision, damage, boss rules, player actions, and wave completion remain
kernel behavior. Add versioned operations, including line scroll, only where
source capture requires them.

## Alternatives considered

- Encode all gameplay in scene bytecode.
- Remove the existing scene format.
- Add speculative effects for future stages.

## Consequences

Frontend presentation remains data-driven without becoming game authority.
Interactive transitions require explicit route/kernel coordination.

## Migration impact

SALVAGE/PROMOTE-08 constrains frontend use; stage templates reject gameplay
claims sourced only from scene operations.

## Evidence still required

Complete frontend and ending/credits captures, measured line-scroll scenes,
and route-to-scene transition differentials.
