-- Replay the verified Stage 1 route to frame 5520, then capture a neutral,
-- dense boss-room window while the first Stalker actor is still alive.
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

local capture_root = ".deps/mame/stalker_actions"
local metadata = assert(io.open(capture_root .. "/samples.tsv", "w"))
metadata:write("frame\tactive_object_bank\tbank_writes\tplayer_health\n")
local frame = 0
local base_frame = 4200
local capture_first = 5520
local capture_last = 7800
local active_object_bank = 1 -- verified active bank at the frame-4200 save
local object_bank_writes = 0
local state_loaded = false
local main_program = machine.devices[":maincpu"].spaces["program"]

stalker_action_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "stalker_action_object_bank",
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
    coin:clear_value()
    start:clear_value()
end

local function dump_sample(sample_frame, player_health)
    local active_share = active_object_bank == 0 and
        machine.memory.shares[":objram1"] or machine.memory.shares[":objram2"]
    write_share_words(string.format(capture_root ..
        "/objram_active_%05d.tsv", sample_frame), active_share)
    write_share_words(string.format(capture_root ..
        "/cps_a_regs_%05d.tsv", sample_frame),
        machine.memory.shares[":cps_a_regs"])
    write_share_words(string.format(capture_root ..
        "/cps_b_regs_%05d.tsv", sample_frame),
        machine.memory.shares[":cps_b_regs"])
    write_palette(string.format(capture_root ..
        "/palette_%05d.tsv", sample_frame))
    write_workram(string.format(capture_root ..
        "/workram_%05d.bin", sample_frame))
    if sample_frame % 10 == 0 then
        screen:snapshot(string.format("stalker_%05d.png", sample_frame))
    end
    metadata:write(string.format("%d\t%d\t%d\t%d\n", sample_frame,
        active_object_bank + 1, object_bank_writes, player_health))
    metadata:flush()
end

stalker_action_post_load_subscription = emu.add_machine_post_load_notifier(function()
    frame = 0
    active_object_bank = 1
    object_bank_writes = 0
    state_loaded = true
    clear_inputs()
end)

stalker_action_capture_subscription = emu.add_machine_frame_notifier(function()
    if not state_loaded then return end
    frame = frame + 1
    local absolute_frame = base_frame + frame

    -- Reproduce the established continuation route exactly until the frame
    -- whose source screenshot proves a live Stalker in the Chrysalis room.
    if absolute_frame < capture_first then
        if frame == 1 then right:set_value(1) end
        if frame % 45 == 0 then gun:set_value(1) end
        if frame % 45 == 7 then gun:clear_value() end
        if frame % 180 == 0 then attack:set_value(1) end
        if frame % 180 == 8 then attack:clear_value() end
        if frame % 240 == 0 then jump:set_value(1) end
        if frame % 240 == 8 then jump:clear_value() end
        if frame % 600 == 30 then coin:set_value(1) end
        if frame % 600 == 34 then coin:clear_value() end
        if frame % 600 == 90 then start:set_value(1) end
        if frame % 600 == 94 then start:clear_value() end
        return
    end

    clear_inputs()
    -- After the long neutral window has exposed locomotion and natural
    -- attacks, resume controlled offence to capture this same pair's native
    -- hit and KO states. Keep weapon and melee pulses disjoint so the probe
    -- never requests the emergency-attack chord.
    if absolute_frame > 7000 then
        right:set_value(1)
        down:set_value(1)
        local damage_phase = absolute_frame - 7001
        if damage_phase % 45 < 7 then gun:set_value(1) end
        if damage_phase % 60 >= 22 and damage_phase % 60 < 28 then
            attack:set_value(1)
        end
    end
    local player_health = main_program:read_u8(0xff83c1)
    dump_sample(absolute_frame, player_health)
    main_program:write_u8(0xff83c1, 0x65)
    if absolute_frame >= capture_last then
        clear_inputs()
        metadata:close()
        machine:exit()
    end
end)

machine:load("avspu_stage1")
