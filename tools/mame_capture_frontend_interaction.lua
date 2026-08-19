-- Cadence-1 ROM-truth capture of AvP's character-select interaction.
-- Raw output is private and git-ignored.  The tracked analyzer serializes
-- only semantic timing, cursor geometry, source addresses, counts and hashes.
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
local button1 = in0["P1 Button 1"]
local button2 = in0["P1 Button 2"]
local button3 = in0["P1 Button 3"]

local route = os.getenv("AVSP_FRONTEND_INTERACTION_ROUTE") or ""
local allowed = {
    topology = true,
    button1 = true,
    button2 = true,
    button3 = true,
    alternate_confirm = true,
}
assert(allowed[route], "invalid AVSP_FRONTEND_INTERACTION_ROUTE: " .. route)

local capture_root = ".deps/mame/frontend_interaction/" .. route
local metadata = assert(io.open(capture_root .. "/samples.tsv", "w"))
metadata:write("frame\tleft\tright\tup\tdown\tbutton1\tbutton2\tbutton3\tactive_object_bank\n")
local selection_writes = assert(io.open(
    capture_root .. "/selection_writes.tsv", "w"))
selection_writes:write("frame\tpc\taddress\tdata\tmask\n")

local frame = 0
local active_object_bank = 0
local main_program = machine.devices[":maincpu"].spaces["program"]
frontend_interaction_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "frontend_interaction_object_bank",
    function(offset, data, mask)
        active_object_bank = data & 1
    end)
local function install_selection_tap(address, name)
    return main_program:install_write_tap(address, address + 1, name,
        function(offset, data, mask)
            selection_writes:write(string.format(
                "%d\t%06x\t%06x\t%08x\t%08x\n", frame,
                machine.devices[":maincpu"].state["PC"].value,
                address, data, mask))
        end)
end
frontend_selection_mask_tap = install_selection_tap(
    0xff81cc, "frontend_selection_mask")
frontend_selection_index_tap = install_selection_tap(
    0xff8452, "frontend_selection_index")

local keys = {left, right, up, down, button1, button2, button3}
local key_state = {0, 0, 0, 0, 0, 0, 0}

local function clear_inputs()
    coin:clear_value()
    start:clear_value()
    for index, key in ipairs(keys) do
        key:clear_value()
        key_state[index] = 0
    end
end

local function set_key(index, pressed)
    if pressed then
        keys[index]:set_value(1)
        key_state[index] = 1
    else
        keys[index]:clear_value()
        key_state[index] = 0
    end
end

local function pulse(index, first, last)
    if frame == first then set_key(index, true) end
    if frame == last then set_key(index, false) end
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

local function write_workram(path)
    local file = assert(io.open(path, "wb"))
    file:write(main_program:read_range(0xff8000, 0xffffff, 8))
    file:close()
end

local function write_active_objram(path)
    local shares = machine.memory.shares
    local active = active_object_bank == 0 and shares[":objram1"] or shares[":objram2"]
    write_share_words(path, active)
end

local full_frames = {
    [1620] = true, [1700] = true, [1760] = true, [1790] = true,
    [2100] = true, [2240] = true, [2400] = true, [2420] = true,
    [2460] = true, [2600] = true, [2695] = true, [2750] = true,
    [2763] = true, [2823] = true, [2883] = true, [2943] = true,
    [3003] = true, [3063] = true, [3123] = true, [3150] = true,
    [3183] = true, [3223] = true, [3250] = true, [3283] = true,
}

local function dump_frame(sample_frame)
    write_active_objram(string.format(
        capture_root .. "/objram_active_%04d.tsv", sample_frame))
    local shares = machine.memory.shares
    if sample_frame >= 2350 then
        write_share_words(string.format(
            capture_root .. "/objram1_%04d.tsv", sample_frame), shares[":objram1"])
        write_share_words(string.format(
            capture_root .. "/objram2_%04d.tsv", sample_frame), shares[":objram2"])
        write_workram(string.format(
            capture_root .. "/workram_%04d.bin", sample_frame))
    end
    screen:snapshot(string.format(
        "frontend_interaction/%s/reference_%04d.png", route, sample_frame))
    if full_frames[sample_frame] then
        write_share_words(string.format(
            capture_root .. "/gfxram_%04d.tsv", sample_frame), shares[":gfxram"])
        write_share_words(string.format(
            capture_root .. "/cps_a_regs_%04d.tsv", sample_frame), shares[":cps_a_regs"])
        write_share_words(string.format(
            capture_root .. "/cps_b_regs_%04d.tsv", sample_frame), shares[":cps_b_regs"])
        write_palette(string.format(
            capture_root .. "/palette_%04d.tsv", sample_frame))
    end
    metadata:write(string.format("%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",
        sample_frame, key_state[1], key_state[2], key_state[3], key_state[4],
        key_state[5], key_state[6], key_state[7], active_object_bank))
end

frontend_interaction_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1

    -- One credit and one Start.  This is the stable route underlying the
    -- earlier frontend capture, without its recurring inputs.
    if frame == 1560 then coin:set_value(1) end
    if frame == 1563 then coin:clear_value() end
    if frame == 1590 then start:set_value(1) end
    if frame == 1593 then start:clear_value() end

    -- The source frontend's story panels accept any gameplay input as a
    -- skip.  Use one explicit common skip so every route reaches the same
    -- settled selection state before its measured interaction begins.
    pulse(6, 2500, 2505)

    if route == "topology" then
        pulse(2, 2760, 2763) -- right
        pulse(4, 2820, 2823) -- down
        pulse(1, 2880, 2883) -- left
        pulse(3, 2940, 2943) -- up
        pulse(1, 3000, 3003) -- left boundary/wrap probe
        pulse(3, 3060, 3063) -- up boundary/wrap probe
        pulse(2, 3120, 3180) -- held-right repeat probe
        pulse(4, 3220, 3280) -- held-down repeat probe
    elseif route == "button1" then
        pulse(5, 2750, 2755)
    elseif route == "button2" then
        pulse(6, 2750, 2755)
    elseif route == "button3" then
        pulse(7, 2750, 2755)
    elseif route == "alternate_confirm" then
        pulse(4, 2760, 2763)
        pulse(2, 2820, 2823)
        pulse(5, 2880, 2885)
    end

    if frame >= 1500 and frame <= 3350 then dump_frame(frame) end
    if frame == 3352 then
        clear_inputs()
        metadata:close()
        selection_writes:close()
        machine:exit()
    end
end)
