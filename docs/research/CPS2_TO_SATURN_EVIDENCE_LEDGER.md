# CPS-2 to Saturn evidence ledger

Audit date: 2026-08-20

Target: `avspu` only

Repository baseline: `codex/avp-master-plan` at `e79f666c865b096192aa102137db1cfdfad6c321`

## Status vocabulary

- **Proven on physical Saturn:** directly exercised on target hardware with a pinned binary and recorded result.
- **Proven in more than one emulator:** same bounded claim reproduced by two independent Saturn emulators.
- **Proven only in one emulator:** bounded Saturn behavior/readback observed only in the pinned Yaba Sanshiro environment.
- **Proven by deterministic MAME trace:** repeated pinned arcade-oracle data supports the claim.
- **Supported by static analysis:** code, manifests, hashes, or calculations support the claim but do not execute the target behavior.
- **Visually plausible:** image/output looks right without a semantic or pixel/readback oracle.
- **Planned but not implemented:** design text exists; runtime path does not.
- **Implemented but not exercised:** code exists without a retained relevant run.
- **Contradicted:** available evidence falsifies the claim as stated.
- **Unknown:** required evidence is absent or ambiguous.

Evidence tiers are not cumulative. A host test cannot become a physical pass; an emulator result cannot become multi-emulator by repetition in the same emulator.

## Claim ledger

