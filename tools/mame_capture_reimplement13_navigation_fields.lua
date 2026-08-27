-- Bounded corrective Oracle for Coffee Shop implementation fields.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local cps_a = machine.memory.shares[":cps_a_regs"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local attack = in0["P1 Button 2"]
local root = assert(os.getenv("AVSP_REIMPLEMENT13_NAV_ROOT"))
local first_frame, last_frame = 3400, 5200
local frame = 0
local player, obstacle, camera = 0xff8380, 0xffb380, 0xff8268
local samples = assert(io.open(root .. "/navigation_fields.tsv", "w"))
local resolves = assert(io.open(root .. "/navigation_resolves.tsv", "w"))
local camera_writes = assert(io.open(root .. "/camera_bound_writes.tsv", "w"))
local terrain_map_path = root .. "/terrain_map.bin"
local terrain_map_dumped = false

samples:write("frame\troute\troute_active\troute_subhandler\troute_timer\tplayer_active\tplayer_state\tplayer_action\tplayer_x\tplayer_y\tplayer_z\tobstacle_active\tobstacle_class\tobstacle_type\tobstacle_x\tobstacle_z\tbound_x\tbound_z\tcamera_enabled\tcamera_override\tcam_x_previous\tcam_x_position\tcam_z_position\tcam_x_target\tcam_z_target\tcam_x_target_previous\tcam_z_target_previous\tcam_z_min\tcam_z_max\tcam_x_min\tcam_x_max\tglobal_cam_x\tglobal_cam_z\tcoffee_phase\tcoffee_snapshot\tcoffee_countdown\tguard_counter\tguard_threshold_byte\tscroll2_x\tscroll2_y\tscroll3_x\tscroll3_y\n")
resolves:write("frame\tpc\tfield\ta1\ta4\ta6\trecord\told_value\twrite_data\tnew_value\tabs_x\thalf_x\tabs_z\thalf_z\tsign_bits\n")
camera_writes:write("frame\tfield\taddress\tpc\ta5\ta6\treturn0\treturn1\treturn2\troute\troute_subhandler\tplayer_x\tplayer_z\told_value\twrite_data\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function bytes(a, count)
    local out = {}
    for offset = 0, count - 1 do
        out[#out + 1] = string.format("%02x", u8((a + offset) & 0xffffff))
    end
    return table.concat(out)
end
local function u32(a) return program:read_u32(a) end
local function stack()
    local sr = maincpu.state["SR"].value & 0xffff
    local sp = (sr & 0x2000) ~= 0 and
        (maincpu.state["SP"].value & 0xffffff) or
        (maincpu.state["USP"].value & 0xffffff)
    return u32(sp) & 0xffffff, u32(sp + 4) & 0xffffff,
        u32(sp + 8) & 0xffffff
end
local function drive(field, on)
    if on then field:set_value(1) else field:clear_value() end
end
local function schedule(f)
    drive(coin, f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3)
    drive(start, f >= 2405 and f < 2408)
    drive(attack, (f >= 2500 and f < 2505) or (f >= 3300 and f < 3305))
    drive(right, f >= 3700 and f < 5000)
    drive(left, false)
end

local function install_player_tap(address, field)
    return program:install_write_tap(address, address + 1,
        "reimplement13_nav_" .. field,
        function(_, data, mask)
            if frame < first_frame or frame > last_frame then return end
            local pc = maincpu.state["PC"].value & 0xffffff
            if pc ~= 0x01d986 and pc ~= 0x01d998 and pc ~= 0x0b1c68 then
                return
            end
            local a1 = maincpu.state["A1"].value & 0xffffff
            local a4 = maincpu.state["A4"].value & 0xffffff
            local a5 = maincpu.state["A5"].value & 0xffffff
            local a6 = maincpu.state["A6"].value & 0xffffff
            resolves:write(string.format(
                "%d\t%06x\t%s\t%06x\t%06x\t%06x\t%s\t%d\t%08x\t%d\t%d\t%d\t%d\t%d\t%d\n",
                frame, pc, field, a1, a4, a6, bytes(a4, 8),
                s16(u16(address)), data & 0xffffffff,
                s16(data & 0xffff), s16(u16(a5 - 0x6746)),
                s16(u16(a5 - 0x6740)), s16(u16(a5 - 0x6742)),
                s16(u16(a5 - 0x673c)), u8(a5 - 0x673a)))
        end)
end

reimplement13_nav_x = install_player_tap(player + 0x10, "x")
reimplement13_nav_z = install_player_tap(player + 0x18, "z")
reimplement13_nav_camera_bounds = {}
for _, item in ipairs({{"z_upper", 0x30}, {"z_lower", 0x32},
                       {"x_lower", 0x34}, {"x_upper", 0x36}}) do
    local field, inner = item[1], item[2]
    local address = camera + inner
    reimplement13_nav_camera_bounds[#reimplement13_nav_camera_bounds + 1] =
        program:install_write_tap(address, address + 1,
            "reimplement13_nav_camera_" .. field,
            function(_, data, _)
                if frame < first_frame or frame > last_frame then return end
                local r0, r1, r2 = stack()
                camera_writes:write(string.format(
                    "%d\t%s\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%06x\t%d\t%d\t%d\t%d\t%d\t%08x\n",
                    frame, field, address,
                    maincpu.state["PC"].value & 0xffffff,
                    maincpu.state["A5"].value & 0xffffff,
                    maincpu.state["A6"].value & 0xffffff,
                    r0, r1, r2, u8(0xff8009), u8(camera + 5),
                    s16(u16(player + 0x10)), s16(u16(player + 0x18)),
                    s16(u16(address)), data & 0xffffffff))
            end)
end

reimplement13_nav_frame = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    schedule(frame)
    if not terrain_map_dumped and u8(player) ~= 0 and
            u16(player + 4) ~= 0 and u8(obstacle) ~= 0 then
        local terrain_map = assert(io.open(terrain_map_path, "wb"))
        for address = 0x904000, 0x907fff do
            terrain_map:write(string.char(u8(address)))
        end
        terrain_map:close()
        terrain_map_dumped = true
    end
    if frame >= 3400 then program:write_u8(player + 0x41, 0x65) end
    if frame >= first_frame and frame <= last_frame then
        samples:write(table.concat({
            frame, u8(0xff8009), u8(camera), u8(camera + 5), u16(camera + 6),
            u8(player), u8(player + 4), u16(player + 6),
            s16(u16(player + 0x10)), s16(u16(player + 0x14)),
            s16(u16(player + 0x18)), u8(obstacle), u8(obstacle + 2),
            u8(obstacle + 8), s16(u16(obstacle + 0x10)),
            s16(u16(obstacle + 0x18)), s16(u16(0xff8278)),
            s16(u16(0xff827c)), u8(0xff81af), u8(0xff81b0),
            s16(u16(camera + 8)), s16(u16(camera + 0x10)),
            s16(u16(camera + 0x14)), s16(u16(camera + 0x20)),
            s16(u16(camera + 0x24)), s16(u16(camera + 0x28)),
            s16(u16(camera + 0x2c)), s16(u16(camera + 0x30)),
            s16(u16(camera + 0x32)), s16(u16(camera + 0x34)),
            s16(u16(camera + 0x36)), s16(u16(0xff8032)),
            s16(u16(0xff8034)), u8(0xffd186), u16(0xffd1c4),
            u16(0xffd1c6), u16(0xff1a1a), u8(0xff820e),
            cps_a:read_u16(16), cps_a:read_u16(18),
            cps_a:read_u16(12), cps_a:read_u16(14)
        }, "\t") .. "\n")
    end
    if frame == last_frame then
        coin:clear_value(); start:clear_value(); attack:clear_value()
        left:clear_value(); right:clear_value()
        samples:close(); resolves:close(); camera_writes:close(); machine:exit()
    end
end)
