-- Continue a debug-enabled state produced by mame_probe_debug_overlays.lua
-- through the end of Round 1.  Hitbox mode samples every source frame;
-- collision mode samples every 30 frames.  Raw screenshots and RAM blocks are
-- private regression evidence and remain under .deps.
local machine = manager.machine
local screen = machine.screens[":screen"]
local program = machine.devices[":maincpu"].spaces["program"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields

local capture_root = assert(os.getenv("AVSP_DEBUG_CAPTURE_ROOT"))
local snapshot_root = assert(capture_root:match("([^/\\]+)$"))
local state_name = assert(os.getenv("AVSP_DEBUG_STATE_NAME"))
local requested_row2 = tonumber(assert(os.getenv("AVSP_DEBUG_ROW2")))
local cadence = tonumber(os.getenv("AVSP_DEBUG_CADENCE") or "1")
local base_frame = 4200
local final_frame = tonumber(os.getenv("AVSP_DEBUG_FINAL_FRAME") or "15000")

local DEBUG_ENABLE = 0xff81c7
local DIP_ROW1 = 0xff806c
local DIP_ROW2 = 0xff806d
local PLAYER_HEALTH = 0xff83c1
local PLAYER_BLOCK_FIRST = 0xff8300
local PLAYER_BLOCK_SIZE = 0x0d00
local ACTOR_BLOCK_FIRST = 0xffa000
local ACTOR_BLOCK_SIZE = 0x2000
local SAMPLE_SIZE = PLAYER_BLOCK_SIZE + ACTOR_BLOCK_SIZE

local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local left = in0["P1 Left"]
local right = in0["P1 Right"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]

local frame = 0
local boot_frames = 0
local state_loaded = false
local sample_index = 0
local metadata = assert(io.open(capture_root .. "/samples.tsv", "w"))
local layout = assert(io.open(capture_root .. "/ram_layout.tsv", "w"))
local state_file = assert(io.open(capture_root .. "/actor_state.bin", "wb"))
metadata:write(
    "frame\tsample_index\tfile_offset\tdebug_enable\tdip_row1\tdip_row2\tplayer_health\n")
layout:write("name\taddress\tbytes\toffset\n")
layout:write(string.format("player_block\t%06x\t%d\t0\n",
    PLAYER_BLOCK_FIRST, PLAYER_BLOCK_SIZE))
layout:write(string.format("actor_block\t%06x\t%d\t%d\n",
    ACTOR_BLOCK_FIRST, ACTOR_BLOCK_SIZE, PLAYER_BLOCK_SIZE))
layout:write(string.format("sample\t000000\t%d\t0\n", SAMPLE_SIZE))
layout:close()

local function write_program_range(first, size)
    local bytes = {}
    for offset = 0, size - 1 do
        bytes[#bytes + 1] = string.char(program:read_u8(first + offset))
        if #bytes == 1024 then
            state_file:write(table.concat(bytes))
            bytes = {}
        end
    end
    if #bytes > 0 then state_file:write(table.concat(bytes)) end
end

local function capture(absolute_frame)
    local file_offset = sample_index * SAMPLE_SIZE
    local enable = program:read_u8(DEBUG_ENABLE)
    local row1 = program:read_u8(DIP_ROW1)
    local row2 = program:read_u8(DIP_ROW2)
    local health = program:read_u8(PLAYER_HEALTH)
    if enable == 0 or (row2 & requested_row2) ~= requested_row2 then
        error(string.format(
            "debug flags lost at frame %d: master=%02x row2=%02x",
            absolute_frame, enable, row2))
    end
    write_program_range(PLAYER_BLOCK_FIRST, PLAYER_BLOCK_SIZE)
    write_program_range(ACTOR_BLOCK_FIRST, ACTOR_BLOCK_SIZE)
    metadata:write(string.format("%d\t%d\t%d\t%02x\t%02x\t%02x\t%02x\n",
        absolute_frame, sample_index, file_offset, enable, row1, row2, health))
    screen:snapshot(string.format(
        snapshot_root .. "/overlay_%05d.png", absolute_frame))
    sample_index = sample_index + 1
end

round1_debug_post_load = emu.add_machine_post_load_notifier(function()
    frame = 0
    state_loaded = true
    print("ROUND1_DEBUG loaded " .. state_name)
end)

round1_debug_subscription = emu.add_machine_frame_notifier(function()
    if not state_loaded then
        boot_frames = boot_frames + 1
        if boot_frames > 600 then
            error("debug-enabled frame-4200 state never loaded")
        end
        return
    end

    frame = frame + 1
    local absolute_frame = base_frame + frame
    local health = program:read_u8(PLAYER_HEALTH)

    if frame == 1 then right:set_value(1) end
    if frame % 45 == 0 then gun:set_value(1) end
    if frame % 45 == 7 then gun:clear_value() end
    if frame % 180 == 0 then attack:set_value(1) end
    if frame % 180 == 8 then attack:clear_value() end
    if frame % 240 == 0 then jump:set_value(1) end
    if frame % 240 == 8 then jump:clear_value() end

    if frame % 600 == 30 then coin:set_value(1) end
    if frame % 600 == 34 then coin:clear_value() end
    -- Debug master turns Start into suicide for a live player.  Use Start only
    -- when health is zero so continues remain possible without perturbing play.
    if (health == 0 or health >= 0x80) and frame % 120 == 30 then
        start:set_value(1)
    end
    if frame % 120 == 34 then start:clear_value() end

    if (absolute_frame - (base_frame + 1)) % cadence == 0 then
        capture(absolute_frame)
    end
    if absolute_frame % 600 == 0 then
        print(string.format(
            "ROUND1_DEBUG frame=%d samples=%d health=%02x",
            absolute_frame, sample_index, health))
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
        state_file:close()
        machine:exit()
    end
end)

machine:load(state_name)
