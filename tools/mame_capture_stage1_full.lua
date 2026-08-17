-- Continue from the verified frame-4200 save and map the rest of Stage 1.
-- This is an offline reference capture only; it is never included in the
-- Saturn executable or disc image.
local machine = manager.machine
local screen = machine.screens[":screen"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local left = in0["P1 Left"]
local right = in0["P1 Right"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]
local frame = 0
local base_frame = 4200
local final_frame = 18200
local active_object_bank = 1 -- verified active bank at the source save
local object_bank_writes = 0
local state_loaded = false
local capture_root = ".deps/mame/full_stage1_complete"
local metadata = assert(io.open(capture_root .. "/route_samples.tsv", "w"))
metadata:write("frame\tactive_object_bank\tbank_writes\n")

local main_program = machine.devices[":maincpu"].spaces["program"]
full_stage1_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "full_stage1_object_bank",
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

local function dump_route_sample(absolute_frame)
    local active_share = active_object_bank == 0 and
        machine.memory.shares[":objram1"] or machine.memory.shares[":objram2"]
    write_share_words(string.format(capture_root ..
        "/objram_active_%05d.tsv", absolute_frame), active_share)
    write_palette(string.format(capture_root ..
        "/palette_%05d.tsv", absolute_frame))
    metadata:write(string.format("%d\t%d\t%d\n", absolute_frame,
        active_object_bank + 1, object_bank_writes))
    metadata:flush()
end

full_stage1_post_load_subscription = emu.add_machine_post_load_notifier(function()
    frame = 0
    active_object_bank = 1
    object_bank_writes = 0
    state_loaded = true
    print("AVSPU_FULL_STAGE1 loaded verified frame-4200 state")
end)

full_stage1_capture_subscription = emu.add_machine_frame_notifier(function()
    if not state_loaded then return end
    frame = frame + 1
    local absolute_frame = base_frame + frame

    -- Bias toward forward progression while pulsing every offensive input.
    if frame == 1 then right:set_value(1) end
    if frame % 45 == 0 then gun:set_value(1) end
    if frame % 45 == 7 then gun:clear_value() end
    if frame % 180 == 0 then attack:set_value(1) end
    if frame % 180 == 8 then attack:clear_value() end
    if frame % 240 == 0 then jump:set_value(1) end
    if frame % 240 == 8 then jump:clear_value() end

    -- Keep credits available and accept a continue if the route loses a life.
    if frame % 600 == 30 then coin:set_value(1) end
    if frame % 600 == 34 then coin:clear_value() end
    if frame % 600 == 90 then start:set_value(1) end
    if frame % 600 == 94 then start:clear_value() end

    if absolute_frame % 60 == 0 then
        screen:snapshot(string.format("full_stage1_%05d.png", absolute_frame))
        dump_route_sample(absolute_frame)
        print(string.format("AVSPU_FULL_STAGE1 frame=%d", absolute_frame))
    end

    if absolute_frame >= final_frame then
        left:clear_value()
        right:clear_value()
        gun:clear_value()
        attack:clear_value()
        jump:clear_value()
        coin:clear_value()
        start:clear_value()
        metadata:close()
        machine:save("avspu_stage1_full_probe")
        machine:exit()
    end
end)

machine:load("avspu_stage1")
