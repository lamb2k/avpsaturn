# First gate

Status: Investigation. Evidence: tiers per line. Lifter semantics not yet validated (backlog item 8).

| Measure | Result | Tier |
| --- | --- | --- |
| Reachable code (lower bound) | 407,232 bytes, 104,301 instructions, 4,656 call targets, 1,565 jump tables | HOST static |
| Unresolved | 57 sites at map build; 152 indirect calls in lifted output; 155 instructions unhandled by lifter | HOST static |
| Round 1 route to frame 14999 | 85,942 bytes executed in 1,369 functions, 116,674 bytes in those functions; 1,407 fetched word addresses outside the map, prefetch not separated | MAME |
| SH-2 GCC 9.3 -O2 size | 4.49 bytes per 68000 byte overall (1,830,242 bytes); random 300 functions 4.37; local-register mode 4.54 | HOST compile |
| Round 1 code, projected | about 524 KB | HOST projection |
| Non-code program data | at most about 1.22 MB (0.64 MB + 0.58 MB nonblank) | HOST static |
| Tick, Coffee Shop route | mean 3.9 to 6.2 ms, p95 5.6 to 8.9 ms, saturated 6.7 to 10.8 ms | MODELLED |

Cycle model: 68000 instruction counts from MAME with idle and dispatcher excluded, times each function's static SH-2 mix (ALU/store 1, load 2, branch 2, call/return 3), times 1.0 to 1.6 for cache. It excludes drawing, cart wait states and interrupts. Tool: tools/gate1_measure.py, probe tools/learn_probe_exec.lua.
Hot set: 100 functions hold 89.5% of modelled cycles, 200 hold 97.2%.
