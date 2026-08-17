-- Reproduce the verified Stage 1 prefix, then observe one natural enemy attack
-- without freezing player health.  This isolates the native contact frame and
-- does not modify player or enemy state.
local machine = manager.machine
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local left = in0["P1 Left"]
local right = in0["P1 Right"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]
local main_program = machine.devices[":maincpu"].spaces["program"]
local capture_root = ".deps/mame/enemy_contact"
local timeline = assert(io.open(capture_root .. "/timeline.tsv", "w"))
timeline:write("frame\tplayer_health\tplayer_x\tplayer_y\tplayer_z\t" ..
    "enemy_active\tenemy_id\tenemy_action\tenemy_state\tenemy_substate\t" ..
    "enemy_x\tenemy_y\tenemy_z\tenemy_animation\t" ..
    "rival_action\trival_x\trival_y\trival_z\trival_animation\n")

local frame = 0
local active_object_bank = 0
enemy_contact_objbank_tap = main_program:install_write_tap(
    0x8040e0, 0x8040e1, "enemy_contact_object_bank",
    function(offset, data, mask)
        active_object_bank = data & 1
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

local function dump_anchor(anchor)
    local active_share = active_object_bank == 0 and
        machine.memory.shares[":objram1"] or machine.memory.shares[":objram2"]
    write_share_words(string.format(capture_root ..
        "/objram_active_%05d.tsv", anchor), active_share)
    write_palette(string.format(capture_root .. "/palette_%05d.tsv", anchor))
end

local function clear_gameplay_inputs()
    left:clear_value()
    right:clear_value()
    gun:clear_value()
    attack:clear_value()
    jump:clear_value()
end

local function word(address)
    return main_program:read_u16(address)
end

enemy_contact_capture_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1

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
    if frame == 4201 then left:set_value(1) end
    if frame == 4210 then left:clear_value() end

    if frame == 4080 or frame == 4164 or frame == 4200 then
        dump_anchor(frame)
    end
    if frame >= 4080 and frame <= 4500 then
        timeline:write(string.format(
            "%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d" ..
            "\t%d\t%d\t%d\t%d\t%d\n",
            frame, word(0xff83c0), word(0xff8390), word(0xff8394),
            word(0xff8398), main_program:read_u8(0xffa000),
            main_program:read_u8(0xffa002), word(0xffa006), word(0xffa00c),
            word(0xffa00e), word(0xffa010), word(0xffa014), word(0xffa018),
            word(0xffa01e), word(0xff9e86), word(0xff9e90),
            word(0xff9e94), word(0xff9e98), word(0xff9e9e)))
        timeline:flush()
    end
    if frame == 4501 then
        clear_gameplay_inputs()
        timeline:close()
        machine:exit()
    end
end)
