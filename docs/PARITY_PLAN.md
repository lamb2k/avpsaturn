# Active parity and capability gates

The 2026-08-20 reset invalidated the old RP sequence as a plan of record. Existing RP artifacts remain evidence inputs. They do not advance the gates below by themselves.

## Separate evidence tracks

| Track | Purpose | Current status |
|---|---|---|
| Shared primitives | Prove byte readers, sparse spans, animation, collision predicate, object/tile emission, palette bounds, scene parsing, and package budgets. | Strong retained host/MAME evidence; complete suite blocked by the pre-existing start-transition declarations until Tranche 2A. |
| Presentation/stage parity | Prove VDP1/VDP2 semantic composition and final output for a bounded scene. | One-emulator RP4 fixture evidence; production cell-map scene and hardware scanout open. |
| Capability slice | Prove integrated gameplay and timing from cold boot on physical Saturn. | 0/12. |

Accepted foundation: Tranche 1 froze the exact `avspu` contract, produced the
two-cold-run oracle plus perturbation control, and classified the complete
executed boundary at accepted HEAD
`a11527a18c6ec02d3bc3f3421674755a3102c6c5`. This is MAME/translated evidence;
it does not close an integrated physical capability condition or change 0/12.

## Capability slice: 0/12

| # | Condition | Status |
|---:|---|---|
| 1 | Exact `avspu` identity and deterministic package provenance | OPEN for new slice artifacts |
| 2 | Two identical cold-boot MAME gameplay oracle runs plus perturbation control | OPEN |
| 3 | Controller input and one playable actor match semantic oracle | OPEN |
| 4 | One class `0x1F` enemy update/animation matches, including HIT/KO repoints | OPEN |
| 5 | Source collision, damage, hit response, and KO match | OPEN |
| 6 | Camera/stage progression and 352 crop/framing contract match | OPEN |
| 7 | VDP1 objects and VDP2 layers/priority/palette/final scanout match | OPEN |
| 8 | SCSP PCM event path is audible and correctly timed | OPEN |
| 9 | CDDA music is audible with no illegal data-read overlap | OPEN |
| 10 | Live work-RAM/cart/VDP1/VDP2/SCSP high-water and canaries pass | OPEN |
| 11 | Physical VDP1 draw-end, CPU/transfer timing, and input latency pass | OPEN |
| 12 | Normal-release cold boot and ten-minute physical soak pass with no missed frame, corruption, or fallback | OPEN |

No partial condition advances the count. A condition closes only when its evidence artifact, exact binary/profile hash, command, environment, and tier are recorded in `docs/research/CPS2_TO_SATURN_EVIDENCE_LEDGER.md`.

## Dependency order

1. Freeze target/fidelity/provenance schema. **Accepted foundation.**
2. Build unified MAME gameplay oracle and executable boundary. **Accepted foundation.**
2A. Restore the strict host-suite baseline with the bounded start-transition declaration/test repair. **Current.**
3. Lift the required executable writer set on host (V2).
4. Build traceable slice packages.
5. Integrate deterministic native runtime.
6. Run VDP1 budget and VDP2 final-composition probes.
7. Integrate audio/residency ownership.
8. Run normal-release regression.
9. Run physical capability slice.

The only current executable body is `docs/NEXT_AGENT_PROMPT.md`.
