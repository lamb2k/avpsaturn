-- Capture a dense, deterministic Chrysalis action window from the verified
-- frame-12660 boss-room state. The private source data never ships on Saturn.
local machine = manager.machine
local screen = machine.screens[":screen"]
local in0 = machine.ioport.ports[":IN0"].fields
local left = in0["P1 Left"]
local right = in0["P1 Right"]
local up = in0["P1 Up"]
local down = in0["P1 Down"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]

local capture_root = ".deps/mame/boss_actions"
local metadata = assert(io.open(capture_root .. "/samples.tsv", "w"))
metadata:write("frame\tactive_object_bank\tbank_writes\tprobe_phase\tplayer_health\n")
local frame = 0
local base_frame = 12660
local capture_last = 900
local active_object_bank = 1
local object_bank_writes = 0
local state_loaded = false

local main_program = machine.devices[":maincpu"].spaces["program"]
boss_action_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "boss_action_object_bank",
    function(offset, data, mask)
        active_object_bank = data & 1
        object_bank_writes = object_bank_writes + 1
    end)

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

local function write_workram(path)
    local file = assert(io.open(path, "wb"))
    file:write(main_program:read_range(0xff8000, 0xffffff, 8))
    file:close()
end

local function clear_inputs()
    left:clear_value()
    right:clear_value()
    up:clear_value()
    down:clear_value()
    gun:clear_value()
    attack:clear_value()
    jump:clear_value()
end

local function probe_phase()
    if frame <= 650 then return "natural" end
    if frame <= 780 then return "weapon" end
    return "melee"
end

local function dump_sample(sample_frame, player_health)
    local active_share = active_object_bank == 0 and
        machine.memory.shares[":objram1"] or machine.memory.shares[":objram2"]
    write_share_words(string.format(capture_root ..
        "/objram_active_%05d.tsv", sample_frame), active_share)
    write_palette(string.format(capture_root ..
        "/palette_%05d.tsv", sample_frame))
    write_share_words(string.format(capture_root ..
        "/cps_a_regs_%05d.tsv", sample_frame), machine.memory.shares[":cps_a_regs"])
    write_share_words(string.format(capture_root ..
        "/cps_b_regs_%05d.tsv", sample_frame), machine.memory.shares[":cps_b_regs"])
    write_workram(string.format(capture_root ..
        "/workram_%05d.bin", sample_frame))
    if sample_frame % 10 == 0 then
        screen:snapshot(string.format("boss_%05d.png", sample_frame))
    end
    metadata:write(string.format("%d\t%d\t%d\t%s\t%d\n", sample_frame,
        active_object_bank + 1, object_bank_writes, probe_phase(),
        player_health))
    metadata:flush()
end

boss_action_post_load_subscription = emu.add_machine_post_load_notifier(function()
    frame = 0
    active_object_bank = 1
    object_bank_writes = 0
    state_loaded = true
    clear_inputs()
end)

boss_action_capture_subscription = emu.add_machine_frame_notifier(function()
    if not state_loaded then return end
    frame = frame + 1

    -- Leave the first 650 frames neutral so the attack beginning at source
    -- frame 12992 can finish without an injected player hit truncating it.
    if frame > 650 and frame <= 780 then
        local phase = (frame - 651) % 45
        if phase == 0 then gun:set_value(1) end
        if phase == 6 then gun:clear_value() end
    end
    if frame > 780 then
        local phase = (frame - 781) % 45
        if phase == 0 then attack:set_value(1) end
        if phase == 6 then attack:clear_value() end
    end

    -- Record health after the emulated frame, then restore it for the next
    -- frame. This exposes exact Chrysalis contact timing without allowing a
    -- Continue transition to reset the observation window.
    local player_health = main_program:read_u8(0xff83c1)
    dump_sample(base_frame + frame, player_health)
    main_program:write_u8(0xff83c1, 0x65)
    if frame >= capture_last then
        clear_inputs()
        metadata:close()
        machine:exit()
    end
end)

machine:load("avspu_stage1_boss_12660")
