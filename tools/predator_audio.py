"""Keep the shared Predator attack sounds in every playable character bank."""

from wolverine.wv_audio import HDR, ROW, ROUND_SOUND_TABLE_ROOM, SCSP_PCM_ROOM, encode, free_guest_pcm, parse


# Warrior's re-entry attack, grab hit and grounded impacts, plus Hunter's ground combo.
WARRIOR_REENTRY = 0x0202
ATTACK_CUES = {1: (0x0106, 0x0046, 0x0111, WARRIOR_REENTRY), 4: (0x010C, 0x0041, 0x004A)}


def required_cues(round_file):
    if not 0x02 <= round_file["stages"][0] <= 0x24:
        return ()
    mask = round_file.get("mask", 0x0F)
    return tuple(cue for slot, cues in ATTACK_CUES.items() if mask & slot for cue in cues)


def donor_cues(pack, commands):
    rows, _, pcm = parse(pack)
    starts = sorted({row["off"] for row in rows} | {len(pcm)})
    ends = dict(zip(starts, starts[1:]))
    donor = {}
    for row in rows:
        if row["cmd"] in commands:
            start = row["off"]
            clip = pcm[start:min(start + row["n"], ends.get(start, len(pcm)))]
            if clip:
                donor[row["cmd"]] = (row, clip)
    return donor


def append_cues(pack, required, donor):
    """Add exact donor PCM within the separate SCSP and command-table limits."""
    rows, music, original_pcm = parse(pack)
    missing = set(required) - {row["cmd"] for row in rows}
    pcm = bytearray(original_pcm)
    added = []
    # Keep the existing impact cues ahead of re-entry when PCM space is tight.
    order = sorted(missing & donor.keys(), key=lambda cue: (cue == WARRIOR_REENTRY, -len(donor[cue][1]), cue))
    for command in order:
        model, clip = donor[command]
        offset = pcm.find(clip)
        while offset >= 0 and offset & 1:
            offset = pcm.find(clip, offset + 1)
        aligned_end = (len(pcm) + 1) & ~1
        end = aligned_end + ((len(clip) + 1) & ~1) if offset < 0 else len(pcm)
        tables = HDR.size + ROW.size * (len(rows) + len(added) + 1) + len(music)
        if end > SCSP_PCM_ROOM or tables > ROUND_SOUND_TABLE_ROOM:
            continue
        if offset < 0:
            offset = aligned_end
            pcm.extend(bytes(aligned_end - len(pcm)))
            pcm.extend(clip)
            pcm.extend(bytes(len(clip) & 1))
        added.append(dict(model, off=offset, n=len(clip)))
        missing.remove(command)
    if not added:
        return pack, missing

    if len(pcm) != len(original_pcm):
        for row in rows:
            # A legacy row that ran past the PCM area must not play new data.
            row["n"] = min(row["n"], max(0, len(original_pcm) - row["off"]))
    rows.extend(added)
    return encode(rows, music, pcm), missing


def prepare(files, audio_paths, output, guest_rates=False):
    # The opening Hunter bank supplies the checked original lengths for both
    # Hunter aliases. Other stock banks supply cues in older input packs.
    pending = {cue for file in files for cue in required_cues(file)}
    donor = {}
    stock = [(file, path) for file, path in zip(files, audio_paths)
             if not file.get("duel") and "guest" not in file]
    for file, path in sorted(stock, key=lambda pair: pair[0]["name"] != "stage02_m4"):
        if not pending:
            break
        available = donor_cues(path.read_bytes(), pending)
        donor.update(available)
        pending.difference_update(available)

    modified = list(audio_paths)
    unfit = {}
    for index, (file, path) in enumerate(zip(files, audio_paths)):
        required = required_cues(file)
        if not required:
            continue
        original = path.read_bytes()
        patched, missing = append_cues(original, required, donor)
        if guest_rates and file.get("guest") == 0 and WARRIOR_REENTRY in missing and WARRIOR_REENTRY in donor:
            _, _, _, size = HDR.unpack_from(patched)
            length = len(donor[WARRIOR_REENTRY][1])
            shortfall = ((size + 1) & ~1) + ((length + 1) & ~1) - SCSP_PCM_ROOM
            if shortfall > 0:
                compacted = free_guest_pcm(patched, shortfall)
                if compacted is not None:
                    restored, remaining = append_cues(compacted, required, donor)
                    if WARRIOR_REENTRY not in remaining:
                        patched, missing = restored, remaining
        if missing:
            unfit[file["name"]] = sorted(missing)
        if patched != original:
            output.mkdir(parents=True, exist_ok=True)
            modified[index] = output / f"r{index:03d}.bin"
            modified[index].write_bytes(patched)
    return modified, unfit
