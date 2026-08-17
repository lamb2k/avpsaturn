-- Capture a dense, deterministic enemy-action window after reproducing the
-- verified Stage 1 route. The first portion is neutral so nearby aliens can
-- expose natural locomotion and attacks; repeated melee inputs then expose
-- authentic hit and KO reactions. These private reference captures never ship
-- on the Saturn disc.
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

local capture_root = ".deps/mame/enemy_actions"
local metadata = assert(io.open(capture_root .. "/samples.tsv", "w"))
metadata:write("frame\tactive_object_bank\tbank_writes\tprobe_phase\n")
local frame = 0
local active_object_bank = 0
local object_bank_writes = 0
local capture_first = 4080
local capture_last = 6200

local main_program = machine.devices[":maincpu"].spaces["program"]
enemy_action_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "enemy_action_object_bank",
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

local function clear_gameplay_inputs()
    left:clear_value()
    right:clear_value()
    up:clear_value()
    down:clear_value()
    gun:clear_value()
    attack:clear_value()
    jump:clear_value()
end

local function probe_phase()
    if frame < 4200 then return "route" end
    if frame < 4420 then return "natural" end
    return "melee"
end

local function dump_sample(sample_frame)
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
    screen:snapshot(string.format("enemy_actions/enemy_%05d.png", sample_frame))
    metadata:write(string.format("%d\t%d\t%d\t%s\n", sample_frame,
        active_object_bank + 1, object_bank_writes, probe_phase()))
    metadata:flush()
end

enemy_action_capture_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1

    -- Reproduce the verified cold traversal and gameplay route byte-for-byte
    -- through frame 4200 so the known independently visible alien track remains
    -- the temporal anchor for this probe.
    if frame >= 1200 and frame <= 2400 then
        if (frame - 1200) % 180 == 0 then coin:set_value(1) end
        if (frame - 1200) % 180 == 3 then coin:clear_value() end
        if (frame - 1200) % 180 == 30 then start:set_value(1) end
        if (frame - 1200) % 180 == 33 then start:clear_value() end
    end
    if frame >= 1500 and frame < 4200 then
        if frame % 90 == 0 then gun:set_value(1) end
        if frame % 90 == 5 then gun:clear_value() end
    end
    if frame == 2600 then right:set_value(1) end
    if frame >= 2600 and frame < 4200 then
        if frame % 75 == 0 then gun:set_value(1) end
        if frame % 75 == 6 then gun:clear_value() end
        if frame % 310 == 0 then attack:set_value(1) end
        if frame % 310 == 7 then attack:clear_value() end
        if frame % 430 == 0 then jump:set_value(1) end
        if frame % 430 == 7 then jump:clear_value() end
    end

    if frame == 4200 then clear_gameplay_inputs() end
    -- Turn toward the approaching group without manufacturing enemy state.
    if frame == 4201 then left:set_value(1) end
    if frame == 4210 then left:clear_value() end

    -- Leave 210 neutral frames for natural attacks, then expose repeated
    -- hit/KO reactions with deterministic, ordinary melee presses.
    if frame >= 4420 and frame <= 6160 then
        local phase = (frame - 4420) % 45
        if phase == 0 then attack:set_value(1) end
        if phase == 5 then attack:clear_value() end
    end

    -- Keep only P1 health full during this offline observation window. Enemy
    -- health, state, positions, hit reactions, and object output remain native;
    -- preventing a Continue transition lets the same encounter run long enough
    -- to distinguish recoverable knockdowns from confirmed enemy KOs.
    if frame >= 4200 then main_program:write_u8(0xff83c1, 0x65) end

    if frame >= capture_first and frame <= capture_last then dump_sample(frame) end
    if frame == capture_last + 1 then
        clear_gameplay_inputs()
        metadata:close()
        machine:exit()
    end
end)
