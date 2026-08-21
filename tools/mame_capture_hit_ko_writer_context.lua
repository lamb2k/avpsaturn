-- Capture private, target-actor write evidence for the bounded AVSP HIT/KO
-- investigation.  This file deliberately writes only below the caller-supplied
-- ignored root; it is not a source of committed ROM, opcode, or trace content.
local machine = manager.machine
local maincpu = machine.devices[":maincpu"]
local program = maincpu.spaces["program"]
local debugger = assert(machine.debugger, "launch MAME with -debug")
local cpu_debug = assert(maincpu.debug, "main CPU debugger is unavailable")

local root = assert(os.getenv("AVSP_HIT_KO_CONTEXT_ROOT"),
    "AVSP_HIT_KO_CONTEXT_ROOT is required")
local first_frame = tonumber(os.getenv("AVSP_HIT_KO_FIRST") or "4080")
local last_frame = tonumber(os.getenv("AVSP_HIT_KO_LAST") or "5469")
local actor_base = 0xffa000
local actor_end = actor_base + 0xbf

local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin, start = in2["Coin 1"], in2["1 Player Start"]
local left, right = in0["P1 Left"], in0["P1 Right"]
local up, down = in0["P1 Up"], in0["P1 Down"]
local gun, attack, jump = in0["P1 Button 1"], in0["P1 Button 2"], in0["P1 Button 3"]

local samples = assert(io.open(root .. "/target_actor_samples.tsv", "w"))
samples:write("source_frame\tstate\tclass\tsub_state\taction\ttype\tanim\ttimer\thealth\thit\n")

local frame = 0
local active = false
local watchpoints_installed = false

local function u16(address)
    return program:read_u16(address)
end

local function u32(address)
    return program:read_u32(address)
end

local function s16(value)
    return value >= 0x8000 and value - 0x10000 or value
end

local function actor_sample()
    return {
        program:read_u8(actor_base + 0x00),
        program:read_u8(actor_base + 0x02),
        u16(actor_base + 0x04),
        u16(actor_base + 0x06),
        program:read_u8(actor_base + 0x08),
        u32(actor_base + 0x1c),
        u16(actor_base + 0x2a),
        s16(u16(actor_base + 0x40)),
        program:read_u8(actor_base + 0x2c),
    }
end

local function clear_inputs()
    coin:clear_value(); start:clear_value(); left:clear_value(); right:clear_value()
    up:clear_value(); down:clear_value(); gun:clear_value(); attack:clear_value()
    jump:clear_value()
end

-- This matches the frozen vertical-slice schedule.  The callback captures the
-- interval that follows the source sample named by `frame`, never a synthetic
-- empty epoch after the final sample.
local function apply_schedule(f)
    local function drive(field, enabled)
        if enabled then field:set_value(1) else field:clear_value() end
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
    if f >= 4420 and f <= 5469 then attack_on = (f - 4420) % 45 < 5 end
    drive(coin, coin_on); drive(start, start_on); drive(left, left_on)
    drive(right, right_on); drive(gun, gun_on); drive(attack, attack_on)
    drive(jump, jump_on)
end

local function watch_action(field)
    -- This is MAME's native debugger watchpoint path: `wpaddr`, `wpdata`,
    -- `pc`, and the live address registers describe an individual executed
    -- store, rather than a PC merely observed somewhere in the epoch.
    return string.format(
        "logerror \"AVP_HIT_KO_WP capture_start=%%d field=%s addr=%%08X data=%%08X pc=%%08X a0=%%08X a1=%%08X a2=%%08X a6=%%08X a7=%%08X\\n\",%d,wpaddr,wpdata,pc,a0,a1,a2,a6,a7 ; g",
        field, first_frame)
end

local function install_watchpoints()
    if watchpoints_installed then return end
    watchpoints_installed = true
    local fields = {
        {"state", 0x00, 1}, {"sub_state", 0x04, 2}, {"action", 0x06, 2},
        {"anim_record", 0x1c, 4}, {"anim_timer", 0x2a, 2},
        {"health", 0x40, 2}, {"hit_value", 0x2c, 1},
    }
    for _, item in ipairs(fields) do
        cpu_debug:wpset(program, "w", actor_base + item[2], item[3], nil,
            watch_action(item[1]))
    end
end

local function mark_interval()
    -- Keep source sample and executed interval alignment in the same private
    -- log as the watchpoints.  The store events following this marker are the
    -- instructions that produce semantic sample `frame + 1`.
    debugger:command(string.format(
        "logerror \"AVP_HIT_KO_INTERVAL_START %d\\n\" ; g", frame))
end

hit_ko_context_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    apply_schedule(frame)
    if frame >= 4200 then program:write_u8(0xff83c1, 0x65) end
    if frame >= first_frame and frame <= last_frame then
        samples:write(string.format("%d\t%s\n", frame, table.concat(actor_sample(), "\t")))
    end
    if frame == first_frame then install_watchpoints() end
    active = frame >= first_frame and frame < last_frame
    if active then mark_interval() end
    if frame == last_frame then
        active = false
        clear_inputs()
        samples:close()
        machine:exit()
    end
end)

debugger.execution_state = "run"
