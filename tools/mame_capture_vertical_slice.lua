-- Tranche 1 MAME semantic capture for the bounded avspu gameplay slice.
--
-- This deliberately reuses the cold-boot enemy_actions schedule.  All
-- frame-level source material, screenshots, register dumps and instruction
-- traces remain private beneath .deps/mame/vertical_slice/.
local machine = manager.machine
local screen = machine.screens[":screen"]
local maincpu = machine.devices[":maincpu"]
local audiocpu = machine.devices[":audiocpu"]
local program = maincpu.spaces["program"]
local shares = machine.memory.shares
local debugger = assert(machine.debugger, "launch MAME with -debug")

local root = assert(os.getenv("AVSP_VSLICE_CAPTURE_ROOT"),
    "AVSP_VSLICE_CAPTURE_ROOT is required")
local first_frame = tonumber(os.getenv("AVSP_VSLICE_FIRST") or "4080")
local last_frame = tonumber(os.getenv("AVSP_VSLICE_LAST") or "5469")
local perturb_frame = tonumber(os.getenv("AVSP_VSLICE_PERTURB_FRAME") or "0")
local trace_path = root .. "/maincpu.trace"

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

local frame = 0
local active_object_bank = 0
local object_bank_writes = 0
local trace_active = false
local qsound_latch = 0
local samples = assert(io.open(root .. "/samples.tsv", "w"))
local qsound = assert(io.open(root .. "/qsound.tsv", "w"))
samples:write("frame\tinput_word\tactive_bank\tbank_writes",
    "\tp_state\tp_class\tp_sub\tp_action\tp_type\tp_facing\tp_x\tp_y\tp_z",
    "\tp_anim\tp_timer\tp_health\tp_hit\tp_source\tp_hurt\tp_attack",
    "\te_state\te_class\te_sub\te_action\te_type\te_facing\te_x\te_y\te_z",
    "\te_anim\te_timer\te_health\te_hit\te_source\te_hurt\te_attack\n")
qsound:write("frame\tpc\tport\tbyte\tregister\tvalue\n")

local function u16(address)
    return program:read_u16(address)
end

local function u32(address)
    return program:read_u32(address)
end

local function s16(value)
    return value >= 0x8000 and value - 0x10000 or value
end

local function write_bytes(path, bytes)
    local output = assert(io.open(path, "wb"))
    output:write(bytes)
    output:close()
end

