#!/usr/bin/env python
"""Build the Saturn image of the lifted game. Everything ROM-derived stays in the work directory, never in git.
usage: build.py [WORK]   default E:/AvP/learning/lane-satrt, which holds src/c*.c, dispatch.inc, rt.bin, opx.bin, opx.json, heat.json (tools/satint_merge.py), pack.bin, pack_hole.bin (tools/satint_pack.py).
env: KERNEL_CFLAGS, LIFT_OPT (-Os; -O2 overflows work RAM), JO (Jo Engine root)."""
import concurrent.futures as cf
import json
import os
import pathlib
import re
import shutil
import subprocess
import time
import sys

import round_cache

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
# The post-credits Wolverine reveal (reveal.c, boot.c unlock record, tools/wolverine/reveal_*.py): on in every SAT_GUESTS build, since the owner's art (art/wolverine-reveal) is in the tree.
# The reveal replaces the GAME OVER card after the ending and, the first time it plays, switches Wolverine on (he is a toggle in OPTION MODE from the first power-on; the setting is saved in backup RAM).
# -DSAT_UNLOCK_DEBUG adds a REVEAL SEEN row to OPTION MODE (clear it and the next ending switches him on again). -DSAT_WOLVERINE_UNLOCKED no longer means anything (nothing is locked).
# REVEAL=0 builds without it. The voice (REVEAL_VOICE, or GUEST_ASSETS/reveal_voice.bin) is ROM-derived and stays out of git: without it the reveal is silent.
REVEAL_ART = REPO / "art/wolverine-reveal/reveal.bin"
if "SAT_GUESTS" in os.environ.get("KERNEL_CFLAGS", "") and "SAT_HOME" in os.environ.get("KERNEL_CFLAGS", "") and REVEAL_ART.exists() and os.environ.get("REVEAL", "1") != "0":
    os.environ["KERNEL_CFLAGS"] += " -DSAT_WV_REVEAL"
WORK = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "E:/AvP/learning/lane-satrt")
JO = pathlib.Path(os.environ.get("JO", "E:/AvP/worktrees/saturn-hw/.deps/joengine"))
BIN = JO / "Compiler/WINDOWS/bin"
GCC, OBJCOPY = [str(BIN / f"sh-elf-{t}.exe") for t in ("gcc", "objcopy")]
NM, OBJDUMP = [str(JO / f"Compiler/WINDOWS/sh-elf/bin/{t}.exe") for t in ("nm", "objdump")]
os.environ["PATH"] = str(BIN) + os.pathsep + os.environ["PATH"]   # compiler DLLs
MKISOFS = str(JO / "Compiler/WINDOWS/Other Utilities/mkisofs.exe")
SGL = JO / "Compiler/COMMON/SGL_302j"
OPT = os.environ.get("LIFT_OPT", "-Os")
CF = ["-m2", "-mb", "-fno-strict-aliasing", "-ffixed-r14", "-w", "-fno-builtin", "-I", str(HERE)]
GEN, OBJ, ISO = WORK / "gen", WORK / f"obj{OPT}", WORK / "disc"
for d in (GEN, OBJ, ISO):
    d.mkdir(parents=True, exist_ok=True)
HW_BASE, HW_LIMIT, LW_BASE, LW_LIMIT = 0x06014000, 0x06100000, 0x00200000, 0x00300000
HW_RESERVED = 0x10000 + 16 * 2048 + 8192 + 16384 + 0x8000 + 0x8000   # game RAM, stacks, kernel, graphics tables and code
LW_RESERVED = 0x20000 + 0x4000 + 0xe400   # graphics RAM, lifted bss, layer shadows, blank tags
NATIVE = ("41ca", "42e4", "212f8")   # EEPROM block read and write; start stock (kernel.c wraps the lifted body for the home LIVES setting)
if "SAT_HOME" in os.environ.get("KERNEL_CFLAGS", ""):   # home only (the arcade build is unchanged): the credit display and the text writers (kernel.c)
    NATIVE += ("ab438", "aba96", "abb0a", "abbae")
# Readable replacements, saturn/game. GAME_OVERRIDES=0 builds without them, for an A/B.
OVERRIDES = () if os.environ.get("GAME_OVERRIDES") == "0" else tuple((REPO / "saturn/game/overrides.txt").read_text().split())
# Bonus characters (SAT_GUESTS only): lifted routines wrapped in game_bind.c, body kept (the collision passes for guest boxes, the player state machine for guest timings).
NATIVE_GFX = "SAT_WV_NATIVE_GFX" in os.environ.get("KERNEL_CFLAGS", "") and bool(os.environ.get("GUEST_ASSETS"))   # Wolverine's native animation data (plan V2; saturn/guests/wolverine)
# native Wolverine: the gun routine of Warrior and Hunter (24060) stays stock; Schaefer's own special routine (24f04, state 020008: attack + jump) is the one his Berserker replaces
GUEST_WRAP = ("1cf54", "1d03e", "1d116", "195ec", "19f9a", "24f04" if NATIVE_GFX else "24060") + (("1a586",) if NATIVE_GFX and "WV_NO_GRAB" in os.environ.get("KERNEL_CFLAGS", "") else ()) if "SAT_GUESTS" in os.environ.get("KERNEL_CFLAGS", "") else ()
CART = dict(ROMB=0x02400000, OPX=0x02600000, SAT_SINK=0x02640000, SAT_OBJ=0x02650000, SAT_PACK=0x02654000)
CART_END = 0x02800000
OPX_MAX = 0x40000
COLD1_ROOM = 0x20000   # cart tail for cold code that no ROM stretch takes
COLD1_AT = CART_END - COLD1_ROOM
# ROM stretches no walk of any stage or character reads (tools/rounds_census.py, WORK/rounds.json): cold chunks of lifted code stay in them for the whole game, per-round tiles take the rest.
ROUNDS = json.loads((WORK / "rounds.json").read_text())
ARCADE_SPRITE_KEYS = {k for f in ROUNDS["files"] for k in f["keys"][0]}
# Per-character button-fuzz censuses (tools/char_fuzz.py, WORK/char_fuzz.json; absent = nothing changes).
#   CHAR_FUZZ_PAGES (default 1, a correctness fix): every stage file also keeps the ROM pages the fuzz runs read in its stage, and the players' whole script stretch 0x161400-0x1717ff.
#     Without them a file overwrites data that a jump attack, special or hurt reaction reads: page 0x171400 holds Linn's last script words and no stage file kept it (a stage file
#     with tiles there hands the script reader garbage: fatal 0xe2 at 0xa9cc4, a word outside its 8 entry jump table), and pages 0xa5800-0xa6bff were read by fuzz runs of stage 04 and others.
#   CHAR_FUZZ_KEYS (default 0, a visible change): a file also asks for the sprite keys the fuzz runs of its characters looked up in its stage and those characters' body
#     tiles (tools/char_fuzz.py ranks), so poses the route never reached stop drawing blank; the room comes from other characters' material. Only the stages in
#     CHAR_FUZZ_KEY_STAGES (default 0e,1c,1e,24, the ones whose files already differ per variant): any other stage would stop its 11 variants packing to identical files
#     and outgrow the sector store (STORE.BIN, 2^18 sectors: 275k unique sectors against 122k).
CHAR_FUZZ = None
if os.environ.get("CHAR_FUZZ", "1") != "0":
    sys.path.insert(0, str(REPO / "tools"))
    import char_fuzz
    CHAR_FUZZ = char_fuzz.load(WORK)
    if True:   # without a census file the players' script stretch is still kept (tools/char_fuzz.py SCRIPT_REGION)
        print("char fuzz:", char_fuzz.augment(ROUNDS, CHAR_FUZZ, keys=os.environ.get("CHAR_FUZZ_KEYS", "0") == "1", pages=os.environ.get("CHAR_FUZZ_PAGES", "1") == "1",
                                                key_stages={int(x, 16) for x in os.environ.get("CHAR_FUZZ_KEY_STAGES", "0e,1c,1e,24").split(",") if x} or None), flush=True)   # the guest files drop a bonus character's remap keys (guest_rounds.extend)
