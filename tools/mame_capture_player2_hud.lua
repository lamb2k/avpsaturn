-- Capture the active Player 2 HUD and a P1-only PRESS START control from the
-- pinned avspu oracle. Set AVSP_P2_HUD_RUN to the pre-created private output
-- directory name and AVSP_P2_HUD_MODE to active or prompt_control.
local machine = manager.machine
local screen = machine.screens[":screen"]
local program = machine.devices[":maincpu"].spaces["program"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields

local coin1 = in2["Coin 1"]
local coin2 = in2["Coin 2"]
local start1 = in2["1 Player Start"]
local start2 = in2["2 Players Start"]
local p1_gun = in0["P1 Button 1"]
local p2_gun = in0["P2 Button 1"]
local p1_right = in0["P1 Right"]
local p2_right = in0["P2 Right"]

local run = os.getenv("AVSP_P2_HUD_RUN") or ""
local mode = os.getenv("AVSP_P2_HUD_MODE") or ""
assert(run:match("^[A-Za-z0-9_-]+$"), "invalid AVSP_P2_HUD_RUN")
assert(mode == "active" or mode == "prompt_control",
    "AVSP_P2_HUD_MODE must be active or prompt_control")

local root = ".deps/mame/player2_hud/" .. run
local samples = assert(io.open(root .. "/samples.tsv", "w"))
samples:write("frame\tmode\tactive_object_bank\tbank_writes\tp1_health\n")
local frame = 0
local active_object_bank = 0
local object_bank_writes = 0

player2_hud_objbank_tap = program:install_write_tap(
    0x8040e0, 0x8040e1, "player2_hud_object_bank",
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
    local chunk = {}
    for address = 0xff8000, 0xff9fff do
        chunk[#chunk + 1] = string.char(program:read_u8(address))
        if #chunk == 1024 then
            file:write(table.concat(chunk))
            chunk = {}
        end
    end
    if #chunk > 0 then file:write(table.concat(chunk)) end
    file:close()
end

local function pulse(field, start_frame)
    if frame == start_frame then field:set_value(1) end
    if frame == start_frame + 3 then field:clear_value() end
end

local function clear_inputs()
    coin1:clear_value()
    coin2:clear_value()
    start1:clear_value()
    start2:clear_value()
    p1_gun:clear_value()
    p2_gun:clear_value()
    p1_right:clear_value()
    p2_right:clear_value()
end

player2_hud_capture_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1

    -- Repeat short pulses across the legal/attract boundary, matching the
    -- established deterministic P1 route. The active route mirrors every
    -- credit, Start and character-confirm pulse through the P2 fields.
    for pulse_frame = 1200, 2280, 180 do
        pulse(coin1, pulse_frame)
        pulse(start1, pulse_frame + 30)
        if mode == "active" then
            pulse(coin2, pulse_frame)
            pulse(start2, pulse_frame + 30)
        end
    end
    for pulse_frame = 1500, 2220, 90 do
        pulse(p1_gun, pulse_frame)
        if mode == "active" then pulse(p2_gun, pulse_frame) end
    end

    if frame == 2520 then
        p1_right:set_value(1)
        if mode == "active" then p2_right:set_value(1) end
    end
    if frame == 3240 then
        p1_right:clear_value()
        p2_right:clear_value()
    end

    if frame >= 1800 and frame <= 3300 and frame % 20 == 0 then
        screen:snapshot(string.format("frame_%04d.png", frame))
        local active_share = active_object_bank == 0 and
            machine.memory.shares[":objram1"] or
            machine.memory.shares[":objram2"]
        write_share_words(string.format(root .. "/objram_%04d.tsv", frame),
            active_share)
        samples:write(string.format("%d\t%s\t%d\t%d\t%d\n", frame, mode,
            active_object_bank + 1, object_bank_writes,
            program:read_u8(0xff83c1)))
        samples:flush()
    end
    if frame >= 1800 and frame <= 3300 and frame % 120 == 0 then
        write_palette(string.format(root .. "/palette_%04d.tsv", frame))
        write_workram(string.format(root .. "/workram_%04d.bin", frame))
    end
    if frame == 3000 then
        write_share_words(root .. "/gfxram_3000.tsv",
            machine.memory.shares[":gfxram"])
        write_share_words(root .. "/cps_a_regs_3000.tsv",
            machine.memory.shares[":cps_a_regs"])
        write_share_words(root .. "/cps_b_regs_3000.tsv",
            machine.memory.shares[":cps_b_regs"])
    end

    if frame == 3320 then
        clear_inputs()
        samples:close()
        print(string.format("AVSPU_PLAYER2_HUD mode=%s frame=%d bank_writes=%d",
            mode, frame, object_bank_writes))
        machine:exit()
    end
end)
