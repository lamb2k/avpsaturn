-- Capture the exact CPS2 video state in the Stage 1 Chrysalis room.
local machine = manager.machine
local screen = machine.screens[":screen"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local right = in0["P1 Right"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]
local frame = 0
local base_frame = 4200
local target_frame = 12660
local state_loaded = false
local active_object_bank = 1

local main_program = machine.devices[":maincpu"].spaces["program"]
stage1_boss_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "stage1_boss_object_bank",
    function(offset, data, mask) active_object_bank = data & 1 end)

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

local function dump_boss_state()
    local root = ".deps/mame/captures/"
    write_share_words(root .. "boss_objram1.tsv", machine.memory.shares[":objram1"])
    write_share_words(root .. "boss_objram2.tsv", machine.memory.shares[":objram2"])
    write_share_words(root .. "boss_gfxram.tsv", machine.memory.shares[":gfxram"])
    write_share_words(root .. "boss_cps_a_regs.tsv", machine.memory.shares[":cps_a_regs"])
    write_share_words(root .. "boss_cps_b_regs.tsv", machine.memory.shares[":cps_b_regs"])
    write_palette(root .. "boss_palette.tsv")
    local bank_file = assert(io.open(root .. "boss_active_object_bank.txt", "w"))
    bank_file:write(string.format("%d\n", active_object_bank + 1))
    bank_file:close()
    screen:snapshot(root .. "boss_stage1_12660.png")
    machine:save("avspu_stage1_boss_12660")
end

stage1_boss_post_load_subscription = emu.add_machine_post_load_notifier(function()
    frame = 0
    active_object_bank = 1
    state_loaded = true
end)

stage1_boss_capture_subscription = emu.add_machine_frame_notifier(function()
    if not state_loaded then return end
    frame = frame + 1
    local absolute_frame = base_frame + frame
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
    if absolute_frame >= target_frame then
        right:clear_value()
        gun:clear_value()
        attack:clear_value()
        jump:clear_value()
        dump_boss_state()
        machine:exit()
    end
end)

machine:load("avspu_stage1")
