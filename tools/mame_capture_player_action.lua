-- Capture one isolated Predator Warrior action after traversing the verified
-- cold boot, credit, Start, character-select, and Round 1 path. The action is
-- selected by AVSP_ACTION_PROBE in the invoking process. These captures are
-- offline reference evidence and are never shipped on the Saturn disc.
local machine = manager.machine
local screen = machine.screens[":screen"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local left = in0["P1 Left"]
local right = in0["P1 Right"]
local up = in0["P1 Up"]
local down = in0["P1 Down"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]
local action = os.getenv("AVSP_ACTION_PROBE") or ""
local isolate_qsound_voices = {}
local isolate_qsound_voice_text = os.getenv("AVSP_QSOUND_ISOLATE_VOICES") or
    os.getenv("AVSP_QSOUND_ISOLATE_VOICE") or ""
for token in string.gmatch(isolate_qsound_voice_text, "[^,]+") do
    local voice = assert(tonumber(token),
        "AVSP_QSOUND_ISOLATE_VOICES must contain integers")
    assert(voice >= 0 and voice < 16,
        "AVSP_QSOUND_ISOLATE_VOICES entries must be 0..15")
    isolate_qsound_voices[voice] = true
end
local isolate_qsound_end_frame = tonumber(
    os.getenv("AVSP_QSOUND_ISOLATE_END_FRAME") or "")
local allowed_actions = {
    idle = true,
    walk = true,
    gun = true,
    melee = true,
    jump = true,
    dash = true,
    special = true,
    damage = true,
}
assert(allowed_actions[action], "invalid AVSP_ACTION_PROBE: " .. action)

local capture_root = ".deps/mame/player_actions/" .. action
local metadata = assert(io.open(capture_root .. "/samples.tsv", "w"))
metadata:write("frame\taction\tactive_object_bank\tbank_writes\tplayer_health\n")
local hud_state = assert(io.open(capture_root .. "/hud_state.tsv", "w"))
hud_state:write("frame\tplayer_health\n")
local qsound_writes = assert(io.open(capture_root .. "/qsound_writes.tsv", "w"))
qsound_writes:write("frame\tpc\tport\tbyte\tregister\tvalue\n")
local frame = 0
local active_object_bank = 0
local object_bank_writes = 0
local action_frame = 2525
local capture_first = 2480
local capture_last = action == "damage" and 3400 or 2608

local main_program = machine.devices[":maincpu"].spaces["program"]
local audio_cpu = machine.devices[":audiocpu"]
local audio_program = audio_cpu.spaces["program"]
local qsound_data_latch = 0
local qsound_isolation_active = false
player_action_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "player_action_object_bank",
    function(offset, data, mask)
        active_object_bank = data & 1
        object_bank_writes = object_bank_writes + 1
    end)

-- CPS2's Z80 writes the QSound word high byte, low byte, then register address
-- at 0xd000..0xd002. Recording that bus transaction exposes the exact voice
-- start/end/rate/volume changes without attempting to separate a mixed WAV.
player_action_qsound_tap = audio_program:install_write_tap(
    0xd000, 0xd002, "player_action_qsound_bus",
    function(offset, data, mask)
        local port = offset & 0xffff
        local byte = data & 0xff
        local pc = audio_cpu.state["PC"].value
        if port == 0xd000 then
            qsound_data_latch = ((byte << 8) | (qsound_data_latch & 0xff)) & 0xffff
            qsound_writes:write(string.format(
                "%d\t%04x\t%04x\t%02x\t\t\n", frame, pc, port, byte))
        elseif port == 0xd001 then
            qsound_data_latch = ((qsound_data_latch & 0xff00) | byte) & 0xffff
            qsound_writes:write(string.format(
                "%d\t%04x\t%04x\t%02x\t\t\n", frame, pc, port, byte))
        elseif port == 0xd002 then
            qsound_writes:write(string.format(
                "%d\t%04x\t%04x\t%02x\t%02x\t%04x\n",
                frame, pc, port, byte, byte, qsound_data_latch))
            if qsound_isolation_active then
                local pcm_volume_voice = nil
                if byte <= 0x7f and (byte & 7) == 6 then
                    pcm_volume_voice = byte >> 3
                end
                local is_other_pcm_volume = pcm_volume_voice ~= nil and
                    not isolate_qsound_voices[pcm_volume_voice]
                local is_late_target_volume = pcm_volume_voice ~= nil and
                    isolate_qsound_voices[pcm_volume_voice] and
                    isolate_qsound_end_frame ~= nil and
                    frame >= isolate_qsound_end_frame and qsound_data_latch ~= 0
                local is_adpcm_volume = byte == 0xcd or byte == 0xd1 or
                    byte == 0xd5
                if is_other_pcm_volume or is_late_target_volume or
                    is_adpcm_volume then
                    -- 0x07 is an intentionally unused PCM-register slot.
                    -- Redirecting only the final address byte preserves the
                    -- driver's data latch while preventing the volume write.
                    return 0x07
                end
            end
        end
    end)