sys.path.insert(0, str(REPO / "tools/wolverine"))
import hud_art
HUD = None   # guest select screen and HUD art (hud_art.build); guests.c always includes a palette table, empty without it
if os.environ.get("GUEST_ASSETS"):   # bonus characters (SAT_GUESTS builds): guest stage file variants, tools/wolverine/guest_rounds.py
    import guest_rounds
    # Select screen and HUD art of the guest (tools/wolverine/hud_art.py): GUEST_HUD_ART, else GUEST_ASSETS/hud_art; GUEST_HUD_ART=0 builds without it.
    hud_dir = os.environ.get("GUEST_HUD_ART") or str(pathlib.Path(os.environ["GUEST_ASSETS"]) / "hud_art")
    if hud_dir != "0" and pathlib.Path(hud_dir).is_dir():
        HUD = hud_art.build(hud_dir, pathlib.Path(os.environ["GUEST_ASSETS"]) / "gfx_wolverine.bin", WORK / "rt.bin", GEN / "hud")
        miss = hud_art.check_keys(ROUNDS, hud_art.GUESTS[0])
        if miss:
            raise SystemExit("NO-GO: guest art tiles no arcade file holds (wrong tile codes or parity?): " + ", ".join("%s %s %x" % m for m in miss[:8]))
        print("guest hud art:", {k: v for k, v in HUD["report"]["tiles"].items()}, "palette copies", sum(p["copies"] for p in HUD["report"]["palettes"]), flush=True)
    DIALOG_KEYS = ()
    if any(f in ("-DSAT_WV_DIALOG", "-DSAT_WV_DIALOG=1") for f in os.environ.get("KERNEL_CFLAGS", "").split()):   # Wolverine's story box wording, from the user's ROM (tools/wolverine/dialog.py)
        import dialog
        DIALOG = dialog.build(WORK / "rt.bin", GEN)
        DIALOG_KEYS = DIALOG["keys"]   # his stage files hold the tiles the new wording draws
        print("guest dialog:", {k: v for k, v in DIALOG.items() if k not in ("include", "keys")}, flush=True)
    guest_rounds.extend(ROUNDS, os.environ["GUEST_ASSETS"], HUD, DIALOG_KEYS, WORK if "SAT_WV_SOUND" in os.environ.get("KERNEL_CFLAGS", "") else None)   # -DSAT_WV_SOUND: Wolverine's sounds (wv_sound/ in the assets) are added to the stage sound packs (tools/wolverine/wv_audio.py)
# Tile keys (sprites and the three layers) of the screens after a KO with no lives left: the continue countdown, name entry, GAME OVER.
# The census routes continue at once, so they never saw the low countdown digits, and a stage whose census had no game over lacked the
# screen's text and picture: the countdown and the "CONTINUE AND GET 1UP!" line drew blank. tools/screen_keys.py writes the list;
# tools/check_screen_keys.py checks every stage file holds it.
SCREEN_KEYS = [set(), set(), set(), set()]   # per section: sprite, scroll 1, 2, 3
for l in (open(WORK / "screen_keys.txt") if (WORK / "screen_keys.txt").exists() else []):
    if l.strip():
        SCREEN_KEYS[int(l.split()[0])].add(int(l.split()[1], 16))
SCREEN_KEYS[0].discard(0)
# The arcade's rare system banners (the timed stages' "HURRY UP!" and its countdown): tools/system_banner_keys.py derives the scroll 1 keys from the
# ROM's own tables. The census never sees them, and a stage file without them drew the second U of the banner blank.
sys.path.insert(0, str(REPO / "tools"))
import system_banner_keys
SCREEN_KEYS[1] |= system_banner_keys.from_work(WORK)
# Every text font the arcade can print (tools/font_glyph_keys.py: the ROM's glyph tables, both banks, both column parities) in every round file, front end included:
# a glyph no census route reached drew blank. FONT_KEYS=0 builds without them (A/B).
import font_glyph_keys
FONT_KEYS = font_glyph_keys.from_work(WORK) if os.environ.get("FONT_KEYS", "1") == "1" else set()
if os.environ.get("SCREEN_KEYS_REQUIRED", "1") == "1" and not SCREEN_KEYS[0]:
    raise SystemExit("WORK/screen_keys.txt missing: run tools/screen_keys.py (SCREEN_KEYS_REQUIRED=0 to build without)")
if os.environ.get("GUEST_ASSETS"):
    assets = pathlib.Path(os.environ["GUEST_ASSETS"])
    remap = json.loads((assets / "remap.json").read_text())
    round_cache.require_unused_remap("Wolverine", remap["keys"], ARCADE_SPRITE_KEYS | SCREEN_KEYS[0])
# The character select's countdown digits (scroll 1 codes 0x0b00-0x0b3f, two cells wide, three rows high, both column halves) in the front file. The census routes press
# Start at once, so only the digits 1, 4 and 5 were ever looked up; 6, 3, 2 and 0 drew blank. The digit's cells are blank or filled from one second to the next, and
# home's column fit shares one map across the screen's rows, so the whole select screen (the stat bars, names, portraits) jumped one column each time the digit appeared
# or vanished (owner 11-08, stat bars shifting on select; lane home-3, selcap/ logs).
SELECT_DIGIT_KEYS = {(c << 1) | h for c in range(0x0b00, 0x0b40) for h in (0, 1)}
# Home builds only: scroll 1 tiles at the outer columns (arcade 0, 1, 47) that the census never read (it reads the centre crop); the home
# picture shows them on the HUD rows and fitted text rows (P1's portrait and 1P mark). tools/edge_keys.lua writes WORK/edge_keys.txt.
EDGE_KEYS = set()
if "SAT_HOME" in os.environ.get("KERNEL_CFLAGS", "") and (WORK / "edge_keys.txt").exists():
    EDGE_KEYS = {int(l.split()[1], 16) for l in open(WORK / "edge_keys.txt") if l.strip() and l.split()[0] == "1"}
# Sprite tiles of the player characters' poses (palettes 0 and 1) from a button-fuzz census (tools/rounds_fuzz.py: jumps, jump attacks, attack bursts, gun, every
# direction, with and without health held). The route censuses move straight ahead and hit one attack now and then, so poses of jumps, combos and hurt
# reactions were never looked up and drew blank (lane avp-vanish: the player's body gone for about a second in a stage 02 fight, 40 tiles of one pose).
# WORK/pose_keys.txt, one hex sprite key a line; tools/pose_keys.py writes it. Every stage file but the front end holds them, ranked POSE_RANK (just under the common census keys; screen keys stay first).
POSE_RANK = int(os.environ.get("POSE_RANK", "400"))   # between the rarely used census keys (rank under 400) and the common ones (500 and up): a stage short of room drops the rare ones first
POSE_KEYS = set()
if (WORK / "pose_keys.txt").exists() and os.environ.get("POSE_KEYS", "1") == "1":
    POSE_KEYS = {int(l, 16) for l in (WORK / "pose_keys.txt").read_text().split()}
FUZZ_STAGE = {}   # stage name -> sprite keys the fuzz runs looked up in that stage (all palettes), unranked
if os.environ.get("POSE_KEYS", "1") == "1" and (WORK / "fuzz_stage_keys").is_dir():
    for f in (WORK / "fuzz_stage_keys").glob("stage*.txt"):
        FUZZ_STAGE[f.stem] = {int(l, 16) for l in f.read_text().split()}
# Home builds only: the whole caption font (scroll 1 codes 0x1260-0x131f, with the 0x1246-9 and 0x1256-9 signs, both column halves) in every round file. The census routes press
# through the story scenes, so the glyphs a stage's own captions use ("These aliens are all from one hive", stage select starts and any
# play that lets the story run) were not in its file: letters drew blank, "These   iens". The font is 192 codes in 12 rows of 16: signs (the apostrophe
# is 0x126d), digits, capitals, lower case, top and bottom halves. 392 keys, about 12 KB of tiles per file.
CAPTION_KEYS = set()
if "SAT_HOME" in os.environ.get("KERNEL_CFLAGS", ""):
    CAPTION_KEYS = {(c << 1) | h for c in list(range(0x1260, 0x1320)) + [0x1246, 0x1247, 0x1248, 0x1249, 0x1256, 0x1257, 0x1258, 0x1259] for h in (0, 1)}
STRETCHES = [(0x02400000 + a, n) for a, n in ROUNDS["holes"] if n >= 0x4000]
# The story captions' ROM pages (tools/story_text_pages.py) stay intact in every round file: a caption the census let skip sat in a page the file treated as free and overwrote
# with tile bytes (stage 14's second caption box, 17 cells of tile bytes before "ized by the aliens!"). Pages under cold lifted code cannot stay. STORY_PAGES=0 builds without.
import story_text_pages
STORY_PAGES = story_text_pages.from_work(WORK, ROUNDS["page"]) if os.environ.get("STORY_PAGES", "1") == "1" else set()


