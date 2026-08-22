# ADR 0007: Common player runtime with four character definitions

## Status

Accepted for staged implementation.

## Context

The measured character-select contract identifies Predator Warrior, Major
Schaefer, Predator Hunter, and Linn Kurosawa. Their full action and ending
differences are not yet captured. Duplicating a player engine would multiply
state, collision, and multiplayer risk.

## Decision

Use one common player runtime configured by `PortV2CharacterDef`, binding
identity, assets, actions, animation, collision, HUD, weapons/projectiles,
audio, character-specific rules, and ending route. Every difference is entered
in the four-character matrix before implementation.

## Alternatives considered

- Four copied player engines.
- A general entity-component system.
- Assume shared Predator/human behavior without measurement.

## Consequences

Shared rules remain consistent while measured deltas stay bounded. The
definition must support real differences without becoming a general scripting
framework.

## Migration impact

The accepted promoted player API stays unchanged during ARCH-01. ORACLE-02 and
character-template cards drive later expansion.

## Evidence still required

Complete four-character action matrix, collision/resources, HUD/audio deltas,
ending selection, full routes, and multiplayer interactions.
