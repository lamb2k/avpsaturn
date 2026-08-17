-- Use stock MAME's debugger watchpoint API after the debug-enabled state is
-- loaded.  This traces the ROM routines that write animation pointers and the
-- state/action fields without requiring a custom MAME build.
local machine = manager.machine
local debug = assert(machine.devices[":maincpu"].debug)
local debugger = assert(machine.debugger)
local program = machine.devices[":maincpu"].spaces["program"]
local state_name = os.getenv("AVSP_WATCH_STATE") or
    "avspu_stage1_debug_hitboxes"
local log_path = os.getenv("AVSP_WATCH_LOG") or
    ".deps/mame/watchpoints/actor_writers.log"
local configured = false
local frame_count = 0
local frame_limit = tonumber(os.getenv("AVSP_WATCH_FRAMES") or "120")
local output = assert(io.open(log_path, "w"))

local function action(kind)
    -- The debugger action has access to wpaddr and wpdata.  The Lua callback
    -- is deliberately not used for the write itself; this remains MAME's
    -- native watchpoint path and the action only emits the evidence line.
    return string.format(
        "logerror \"AVP_WP_%s addr=%%08X data=%%08X pc=%%08X\\n\",wpaddr,wpdata,pc ; g",
        kind)
end

local function install_watchpoints()
    if configured then return end
    configured = true
    for base = 0xffa000, 0xffbfc0, 0xc0 do
        debug:wpset(program, "w", base + 0x1c, 4, nil, action("ANIM"))
        debug:wpset(program, "w", base + 0x06, 2, nil, action("ACTION"))
        debug:wpset(program, "w", base + 0x0c, 2, nil, action("STATE"))
    end
    output:write(string.format("configured\tstate=%s\tframes=%d\n",
        state_name, frame_limit))
    output:flush()
end

watch_subscription = emu.add_machine_frame_notifier(function()
    frame_count = frame_count + 1
    if frame_count == 1 then
        -- Loading from the first frame avoids the debugger's initial stop
        -- state. Install watchpoints only after the state has been restored.
        machine:load(state_name)
        install_watchpoints()
        debugger.execution_state = "run"
    end
    if frame_count >= frame_limit then
        output:close()
        machine:exit()
    end
end)

-- The debugger starts paused. Allow the first notifier invocation to perform
-- the state load and install the post-load watchpoints.
debugger.execution_state = "run"