| Claim | Current status | Evidence | File or source reference | Emulator or hardware | Cheapest falsification test | Consequence if false | Decision |
|---|---|---|---|---|---|---|---|
| The implementation target is `avspu`, USA 940520, clone of `avsp`. | Proven by canonical metadata and local ROM verification | MAME 0.289 list XML; all 16 canonical files verify. | `.deps/mame-source/cps2.cpp:2526-2552`, `12600`; source ledger ROM table | MAME 0.289 | `mame.exe -rompath . -verifyroms avspu` plus list XML diff | Every offset, capture, and package may be for the wrong revision. | **Keep; embed identity in every manifest.** |
| MSHvSF is a reference lane, not the AvP target. | Proven by repository/worktree structure | Separate clean branch/worktree and explicit reference policy. | `../AvPSaturnCapabilityTest-MSHvSF/docs/MSHVSF_REFERENCE_LANE.md:1-35` | Static/local | Attempt to find any MSHvSF runtime asset or code dependency in AvP production build. | Title-specific evidence would be contaminated. | **Keep isolated; no broad cherry-pick.** |
| Capability Gate 1 had advanced because RP4-RP7 passed. | Contradicted at audit baseline | Gate was 0/7; RP packages were shared-primitives/presentation inputs. | `docs/archive/pre-reset-2026-08-20/PARITY_PLAN.pre-reset.md:47-60`; `AGENT_HANDOFF.pre-reset.md:180-187`, `330` | Documentation/evidence | Exercise every gate condition with one normal hardware image. | Roadmap gives false completion signal. | **Replaced by the reset 0/12 slice gate; keep categories separate.** |
| Pre-reset repository status prose was current. | Contradicted | Top handoff/README/architecture/test text called RP4 active/pending while HEAD contained RP5-RP7. | `docs/archive/pre-reset-2026-08-20/AGENT_HANDOFF.pre-reset.md:18-26`, `119-187`; `README.pre-reset.md:13-25`; `ARCHITECTURE.pre-reset.md:273-303` | Static | Compare each status line with `git log` and live artifacts. | Agents execute obsolete work. | **Active instructions replaced; old roadmap archived.** |
| The current runtime is a translated AvP gameplay core. | Contradicted | Player, enemy AI, waves, boss, camera, and timings are authored in `capability_model.c`. | `capability_model.c:148-309`, `402-747`, `828-1008` | Host/static | Diff one gameplay state ledger against MAME for 10,000 ticks. | Presentation can never establish behavioral fidelity. | **Replace incrementally with selective lifted state writers.** |
| A useful ROM-backed actor spine exists. | Proven by deterministic MAME trace and host tests; narrow runtime implementation | Actor fields, collision predicate, animation records, table-set/class attribution, object emission, and sparse spans pass bounded tests. | `avsp_actor.c`; `avsp_anim_script.c`; `avsp_emit.c`; isolated `test.ps1` output | MAME/host | Add a perturbed pointer/table negative control or replay an unobserved action. | The selective-lift premise becomes weaker. | **Reuse analyzers and sparse views.** |
| ROM actor gameplay covers more than one meaningful live path. | Contradicted | Runtime accepts only street wave 1/2 WALK/ATTACK; HIT/KO and other types use fallback. | `main.c:1660-1744`, `1823-1834` | Static/runtime code | Force HIT, KO, and a second type while counting fallback/gap paths. | Slice scope is larger than assumed. | **Limit tranche 1 to one player and class `0x1F`; translate repoints.** |
| HIT/KO animation continuity is understood. | Contradicted / explicit gap | Isolated suite reports `GAP_EXTERNAL_REPOINT`: HIT 3/36 mismatches, KO 90/140. | `test.ps1:168-175`; `tools/verify_avsp_anchor_anim_replay.py` | Host/MAME evidence | Trace the class `0x1F` writer and lift it into the host model. | Hit response cannot be accepted. | **Make it a tranche-1 dependency.** |
| Player attack reach and full collision are ROM faithful. | Contradicted | Defender ROM hurt boxes are used for one path; attacker lane/reach stays fixed/adapted and other actors use point approximation. | `capability_model.c:343-399`; `main.c:1641-1806` | Static plus host predicate test | Record source attacker/hurt selectors and compare all candidate pairs over the slice. | Hit timing/range and difficulty differ. | **Replace fallback before slice acceptance.** |
| One VDP1 command per CPS-2 object is the current/default renderer. | Contradicted | Current renderer emits one `jo_sprite_draw3D` for each expanded tile; comment is inaccurate. | `main.c:1853-1858`, `1956-2017` | Static | Count VDP1 commands for one multi-tile CPS object. | Per-object roadmap work is based on a false description. | **Use per-tile baseline; fix governance/comment later.** |
| Per-tile VDP1 is semantically viable. | Proven in one emulator plus deterministic MAME/host evidence; physical performance unknown | Tile conversion/oracles pass; RP4 readback passes; MSHvSF official port is per-tile. | `tests/avsp_tiles_test.c`; `data/rp4_street_readback.json`; MSHvSF architecture `:66-105` | One Saturn emulator; original-port static/runtime capture | Hardware replay representative and 909-tile peak frames, check draw end. | Must add bounded composite/hybrid path. | **Keep as baseline, physical gate required.** |
| Per-tile VDP1 meets AvP worst-case timing. | Unknown | Demand peaks at 909 tiles; no physical draw-end/CPU/transfer data. | `data/avsp_sprite_demand.json:3-29` | None on physical Saturn | Probe 3 with representative/peak schedule and overload control. | Late frame misses or corruption. | **No performance claim; do not scale content first.** |
| CPS-2 tiles fit Saturn 16-color bank mode. | Supported by source docs and proven in one emulator for bounded assets | CPS-2/MAME tiles are 16x16 4bpp; VDP1 mode 0 is 4bpp banked; local readbacks pass. | MAME source; [Sega VDP1 manual](https://antime.kapsi.fi/sega/files/ST-013-R3-061694.pdf); `avsp_tiles.c` | Host and one emulator | Hardware palette sweep banks 0-31 with canaries/final capture. | Asset representation/VRAM doubles if 8bpp required. | **Keep 4bpp banked.** |
| A linked VDP1 command architecture is required. | Unknown / unsupported | VDP1 supports links, but MSHvSF's measured list is flat `JUMP_NEXT` and current AvP path does not need links. | [VDP1 manual](https://antime.kapsi.fi/sega/files/ST-013-R3-061694.pdf); MSHvSF architecture `:77-105` | Original-port capture; no AvP hardware need | Flat-list worst-case draw probe. | Linked-list work is unnecessary complexity. | **Park; flat contiguous list first.** |
| The shipped palette archive covers the route. | Contradicted | 10 shipped banks; route references 15; five uncovered; 4.0-4.4% of drawn objects outside shipped banks in measured routes. | `data/avsp_palette_coverage.json:27-86` | MAME trace/static archive | Generate exact slice phase palette set and rerun coverage. | Wrong/missing colors when actor scope expands. | **Revise package contents, not CRAM design.** |
| The palette problem is a Saturn CRAM capacity limit. | Contradicted | Peak concurrent object palettes is 13; code accepts 32 slots; missing archive content is binding. | `data/avsp_sprite_demand.json:3-29`; `data/avsp_palette_coverage.json:4` | MAME/static | Fill all referenced slice banks and measure CRAM ownership/readback. | Wrong optimization would waste architecture work. | **Treat as provenance/lifetime issue.** |
| Frontend one-based CRAM ownership is fixed. | Proven in one emulator with negative controls | 25 holds/22 exact surface comparisons; zero-based and perturbed controls fail; no boundary writes. | `data/avsp_frontend_cram_readback.json`; `test.ps1:86-97` | One emulator/readback | Physical full-bank canary sweep. | Frontend colors/bounds regress. | **Keep regression; not a gameplay gate.** |
| Indexed 8bpp frontend is source-faithful. | Proven by deterministic reconstruction and one-emulator readback for the bounded screens | ROM-derived fitted title/select surfaces and object schedules pass. | `avsp_frontend.c`; `data/avsp_frontend_assets.json`; frontend readback JSON | MAME plus one Saturn emulator | Final hardware title/select capture with CRAM/objects. | Presentation-specific mode must change. | **Keep, deprioritize.** |
| The 384-to-352 transform is canonical. | Contradicted | It is an adapted endpoint fit; no original-port or arcade evidence establishes it. | `capability_model.c:75-108`; `docs/archive/pre-reset-2026-08-20/ARCHITECTURE.pre-reset.md:101-115` | Static/one-emulator fixture | Side-by-side crop versus fit on chosen gameplay oracle; review off-edge interactions. | Framing/gameplay visibility changes. | **Adopt explicit 352 crop/camera contract.** |
| Scroll2 and scroll3 are necessarily flattened. | Contradicted for RP4 fixture; planned for production | Bounded fixture uses two VDP2 planes and exact readback. Production still uses fixture/static assets rather than full semantic stage runtime. | `main.c:2021-2030`; `data/rp4_street_readback.json` | One emulator | Generate one source cell-map scene and compare both planes/priority/final scanout. | Stage architecture is structurally wrong. | **Reuse two-plane mapping, replace fixture.** |
| Gameplay requires route-wide line scroll. | Contradicted for captured route; untraced full game unknown | 18,000 cadence-1 frames: six frontend scenes require line scroll; captured gameplay scenes and RP4 street do not. | `data/round1_rowscroll_classification.json:2-18` | Deterministic MAME trace | Extend classifier to any selected/untraced slice and perturb line-table output. | Scene schema/VDP2 budget changes. | **Add narrow versioned support only where traced.** |
| Scene v0 can express all classified presentation effects. | Contradicted | Opcode list has hold/layer/scroll/palette/object/map/audio/transition but no line-scroll operation. | `avsp_scene.h:43-53` | Static | Encode one of six line-scroll scenes without opaque payload. | RP8 would hard-code or misrepresent effects. | **Version schema before those scenes; park RP8.** |
| RP4 street fixture proves production stage composition. | Contradicted as stated | It proves 124 pixel frames/12,118 objects over a selected captured fixture, not a ROM-driven production scene or hardware output. | `data/rp4_street_readback.json`; `main.c:2021-2030` | One emulator | Replace strips with source cell maps, then rerun same controls and final scanout. | Full-route stage implementation may fail late. | **Keep fixture as regression only.** |
| Screenshots alone prove final VDP2 composition. | Contradicted / insufficient | Internal readback was necessary; MSHvSF's VDP2 register instrument returned zeros even while output existed. | MSHvSF architecture `:111-149`; RP4 controls | One emulator | Correlate register/VRAM/CRAM/VDP1 reads with final hardware capture. | Internal pass can hide final output error. | **Require final-scanout provenance.** |
| Static residency budgets prove live safety. | Contradicted as a general claim | Ledger passes calculations but says allocator/SCSP high-water is a gap; debug Encounter work-RAM headroom is only 320 bytes. | `data/avsp_residency_budget.json:35-104` | Static only | Instrument all arenas, canaries, transfers, and ten-minute high-water. | Memory corruption or late load stalls. | **Use as bound, not acceptance.** |
| MSHvSF demonstrates 4 MB cart combat residency. | Proven for one bounded original-port window | 3,549,571 nonzero bytes across 909 pages, stable at four combat anchors. | MSHvSF architecture `:51-64`, `151` | Rights-owned original disc in emulator/instrument | Capture load transition and compare cart configurations. | Nonzero/stable data may not be active occupancy. | **Candidate pattern only.** |
| Original Capcom Saturn ports establish a general per-tile/cart rule. | Unknown / unsupported | Only one official port has been measured with these instruments. | MSHvSF `data/mshvsf_porting_patterns.json:3` | One original title | Measure a second rights-owned official CPS-2 Saturn conversion. | General engine abstraction could encode a one-title accident. | **No generalization.** |
| Stage CDDA is implemented and guarded. | Contradicted | Actual `jo_audio_play_cd_track` call is commented out while ownership flag/guard is set. | `main.c:3209-3225`; `data/avsp_residency_budget.json:24-35` | Static | Enable in isolated branch after G0 residency; capture audible track and attempt guarded read. | Silent port; guard gives false confidence. | **Make audible music and real ownership tranche dependencies.** |
| Current audio event assets prove faithful QSound behavior. | Contradicted as stated | PCM files are capture-derived/event-mapped; stage music is disabled; no physical audible comparison. | `build/hardware_release_manifest.txt`; `prepare_*audio.ps1` | Host/static; one emulator at most | Event-ledger timing plus recorded Saturn A/B against MAME reference. | Timing/mix/identity differs. | **Use pragmatic PCM/CDDA, label compromise.** |
| The current ISO is a normal hardware release candidate. | Contradicted | `build/last_compile_profile.txt` and manifest say `debug-encounter-test` / `profile=encounter-test`. | `build/last_compile_profile.txt`; `build/hardware_release_manifest.txt` | Build artifact only | Run clean `-Release` normal profile after tests and re-read manifest. | Hardware testing would validate the wrong path. | **Do not ship/test as release candidate.** |
| `test.ps1` currently passes. | Proven in isolated shadow copy on 2026-08-20 | Complete invocation exited 0; deterministic models, negative controls, RP4 fixture, scene/residency/row-scroll, class/table-set, palette and VDP1 model passed. | Command ledger below; `test.ps1` | Host + retained MAME/emulator artifacts | Rerun in another isolated copy at the supervisor commit. | Architecture rests on stale/broken evidence. | **Keep; never run against dirty live data without isolation.** |
| Current build runs and physical hardware timing are proven. | Unknown | Audit did not run a target build because the live Jo checkout has shared object outputs and the main worktree is intentionally dirty. No physical run occurred. | `build.ps1:184-220`; audit command ledger | None this audit | Fresh implementation worktree, pinned dependencies, normal release, physical probe. | Feasibility remains open. | **Mandatory before capability claim.** |
| A unified cold-boot gameplay oracle exists for the selected HIT/KO slice. | Proven by deterministic MAME trace | Two independent 1,390-frame cold boots are byte-identical; all declared gameplay, actor, object, palette, scroll/row-scroll, QSound, and scanout fields are present; a one-frame input perturbation first changes semantic identity at frame 4510. | `data/avsp_vertical_slice_contract.json`; `data/avsp_vertical_slice_oracle_manifest.json` | MAME 0.289 only | Re-run from the pinned EEPROM/config and require a byte-identical ledger; suppress the known input frame and require changed identity. | No fidelity-bearing runtime integration may advance. | **Keep as V1/Probe 2 gate; not emulator or hardware evidence.** |
| The selected slice has a complete executable writer boundary. | Proven by deterministic MAME trace plus static classification | Private main-CPU opcode trace has 7,314 PCs/8,478 edges, all classified; all computed targets observed resolve; 9.762% of PCs are manually semantic, 44 hardware-facing. | `data/avsp_translation_boundary.json`; ignored `.deps/mame/vertical_slice/cold_run_1/maincpu.trace` | MAME 0.289 only | Remove a known PC/edge/global attribution and require completeness failure; re-run trace after any route/ROM change. | V2 would lift an unbounded or wrong code/data set. | **Keep as V2 boundary; no production C emitted here.** |
| The complete legacy host suite passes at the immutable reset base. | Contradicted / declared stop for this tranche | `test.ps1` fails compiling unmodified `capability_model.c`: undefined `CAP_ENCOUNTER_START_TRANSITION` and `CAP_START_TRANSITION_FRAMES`; both references are present at base while the header does not define them. | `capability_model.c:961,967`; `capability_model.h:75`; Tranche 1 command record | Host C compile | Fix only in an authorized runtime-maintenance tranche, then rerun the complete suite. | Tranche 1 cannot claim full legacy-suite GREEN without prohibited runtime work. | **Record exact blocker; preserve passing focused oracle/boundary checks.** |

## Audit command ledger

| Command / environment | Result | What it proves | What it does not prove |
|---|---|---|---|
| `git branch --show-current`; `git rev-parse HEAD`; `git log -8 --oneline`; `git status --short` in `C:\Game Dev\BrooklynBangoutX\AvPSaturnCapabilityTest` | Branch `codex/avp-master-plan`; HEAD `e79f666...`; dirty tree with 44 tracked modifications and many untracked private diagnostics. | Exact inspected repository baseline and preservation constraint. | Which dirty changes are correct or ready to commit. |
| `.deps\mame\mame0289\mame.exe -version` | `0.289 (mame0289)`; executable SHA-256 `af6966...37a3`. | Oracle binary identity. | Physical CPS-2 identity. |
| `.deps\mame\mame0289\mame.exe -rompath . -verifyroms avspu` | Exit 0; set good; 1/1 OK. | Local canonical set contents satisfy MAME 0.289. | Derived capture freshness or correctness of every MAME model. |
| MAME `-listxml avspu`, parsed for the `avspu` machine | USA 940520, clone/romof `avsp`, 16 canonical files, 384x224 at 59.637405 Hz, `qsound_hle`. | Exact target metadata and canonical CRC/SHA-1 inventory. | Local SHA-256, handled separately. |
| `Get-FileHash -Algorithm SHA256` over all target/derived/tool inputs | Values recorded in source ledger. | Byte identity of local inputs. | Provenance before the first recorded hash. |
| `test.ps1` invoked from an isolated shadow copy at `C:\Game Dev\BrooklynBangoutX\AvPAuditShadow-892e09cc62e64705abb3071604a1bfc4`, with `.deps` junctioned read-only-by-convention to the live dependency cache | Exit 0. Core outputs: 12,000 deterministic model frames; actor loads 481,566/0 mismatches; runtime street input assembly 1,392/0; object corpus verifier 18,986 eligible/0 mismatches; street planes 124 pixel frames/0 mismatches; line-scroll 6 scenes; all listed negative controls passed. | Current working-copy host/generator assertions and retained evidence are internally consistent. | Target compile, clean release, new emulator execution, audible audio, or physical hardware. The temporary shadow is not a production artifact. |
| `git diff --check` before documentation changes | Exit 0 with only line-ending conversion warnings observed elsewhere. | No pre-existing whitespace-error report. | Code correctness. |
| `Get-Process` filtered for MAME/Yaba/Kronos | No active emulator processes at audit snapshot. | No hidden live emulator run was mistaken for evidence. | Historical process state. |
| `sh-elf-gcc --version`, WSL `gcc --version`, `py --version` | SH GCC 9.3.0; host GCC 13.3.0; Python 3.13.0. | Tool identities used/available. | Reproducible target binary until a normal build manifest records them. |

The initial shadow attempt under the Windows temp directory failed before host compilation because `test.ps1`/`wslpath` mis-parsed that path. The successful space-containing `C:\Game Dev\...` shadow path demonstrates a harness path-conversion quirk, not a product test failure.

## Existing evidence snapshot

### Strong retained evidence

- Exact target ROM verification and hashes.
- Deterministic stage route anchors and scene census.
- Actor field/collision predicate reproduction over retained captures.
- Sparse animation record walk equivalence for shipped spans, with explicit external-repoint gaps.
- Object-emission algorithm with zero mismatches over 18,986 eligible entries and explicit 961 game omissions.
- 2,253-tile street archive, 297,764 bytes, within a 327,680-byte carve; over-budget Round 1 archive is rejected.
- Frontend one-based CRAM and VDP1 object readbacks with negative controls.
- RP4 selected fixture: 124 pixel frames, zero plane/column mismatches, 12,118 exact objects.
- 122-scene route census and six-scene line-scroll classification.
- Static residency ledger with declared gaps.

### Evidence drift that must be resolved at the supervisor boundary

- `avsp_emit.h:40-45` contains older corpus counts than `data/avsp_object_corpus_verification.json:106-112`.
- `docs/AGENT_HANDOFF.md` names an older baseline and reports RP4 status inconsistently with live HEAD.
- The live dirty `data/rp4_street_live_readback.json` reports a different command count and `__bend` value than the committed handoff report. Both may be valid builds; neither may be cited without its artifact/build fingerprint.
- `build/hardware_release_manifest.txt` is named like a release manifest but records an EncounterTest diagnostic profile.

### Explicitly unverified

- Any AvP result on physical Saturn during this audit.
- Multi-emulator agreement for the current build.
- A normal-release build at the inspected working-copy state.
- VDP1 draw completion and CPU/transfer headroom at representative or 909-tile frames.
- Final VDP2 352x224 physical scanout.
- Input-to-photon latency.
- Live cart/work-RAM/VDP1/VDP2/SCSP high-water and canaries for the integrated slice.
- Audible CDDA plus PCM with no data-read overlap.
- Complete player/class `0x1F` gameplay semantic equivalence.
- Any reusable original-Port “Capcom rule” across two titles.

## Evidence required to advance the new slice

1. **Shared-primitives check:** isolated unit/differential tests for byte readers, sparse spans, animation, collision, emission, palette, commands, and package bounds. This can pass on host/MAME.
2. **Presentation/stage check:** bounded VDP1/VDP2 semantic and final-scanout comparisons for the chosen scene. This can pass in emulator first but needs a hardware final-output result.
3. **Capability slice gate:** one normal release from cold boot through controlled gameplay, hit/KO, camera/stage, PCM, CDDA, load ownership, and ten-minute physical timing. Only this can advance the new capability gate.

No screenshot, host test, fixture, or old RP package may be counted as the capability slice by substitution.
