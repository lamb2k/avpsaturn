# Player block interface (census, 2026-11-08)

What code outside a player's own update reads and writes in the player block. A native fighter in Schaefer's slot
must keep these fields current, so enemies, damage, grabs, pickups, the HUD and stage scripts keep working.

## How it was measured

- **Tool:** `tools/wolverine/run_iface_census.sh sch 1` runs `iface_census.lua` over pal_census.lua's whole-game walk.
  MAME 0.289 avspu, Schaefer, stages 02 to 26, 328,049 frames, 18 min.
- **Taps:** every read and write of player 1's block (ff8380..ff847f), keyed by field offset, PC and the running actor
  (a6). a6 = ff8380 is the player's own code.
- **Outbound writes:** every write made while a6 = ff8380 outside the block (the player's effect on other actors).
- **Routines:** each PC maps to its lifted routine (`f_<addr>` in the lifted source).
- **Excluded:** block clears and spawn copies (f_900, f_960, f_17612).
- **Not covered:** health is held by the walk, so dying, continue and game over are not in this census. A second
  short run without the hold is still to do.
- **Output:** E:/AvP/learning/lane-wolverine/iface/sch (iface.tsv, summary.txt). It is ROM-derived and stays on this PC.

## Result

All 128 word fields are touched. 61 of them have readers or writers outside the player's own code.

**Read every frame by many routines** (core contract):
- +00 active;
- +04 state;
- +10 x;
- +18 depth;
- +1c/+1e;
- +54;
- +5c;
- +d0;
- +d2.

**Read by enemy AI** (actor tag 0c and the boss and object kinds):
- position: +0e, +14, +18, +1c, +5c, +70, +74, +92, +96;
- state, character, size: +4c, +50, +52, +54.

**Damage and collision engine.** f_1cf54, f_1d25e, f_1d314, f_1d492, f_1d504, f_1d622, f_1d6e2 and f_1d73a run
for every attacker and target.
- They read the player's box and state words: +2c, +46, +48, +4e, +50, +52, +5c, +6e, +70, +72, +98, +d0.
- They write damage into the player: +06 hit state, +40 health, +46/+48, +4e, +6a/+6c, +70, +98.
- The player's own attacks call the same routines and write into enemy blocks (ff9a00..ffc6ff) through f_1d314,
  f_1d492, f_1d504 and f_1d6e2. That is the "damage event out" side.

**Grabs and throws.** f_1d908 (actor tag 14) reads and writes +12, +16, +1a, +5c, +5e: the grab link and the
held position.

**Pickups.** f_1bc38 reads and writes +74. f_21ef8 (projectiles, tag 20) reads and writes +c0..+ca.

**HUD and score** (system routines f_ac*, f_ad*, f_8164, f_8836, f_91e4, f_9750, f_a000):
- read +40 and +44 health;
- read and write +42/+44;
- read and write +d0, +d4, +f2, +f4, +f6, +f8, +fc.

**Stage scripts** (tag 18): f_797d6, f_94b3a, f_98436.
- They read +02, +d2, +ee, +ae.
- They write +02, +14 and +d2: cutscene positioning and the active flag.

**Camera and scroll:**
- f_166ac reads and writes +ee;
- f_c400 writes +8a;
- f_ccf8 writes +8c;
- f_1ce98 writes +8e.

## Field table

Columns: field | external readers (count: routines) | reader actor tags | external writers | writer tags.
Tags are the running actor's byte +8; 00 or sys means system code.

| Field | Readers | Reader tags | Writers | Writer tags |
|---|---|---|---|---|
| +00 | 413: 940, d10, de6, dea, dfa, f5a, 1060, 106c, 1092, 1096, 10ec, 1188, 11a0, 11ba, 11d4, 11ec, ... | 00/01/02/03/04/05/06/07/08/09/0a/0c/10/14/18/1c/20/24/p2/sys | 3: 91e4, 9750, a466 | 00 |
| +02 | 3: 1d314, 1e396, 797d6 | 00/10/18 | 4: 8164, 1e396, 1e41c, 797d6 | 00/18 |
| +04 | 299: 940, d10, de6, dea, dfa, f5a, 1060, 106c, 1092, 1096, 10ec, 1188, 11a0, 11ba, 11d4, 11ec, ... | 00/01/02/03/04/05/06/07/08/09/0a/0c/10/14/18/1c/20/24/p2/sys | 1: 1d492 | 0c/10 |
| +06 | 1: a0674 | 1c | 1: 1d492 | 0c/10 |
| +08 | 5: 1cf54, 1d314, 1d504, a072a, a6a7c | 0c/10/1c | - | - |
| +0e | 23: 1689a, 1d25e, 1d314, 1f652, 3770a, 420a8, 44f92, 468b6, 48ad0, 48bce, 4aec4, 4ebec, 4ec46,... | 04/08/0c/10/14/18/1c/24 | 1: 1d314 | 10 |
| +10 | 594: 940, d10, de6, dea, dfa, f5a, 1060, 106c, 1092, 1096, 10ec, 1188, 11a0, 11ba, 11d4, 11ec, ... | 00/01/02/03/04/05/06/07/08/09/0a/0c/10/14/18/1c/20/24/p2/sys | 2: 1d908, 98436 | 14/18 |
| +12 | 2: 1d908, 3ac0c | 08/14 | 1: 1d908 | 14 |
| +14 | 10: 1d25e, 1f652, 32422, 36e10, 40800, 50e9c, 600be, 94b3a, 9aa90, bca58... | 04/08/0c/10/18/1c/24 | 1: 98436 | 18 |
| +16 | 1: 1d908 | 14 | 1: 1d908 | 14 |
| +18 | 198: 1689a, 17020, 1d25e, 1d6b2, 1db8a, 1ddfa, 367fe, 37082, 372e0, 37322, 3735a, 374be, 37542,... | 01/02/03/04/05/08/09/0a/0c/10/14/18/1c/24 | 1: 98436 | 18 |
| +1a | 2: 1d908, 3ac0c | 08/14 | 1: 1d908 | 14 |
| +1c | 10: 1cf54, 1d1f8, 1f652, 3bfdc, 3c062, 483ee, 52188, 585be, aaa12, bca58... | 04/08/0c/10/14/18/1c | - | - |
| +1e | 10: 1cf54, 1d1f8, 1f652, 3bfdc, 3c062, 483ee, 52188, 585be, aaa12, bca58... | 04/08/0c/10/14/18/1c | - | - |
| +24 | 3: 30d34, 32422, 9aa90 | 04/24 | - | - |
| +2c | 2: 1cf54, 1d1f8 | 0c/10/1c | 1: 1cf54 | 0c/10 |
| +40 | 7: 1d492, 1d504, 20a10, 3c29e, 5767e, ac92a, ac9fc | 00/08/0c/10/20 | 296: 940, d10, de6, dea, dfa, f5a, 1060, 106c, 1092, 1096, 10ec, 1188, 11a0, 11ba, 11d4, 11ec, ... | 00/01/02/03/04/05/06/07/08/09/0a/0c/10/14/18/1c/20/24/p2/sys |
| +42 | - | - | 1: ad28c | 00 |
| +44 | 2: ac92a, ac9fc | 00 | 1: ad28c | 00 |
| +46 | 1: 1d314 | 0c/10 | 1: 1d314 | 0c/10 |
| +48 | - | - | 1: 1d314 | 0c/10 |
| +4c | 4: 483ee, 52188, 585be, 600be | 0c | - | - |
| +4e | 3: 1cf54, 1d314, 1d622 | 0c/10 | 2: 1cf54, 1d314 | 0c/10 |
| +50 | 2: 1cf54, 1d1f8 | 0c/10/1c | - | - |
| +52 | 2: 1cf54, 1d1f8 | 0c/10/1c | - | - |
| +54 | 9: 1d1f8, 1ddfa, 3bfdc, 3c062, 483ee, 52188, 585be, b0c22, b0c5e... | 01/02/03/04/05/08/09/0a/0c/14/1c | 1: 1f652 | 0c |
| +56 | - | - | 1: bca58 | 1c |
| +5c | 8: 1d1f8, 1d314, 1d8e0, 1d908, 3bfdc, 483ee, 52188, 5757a | 08/0c/10/14/1c | 1: 1d908 | 14 |
| +5e | 1: 1d908 | 14 | - | - |
| +6a | - | - | 1: 1d314 | 0c/10 |
| +6c | - | - | 1: 1d314 | 0c/10 |
| +6e | 1: 1d314 | 0c/10 | - | - |
| +70 | 5: 1cf54, 3bfdc, 3c062, 483ee, 585be | 08/0c/10 | 1: 1d6e2 | 0c/10 |
| +72 | 1: 1d314 | 0c/10 | - | - |
| +74 | 5: 1bc38, 3bfdc, 483ee, 52188, 585be | 00/08/0c/14 | 1: 1bc38 | 00/14 |
| +7c | 1: 9aa90 | 24 | 1: 9aa90 | 24 |
| +84 | 1: 1689a | 0c | - | - |
| +8a | - | - | 1: c400 | 00 |
| +8c | - | - | 1: ccf8 | 00 |
| +8e | - | - | 1: 1ce98 | 1c |
| +92 | 19: 1689a, 3770a, 38b28, 3a4d0, 3be4c, 41fc4, 42000, 420a8, 44f92, 468b6, 48a34, 48ad0, 4ae28,... | 08/0c | - | - |
| +96 | 58: 374be, 37542, 39c4c, 3a394, 3b496, 3bfdc, 3c062, 3c1f4, 3c258, 3c29e, 3c2cc, 420a8, 42b7e,... | 08/0c/14 | - | - |
| +98 | 1: 1d73a | 0c/10 | 1: 1d73a | 0c/10 |
| +9e | 5: 1c9a8, 483ee, 52188, 54192, 55902 | 00/0c | - | - |
| +ae | 1: 94b3a | 18 | - | - |
| +c0 | 1: 21ef8 | 00/20 | 1: 21ef8 | 00/20 |
| +c2 | 1: 21ef8 | 00/20 | 1: 21ef8 | 00/20 |
| +c4 | - | - | 1: 21ef8 | 00/20 |
| +c6 | - | - | 1: 21ef8 | 00/20 |
| +ca | 1: 21ef8 | 00/20 | 1: 21ef8 | 00/20 |
| +d0 | 28: 8836, 1d504, 1d716, 1d73a, 43722, 437c6, 437ee, 4390e, 43970, 439b0, 46636, 4676c, 46830, ... | 00/0c/10 | 3: 519e, 8164, 8836 | 00 |
| +d2 | 10: 9750, 1689a, 1f652, 21ef8, 797d6, 799e8, 94b3a, ac5ea, bc692, bca3a... | 00/0c/14/18/1c/20 | 1: 797d6 | 18 |
| +d4 | - | - | 1: 8164 | 00 |
| +e0 | 3: abdd2, abe4a, abed0 | 00/08/0c/14 | 2: abdd2, abe4a | 00/08/0c/14 |
| +e2 | 3: abdd2, abe4a, abed0 | 00/08/0c/14 | 2: abdd2, abe4a | 00/08/0c/14 |
| +ee | 2: 166ac, 797d6 | 00/18 | 1: 166ac | 00 |
| +f2 | 5: 91e4, 9750, a000, acd1e, acdd2 | 00 | 3: 91e4, 9750, a000 | 00 |
| +f4 | 5: 91e4, 9750, a000, acb52, acc04 | 00 | 3: 91e4, 9750, a000 | 00 |
| +f6 | 6: ad070, ad090, ad17a, ad216, ad4f2, ad518 | 00 | 3: ac77a, ad4f2, ad518 | 00 |
| +f8 | - | - | 2: 8836, cad6 | 00 |
| +fc | 1: 8164 | 00 | 1: 8164 | 00 |
## Outbound: what the player's own code writes elsewhere

These writes come from a6 = ff8380, grouped by 256-byte page.
- ff9a00..ffc6ff: enemy and object blocks, through the damage routines above.
- ff8600..ff8aff and ffdd00..ffe2ff: effect and projectile spawns (f_21d7c, f_2576a, f_25942).
- ff7f00 and ff8000..ff82ff: globals (score, camera, timers).
- ff1800: the collision lists (f_1cf1c, f_1d03e, f_1d25e).

The full list is in summary.txt in the evidence folder.
