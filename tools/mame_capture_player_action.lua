-- Capture one isolated Predator Warrior action after traversing the verified
-- cold boot, credit, Start, character-select, and Round 1 path. The action is
-- selected by AVSP_ACTION_PROBE in the invoking process. These captures are
-- offline reference evidence and are never shipped on the Saturn disc.
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
local action = os.getenv("AVSP_ACTION_PROBE") or ""
local allowed_actions = {
    idle = true,
    gun = true,
    melee = true,
    jump = true,
    dash = true,
    special = true,
    damage = true,
}
assert(allowed_actions[action], "invalid AVSP_ACTION_PROBE: " .. action)

local capture_root = ".deps/mame/player_actions/" .. action
local metadata = assert(io.open(capture_root .. "/samples.tsv", "w"))
metadata:write("frame\taction\tactive_object_bank\tbank_writes\n")
local frame = 0
local active_object_bank = 0
local object_bank_writes = 0
local action_frame = 2525
local capture_first = 2480
local capture_last = action == "damage" and 3400 or 2608

local main_program = machine.devices[":maincpu"].spaces["program"]
player_action_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "player_action_object_bank",
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

local function clear_gameplay_inputs()
    left:clear_value()
    right:clear_value()
    up:clear_value()
    down:clear_value()
    gun:clear_value()
    attack:clear_value()
    jump:clear_value()
end

local function dump_sample(sample_frame)
    local active_share = active_object_bank == 0 and
        machine.memory.shares[":objram1"] or machine.memory.shares[":objram2"]
    write_share_words(string.format(capture_root ..
        "/objram_active_%05d.tsv", sample_frame), active_share)
    write_palette(string.format(capture_root ..
        "/palette_%05d.tsv", sample_frame))
    screen:snapshot(string.format("player_actions/%s/%s_%05d.png",
        action, action, sample_frame))
    metadata:write(string.format("%d\t%s\t%d\t%d\n", sample_frame,
        action, active_object_bank + 1, object_bank_writes))
    metadata:flush()
end

player_action_capture_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1

    -- Match the verified opening traversal, but stop action-button pulses as
    -- soon as the default Predator Warrior has been selected.
    if frame >= 1200 and frame <= 2400 then
        if (frame - 1200) % 180 == 0 then coin:set_value(1) end
        if (frame - 1200) % 180 == 3 then coin:clear_value() end
        if (frame - 1200) % 180 == 30 then start:set_value(1) end
        if (frame - 1200) % 180 == 33 then start:clear_value() end
    end
    if frame >= 1500 and frame <= 1895 then
        if frame % 90 == 0 then gun:set_value(1) end
        if frame % 90 == 5 then gun:clear_value() end
    end

    if frame == action_frame then
        if action == "gun" then gun:set_value(1) end
        if action == "melee" then attack:set_value(1) end
        if action == "jump" then jump:set_value(1) end
        if action == "dash" then
            right:set_value(1)
            jump:set_value(1)
        end
        if action == "special" then
            gun:set_value(1)
            attack:set_value(1)
        end
        print(string.format("AVSPU_PLAYER_ACTION action=%s frame=%d",
            action, frame))
    end
    if frame == action_frame + 5 then
        gun:clear_value()
        attack:clear_value()
        jump:clear_value()
    end
    if frame == action_frame + 20 then
        left:clear_value()
        right:clear_value()
        up:clear_value()
        down:clear_value()
    end

    if frame >= capture_first and frame <= capture_last then
        dump_sample(frame)
    end

    if frame == capture_last + 1 then
        clear_gameplay_inputs()
        coin:clear_value()
        start:clear_value()
        metadata:close()
        machine:exit()
    end
end)