local function share_bytes(share)
    local chunks = {}
    local aligned = share.size - share.size % 4
    for offset = 0, aligned - 4, 4 do
        chunks[#chunks + 1] = string.pack(">I4", share:read_u32(offset))
    end
    for offset = aligned, share.size - 1 do
        chunks[#chunks + 1] = string.char(share:read_u8(offset))
    end
    return table.concat(chunks)
end

local function palette_bytes()
    local palette = machine.palettes[":palette"]
    local chunks = {}
    for index = 0, palette.entries - 1 do
        chunks[#chunks + 1] = string.pack(">I4", palette:pen_color(index))
    end
    return table.concat(chunks)
end

local function actor(base)
    local anim = u32(base + 0x1c)
    return {
        state = program:read_u8(base + 0x00),
        class_id = program:read_u8(base + 0x02),
        sub_state = u16(base + 0x04),
        action = u16(base + 0x06),
        type = program:read_u8(base + 0x08),
        facing = program:read_u8(base + 0x0f),
        x = s16(u16(base + 0x10)),
        y = s16(u16(base + 0x14)),
        z = s16(u16(base + 0x18)),
        anim = anim,
        timer = u16(base + 0x2a),
        health = s16(u16(base + 0x40)),
        hit = program:read_u8(base + 0x2c),
        source = program:read_u8(base + 0x2d),
        hurt = anim ~= 0 and program:read_u8(anim + 8) or 0,
        attack = anim ~= 0 and program:read_u8(anim + 9) or 0,
    }
end

local function write_actor(fields, actor_value)
    fields[#fields + 1] = actor_value.state
    fields[#fields + 1] = actor_value.class_id
    fields[#fields + 1] = actor_value.sub_state
    fields[#fields + 1] = actor_value.action
    fields[#fields + 1] = actor_value.type
    fields[#fields + 1] = actor_value.facing
    fields[#fields + 1] = actor_value.x
    fields[#fields + 1] = actor_value.y
    fields[#fields + 1] = actor_value.z
    fields[#fields + 1] = string.format("%08x", actor_value.anim)
    fields[#fields + 1] = actor_value.timer
    fields[#fields + 1] = actor_value.health
    fields[#fields + 1] = actor_value.hit
    fields[#fields + 1] = actor_value.source
    fields[#fields + 1] = actor_value.hurt
    fields[#fields + 1] = actor_value.attack
end

local function clear_inputs()
    coin:clear_value(); start:clear_value(); left:clear_value(); right:clear_value()
    up:clear_value(); down:clear_value(); gun:clear_value(); attack:clear_value()
    jump:clear_value()
end

-- Exact enemy_actions cold-boot route.  The perturbation only suppresses the
-- attack assertion for one source frame; every other input bit is unchanged.
local function apply_schedule(f)
    local word = 0
    local function drive(field, enabled, bit)
        if enabled then field:set_value(1); word = word | bit
        else field:clear_value() end
    end
    local coin_on = f >= 1200 and f <= 2400 and (f - 1200) % 180 < 3
    local start_on = f >= 1200 and f <= 2400 and
        (f - 1200) % 180 >= 30 and (f - 1200) % 180 < 33
    local gun_on = (f >= 1500 and f < 4200 and f % 90 < 5) or
        (f >= 2600 and f < 4200 and f % 75 < 6)
    local right_on = f >= 2600 and f < 4200
    local attack_on = f >= 2600 and f < 4200 and f % 310 < 7
    local jump_on = f >= 2600 and f < 4200 and f % 430 < 7
    local left_on = f >= 4201 and f < 4210
    if f >= 4420 and f <= 5469 then
        local phase = (f - 4420) % 45
        attack_on = phase < 5
    end
    if f == perturb_frame then attack_on = false end
    drive(coin, coin_on, 1)
    drive(start, start_on, 2)
    drive(left, left_on, 4)
    drive(right, right_on, 8)
    drive(gun, gun_on, 16)
    drive(attack, attack_on, 32)
    drive(jump, jump_on, 64)
    return word
end

vertical_slice_objbank_tap = program:install_write_tap(
    0x8040e0, 0x8040e1, "vertical_slice_object_bank",
    function(offset, data, mask)
        active_object_bank = data & 1
        object_bank_writes = object_bank_writes + 1
    end)

vertical_slice_qsound_tap = audiocpu.spaces["program"]:install_write_tap(
    0xd000, 0xd002, "vertical_slice_qsound",
    function(offset, data, mask)
        if frame < first_frame or frame > last_frame then return end
        local port = offset & 0xffff
        local byte = data & 0xff
        local pc = audiocpu.state["PC"].value
        if port == 0xd000 then
            qsound_latch = ((byte << 8) | (qsound_latch & 0xff)) & 0xffff
            qsound:write(string.format("%d\t%04x\t%04x\t%02x\t\t\n",
                frame, pc, port, byte))
        elseif port == 0xd001 then
            qsound_latch = ((qsound_latch & 0xff00) | byte) & 0xffff
            qsound:write(string.format("%d\t%04x\t%04x\t%02x\t\t\n",
                frame, pc, port, byte))
        else
            qsound:write(string.format("%d\t%04x\t%04x\t%02x\t%02x\t%04x\n",
                frame, pc, port, byte, byte, qsound_latch))
        end
    end)

local function capture_frame(input_word)
    local player = actor(0xff8380)
    local enemy = actor(0xffa000)
    local active = active_object_bank == 0 and shares[":objram1"] or shares[":objram2"]
    write_bytes(string.format(root .. "/objram/%05d.bin", frame), share_bytes(active))
    write_bytes(string.format(root .. "/cps_a/%05d.bin", frame), share_bytes(shares[":cps_a_regs"]))
    write_bytes(string.format(root .. "/cps_b/%05d.bin", frame), share_bytes(shares[":cps_b_regs"]))
    write_bytes(string.format(root .. "/palette/%05d.bin", frame), palette_bytes())
    screen:snapshot(string.format(root .. "/frames/%05d.png", frame))
    local row = {frame, input_word, active_object_bank + 1, object_bank_writes}
    write_actor(row, player)
    write_actor(row, enemy)
    samples:write(table.concat(row, "\t") .. "\n")
end

vertical_slice_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    local input_word = apply_schedule(frame)
    -- Preserve the accepted enemy_actions observation: player health only is
    -- held so the route cannot divert through Continue; enemy behavior stays native.
    if frame >= 4200 then program:write_u8(0xff83c1, 0x65) end
    if frame == first_frame then
        debugger:command("trace " .. trace_path .. ",:maincpu")
        trace_active = true
    end
    if frame >= first_frame and frame <= last_frame then capture_frame(input_word) end
    if frame == last_frame then
        if trace_active then debugger:command("trace off,:maincpu") end
        debugger:command("traceflush")
        clear_inputs()
        samples:close()
        qsound:close()
        machine:exit()
    end
end)

-- MAME starts paused when -debug is present.  The frame notifier owns the
-- bounded trace lifetime, so permit emulation to reach it immediately.
debugger.execution_state = "run"
