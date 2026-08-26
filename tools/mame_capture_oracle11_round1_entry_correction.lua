-- ORACLE-11 corrective probe for the executable Round 1 entry boundary.
-- Raw ledgers stay private under .deps/mame/oracle11_round1_entry_*.
local machine = manager.machine
local cpu = machine.devices[":maincpu"]
local program = cpu.spaces["program"]
local opcodes = cpu.spaces["opcodes"]
local root = assert(os.getenv("AVSP_ORACLE11_ENTRY_ROOT"))
local variant = assert(os.getenv("AVSP_ORACLE11_ENTRY_VARIANT"))
assert(variant == "baseline" or variant == "suppress_gate_clear")

local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local up, down = in0["P1 Up"], in0["P1 Down"]
local gun, attack, jump = in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"]

local frame = 0
local player = 0xff8380
local actor_first, actor_stride = 0xff9580, 0xc0
local samples = assert(io.open(root .. "/entry_samples.tsv", "w"))
local actors = assert(io.open(root .. "/entry_actors.tsv", "w"))
local writes = assert(io.open(root .. "/entry_writes.tsv", "w"))
local calls = assert(io.open(root .. "/entry_calls.tsv", "w"))
local player_writes = assert(io.open(root .. "/entry_player_writes.tsv", "w"))
local script = assert(io.open(root .. "/entry_script.tsv", "w"))
local result = assert(io.open(root .. "/result.tsv", "w"))
samples:write("frame\troute\tgate8236\tgate81af\tplayer_active\tplayer_state\tplayer_phase\tplayer_timer\tplayer_x\tplayer_y\tplayer_z\tplayer_anim\tplayer_action\tanim_state_c0\tanim_state_c1\tanim_state_c2\tanim_timer_c8\tgate_bit_d1\tgate_bit_d2\tscript_cursor_c4\n")
actors:write("frame\tsequence\tslot\tactive\tclass\ttype\tstate\tphase\tfacing\tx\ty\tz\tanim\thealth\n")
writes:write("frame\taddress\tpc\told\tdata\tmask\tsuppressed\n")
calls:write("frame\tpc\ta1\ta6\tcontroller_active\tcontroller_class\tcontroller_type\tcontroller_state\tcontroller_phase\ttable_hex\n")
player_writes:write("frame\toffset\tpc\told\tdata\tmask\n")
script:write("frame\tcursor\tbytes32\n")
result:write("variant\tfinal_frame\troute\tgate8236\tgate81af\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function u32(a) return program:read_u32(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function drive(field, enabled)
    if enabled then field:set_value(1) else field:clear_value() end
end

local function schedule(f)
    local coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
    local start_on = f >= 1200 and f <= 2400 and
        (f - 1200) % 180 >= 30 and (f - 1200) % 180 < 33
    local gun_on = f >= 1500 and f < 2300 and f % 90 < 5
    drive(coin, coin_on); drive(start, start_on)
    drive(gun, gun_on); drive(left, false); drive(right, false)
    drive(up, false); drive(down, false); drive(attack, false); drive(jump, false)
end

oracle11_entry_spawn_call = opcodes:install_read_tap(
    0x028874, 0x028875, "oracle11_entry_spawn_call",
    function(offset, data, mask)
        if frame == 2073 then
            local a1 = cpu.state["A1"].value & 0xffffff
            local a6 = cpu.state["A6"].value & 0xffffff
            local bytes = {}
            local index
            for index = 0, 79 do
                bytes[#bytes + 1] = string.format("%02x", u8(a1 + index))
            end
            calls:write(string.format(
                "%d\t%06x\t%06x\t%06x\t%d\t%02x\t%d\t%d\t%d\t%s\n",
                frame, cpu.state["PC"].value & 0xffffff, a1, a6, u8(a6),
                u8(a6 + 2), u8(a6 + 8), u16(a6 + 4), u16(a6 + 6),
                table.concat(bytes)))
        end
        return data
    end)

oracle11_entry_gate_writes = program:install_write_tap(
    0xff81ae, 0xff8237, "oracle11_entry_gate_writes",
    function(offset, data, mask)
        local address = offset & 0xffffff
        if frame < 1972 or frame > 2300 or
            not (address == 0xff81ae or address == 0xff8236) then return end
        local pc = cpu.state["PC"].value & 0xffffff
        local suppress = variant == "suppress_gate_clear" and
            address == 0xff8236 and pc == 0x02151e
        writes:write(string.format("%d\t%06x\t%06x\t%04x\t%08x\t%08x\t%d\n",
            frame, address, pc, u16(address), data & 0xffffffff,
            mask & 0xffffffff, suppress and 1 or 0))
        if suppress then return u16(address) end
    end)

oracle11_entry_player_writes = program:install_write_tap(
    player, player + 0xd3, "oracle11_entry_player_writes",
    function(offset, data, mask)
        if frame < 2070 or frame > 2240 then return end
        player_writes:write(string.format("%d\t%02x\t%06x\t%08x\t%08x\t%08x\n",
            frame, (offset - player) & 0xff,
            cpu.state["PC"].value & 0xffffff, u32(offset & 0xfffffc),
            data & 0xffffffff, mask & 0xffffffff))
    end)

local function emit_sample()
    samples:write(string.format("%d\t%04x\t%02x\t%02x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%08x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%08x\n",
        frame, u16(0xff8008), u8(0xff8236), u8(0xff81af), u8(player),
        u16(player + 4), u16(player + 6), u16(player + 0x0e),
        s16(u16(player + 0x10)), s16(u16(player + 0x14)),
        s16(u16(player + 0x18)), u32(player + 0x1c), u16(player + 0x2a),
        u8(player + 0xc0), u8(player + 0xc1), u8(player + 0xc2),
        u16(player + 0xc8), u8(player + 0xd1), u8(player + 0xd2),
        u32(player + 0xc4)))
end

local script_witnesses = {[2072]=true, [2073]=true, [2133]=true,
    [2191]=true, [2237]=true}
local function emit_script()
    local cursor = u32(player + 0xc4) & 0xffffff
    local bytes = {}
    local index
    for index = 0, 31 do bytes[#bytes + 1] = string.format("%02x", u8(cursor + index)) end
    script:write(string.format("%d\t%06x\t%s\n", frame, cursor, table.concat(bytes)))
end

local function emit_entry_actors()
    local sequence
    for sequence = 0, 9 do
        local index = 19 - sequence
        local base = actor_first + index * actor_stride
        actors:write(string.format(
            "%d\t%d\t%06x\t%d\t%02x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%08x\t%d\n",
            frame, sequence, base, u8(base), u8(base + 2), u8(base + 8),
            u16(base + 4), u16(base + 6), u8(base + 0x0f),
            s16(u16(base + 0x10)), s16(u16(base + 0x14)),
            s16(u16(base + 0x18)), u32(base + 0x1c), s16(u16(base + 0x40))))
    end
end

oracle11_entry_frame = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    schedule(frame)
    if frame >= 1972 then emit_sample() end
    if script_witnesses[frame] then emit_script() end
    if frame == 2074 then emit_entry_actors() end
    if frame == 2300 then
        result:write(string.format("%s\t%d\t%04x\t%02x\t%02x\n",
            variant, frame, u16(0xff8008), u8(0xff8236), u8(0xff81af)))
        coin:clear_value(); start:clear_value(); left:clear_value(); right:clear_value()
        up:clear_value(); down:clear_value(); gun:clear_value(); attack:clear_value(); jump:clear_value()
        samples:close(); actors:close(); writes:close(); calls:close()
        player_writes:close(); script:close(); result:close()
        machine:exit()
    end
end)
