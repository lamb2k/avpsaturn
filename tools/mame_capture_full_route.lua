-- RP2: full-route cadence-1 source capture (cold boot -> held Round 2 title).
--
-- Deterministic composite input schedule:
--   frames 0-4200: verbatim mame_capture_stage1.lua opening schedule
--     (coin/start pulses 1200-2400, gun pulses from 1500, walk right from
--     2600 with gun/attack/jump pulses);
--   frames 4201+: verbatim mame_capture_stage1_full.lua continuation
--     schedule re-based to relative = frame - 4200 (forward bias, offensive
--     pulses, coin/start continue pulses every 600 relative frames).
--
-- Both source schedules are pure functions of the frame counter, so the
-- composite run is deterministic given the same NVRAM baseline; the runner
-- (capture_full_route.ps1) restores the recorded NVRAM before every run.
--
-- Per-frame capture, cadence 1, delta-encoded:
--   RAM regions are read as binary strings from the 68000 program space and
--   the write-only register/object regions from their named MAME shares; a
--   region is appended to its blob stream only on change, with an index
--   line (frame, region, offset, length). Unchanged frames are implicit
--   repeats. Screenshots are written every frame. All raw output lands in
--   .deps/mame/full_route (git-ignored, private); the tracked census is
--   produced offline by tools/census_full_route.py and carries hashes,
--   counts, and ranges only.
--
-- Regions (68000 addresses, MAME cps2.cpp map):
--   gfxram  0x900000 len 0x30000  tilemaps + palette + row-scroll tables
--   cps_a / cps_b / objram1 / objram2 / output: named shares (write-only
--   through the read map), serialized big-endian in address order
--   workram 0xff0000 len 0x10000
--   qsound  0x618000 len 0x2000   QSound shared RAM (audio command state)

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

local capture_root = ".deps/mame/full_route"
local final_frame = 18000
local frame = 0

local active_object_bank = 0
local object_bank_writes = 0
local main_program = machine.devices[":maincpu"].spaces["program"]
full_route_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "full_route_object_bank",
    function(offset, data, mask)
        active_object_bank = data & 1
        object_bank_writes = object_bank_writes + 1
    end)

-- gfxram is split into 64 KiB thirds: read_range is capped and the split
-- also localizes deltas (scroll1+2 / scroll3+star / palette+row tables).
-- The CPS register blocks and both object banks are WRITE-ONLY through the
-- 68000 read map (program-space reads return zero), so those regions are
-- read from their named MAME shares instead, exactly as the proven
-- mame_capture_frontend_rom.lua does.
local shares = machine.memory.shares
local function share_reader(share)
    return function()
        local words = {}
        local size = share.size
        local aligned = size - size % 4
        for offset = 0, aligned - 4, 4 do
            words[#words + 1] = string.pack(">I4", share:read_u32(offset))
        end
        for offset = aligned, size - 1 do
            words[#words + 1] = string.char(share:read_u8(offset))
        end
        return table.concat(words)
    end
end
local function range_reader(base, last)
    return function() return main_program:read_range(base, last, 8) end
end
local regions = {
    {name = "gfxram0", read = range_reader(0x900000, 0x90ffff)},
    {name = "gfxram1", read = range_reader(0x910000, 0x91ffff)},
    {name = "gfxram2", read = range_reader(0x920000, 0x92ffff)},
    {name = "cps_a",   read = share_reader(shares[":cps_a_regs"])},
    {name = "cps_b",   read = share_reader(shares[":cps_b_regs"])},
    {name = "objram1", read = share_reader(shares[":objram1"])},
    {name = "objram2", read = share_reader(shares[":objram2"])},
    {name = "output",  read = share_reader(shares[":output"])},
    {name = "workram", read = range_reader(0xff0000, 0xffffff)},
    {name = "qsound",  read = range_reader(0x618000, 0x619fff)},
}
for _, region in ipairs(regions) do
    region.blob = assert(io.open(
        capture_root .. "/region_" .. region.name .. ".bin", "wb"))
    region.offset = 0
    region.previous = nil
end

local index = assert(io.open(capture_root .. "/region_index.tsv", "w"))
index:write("frame\tregion\toffset\tlength\n")
local samples = assert(io.open(capture_root .. "/samples.tsv", "w"))
samples:write("frame\tinput_word\tactive_object_bank\tbank_writes\n")

-- Deterministic input schedule as a pure function of the frame counter.
-- Returns the applied input word for the samples log:
--   bit0 coin, bit1 start, bit2 right, bit3 gun, bit4 attack, bit5 jump.
local function apply_schedule(f)
    local word = 0
    local function drive(field, on, bit)
        if on then field:set_value(1); word = word + bit
        else field:clear_value() end
    end
    if f <= 4200 then
        -- mame_capture_stage1.lua opening schedule, verbatim windows.
        local coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
        local start_on = f >= 1200 and f <= 2400 and
            (f - 1200) % 180 >= 30 and (f - 1200) % 180 < 33
        local gun_on = (f >= 1500 and f < 4200 and f % 90 < 5) or
            (f >= 2600 and f < 4200 and f % 75 < 6)
        local right_on = f >= 2600 and f < 4200
        local attack_on = f >= 2600 and f < 4200 and f % 310 < 7
        local jump_on = f >= 2600 and f < 4200 and f % 430 < 7
        drive(coin, coin_on, 1)
        drive(start, start_on, 2)
        drive(right, right_on, 4)
        drive(gun, gun_on, 8)
        drive(attack, attack_on, 16)
        drive(jump, jump_on, 32)
    else
        -- mame_capture_stage1_full.lua continuation, relative = f - 4200.
        local r = f - 4200
        drive(coin, r % 600 >= 30 and r % 600 < 34, 1)
        drive(start, r % 600 >= 90 and r % 600 < 94, 2)
        drive(right, true, 4)
        drive(gun, r % 45 < 7, 8)
        drive(attack, r % 180 < 8, 16)
        drive(jump, r % 240 < 8, 32)
    end
    return word
end

local function capture_frame(f)
    for _, region in ipairs(regions) do
        local bytes = region.read()
        if bytes ~= region.previous then
            region.blob:write(bytes)
            index:write(string.format("%d\t%s\t%d\t%d\n",
                f, region.name, region.offset, #bytes))
            region.offset = region.offset + #bytes
            region.previous = bytes
        end
    end
    screen:snapshot(string.format("full_route/reference_%05d.png", f))
end

full_route_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local input_word = apply_schedule(frame)
    capture_frame(frame)
    samples:write(string.format("%d\t%d\t%d\t%d\n",
        frame, input_word, active_object_bank, object_bank_writes))

    if frame % 600 == 0 then
        print(string.format("AVSPU_FULL_ROUTE frame=%d", frame))
    end
    if frame >= final_frame then
        coin:clear_value(); start:clear_value(); left:clear_value()
        right:clear_value(); gun:clear_value(); attack:clear_value()
        jump:clear_value()
        for _, region in ipairs(regions) do region.blob:close() end
        index:close()
        samples:close()
        machine:exit()
    end
end)
