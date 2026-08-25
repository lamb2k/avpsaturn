-- ORACLE-08: class-0x1f use of Coffee Shop world-space bounds.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local right, attack = in0["P1 Right"], in0["P1 Button 2"]
local root = assert(os.getenv("AVSP_ORACLE08_ENEMY_ROOT"))
local variant = os.getenv("AVSP_ORACLE08_ENEMY_VARIANT") or "baseline"
local valid = {baseline=true, beyond_left=true, beyond_right=true,
    beyond_lower=true, beyond_upper=true}
assert(valid[variant], "unsupported ORACLE-08 enemy variant")
local first_frame, last_frame = 4150, 4300
local frame, target = 0, 0xffa000
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local writes = assert(io.open(root .. "/enemy_writes.tsv", "w"))
samples:write("frame\tvariant\tinput_word\te_active\te_class\te_state\te_inner\te_action\te_x\te_z\tbound_x\tbound_z\n")
writes:write("frame\tvariant\taddress\toffset\tdata\tmask\tpc\ta5\ta6\tvalue\n")

local function u8(a) return program:read_u8(a) end
local function u16(a) return program:read_u16(a) end
local function s16(v) return v >= 0x8000 and v - 0x10000 or v end
local function drive(field, on, bit, word)
    if on then field:set_value(1); return word | bit end
    field:clear_value(); return word
end

oracle08_enemy_taps = {}
for _, address in ipairs({target + 0x10, target + 0x18}) do
    local watched = address
    oracle08_enemy_taps[#oracle08_enemy_taps + 1] = program:install_write_tap(
        watched, watched + 1, string.format("oracle08_enemy_%06x", watched),
        function(offset, data, mask)
            if frame < first_frame or frame > last_frame then return end
            writes:write(string.format("%d\t%s\t%06x\t%02x\t%04x\t%04x\t%06x\t%06x\t%06x\t%04x\n",
                frame, variant, watched, watched - target, data & 0xffff,
                mask & 0xffff, maincpu.state["PC"].value & 0xffffff,
                maincpu.state["A5"].value & 0xffffff,
                maincpu.state["A6"].value & 0xffffff, u16(watched)))
        end)
end

local function schedule(f)
    local word = 0
    word = drive(coin, f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3, 1, word)
    word = drive(start, f >= 2405 and f < 2408, 2, word)
    word = drive(right, f >= 3700 and f < 4200, 8, word)
    word = drive(attack, (f >= 2500 and f < 2505) or
        (f >= 3300 and f < 3305), 32, word)
    return word
end

local function isolate_target()
    for index = 0, 19 do
        local base = 0xff9580 + index * 0xc0
        if base ~= target and u8(base) ~= 0 and u8(base + 2) == 0x1f then
            program:write_u8(base, 0)
        end
    end
end

oracle08_enemy_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local word = schedule(frame)
    if frame >= 4150 then program:write_u8(target + 0x41, 0x65) end
    if frame >= 4200 then isolate_target() end
    if frame == 4210 then
        if variant == "beyond_left" then program:write_u16(target + 0x10, 840) end
        if variant == "beyond_right" then program:write_u16(target + 0x10, 1200) end
        if variant == "beyond_lower" then program:write_u16(target + 0x18, 200) end
        if variant == "beyond_upper" then program:write_u16(target + 0x18, 420) end
    end
    if frame >= first_frame and frame <= last_frame then
        samples:write(table.concat({frame, variant, word, u8(target),
            u8(target + 2), u8(target + 4), u8(target + 5), u16(target + 6),
            s16(u16(target + 0x10)), s16(u16(target + 0x18)),
            s16(u16(0xff8278)), s16(u16(0xff827c))}, "\t") .. "\n")
    end
    if frame == last_frame then
        coin:clear_value(); start:clear_value(); right:clear_value(); attack:clear_value()
        samples:close(); writes:close(); machine:exit()
    end
end)
