"""Wolverine's wording for the story boxes (lane wv-talkbox, 2026-11-10; DRAFT for the owner's approval, see docs/notes/AVP_WOLVERINE_DIALOG_20261110.md).

Our own text, no ROM data. A story box line is 28 characters; a record holds two lines. LINES maps the ROM offset of each record the game
shows for Schaefer's slot (speaker code 0x100: every "sel=1" record, plus the soldier's line that names him) to (line 1, line 2).
Only the lines that change are listed; any other record is left as the arcade has it. tools/wolverine/dialog.py checks every record's
old bytes against a hash taken from the user's ROM, so a different ROM revision fails loudly instead of being patched blind.

Characters the font has: letters, space, ! ? ' , . - (and the arcade's own wide !! which only old lines use).
"""

# ROM offset of the record (the 0xffff that opens it) -> (line 1, line 2, each at most 28 characters)
LINES = {
    # first block: stage 02 opening, stage 06 lift, stage 0a/0c story, the soldiers' conversation
    0xbec02: ("They keep coming, bub.", "We gotta fall back!"),
    0xbed82: ("Why'd you help us, pal?", ""),
    0xbf002: ("Forget it!", "Get back, here they come!"),
    0xbf082: ("Fall back, keep fighting!", ""),
    0xbf302: ("Gah! It's stuck again!", ""),
    0xbf502: ("Hold on! I figured there'd", "be a backup up here."),
    0xbf982: ("Wait, they're alive!", ""),
    0xbfa02: ("Gah! All I can do is end", "their suffering."),
    0xbfc82: ("Yeah. But they're done for.", ""),
    0xbfd82: ("Their nest, if you ask me.", ""),
    0xc0402: ("Army pulled out already.", "Can't be theirs."),
    0xc0602: ("Nope. We're the only unit", "they sent here."),
    0xc0802: ("They tossed us aside!", ""),
    0xc0982: ("Those aren't soldiers.", "They're vermin."),
    0xc0b82: ("Only a few left.", "This city's done for."),
    0xc0d02: ("They won't buy that.", "I barely buy it myself!"),
    0xc0e82: ("They've lost it...", "We gotta stop 'em!"),
    0xc1082: ("They're not getting away.", ""),
    0xc1282: ("Then we fight together.", "I've lost friends too."),
    # second block: the per-character sets (stage 02, 04, 06, 08, 0a, 0c, 0e, 10, 12, 14, 16, 18, 1a, 1c, 24)
    0xcf842: ("They keep coming, bub.", "Is there no end to 'em?"),
    0xcf8c2: ("They keep coming, bub.", "Is there no end to 'em?"),
    0xcf942: ("They keep coming, bub.", "Is there no end to 'em?"),
    0xcfa42: ("More than we can handle", "right now!"),
    0xcfc42: ("Head for that building", "over there, now!"),
    0xcfe42: ("Lucky break. We lost 'em", "for now."),
    0xd0242: ("Figures. Just our luck!", ""),
    0xd0442: ("Somethin's off...", "Check the ceiling."),
    0xd0c42: ("Leave it to me, bub.", "I've handled worse."),
    0xd0e42: ("See? Told ya I could", "handle it."),
    0xd1042: ("Wolverine? Clear out!", "It's coming!"),      # the soldier's line names Schaefer
    0xd1442: ("Kevin's unit.", "I'll make 'em pay, Kevin!"),
    0xd1642: ("More of 'em every second.", "Let's get to that nest!"),
    0xd1842: ("Nothing to overheat here.", "Cut loose!"),
    0xd1a42: ("So this is it. Time to", "get to work!"),
    0xd1e42: ("We'll check it out later.", "Let's cut 'em down now!"),
    0xd21c2: ("We did it!", "Can't believe we made it!"),
    0xd2242: ("We did it!", "Can't believe we made it!"),
    0xd22c2: ("We did it!", "Can't believe we made it!"),
    0xd2342: ("We did it!", "Can't believe we made it!"),
    0xd3642: ("The army's turning the", "aliens into weapons!"),
    0xd3842: ("So they're behind this!", ""),
    0xd4042: ("People are dead because", "of them! Don't you care?!"),
    0xd4842: ("Let's do this!", ""),
    0xd4c42: ("We got a problem here!", ""),
    0xd5c42: ("Let's end this thing now!", ""),
    0xd7442: ("Time to pop the claws!", ""),
    0xd77c2: ("Move it, bub! Get to the", "escape pod!"),
    0xd7842: ("Move it, bub! Get to the", "escape pod!"),
    0xd78c2: ("Move it, bub! Get to the", "escape pod!"),
    0xd7942: ("Move it, bub! Get to the", "escape pod!"),
}

# Stage-clear banner ("CONGRATULATIONS! <name> HAS DESTROYED STAGE n BOSS"): the 20-byte and the centred name fields of Schaefer.
# (ROM offset, field length, new text, "left" or "centre"): the field is padded with spaces as the arcade pads it. The first is one of four
# 20-byte fields of a name table (left aligned, as the arcade's names are); the second is a single name printed at a fixed position.
NAMES = (
    (0x11a75f, 20, "WOLVERINE", "left"),
    (0x11a7d3, 16, "WOLVERINE", "centre"),
)