def guest_plan():
    """Bonus characters (SAT_GUESTS with SAT_GUEST_DATA="IDX=DIR[;IDX=DIR]", IDX the guests.c row, DIR an assets.py output with remap.json
    and gfx_*.bin): one extra round file per AvP file of the replaced slot, keys = that file's keys - the slot character's own keys + the
    guest's one trimmed set, tiles from the guest's graphics region. Appended after the arcade's files, so their numbers do not move.
    GUEST_STAGES (e.g. "02") limits the stages, for a quick test build. Without SAT_GUEST_DATA nothing changes."""
    spec = os.environ.get("SAT_GUEST_DATA", "")
    if not spec or "SAT_GUESTS" not in os.environ.get("KERNEL_CFLAGS", ""):
        return
    sys.path.insert(0, str(REPO / "tools"))
    import rounds_variants
    data = rounds_variants.Data(os.environ.get("GUEST_SPEC", "E:/AvP/learning/lane-packs/spec.json"))
    slots = {0: 2, 1: 4}   # guests.c rows: Wolverine (Schaefer), Mega Man (Hunter)
    only = [int(x, 16) for x in os.environ.get("GUEST_STAGES", "").split(",") if x]
    masks, vf = ROUNDS.get("variant_masks", []), ROUNDS.get("variant_file", {})
    gf = ROUNDS.setdefault("guest_files", {})
    for item in spec.split(";"):
        gi, d = item.split("=", 1)
        gi, d = int(gi), pathlib.Path(d)
        if str(gi) in gf:
            raise SystemExit(f"NO-GO: guest row {gi} configured twice; use GUEST_ASSETS for Wolverine and SAT_GUEST_DATA only for other guests")
        A = json.loads((d / "remap.json").read_text())
        gfx = str(next(d.glob("gfx_*.bin")))
        round_cache.require_unused_remap(str(d), A["keys"], ARCADE_SPRITE_KEYS | SCREEN_KEYS[0])
        slot = slots[gi]
        made, per = {}, gf.setdefault(str(gi), {})
        for st, files in vf.items():
            if only and int(st) not in only:
                continue
            row = [0] * (len(masks) + 1)
            for v in range(1, len(masks) + 1):
                if not masks[v - 1] & slot:
                    continue
                b = files[v]
                if b not in made:
                    base = ROUNDS["files"][b]
                    # A trimmed asset set may keep the full extraction in keys;
                    # gameplay must use its selected set, as GUEST_ASSETS does.
                    gkeys = set(A.get("stage_keys", {}).get(f"{int(st):02x}", A["keys"]))
                    own = set(base["keys"][0]) & data.own[slot]
                    nf = dict(base, name=base["name"] + f"_g{gi}", rank_from=base["name"], audio_from=b, gfx=gfx, guest_keys=sorted(gkeys),
                              keys=[sorted(set(base["keys"][0]) - own | gkeys)] + [list(k) for k in base["keys"][1:]])
                    made[b] = len(ROUNDS["files"])
                    ROUNDS["files"].append(nf)
                row[v] = made[b]
            per[st] = row
        print("guest", gi, "files", len(made), flush=True)


guest_plan()


DUEL_ARENAS = (0x0e, 0x1c, 0x1e, 0x24)
def duel_plan():
    """Versus mode (SAT_DUEL_MENU): the RANDOM arenas 0e, 1c, 1e and 24 read ROM pages that stage 02's walk reads and their own walks never do (lane versus: the colour
    tables 0xffc00-0x1053ff and the effect and alien frame data around 0xbf000, 0xcf400, 0x190800), and their round files spill sprite tiles into exactly those pages: the duel
    drew wrong tiles, noise blocks and black aliens. A copy of each pair file of an arena stage (arcade and guest files alike, appended after them so no number moves) keeps stage 02's
    pages as well, and the kernel runs the copy while a duel is on (kernel.c duel_pairs). Normal play keeps its files, so the main game loses no sprite keys to it.
    DUEL_FILES=0 builds without the copies (A/B). ROUNDS["duel_files"] = [[file, its duel copy]]."""
    if "SAT_DUEL_MENU" not in os.environ.get("KERNEL_CFLAGS", "") or os.environ.get("DUEL_FILES", "1") == "0":
        ROUNDS["duel_files"] = []
        return
    files, masks, vf = ROUNDS["files"], ROUNDS.get("variant_masks", []), ROUNDS.get("variant_file", {})
    k02 = set(next(f for f in files if f["name"] == "stage02")["keep_pages"])
    tables = [("%02x" % st, vf.get(str(st))) for st in DUEL_ARENAS]
    tables = [(st, t, False) for st, t in tables if t] + [(st, t, True) for g in ROUNDS.get("guest_files", {}).values() for st, t in g.items() if st != "0" and int(st) in DUEL_ARENAS]
    pairs, made = [], {}
    for st, row, guest in tables:
        for v, m in enumerate(masks, start=1):
            i = row[v]
            if bin(m).count("1") != 2 or not i or i in made:
                continue
            f = dict(files[i], name=files[i]["name"] + "_d", duel=True, audio_from=files[i].get("audio_from", i), rank_from=files[i].get("rank_from", files[i]["name"]),
                     keep_pages=sorted(set(files[i]["keep_pages"]) | k02))
            made[i] = len(files)
            files.append(f)
            pairs.append([i, made[i]])
    ROUNDS["duel_files"] = pairs
    print("duel files:", len(pairs), "keeping stage 02's", len(k02), "pages", flush=True)


duel_plan()


OPMAP = json.loads((WORK / "opx.json").read_text())


