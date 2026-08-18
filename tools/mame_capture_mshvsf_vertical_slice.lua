-- Deterministic MSHvSF CPS-2 evidence capture for the first Ryu vertical slice:
-- idle -> walk -> jump -> light punch -> Hadouken -> collision/reaction.
local machine = manager.machine
local screen = machine.screens[":screen"]
local maincpu = machine.devices[":maincpu"]
local main_program = maincpu.spaces["program"]
local audiocpu = machine.devices[":audiocpu"]
local audio_program = audiocpu.spaces["program"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields

local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local start2 = in2["2 Players Start"]
local left = in0["P1 Left"]
local right = in0["P1 Right"]
local up = in0["P1 Up"]
local down = in0["P1 Down"]
local light_punch = in0["P1 Button 1"]
local p2_light_punch = in0["P2 Button 1"]

local capture_root = ".deps/mame/mshvsf_vertical_slice"
local samples = assert(io.open(capture_root .. "/samples.tsv", "w"))
samples:write("frame\tphase\tactive_object_bank\tbank_writes\tpc\n")
local inputs = assert(io.open(capture_root .. "/input_events.tsv", "w"))
inputs:write("frame\tinput\tvalue\tpc\n")
local qsound = assert(io.open(capture_root .. "/qsound_writes.tsv", "w"))
qsound:write("frame\tpc\tport\tbyte\tregister\tvalue\n")

local frame = 0
local active_object_bank = 0
local object_bank_writes = 0
local qsound_data_latch = 0
local capture_first = 1560
local capture_last = 1960

mshvsf_vertical_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "mshvsf_vertical_object_bank",
    function(offset, data, mask)
        active_object_bank = data & 1
        object_bank_writes = object_bank_writes + 1
    end)

mshvsf_vertical_qsound_tap = audio_program:install_write_tap(
    0xd000, 0xd002, "mshvsf_vertical_qsound_bus",
    function(offset, data, mask)
        local port = offset & 0xffff
        local byte = data & 0xff
        local pc = audiocpu.state["PC"].value
        if port == 0xd000 then
            qsound_data_latch = ((byte << 8) | (qsound_data_latch & 0xff)) & 0xffff
            qsound:write(string.format(
                "%d\t%04x\t%04x\t%02x\t\t\n", frame, pc, port, byte))
        elseif port == 0xd001 then
            qsound_data_latch = ((qsound_data_latch & 0xff00) | byte) & 0xffff
            qsound:write(string.format(
                "%d\t%04x\t%04x\t%02x\t\t\n", frame, pc, port, byte))
        elseif port == 0xd002 then
            qsound:write(string.format(
                "%d\t%04x\t%04x\t%02x\t%02x\t%04x\n",
                frame, pc, port, byte, byte, qsound_data_latch))
        end
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

local function input_edge(field, value, name)
    field:set_value(value)
    inputs:write(string.format("%d\t%s\t%d\t%08x\n", frame, name, value,
        maincpu.state["PC"].value))
    inputs:flush()
end

local function pulse(field, first, last, name)
    if frame == first then input_edge(field, 1, name) end
    if frame == last then input_edge(field, 0, name) end
end

local function phase()
    if frame < 1600 then return "round_start" end
    if frame < 1640 then return "idle" end
    if frame < 1671 then return "walk" end
    if frame < 1780 then return "jump" end
    if frame < 1850 then return "normal_attack" end
    if frame < 1886 then return "hadouken_input" end
    return "projectile_aftermath"
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
    screen:snapshot(string.format("mshvsf_vertical_slice/frame_%05d.png",
        sample_frame))
    samples:write(string.format("%d\t%s\t%d\t%d\t%08x\n", sample_frame,
        phase(), active_object_bank + 1, object_bank_writes,
        maincpu.state["PC"].value))
    samples:flush()
end

local function clear_inputs()
    coin:clear_value()
    start:clear_value()
    start2:clear_value()
    left:clear_value()
    right:clear_value()
    up:clear_value()
    down:clear_value()
    light_punch:clear_value()
    p2_light_punch:clear_value()
end

mshvsf_vertical_capture_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1

    -- Deterministic frontend route established by mame_probe_mshvsf_boot.lua.
    for coin_frame = 600, 690, 30 do
        pulse(coin, coin_frame, coin_frame + 3,
            "coin_" .. tostring(math.floor((coin_frame - 600) / 30) + 1))
    end
    pulse(start, 720, 723, "start_p1")
    pulse(start2, 750, 753, "start_p2")
    for confirm_frame = 810, 1290, 120 do
        pulse(light_punch, confirm_frame, confirm_frame + 4,
            "p1_frontend_confirm_" .. tostring(confirm_frame))
        pulse(p2_light_punch, confirm_frame + 15, confirm_frame + 19,
            "p2_frontend_confirm_" .. tostring(confirm_frame + 15))
    end

    if frame == 1640 then input_edge(right, 1, "right") end
    if frame == 1671 then input_edge(right, 0, "right") end

    if frame == 1700 then input_edge(up, 1, "up") end
    if frame == 1704 then input_edge(up, 0, "up") end

    pulse(light_punch, 1780, 1784, "light_punch")

    -- Quarter-circle forward + light punch.
    if frame == 1850 then input_edge(down, 1, "down") end
    if frame == 1855 then input_edge(right, 1, "right") end
    if frame == 1860 then
        input_edge(down, 0, "down")
        input_edge(light_punch, 1, "light_punch")
    end
    if frame == 1865 then input_edge(light_punch, 0, "light_punch") end
    if frame == 1870 then input_edge(right, 0, "right") end

    if frame >= capture_first and frame <= capture_last then
        dump_sample(frame)
    end
    if frame == capture_last + 1 then
        clear_inputs()
        samples:close()
        inputs:close()
        qsound:close()
        machine:exit()
    end
end)
