-- Bounded ORACLE-11 follow-up for the Coffee Shop route-6 player program.
-- The accepted route harness supplies the deterministic input route.  This
-- probe records only player-owned opcode execution and player-record writes
-- around the source withdrawal; raw output remains private under .deps/mame.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local opcodes = maincpu.spaces["opcodes"]
local root = assert(os.getenv("AVSP_ORACLE11_COFFEE_EXIT_ROOT"))
local player = 0xff8380
local frame = 0
local first, last = 5448, 5567
local trace = assert(io.open(root .. "/coffee_exit_player_trace.tsv", "w"))
local writes = assert(io.open(root .. "/coffee_exit_player_writes.tsv", "w"))
trace:write("frame\tpc\ta0\ta1\ta2\ta3\ta6\td0\td1\td2\td3\tstate\tsubstate\tx_fp\ty_fp\tz\tgate8236\troute\n")
writes:write("frame\taddress\tpc\tdata\tmask\tstate\tsubstate\tx_fp\ty_fp\tz\tgate8236\troute\n")
local globals = assert(io.open(root .. "/coffee_exit_global_writes.tsv", "w"))
globals:write("frame\taddress\tpc\tdata\tmask\tgate8236\troute\tsubroute\n")
local route_trace = assert(io.open(root .. "/coffee_exit_route_trace.tsv", "w"))
route_trace:write("frame\tpc\ta5\td0\td1\troute\tsubroute\tguard837c\tloader802c\tloader804a\tload81c2\n")
local frames = assert(io.open(root .. "/coffee_exit_player_frames.tsv", "w"))
frames:write("frame\tstate\tsubstate\tx_fp\ty_fp\tz\tdirection\tfacing\tanimation_record\tanimation_timer\tanimation_branch\tscript_handler\tscript_substate\tscript_argument\tscript_timer\tx_velocity\ty_velocity\tx_acceleration\ty_acceleration\ttarget_x\ttarget_z\tmotion_calls\tballistic_calls\tdwell_decrements\tgate8236\troute\n")
local motion_calls, ballistic_calls, dwell_decrements = 0, 0, 0

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end

coffee_exit_player_opcodes = opcodes:install_read_tap(
    0x020000, 0x024fff, "coffee_exit_player_opcodes", function()
        if frame < first or frame > last or
           (maincpu.state["A6"].value & 0xffffff) ~= player then return end
        trace:write(string.format(
            "%d\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%08x\t%08x\t%08x\t%08x\t%04x\t%04x\t%08x\t%08x\t%d\t%02x\t%d\n",
            frame, maincpu.state["PC"].value & 0xffffff,
            maincpu.state["A0"].value & 0xffffff,
            maincpu.state["A1"].value & 0xffffff,
            maincpu.state["A2"].value & 0xffffff,
            maincpu.state["A3"].value & 0xffffff,
            maincpu.state["A6"].value & 0xffffff,
            maincpu.state["D0"].value & 0xffffffff,
            maincpu.state["D1"].value & 0xffffffff,
            maincpu.state["D2"].value & 0xffffffff,
            maincpu.state["D3"].value & 0xffffffff,
            u16(player + 4),
            u16(player + 6), u32(player + 0x10), u32(player + 0x14),
            u16(player + 0x18), u8(0xff8236), u16(0xff8008)))
    end)

coffee_exit_route_opcodes = opcodes:install_read_tap(
    0x008000, 0x009fff, "coffee_exit_route_opcodes", function()
        if frame < 5520 or frame > last then return end
        route_trace:write(string.format(
            "%d\t%06x\t%06x\t%08x\t%08x\t%d\t%d\t%d\t%d\t%d\t%d\n",
            frame, maincpu.state["PC"].value & 0xffffff,
            maincpu.state["A5"].value & 0xffffff,
            maincpu.state["D0"].value & 0xffffffff,
            maincpu.state["D1"].value & 0xffffffff,
            u16(0xff8008), u16(0xff800c), u16(0xff837c),
            u16(0xff802c), u16(0xff804a), u16(0xff81c2)))
    end)

coffee_exit_global_writes = program:install_write_tap(
    0xff8008, 0xff837d, "coffee_exit_global_writes",
    function(offset, data, mask)
        if frame < first or frame > last then return end
        local address = offset & 0xffffff
        if address ~= 0xff8008 and address ~= 0xff800c and
           address ~= 0xff81f3 and address ~= 0xff8236 and
           address ~= 0xff837c then return end
        globals:write(string.format(
            "%d\t%06x\t%06x\t%08x\t%08x\t%02x\t%d\t%d\n",
            frame, address, maincpu.state["PC"].value & 0xffffff,
            data & 0xffffffff, mask & 0xffffffff, u8(0xff8236),
            u16(0xff8008), u16(0xff800c)))
    end)

coffee_exit_player_writes = program:install_write_tap(
    player, player + 0xff, "coffee_exit_player_writes",
    function(offset, data, mask)
        if frame < first or frame > last then return end
        local pc = maincpu.state["PC"].value & 0xffffff
        if pc == 0x016266 then motion_calls = motion_calls + 1 end
        if pc == 0x01a8f6 then ballistic_calls = ballistic_calls + 1 end
        if pc == 0x02177a then dwell_decrements = dwell_decrements + 1 end
        writes:write(string.format(
            "%d\t%06x\t%06x\t%08x\t%08x\t%04x\t%04x\t%08x\t%08x\t%d\t%02x\t%d\n",
            frame, offset & 0xffffff,
            maincpu.state["PC"].value & 0xffffff, data & 0xffffffff,
            mask & 0xffffffff, u16(player + 4), u16(player + 6),
            u32(player + 0x10), u32(player + 0x14), u16(player + 0x18),
            u8(0xff8236), u16(0xff8008)))
    end)

coffee_exit_player_frame = emu.add_machine_frame_notifier(function()
    if frame >= first and frame <= last then
        frames:write(string.format(
            "%d\t%04x\t%04x\t%08x\t%08x\t%d\t%02x\t%02x\t%08x\t%04x\t%04x\t%02x\t%02x\t%02x\t%04x\t%08x\t%08x\t%08x\t%08x\t%d\t%d\t%d\t%d\t%d\t%02x\t%d\n",
            frame, u16(player + 4), u16(player + 6),
            u32(player + 0x10), u32(player + 0x14), u16(player + 0x18),
            u8(player + 0x0c), u8(player + 0x0f), u32(player + 0x1c),
            u16(player + 0x0a), u16(player + 0x24),
            u8(player + 0xc1), u8(player + 0xc2), u8(player + 0xc3),
            u16(player + 0xc8), u32(player + 0x30), u32(player + 0x34),
            u32(player + 0x38), u32(player + 0x3c),
            u16(player + 0x60), u16(player + 0x62),
            motion_calls, ballistic_calls, dwell_decrements,
            u8(0xff8236), u16(0xff8008)))
    end
    motion_calls, ballistic_calls, dwell_decrements = 0, 0, 0
    frame = frame + 1
    if frame == 18000 then
        trace:close(); writes:close(); globals:close(); route_trace:close(); frames:close()
    end
end)

dofile("tools/mame_capture_oracle11_round1_route.lua")