def sh(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(" ".join(map(str, cmd)) + "\n" + r.stdout[-3000:] + r.stderr[-3000:])
    return r.stdout


def update(path, text):
    if not path.exists() or path.read_text() != text:
        path.write_text(text)
    return path


def opx_rewrite(m):
    paren = "((" if m[0].count("(") == 2 else "("
    return f"OP{m[1]}{paren}0x{OPMAP[hex(int(m[2], 16))]:x}u"


TABLE_BASES = re.compile(r"\(\(u32\)(0x(?:162f90|163032|163074|1630f6)u)\)")   # Schaefer\'s four animation index tables as immediates of the lifted code


def gen_sources():
    out = []
    for s in sorted((WORK / "src").glob("c*.c"), key=lambda p: int(p.stem[1:])):
        t = s.read_text()
        a, b = t.index("#else\nregister Cpu *R"), t.index("#define SHL8(")
        t = t[:a] + '#else\n#include "lift_target.h"\n#endif\n' + t[b:]
        t = re.sub(r"\bOP(8|16|32)\(\(?0x([0-9a-f]+)u", opx_rewrite, t)
        if NATIVE_GFX:   # the table-base immediates read sat_wv_tb[] (wolverine.c): Schaefer's own table addresses while the setting is off, the relocated ones while his native block is on
            t = TABLE_BASES.sub(lambda m: "((u32)sat_wv_tb[" + str(["0x162f90u", "0x163032u", "0x163074u", "0x1630f6u"].index(m[1])) + "])", t)
            t = t.replace('#include "lift_target.h"' + chr(10) + '#endif' + chr(10), '#include "lift_target.h"' + chr(10) + '#endif' + chr(10) + 'extern unsigned sat_wv_tb[4];' + chr(10) + 'extern unsigned char sat_wv_cn[2];' + chr(10), 1)
            # Schaefer's attack chain counter (+0x81) wraps at 4 stages (two `& 3` sites of f_24454); a Wolverine player's count is set by wolverine.c (sat_wv_cn, 4 for everyone else, so the arcade is unchanged)
            for site in ("24528", "2454c"):
                t = t.replace("P(0x%su);{{u8 s=((u8)0x3u);u8 v=RD8((a6+(129)))&s;WR8((a6+(129)),(u8)(v));}}" % site,
                              "P(0x%su);{{u8 s=((u8)0x3u);u8 v=RD8((a6+(129)))&s;if(v>=sat_wv_cn[((a6>>8)+1)&1])v=0;WR8((a6+(129)),(u8)(v));}}" % site)
        for n in NATIVE + OVERRIDES + GUEST_WRAP:   # replaced natively; the lifted body stays linked as lifted_NNN
            t = t.replace(f"void f_{n}(void){{", f"void lifted_{n}(void){{")
        for n in OVERRIDES:   # memory is tight and the target never falls back: the replaced body goes
            t = re.sub(r"^void lifted_%s\(void\)\{.*?^\}\n" % n, "", t, flags=re.M | re.S)
        out.append(update(GEN / s.name, t))
    d = re.sub(r'void f_([0-9a-f]+)\(void\)\{puts\("MISSING [0-9a-f]+"\);fflush\(stdout\);exit\(3\);\}',
               lambda m: f"void f_{m[1]}(void){{sat_fatal(0xe9,0x{m[1]}u);}}", (WORK / "dispatch.inc").read_text())
    out.append(update(GEN / "dispatch.c", "typedef unsigned int u32;extern void sat_fatal(u32,u32);\n" + d +
                      "void f_dispatch(u32 a){VF f=lookup(a);if(!f)sat_fatal(0xe1,a);f();}\n"))
    seed = WORK / "golden_seed.bin"   # 16 bytes the skipped hardware test leaves at 0xff0e90, from the golden dump
    if not seed.exists():
        with open("E:/AvP/learning/mame/golden_c/probe.tsv", "rb") as f:
            f.seek(72 + 0xe90)
            seed.write_bytes(f.read(16))
    update(GEN / "seed.inc", ",".join(str(x) for x in seed.read_bytes()))
    update(GEN / "guest_hudpal.inc", pathlib.Path(HUD["include"]).read_text() if HUD else hud_art.pal_include([]))   # guests.c: select screen and HUD colours of the guests
    update(GEN / "guest_face.inc", pathlib.Path(HUD["face_include"]).read_text() if HUD else hud_art.face_include_empty())   # guests.c: his talk box face cells, drawn in every stage file while he is on
    save = WORK / "save_seed.bin"   # settings block the arcade keeps in EEPROM, from the golden dump
    if not save.exists():
        with open("E:/AvP/learning/mame/golden_c/probe.tsv", "rb") as f:
            f.seek(72 + 0xef0)
            save.write_bytes(f.read(0x80))
    update(GEN / "save_seed.inc", ",".join(str(x) for x in save.read_bytes()))
    # Stage word -> row; row, variant -> file. Row 0 is the front end. Mask ff81cc -> variant; 0 is the one-for-all file.
    vf, masks = ROUNDS.get("variant_file", {}), ROUNDS.get("variant_masks", [])
    rows = [[0] * (len(masks) + 1)]
    srow = [0] * 256
    for i in range(256):
        f = ROUNDS["stage_file"].get(str(i), 0)
        if f:
            srow[i] = len(rows)
            rows.append(vf.get(str(i), [f] * (len(masks) + 1)))
    mvar = [masks.index(m) + 1 if m in masks else 0 for m in range(16)]
    dp = ROUNDS.get("duel_files", [])
    update(GEN / "rounds.inc", "static const u8 stage_row[256] = {%s};\nstatic const u8 mask_variant[16] = {%s};\nstatic const unsigned short row_file[%d][%d] = {%s};\n#define DUEL_PAIRS %d\nstatic const unsigned short duel_pairs[%d][2] = {%s};\n" % (
        ",".join(map(str, srow)), ",".join(map(str, mvar)), len(rows), len(masks) + 1, ",".join("{" + ",".join(map(str, r)) + "}" for r in rows), len(dp), len(dp) + 1, ",".join("{%d,%d}" % tuple(x) for x in dp) or "{0,0}"))
    # Bonus characters (SAT_GUESTS): guest -> stage word -> file per variant, from rounds.json "guest_files"; 0 = the arcade's file.
    gf = ROUNDS.get("guest_files", {})
    ng = max([1] + [int(g) + 1 for g in gf])   # indexed by the guests.c row
    tab = [[[0] * (len(masks) + 1) for _ in rows] for _ in range(ng)]
    for g, per in gf.items():
        gi = int(g)
        for st, files in per.items():
            if srow[int(st)] or int(st) == 0:   # stage word 0: the front end, row 0 (a guest's own front file, select screen art)
                tab[gi][srow[int(st)]] = files
    update(GEN / "guest_files.inc", ("#define GUEST_ROWS %d" + chr(10) + "static const unsigned short guest_file[%d][%d][%d] = {%s};" + chr(10)) % (
        len(gf) and ng, ng, len(rows), len(masks) + 1, ",".join("{" + ",".join("{" + ",".join(map(str, r)) + "}" for r in t) + "}" for t in tab)))
    return out


def cc(src, obj, extra=()):
    newest = max(src.stat().st_mtime, (HERE / "lift_target.h").stat().st_mtime)
    if src.name in ("kernel.c", "pad.c", "sat_gfx.c", "home.c", "home_cold.c", "fps_hud.c", "home_font_cold.c", "guests.c", "megaman.c", "wolverine.c", "wv_features.c", "game_bind.c", "reveal.c"):
        newest = max(newest, (HERE / "sat_rt.h").stat().st_mtime, time.time() if os.environ.get("KERNEL_CFLAGS") else 0)
    if src.name == "sat_gfx.c":
        newest = max(newest, (src.parent / "sat_gfx.h").stat().st_mtime)
    if not obj.exists() or obj.stat().st_mtime < newest:
        sh([GCC, *CF, *extra, "-c", src, "-o", obj])
    return obj


def code_size(o):
    rows = (l.split() for l in sh([OBJDUMP, "-h", o]).splitlines())
    return sum(int(r[2], 16) for r in rows if len(r) > 3 and r[1].startswith((".text", ".rodata", ".data")))


SHARED_MIN = int(os.environ.get("ROUND_SHARED_MIN", "10"))   # stages
MIN_RUN = int(os.environ.get("ROUND_MIN_RUN", "1"))   # pages; a stretch costs 8 bytes of table, about 1 KB of a page is 8 sprites
ROWTRIM = int((re.search(r"-DSAT_TILE_ROWTRIM(?:=(\d))?(?!\w)", os.environ.get("KERNEL_CFLAGS", "")) or [0, 0])[1] or 1) if "SAT_TILE_ROWTRIM" in os.environ.get("KERNEL_CFLAGS", "") else 0   # default off: sprite tiles as row masked records, SGP2 (tools/satgfx_pack.py record, saturn/gfx/sat_gfx.c rowtrim_load); the kernel and the packs must agree
TAIL_FILL = os.environ.get("PACK_TAIL_FILL", "0") == "1"   # default off: tile spill uses the last odd page of a ROM stretch too (tools/rounds_pack.py plan, assemble)


def round_files(rom, code_end, cold1_at, only=None):
    """only: file numbers to build alone (kept round files beside them; guest files): no spill into ROM stretches, every kept page restored.
    One RNN.BIN per stage. Sprites past the cart's room go to ROM stretches that stage does not read; whatever any file overwrites, each stage that reads it gets back."""
    sys.path.insert(0, str(REPO / "tools"))
    import rounds_pack
    raw = pathlib.Path(os.environ.get("GFX_BIN", "E:/AvP/learning/lane-satgfx/gfx.bin")).read_bytes()
    room = cold1_at - CART["SAT_PACK"]
    page = ROUNDS["page"]
    code = bytearray(0x200000 // page)   # pages holding lifted cold code never take tiles
    for at, end in code_end:
        for q in range((at - CART["ROMB"]) // page, (end - CART["ROMB"] + page - 1) // page):
            code[q] = 1
    plans, written = [], set()
    if STORY_PAGES:
        print("story caption pages kept in every round file: %d, of them under cold code (cannot stay): %s" % (len(STORY_PAGES), ", ".join("%#x" % (q * page) for q in sorted(STORY_PAGES) if code[q]) or "none"), flush=True)
    # Census gap: a mode or setting outside the census can read common tables a walk of this stage never touched. Pages most stages read stay in every stage. Costs sprites only in stages already short of room.
    base = [f for f in ROUNDS["files"] if re.fullmatch(r"stage[0-9a-f]{2}", f["name"])]
    seen = {}
    for f in base:
        for q in set(f["keep_pages"]):
            seen[q] = seen.get(q, 0) + 1
    shared = {q for q, c in seen.items() if c >= SHARED_MIN}
    rank = json.loads((WORK / "key_rank.json").read_text()) if (WORK / "key_rank.json").exists() else {}   # tools/rounds_rank.py
    # ARENA_KEEP (test): the duel's RANDOM arenas also keep the pages stage 02's walk reads, so their spilled sprites stay off what the duel reads there.
    k02 = set(next(f for f in base if f["name"] == "stage02")["keep_pages"]) if os.environ.get("ARENA_KEEP") else set()
    if os.environ.get("ARENA_KEEP", "1") not in ("1", "all"):   # ranges of byte addresses, e.g. ffc00-105400,bf000-bf400: only those of 02's pages
        want = set()
        for r in os.environ["ARENA_KEEP"].split(","):
            lo, hi = (int(x, 16) for x in r.split("-"))
            want.update(range(lo // page, (hi + page - 1) // page))
        k02 &= want
    raws = {}
    for fi, f in enumerate(ROUNDS["files"]):
        if only is not None and fi not in only:
            plans.append(None)
            continue
        keep = set(f["keep_pages"]) | shared | STORY_PAGES
        if k02 and set(f.get("stages", [])) & {0x0e, 0x1c, 0x1e, 0x24}: keep |= k02
        free, st = [], None
        for q in range(0x200000 // page + 1):
            ok = q < 0x200000 // page and q not in keep and not code[q]
            if ok and st is None:
                st = q
            if not ok and st is not None:
                if q - st >= MIN_RUN:
                    # PACK_TAIL_FILL: a run ending in a page this file keeps (plain ROM, no cold code) may use its odd page: the sector's tail rewrites that page with the ROM's bytes
                    free.append([st * page, (q - st) * page] + ([True] if TAIL_FILL and q < 0x200000 // page and q in keep and not code[q] else []))
                st = None
        free.sort(key=lambda r: -r[1])
        keys, frank = [set(k) for k in f["keys"]], {int(x): v for x, v in rank.get(f.get("rank_from", f["name"]), {}).items()}
        char_fuzz.rank(f, frank) if CHAR_FUZZ else None   # fuzz and body keys (tools/char_fuzz.py); a guest's keys below still outrank them
        frank.update({k: 1 << 39 for k in f.get("guest_keys", ())})   # a guest's frames rank as the playing character's own route
        if only is not None:
            free = []
        if not f["name"].startswith("front"):   # (front_wv, a guest's front file, is a front file too) continue and game over screens: reachable from every stage, kept first (tools/screen_keys.py)
            keys = [k | e for k, e in zip(keys, SCREEN_KEYS)]
            keys[0] = keys[0] | POSE_KEYS
            keys[0] = keys[0] | FUZZ_STAGE.get(f["name"].split("_")[0], set())
            frank.update({k: POSE_RANK for k in POSE_KEYS if k not in frank or frank[k] < POSE_RANK})
            frank.update({k: 1 << 40 for k in SCREEN_KEYS[0]})
        if f.get("gfx") and f["gfx"] not in raws:
            raws[f["gfx"]] = pathlib.Path(f["gfx"]).read_bytes()
        if FONT_KEYS:
            keys[1] = keys[1] | FONT_KEYS
        if EDGE_KEYS:
            keys[1] = keys[1] | EDGE_KEYS
        if CAPTION_KEYS:
            keys[1] = keys[1] | CAPTION_KEYS
        if f["name"] == "front":
            keys[1] = keys[1] | SELECT_DIGIT_KEYS
        p, dropped = rounds_pack.fit(raws.get(f.get("gfx"), raw), keys, room, free, frank, ROWTRIM)
        # Check every plan before the write loop, including optional guest stages
        # 06/1c/1e. A high rank alone never guarantees that the tiles fit.
        round_cache.require_guest_tiles(f["name"], f.get("guest_keys", ()), keys[0], dropped, p)
        for si, (first, a, take) in enumerate(p["segs"]):
            written.update(range(a // page, (a + (rounds_pack.seg_len(p, si) + 2047 & -2048) + page - 1) // page))
        plans.append((p, dropped))
    stats = {}
    if only is None:   # the pages each file keeps as the planner saw them (own, front end, next stage, fuzz, shared): tools/check_round_pages.py reads the built files against this
        (WORK / "round_keep.json").write_text(json.dumps([[f["name"], sorted(set(f["keep_pages"]) | shared)] for f in ROUNDS["files"]]))
    for i, (f, pl) in enumerate(zip(ROUNDS["files"], plans)):
        if pl is None:
            continue
        p, dropped = pl
        if only is not None:
            written = set(f["keep_pages"]) | shared   # built alone: restore every kept page
        own = {x for si, (first, a, take) in enumerate(p["segs"]) for x in range(a // page, (a + (rounds_pack.seg_len(p, si) + 2047 & -2048) + page - 1) // page)}
        back = sorted((written & (set(f["keep_pages"]) | shared)) - own)
        restores, st = [], None
        for q in back + [None]:
            if st is not None and (q is None or q != st[1]):
                restores.append((CART["ROMB"] + st[0] * page, bytes(rom[st[0] * page:st[0] * page + ((st[1] - st[0]) * page + 2047 & -2048)]))); st = None   # whole sectors of ROM, so no padding lands on the next page
            if q is None:
                break
            st = [q, q + 1] if st is None else [st[0], q + 1]
        audio = (WORK / "audio" / f"r{f.get('audio_from', i):03d}.bin").read_bytes()
        n = rounds_pack.write_file(ISO / f"R{i:03d}.BIN", audio, restores, rounds_pack.assemble(p, CART["SAT_PACK"], rom if TAIL_FILL else None))
        stats[f["name"]] = dict(file=n, sprites_in_main=p["inmain"], sprites_spill=sum(x[2] for x in p["segs"]), spill_runs=len(p["segs"]), restore=sum(len(d) for _, d in restores), restore_runs=len(restores), dropped_keys=len(dropped), dropped=dropped, audio=len(audio))
        print(f["name"], {k: v for k, v in stats[f["name"]].items() if k != "dropped"}, flush=True)
    if only is None:
        (WORK / "round_stats.json").write_text(json.dumps(stats, indent=0))
    else:
        (WORK / "guest_round_stats.json").write_text(json.dumps(stats, indent=0))


def refresh_restores(rom):
    """Round files restore ROM pages, and a page can hold cold code, whose calls name kernel addresses: a kept file must carry this build's bytes. Layout as boot.c reads it: one head sector of count, then destination and bytes pairs."""
    import struct
    n = 0
    for f in ISO.glob("R[0-9][0-9][0-9].BIN"):
        with open(f, "r+b") as h:
            head = h.read(2048)
            at, changed, packs = 2048, False, 0
            for i in range(struct.unpack_from(">I", head)[0]):
                dest, size = struct.unpack_from(">II", head, 4 + i * 8)
                if dest == 1:
                    continue
                packs += dest == CART["SAT_PACK"]
                if packs >= 2:   # the tile pack and its sprite spills into ROM stretches follow: those are tiles, not ROM restores (rounds_pack.write_file order)
                    break
                if CART["ROMB"] <= dest < CART["ROMB"] + len(rom):
                    h.seek(at)
                    want = bytes(rom[dest - CART["ROMB"]:dest - CART["ROMB"] + size])
                    if h.read(size) != want:
                        h.seek(at); h.write(want); changed = True
                at += size
            n += changed
    return n


def main():
    gen = gen_sources()
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        objs = list(ex.map(lambda s: cc(s, OBJ / (s.stem + ".o"), [OPT]), gen))
    home = "SAT_HOME" in os.environ.get("KERNEL_CFLAGS", "")
    if home:
        sh([sys.executable, REPO / "tools/home_font.py", WORK, os.environ.get("GFX_BIN", "E:/AvP/learning/lane-satgfx/gfx.bin")])
    gfx_dir = REPO / "saturn/gfx"
    gfx = [gfx_dir / "sat_gfx.c"]
    own = [cc(HERE / "ctx.s", OBJ / "ctx.o"), cc(HERE / "kernel.c", OBJ / "kernel.o", ["-O2", "-I", GEN] + os.environ.get("KERNEL_CFLAGS", "").split()), cc(HERE / "present.c", OBJ / "present.o", ["-O2"]), cc(HERE / "pad.c", OBJ / "pad.o", ["-O2"] + os.environ.get("KERNEL_CFLAGS", "").split())]
    own += [cc(REPO / "saturn/audio/sat_audio.c", OBJ / "sat_audio.o", ["-Os"] + os.environ.get("AUDIO_CFLAGS", "").split())]
    own += [cc(s, OBJ / f"gfx_{s.stem}.o", ["-O2", "-I", gfx_dir, "-I", GEN] + os.environ.get("KERNEL_CFLAGS", "").split()) for s in gfx]
    if home:
        own += [cc(HERE / "home.c", OBJ / "home.o", ["-Os"] + os.environ.get("KERNEL_CFLAGS", "").split())]
    home_cold_extra = []   # guest code and tables run from the cart tail with the cold home code (high RAM is full)
    reveal_obj = None
    if "SAT_WV_REVEAL" in os.environ.get("KERNEL_CFLAGS", ""):   # the post-credits reveal is an overlay on the disc (REVCODE.BIN, linked after sat.elf below), not resident code: the cart step and high RAM stay as they were
        reveal_obj = cc(HERE / "reveal.c", OBJ / "reveal.o", ["-Os", "-I", gfx_dir, "-I", GEN] + os.environ.get("KERNEL_CFLAGS", "").split())
    if "SAT_GUESTS" in os.environ.get("KERNEL_CFLAGS", ""):   # bonus characters; builds without the flag are unchanged
        home_cold_extra.append(cc(HERE / "guests.c", OBJ / "guests.o", ["-Os", "-I", GEN] + os.environ.get("KERNEL_CFLAGS", "").split()))
        if os.environ.get("GUEST_ASSETS"):   # Wolverine's tables come from the user's ROM set at build time; his code runs from the cart
            if NATIVE_GFX:   # his native animation block, from his program ROM (a MAME dump, tools/wolverine/mshvsf_dump.lua) and the guest assets
                sh([sys.executable, REPO / "tools/wolverine/gen_native.py", WORK, os.environ["GUEST_ASSETS"], os.environ.get("WV_MSHVSF", "E:/AvP/learning/lane-wv-native-gfx/mshvsf"), GEN / "wv_native.inc"])
            sh([sys.executable, REPO / "tools/wolverine/gen_c.py", os.environ["GUEST_ASSETS"], GEN / "wolverine_data.inc"] + ([os.environ["WV_COLOUR"]] if os.environ.get("WV_COLOUR") else []))   # WV_COLOUR: a colours entry of remap.json (default: its default_colour)
            # guests.c dispatches: his whole-list pass is renamed so the group-indexed guests (Mega Man) run first
            # Lane wv-features: with SAT_WV_HEAL / SAT_WV_FLASH his tick and pad hooks are renamed so saturn/guests/wolverine/wv_features.c wraps them (no edit to wolverine.c)
            wvf = "SAT_WV_HEAL" in os.environ.get("KERNEL_CFLAGS", "") or "SAT_WV_FLASH" in os.environ.get("KERNEL_CFLAGS", "")
            wv_ren = (["-Dsat_guest_wolverine_tick=wv_tick_inner"] if ("SAT_WV_HEAL" in os.environ.get("KERNEL_CFLAGS", "") or "SAT_WV_FLASH_HOLD=1" in os.environ.get("KERNEL_CFLAGS", "")) else []) + (["-Dsat_guest_wolverine_pad=wv_pad_inner"] if "SAT_WV_FLASH" in os.environ.get("KERNEL_CFLAGS", "") else [])
            home_cold_extra.append(cc(REPO / "saturn/guests/wolverine/wolverine.c", OBJ / "wolverine.o", ["-Os", "-I", GEN, "-I", HERE, "-Dsat_guest_objects=sat_guest_wolverine_objects"] + wv_ren + os.environ.get("KERNEL_CFLAGS", "").split()))
            if wvf:
                home_cold_extra.append(cc(REPO / "saturn/guests/wolverine/wv_features.c", OBJ / "wv_features.o", ["-Os", "-I", GEN, "-I", HERE] + os.environ.get("KERNEL_CFLAGS", "").split()))
            if "SAT_WV_SOUND" in os.environ.get("KERNEL_CFLAGS", ""):   # wv_sfx(): Wolverine's own sounds (lane wv-sounds); default off, the objects without the flag are unchanged
                home_cold_extra.append(cc(REPO / "saturn/guests/wolverine/wv_sound.c", OBJ / "wv_sound.o", ["-Os", "-I", REPO / "saturn/guests/wolverine"]))
                if "SAT_WV_SOUND_HOOKS" in os.environ.get("KERNEL_CFLAGS", "") and not wvf:   # test-only Berserker hook bodies; the features lane owns the real ones
                    home_cold_extra.append(cc(REPO / "saturn/guests/wolverine/wv_sound_hooks.c", OBJ / "wv_sound_hooks.o", ["-Os", "-I", REPO / "saturn/guests/wolverine"]))
        for item in filter(None, os.environ.get("SAT_GUEST_DATA", "").split(";")):   # per-guest drawing code and tables (saturn/guests/<name>)
            gi, d = item.split("=", 1)
            name = {"1": "megaman"}.get(gi)
            if name:
                sh([sys.executable, REPO / f"tools/{name}/gen_runtime.py", pathlib.Path(d) / "remap.json", GEN / f"guest_{name}.inc"])
                home_cold_extra.append(cc(REPO / f"saturn/guests/{name}/{name}.c", OBJ / f"guest_{name}.o", ["-Os", "-I", GEN] + os.environ.get("KERNEL_CFLAGS", "").split()))
    if "SAT_HOME_FONT_COLD" in os.environ.get("KERNEL_CFLAGS", ""):   # menu font and text palettes in the cart tail (lane perf-reconcile), default off
        home_cold_extra.append(cc(HERE / "home_font_cold.c", OBJ / "home_font_cold.o", ["-Os", "-I", GEN] + os.environ.get("KERNEL_CFLAGS", "").split()))
    if "SAT_FPS_HUD" in os.environ.get("KERNEL_CFLAGS", ""):   # performance readout (lane perf-reconcile): cold code in the cart tail, default off
        home_cold_extra.append(cc(HERE / "fps_hud.c", OBJ / "fps_hud.o", ["-Os", "-I", GEN] + os.environ.get("KERNEL_CFLAGS", "").split()))
    snap_bytes = 0
    if home:   # stage select's held title picture (home_cold.c sat_home_snap_frame) copies the graphics snapshot: its size comes from the gfx object (nm -S), so no constant stays in high RAM
        for l in sh([NM, "-S", OBJ / "gfx_sat_gfx.o"]).splitlines():
            f = l.split()
            if len(f) == 4 and f[3] in ("snap", "_snap"):
                snap_bytes = int(f[1], 16)
        stamp = GEN / "snap_bytes.txt"
        if not stamp.exists() or stamp.read_text() != str(snap_bytes):
            (OBJ / "home_cold.o").unlink(missing_ok=True)
            stamp.write_text(str(snap_bytes))
    home_cold = [cc(HERE / "home_cold.c", OBJ / "home_cold.o", ["-Os", f"-DSAT_SNAP_BYTES={snap_bytes}"] + os.environ.get("KERNEL_CFLAGS", "").split())] if home else []
    home_cold += home_cold_extra
    if OVERRIDES:
        bind_flags = ["-DSAT_GUESTS"] if "SAT_GUESTS" in os.environ.get("KERNEL_CFLAGS", "") else []
        if "SAT_WOLVERINE_DEBUG" in os.environ.get("KERNEL_CFLAGS", ""):
            bind_flags.append("-DSAT_WOLVERINE_DEBUG")
        if NATIVE_GFX:
            bind_flags.append("-DSAT_WV_NATIVE_GFX")
        own += [cc(REPO / "saturn/game" / f"{n}.c", OBJ / f"game_{n}.o", ["-O2", "-DSAT_TARGET", "-I", REPO / "saturn/game"] + bind_flags) for n in ("game_hot", "game_bind")]
    sizes = {o: code_size(o) for o in objs}
    # Hottest chunks in high work RAM, then low work RAM; the coldest run from the cart. Heat comes from the MAME route.
    heat = json.loads((WORK / "heat.json").read_text())
    objs_o = sorted(objs, key=lambda o: -heat.get(o.stem, 1 << 40))
    room_hw = HW_LIMIT - HW_BASE - HW_RESERVED
    room_lw = LW_LIMIT - LW_BASE - LW_RESERVED
    # The seven hottest chunks hold about 97% of the instructions and always go first. The rest barely differ in heat, so they are chosen to fill the RAM.
    hw, used = [], 0
    room_hw -= 9600   # own code and data the count leaves out
    for o in objs_o[:7]:
        if used + sizes[o] <= room_hw:
            hw.append(o); used += sizes[o]
    tail = [o for o in objs_o if o not in hw]
    fill = {0: []}
    for o in tail:
        for total, picked in list(fill.items()):
            t = total + sizes[o]
            if used + t <= room_hw and t not in fill:
                fill[t] = picked + [o]
    best_fill = max(fill)
    hw += fill[best_fill]; used += best_fill
    rest = [o for o in objs_o if o not in hw]
    cold1_at = COLD1_AT
    room_cold1 = COLD1_ROOM
    best = None
    for mask in range(1 << len(rest)):
        out = [o for i, o in enumerate(rest) if mask >> i & 1]
        if sum(sizes[o] for o in rest) - sum(sizes[o] for o in out) > room_lw - 8192:   # margin: bss the size count leaves out
            continue
        placed, rooms = [[] for _ in STRETCHES], [s[1] for s in STRETCHES]
        for o in sorted(out, key=lambda o: -sizes[o]):   # largest first into the ROM stretches, tightest that fits
            fit = [i for i in range(len(rooms)) if sizes[o] <= rooms[i]]
            if fit:
                i = min(fit, key=lambda i: rooms[i])
                placed[i].append(o); rooms[i] -= sizes[o]
        two = [o for p in placed for o in p]
        three = []
        if sum(sizes[o] for o in out if o not in two and o not in three) > room_cold1:
            continue
        score = (sum(heat.get(o.stem, 1 << 40) for o in out), len(out))
        if best is None or score < best[0]:
            best = (score, out, placed, three)
    if best is None:
        raise SystemExit(f"NO-GO: no placement fits: rest {sum(sizes[o] for o in rest)} room_lw {room_lw} cold1 {room_cold1} stretches {STRETCHES} sizes {sorted(sizes[o] for o in rest)}")
    cold = best[1]
    placed = best[2]
    cold2 = [o for p in placed for o in p]
    cold3 = best[3]
    cold1 = [o for o in cold if o not in cold2 and o not in cold3]
    # The cart tail holds only what cold code needs; the rest is sprite room.
    cold1_at = CART_END - ((sum(sizes[o] for o in cold1) + sum(code_size(o) for o in home_cold) + 0x1fff) & ~0xfff)
    lw = [o for o in rest if o not in cold]
    usedl = sum(sizes[o] for o in lw)
    print("placement", {"hw": len(hw), "lw": [o.stem for o in lw], "cold1": [(o.stem, sizes[o], heat.get(o.stem)) for o in cold1], "stretches": [[o.stem for o in p] for p in placed]})
    inp = lambda l, s: "\n".join(f'    "{o.as_posix()}"({s})' for o in l)
    tx = ".text .text.* .rodata .rodata.* .data .data.*"
    stretch_ld = "".join(f"""  .st{i} {s[0]:#x} : {{
{inp(placed[i], tx)}
    . = ALIGN(4);
    _sat_st{i}_end = .;
  }}
""" for i, s in enumerate(STRETCHES))
    ld = f"""ENTRY(_sat_start)
SECTIONS {{
  .hw {HW_BASE:#x} : {{
{inp(own, '.text .text.*')}
{inp(hw, tx)}
{inp(own, '.rodata .rodata.* .data .data.*')}
    . = ALIGN(4);
  }}
  .hwbss (NOLOAD) : {{
    _sat_bss_start = .;
{inp(own, '.bss COMMON')}
{inp(hw, '.bss COMMON')}
    . = ALIGN(4);
    _sat_bss_end = .;
  }}
  .cold1 {cold1_at:#x} : {{
{inp(cold1 + home_cold, tx)}
    . = ALIGN(4);
    _sat_cold1_end = .;
  }}
{stretch_ld}  .lw {LW_BASE:#x} : {{
    *(.text .text.* .rodata .rodata.* .data .data.*) *(.lwcode)
    . = ALIGN(4);
  }}
  .lwbss (NOLOAD) : {{ _sat_lw_bss_start = .; *(.lwgfx) *(.bss COMMON) . = ALIGN(4); _sat_lw_bss_end = .; }}
  /DISCARD/ : {{ *(.comment) *(.eh_frame*) }}
}}
""" + "".join(f"_{k} = {v:#x};\n" for k, v in CART.items())
    (WORK / "sat.ld").write_text(ld)
    elf = WORK / "sat.elf"
    sh([GCC, "-m2", "-mb", "-nostdlib", "-T", WORK / "sat.ld", *own, *home_cold, *objs, "-lgcc", "-o", elf, f"-Wl,-Map={WORK / 'sat.map'}"])
    sh([OBJCOPY, "-O", "binary", "-j", ".hw", elf, ISO / "HW.BIN"])
    sh([OBJCOPY, "-O", "binary", "-j", ".lw", elf, ISO / "LW.BIN"])
    syms = {p[2]: int(p[0], 16) for p in (l.split() for l in sh([NM, elf]).splitlines()) if len(p) == 3}
    shutil.copy(WORK / "opx.bin", ISO / "OPX.BIN")
    if reveal_obj:   # the reveal's code: linked at 0x02750000 against the finished sat.elf (its symbols only), read from the disc at the ending (reveal.c, guests.c sat_reveal_poll)
        ov = WORK / "reveal_ov.elf"
        sh([GCC, "-m2", "-mb", "-nostdlib", "-T", HERE / "reveal_ov.ld", reveal_obj, f"-Wl,--just-symbols={elf}", "-o", ov])
        sh([OBJCOPY, "-O", "binary", "-j", ".ov", ov, ISO / "REVCODE.BIN"])
        if not 16 <= (ISO / "REVCODE.BIN").stat().st_size <= 0x4000:   # the art buffer starts at 0x02754000
            raise SystemExit("NO-GO: REVCODE.BIN is %d bytes (room 16 KB below the art buffer)" % (ISO / "REVCODE.BIN").stat().st_size)
        print("reveal: code", (ISO / "REVCODE.BIN").stat().st_size, "bytes (overlay at 0x02750000)", flush=True)
    if "SAT_WV_REVEAL" in os.environ.get("KERNEL_CFLAGS", ""):   # the reveal's art (the owner's, in git) and its voice (ROM-derived, never in git)
        shutil.copy(REVEAL_ART, ISO / "REVEAL.BIN")
        voice = pathlib.Path(os.environ.get("REVEAL_VOICE") or (pathlib.Path(os.environ.get("GUEST_ASSETS", ".")) / "reveal_voice.bin"))
        if voice.is_file():
            shutil.copy(voice, ISO / "RVVOICE.BIN")
        else:
            (ISO / "RVVOICE.BIN").unlink(missing_ok=True)
            print("reveal: no voice file (REVEAL_VOICE or GUEST_ASSETS/reveal_voice.bin): the reveal plays silent", flush=True)
        print("reveal: art", (ISO / "REVEAL.BIN").stat().st_size, "bytes; voice", (ISO / "RVVOICE.BIN").stat().st_size if (ISO / "RVVOICE.BIN").exists() else 0, "bytes", flush=True)
    if (WORK / "opx.bin").stat().st_size > OPX_MAX:
        raise SystemExit("NO-GO: store past its room")
    sh([OBJCOPY, "-O", "binary", "-j", ".cold1", elf, ISO / "COLD1.BIN"])
    if not (ISO / "COLD1.BIN").stat().st_size:   # the loader halts on an empty read
        (ISO / "COLD1.BIN").write_bytes(bytes(4))
    for i in range(len(STRETCHES)):
        sh([OBJCOPY, "-O", "binary", "-j", f".st{i}", elf, WORK / f"st{i}.bin"])
    hw_end, lw_end = syms["_sat_bss_end"], syms["_sat_lw_bss_end"]
    print({"hw_image": (ISO / "HW.BIN").stat().st_size, "hw_end": hex(hw_end), "hw_free": HW_LIMIT - hw_end,
           "lw_image": (ISO / "LW.BIN").stat().st_size, "lw_end": hex(lw_end), "lw_free": LW_LIMIT - lw_end,
           "lifted_code_total": sum(sizes.values()), "lifted_in_hw": used, "chunks_lw": [o.stem for o in lw],
           "cart_free": CART_END - syms["_sat_cold1_end"], "stretch_free": [s[0] + s[1] - syms[f"_sat_st{i}_end"] for i, s in enumerate(STRETCHES)]})
    if NATIVE_GFX:   # canary for every stage including 26: his block sits in the cart tail, outside the ROM image and every ROM stretch the stage files spill tiles over
        blk = syms["_wv_blk"]
        sz = int(re.search(r"#define WV_NAT_SIZE (\d+)", (GEN / "wv_native.inc").read_text())[1])
        bad = [n for n, (lo, hi) in [("ROM image", (CART["ROMB"], CART["ROMB"] + 0x200000))] + [("stretch %d" % k, (st[0], st[0] + st[1])) for k, st in enumerate(STRETCHES)] if blk < hi and blk + sz > lo]
        ok = not bad and cold1_at <= blk and blk + sz <= CART_END
        print({"wv_blk": hex(blk), "size": sz, "end": hex(blk + sz), "cold1_at": hex(cold1_at), "canary": "OUTSIDE the ROM image and every stretch, inside the cart tail" if ok else "BAD " + ",".join(bad)})
        if not ok:
            raise SystemExit("NO-GO: the native block overlaps pages a stage file takes: " + ",".join(bad))
    if syms["_sat_cold1_end"] > CART_END or any(syms[f"_sat_st{i}_end"] > s[0] + s[1] for i, s in enumerate(STRETCHES)):
        raise SystemExit("NO-GO: past the cart")
    if hw_end > HW_LIMIT or lw_end > LW_LIMIT:
        raise SystemExit("NO-GO on this layout: segment past its RAM")
    rom = bytearray((WORK / "rt.bin").read_bytes())
    for i, st in enumerate(STRETCHES):
        d = (WORK / f"st{i}.bin").read_bytes()
        at = st[0] - CART["ROMB"]
        rom[at:at + len(d)] = d
    (ISO / "ROM.BIN").write_bytes(rom)
    # KEEP_ROUND_FILES=1, for a kernel-only rebuild: round files never touch pages holding cold code, so they stay valid while those pages are the same.
    # The pack in main ends where cold1 starts: a kept file built for a lower cold1 would have its last tiles overwritten by cold code (seen as wrong tiles on crates in stages 24 and 1e).
    ends = [[st[0], syms[f"_sat_st{i}_end"]] for i, st in enumerate(STRETCHES)] + [[cold1_at, 0]]
    ends_file = WORK / "round_code_ends.json"
    names = round_cache.round_names(len(ROUNDS["files"]))
    head_sectors = round_cache.store_header_sectors(len(names))
    for f in (WORK / "rounds").glob("R[0-9][0-9][0-9].BIN"):   # SECTOR_STORE parks the round files here; kept files come back first
        if not (ISO / f.name).exists():
            shutil.move(str(f), ISO / f.name)
    # Stage files depend on more than memory addresses: reselected poses, changed
    # graphics or ranking can otherwise leave a new runtime using an old pack.
    inputs = {
        "build.py": pathlib.Path(__file__),
        "round_cache.py": HERE / "round_cache.py",
        "rounds_pack.py": REPO / "tools/rounds_pack.py",
        "satgfx_pack.py": REPO / "tools/satgfx_pack.py",
        "key_rank.json": WORK / "key_rank.json" if (WORK / "key_rank.json").exists() else None,
        "gfx": pathlib.Path(os.environ.get("GFX_BIN", "E:/AvP/learning/lane-satgfx/gfx.bin")),
    }
    for i, f in enumerate(ROUNDS["files"]):
        inputs[f"audio:{i}"] = WORK / "audio" / f"r{f.get('audio_from', i):03d}.bin"
        if f.get("gfx"):
            inputs[f"gfx:{i}"] = pathlib.Path(f["gfx"])
    fingerprint = round_cache.packing_inputs(ROUNDS, ends, dict(
        shared_min=SHARED_MIN, min_run=MIN_RUN, tail_fill=TAIL_FILL, rowtrim=ROWTRIM, arena_keep=os.environ.get("ARENA_KEEP"),
        screen_keys=[sorted(k) for k in SCREEN_KEYS], pack_address=CART["SAT_PACK"]), inputs)
    receipt = WORK / "round_pack_receipt.json"
    reason = round_cache.reuse_reason(receipt, fingerprint, ISO, names)
    if os.environ.get("KEEP_ROUND_FILES") and reason is None:
        n = refresh_restores(rom)
        print("round files kept; ROM restore bytes refreshed in", n, "files")
    else:
        if os.environ.get("KEEP_ROUND_FILES"):
            print("round files rebuilt:", reason)
        round_files(rom, [tuple(e) for e in ends[:-1]], cold1_at)
    # A smaller plan must not leave surplus generated files in STORE.BIN. Park
    # them for inspection instead of deleting an earlier build's artifacts.
    for f in round_cache.extra_rounds(ISO, names):
        parked = WORK / "stale_rounds" / (round_cache.file_hash(f) + "_" + f.name)
        parked.parent.mkdir(parents=True, exist_ok=True)
        if parked.exists():
            if round_cache.file_hash(parked) != round_cache.file_hash(f):
                raise SystemExit("NO-GO: stale-round archive conflict: " + str(parked))
            f.unlink()   # identical preserved copy already exists
        else:
            shutil.move(str(f), str(parked))
    round_cache.save_receipt(receipt, fingerprint, ISO, names)
    ends_file.write_text(json.dumps(ends))
    (WORK / "rom_final.bin").write_bytes(rom)
    b = OBJ / "boot.o"
    # SECTOR_STORE (default 1; 0 = old R*.BIN files, for A/B): the round files become runs of one shared STORE.BIN (tools/sector_store.py), so the game fits an 80-minute CD-R.
    store = os.environ.get("SECTOR_STORE", "1") != "0"
    if store:
        print(sh([sys.executable, REPO / "tools/sector_store.py", ISO, "--keep", WORK / "rounds"]).strip())
    else:
        (ISO / "STORE.BIN").unlink(missing_ok=True)
    sh([GCC, "-m2", "-mb", "-O2", "-w", "-fno-builtin", "-I", SGL / "INC", f"-DCOLD1_ADDR={cold1_at:#x}u"] + (["-DSECTOR_STORE"] if store else []) + (["-DSTORE_HEAD2"] if head_sectors == 2 else []) + (["-DSAT_WV_REVEAL"] + ([f"-DGUEST_SEL_ADDR={syms['_sat_guest_sel']:#x}u"] if "_sat_guest_sel" in syms else []) if "SAT_WV_REVEAL" in os.environ.get("KERNEL_CFLAGS", "") else []) + [ "-c", HERE / "boot.c", "-o", b])
    lib = SGL / "LIB_ELF"
    sh([GCC, "-m2", "-mb", "-nostartfiles", "-T", HERE / "boot.ld", b, "-Wl,--start-group", lib / "SEGA_SYS.A", lib / "LIBCD.A", lib / "LIBSGL.A", "-lgcc", "-lc", "-Wl,--end-group",
        "-o", WORK / "boot.elf", f"-Wl,-Map={WORK / 'boot.map'},-e,_main"])
    sh([OBJCOPY, "-O", "binary", "-j", ".text", WORK / "boot.elf", ISO / "0.BIN"])
    bend = next(int(l.split()[0], 16) for l in sh([NM, WORK / "boot.elf"]).splitlines() if l.endswith("__bend"))
    print("boot", (ISO / "0.BIN").stat().st_size, "bytes, bss end", hex(bend))
    if bend > 0x06013fe0:
        raise SystemExit("loader overlaps the runtime")
    ip = WORK / "IP.BIN"
    sh([sys.executable, REPO / "tools/build_loader_ip.py", JO / "Compiler/COMMON/IP.BIN", ip])
    for n in ("ABS.TXT", "CPY.TXT", "BIB.TXT"):
        (ISO / n).write_bytes((REPO / "cd" / n).read_bytes())
    iso = WORK / "sat.iso"
    r = subprocess.run([MKISOFS, "-quiet", "-sysid", "SEGA SATURN", "-volid", "AVP_SAT_RT", "-generic-boot", str(ip), "-full-iso9660-filenames",
                        "-abstract", "ABS.TXT", "-copyright", "CPY.TXT", "-biblio", "BIB.TXT", "-o", str(iso), "."],
                       cwd=ISO, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-2000:])
    (WORK / "sat.cue").write_text(f'FILE "{iso}" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n')
    print("image", iso, iso.stat().st_size)


if __name__ == "__main__":
    main()
