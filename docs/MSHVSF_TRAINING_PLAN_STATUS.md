# MSHvSF training-plan completion audit

This audit maps the pasted training plan to current evidence. `PARTIAL` means a
tracked artifact exists but the requested end-to-end structural proof is not
complete. `OPEN` means required evidence is absent. Nothing below changes AvP's
production route or Git history.

| Required output | Status | Authoritative evidence | Remaining proof |
|---|---|---|---|
| CPS-2 semantic model | PARTIAL | `data/mshvsf_cps2_semantic_model.json` | Actor addresses, writers, animation tables, collision, health, and audio semantics |
| Saturn semantic model | PARTIAL | `data/mshvsf_saturn_semantic_model.json` | SH-2 state/data/functions and hardware traces |
| Function/data correspondence | PARTIAL | `data/mshvsf_correspondence.json` | Concrete addresses and functions on both systems |
| Measured difference ledger | PARTIAL | `data/mshvsf_difference_ledger.json` | Same-attack mechanics, normalized presentation, audio, performance, and content differences |
| Reconstructed vertical slice | PARTIAL | `data/mshvsf_reconstructed_vertical_slice.json` | Saturn Hadouken and paired internal state; this is semantic reconstruction, not an executable port |
| Saturn reference architecture | PARTIAL | `docs/MSHVSF_SATURN_ARCHITECTURE.md`, `data/mshvsf_saturn_program_inventory.json`, `data/mshvsf_saturn_runtime_memory.json` | Join measured changes to SH-2 writers and resolve VDP1/VDP2, SCSP, cart, CD, and DMA ownership |
| Fidelity standard and scorecard | PARTIAL | `docs/CAPCOM_SATURN_FIDELITY_STANDARD.md`, `data/mshvsf_fidelity_scorecard.json` | Full route, roster, stress, audio, performance, and hardware validation |
| Candidate assessment | COMPLETE AS TEMPLATE | `templates/capcom_saturn_porting/candidate_assessment.template.json` | Apply to each future title with measured evidence |
| System mapping template | COMPLETE AS TEMPLATE | `templates/capcom_saturn_porting/system_mapping.template.json` | Apply per semantic concept |
| Hardware budget template | COMPLETE AS TEMPLATE | `templates/capcom_saturn_porting/hardware_budget.template.json` | Apply with focused/full-route peaks |
| MSHvSF hardware budget | PARTIAL | `data/mshvsf_hardware_budget.json`, `data/mshvsf_saturn_asset_topology.json` | Runtime peaks, ownership, lifetimes, and fit |
| Difference-ledger template | COMPLETE AS TEMPLATE | `templates/capcom_saturn_porting/difference_ledger.template.json` | Apply per observed deviation |
| Port acceptance checklist | COMPLETE AS TEMPLATE | `docs/CAPCOM_SATURN_PORT_ACCEPTANCE_CHECKLIST.md` | Execute it for a full candidate and physical release |
| Porting pattern library | PARTIAL | `data/mshvsf_porting_patterns.json` | Runtime confirmation and second-title validation for Capcom implementation candidates |
| Training exercises | COMPLETE AS CURRICULUM | `docs/CAPCOM_SATURN_TRAINING_EXERCISES.md` | Engineers must execute open exercises; a written exercise is not a passed exercise |
| Port candidate checklist | COMPLETE AS TEMPLATE | `docs/CAPCOM_SATURN_PORT_CANDIDATE_CHECKLIST.md` | Apply before each title decision |
| Second official-port validation | OPEN | None | Obtain an authorized X-Men vs. Street Fighter, Street Fighter Zero 3, or Vampire Savior CPS/Saturn pair and repeat the workflow |

## Current phase assessment

- Phase 1 is partial: deterministic external behavior exists on both systems,
  but the preferred projectile slice and internal function/data mapping do not.
- Phase 2 is partial structurally: exact-frame work RAM, cartridge, VDP1,
  VDP2, color-RAM, and SCSP dumps now exist for a normal-hit window, but
  ownership, allocation, loading transitions, and processor division remain
  unresolved.
- Phase 3 has a complete standard and a deliberately incomplete pilot scorecard.
- Phase 4 now has reusable templates, curriculum, and candidate gates.
- Phase 5 is open because no second authorized title pair is present in this
  lane.

## Next evidence order

1. Use the measured changed-page ranges and MCP breakpoints to locate Saturn
   player structures and normal attack/collision/damage writers, including an
   out-of-range falsification replay.
2. Traverse the measured VDP1 command jumps/calls and map referenced textures
   to stable cartridge and VDP1 residency.
3. Capture team/stage loading to resolve cartridge writes, VDP2 ownership,
   CD reads, and DMA transfers; do not infer them from the stable combat window.
4. Locate the matching CPS-2 normal attack/collision/damage writers.
5. Decode one CPS-2 and Saturn Ryu animation table and normalize pose timing.
6. Add the Saturn Hadouken route only after the normal-hit structures are proven.
7. Map normal/hit/Hadouken audio events and transport.
8. Measure a worst-case super/tag route and fill the hardware peaks.
9. Repeat the method on a second official port before promoting any candidate
   Capcom architecture pattern to a team standard.
