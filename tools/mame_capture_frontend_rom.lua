-- ROM-truth capture of the frontend (title / character select / confirm).
--
-- The existing frontend capture (mame_capture_frontend.lua) saves SCREEN
-- PIXELS, which is why the shipped title and select screens are flat
-- keyframes. This capture instead saves the state the ROM composes those
-- screens FROM - the same share set mame_capture_stage1.lua dumps for the
-- stage background, which tools/extract_avspu_stage1.py already knows how to
-- decode with exact MAME semantics:
--
--   gfxram      the three live CPS tilemaps (scroll1/2/3) -> render_background
--   cps_a_regs  tilemap base addresses, scroll offsets, row-scroll control
--   cps_b_regs  layer enable/priority
--   objram1/2   the sprite/object list  -> decode_objects
--   output      the bank-select / control block
--   palette     the live 4096-entry palette
--
-- Purpose: determine what the select screen is actually MADE OF (scroll
-- layers vs objects vs both) and give the native port the real tile codes,
-- so the screen can be rebuilt from original assets rather than replayed as
-- a picture. Nothing here decides that answer in advance.
--
-- The input schedule is copied verbatim from mame_capture_frontend.lua so
-- the frame numbering matches data/frontend_segments.json (start_transition
-- 1770-1798, character_confirm 1800-2038, round_1_title 2040-2160); the
-- select screen itself precedes 1770.
--
-- gfxram and the palette are large, so the FULL set is written only at the
-- listed key frames. objram is small and is written densely so cursor motion
-- (an object, if the cursor is one) is observable frame to frame.

local machine = manager.machine
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local gun = in0["P1 Button 1"]
local capture_root = ".deps/mame/frontend_rom"

local frame = 0
local dense_first = 1600
local dense_last = 1820
local dense_cadence = 2

-- Full ROM-truth snapshots: two well inside the select screen, one at the
-- start transition, one mid-confirm, one on the round title.
local key_frames = {1620, 1700, 1760, 1790, 1900, 2100}

local active_object_bank = 0
local main_program = machine.devices[":maincpu"].spaces["program"]
frontend_rom_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "frontend_rom_object_bank",
    function(offset, data, mask)
        active_object_bank = data & 1
    end)

local metadata = assert(io.open(capture_root .. "/samples.tsv", "w"))
metadata:write("frame\tkind\tactive_object_bank\n")

local function write_share_words(path, share)
    if not share then return end
    local file = assert(io.open(path, "w"))
    file:write("word\tvalue\n")
    for offset = 0, share.size - 2, 2 do
        file:write(string.format("%04x\t%04x\n", offset / 2, share:read_u16(offset)))
    end
    file:close()
end

local function write_palette(path)
    local palette = machine.palettes[":palette"]
    local file = assert(io.open(path, "w"))
    file:write("index\targb\n")
    for index = 0, palette.entries - 1 do
        file:write(string.format("%04x\t%08x\n", index, palette:pen_color(index)))
    end
    file:close()
end

local function write_active_objram(sample_frame)
    local shares = machine.memory.shares
    local active = (active_object_bank == 1 and shares[":objram2"])
        or shares[":objram1"] or shares[":objram2"]
    write_share_words(string.format(
        capture_root .. "/objram_active_%04d.tsv", sample_frame), active)
end

local function write_full_set(sample_frame)
    local shares = machine.memory.shares
    write_share_words(string.format(
        capture_root .. "/gfxram_%04d.tsv", sample_frame), shares[":gfxram"])
    write_share_words(string.format(
        capture_root .. "/cps_a_regs_%04d.tsv", sample_frame), shares[":cps_a_regs"])
    write_share_words(string.format(
        capture_root .. "/cps_b_regs_%04d.tsv", sample_frame), shares[":cps_b_regs"])
    write_share_words(string.format(
        capture_root .. "/objram1_%04d.tsv", sample_frame), shares[":objram1"])
    write_share_words(string.format(
        capture_root .. "/objram2_%04d.tsv", sample_frame), shares[":objram2"])
    write_share_words(string.format(
        capture_root .. "/output_%04d.tsv", sample_frame), shares[":output"])
    write_palette(string.format(
        capture_root .. "/palette_%04d.tsv", sample_frame))
    machine.screens[":screen"]:snapshot(string.format(
        "frontend_rom/reference_%04d.png", sample_frame))
end

local function is_key_frame(f)
    for _, k in ipairs(key_frames) do
        if k == f then return true end
    end
    return false
end

frontend_rom_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1

    -- Verbatim from mame_capture_frontend.lua so frame numbers line up with
    -- the existing segmentation report.
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

    if frame >= dense_first and frame <= dense_last and
        (frame - dense_first) % dense_cadence == 0 then
        write_active_objram(frame)
        metadata:write(string.format("%d\tobjram\t%d\n", frame, active_object_bank))
    end

    if is_key_frame(frame) then
        write_full_set(frame)
        metadata:write(string.format("%d\tfull\t%d\n", frame, active_object_bank))
    end

    if frame == 2162 then
        coin:clear_value()
        start:clear_value()
        gun:clear_value()
        metadata:close()
        machine:exit()
    end
end)