local function qsound_write(register, value)
    audio_program:write_u8(0xd001, value & 0xff)
    audio_program:write_u8(0xd000, (value >> 8) & 0xff)
    audio_program:write_u8(0xd002, register & 0xff)
end

local function begin_qsound_voice_isolation()
    if next(isolate_qsound_voices) == nil then return end
    -- Silence every voice before filtering subsequent driver volume writes.
    -- Global QSound pan, echo and filter programming remains untouched.
    for voice = 0, 15 do
        qsound_write((voice << 3) + 6, 0)
    end
    for voice = 0, 2 do
        qsound_write(0xcd + (voice << 2), 0)
    end
    qsound_isolation_active = true
    print(string.format("AVSPU_QSOUND_ISOLATE voices=%s frame=%d",
        isolate_qsound_voice_text, frame))
end

local function write_share_words(path, share)
    local file = assert(io.open(path, "w"))
    file:write("word\tvalue\n")
    for offset = 0, share.size - 2, 2 do
        file:write(string.format("%04x\t%04x\n", offset / 2,
            share:read_u16(offset)))
    end
    file:close()
end

local function write_palette(path)
    local palette = machine.palettes[":palette"]
    local file = assert(io.open(path, "w"))
    file:write("index\targb\n")
    for index = 0, palette.entries - 1 do
        file:write(string.format("%04x\t%08x\n", index,
            palette:pen_color(index)))
    end
    file:close()
end

local function clear_gameplay_inputs()
    left:clear_value()
    right:clear_value()
    up:clear_value()
    down:clear_value()
    gun:clear_value()
    attack:clear_value()
    jump:clear_value()
end

local function dump_sample(sample_frame)
    local active_share = active_object_bank == 0 and
        machine.memory.shares[":objram1"] or machine.memory.shares[":objram2"]
    write_share_words(string.format(capture_root ..
        "/objram_active_%05d.tsv", sample_frame), active_share)
    write_palette(string.format(capture_root ..
        "/palette_%05d.tsv", sample_frame))
    screen:snapshot(string.format("player_actions/%s/%s_%05d.png",
        action, action, sample_frame))
    metadata:write(string.format("%d\t%s\t%d\t%d\t%d\n", sample_frame,
        action, active_object_bank + 1, object_bank_writes,
        main_program:read_u16(0xff83c0)))
    metadata:flush()
end

player_action_capture_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1

    -- Match the verified opening traversal, but stop action-button pulses as
    -- soon as the default Predator Warrior has been selected.
    if frame >= 1200 and frame <= 2400 then
        if (frame - 1200) % 180 == 0 then coin:set_value(1) end
        if (frame - 1200) % 180 == 3 then coin:clear_value() end
        if (frame - 1200) % 180 == 30 then start:set_value(1) end
        if (frame - 1200) % 180 == 33 then start:clear_value() end
    end
    if frame >= 1500 and frame <= 1895 then
        if frame % 90 == 0 then gun:set_value(1) end
        if frame % 90 == 5 then gun:clear_value() end
    end

    if frame == action_frame then
        if action == "walk" then right:set_value(1) end
        if action == "gun" then gun:set_value(1) end
        if action == "melee" then attack:set_value(1) end
        if action == "jump" then jump:set_value(1) end
        if action == "dash" then
            right:set_value(1)
            jump:set_value(1)
        end
        if action == "special" then
            gun:set_value(1)
            attack:set_value(1)
        end
        print(string.format("AVSPU_PLAYER_ACTION action=%s frame=%d",
            action, frame))
    end
    if frame == action_frame - 1 then
        begin_qsound_voice_isolation()
    end
    if frame == action_frame + 5 then
        gun:clear_value()
        attack:clear_value()
        jump:clear_value()
    end
    local direction_release_frame = action == "walk" and
        action_frame + 64 or action_frame + 20
    if frame == direction_release_frame then
        left:clear_value()
        right:clear_value()
        up:clear_value()
        down:clear_value()
    end

    if frame >= capture_first and frame <= capture_last then
        dump_sample(frame)
    end
    if frame >= 1800 and frame <= capture_last then
        hud_state:write(string.format("%d\t%d\n", frame,
            main_program:read_u16(0xff83c0)))
    end

    if frame == capture_last + 1 then
        clear_gameplay_inputs()
        coin:clear_value()
        start:clear_value()
        metadata:close()
        hud_state:close()
        qsound_writes:close()
        machine:exit()
    end
end)
