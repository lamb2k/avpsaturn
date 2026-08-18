-- Deterministic cold-boot probe for the authorized MSHvSF CPS-2 reference.
-- It records input edges and low-cadence screenshots only to locate the first
-- stable Ryu gameplay state. A later capture will use cadence 1 around actions.
local machine = manager.machine
local screen = machine.screens[":screen"]
local maincpu = machine.devices[":maincpu"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local button1 = in0["P1 Button 1"]
local frame = 0
local capture_root = ".deps/mame/mshvsf_boot_probe"
local events = assert(io.open(capture_root .. "/events.tsv", "w"))
events:write("frame\tevent\tpc\n")

local function set_input(field, value, event)
    field:set_value(value)
    events:write(string.format("%d\t%s\t%08x\n", frame, event,
        maincpu.state["PC"].value))
    events:flush()
end

local function pulse(field, first, last, name)
    if frame == first then set_input(field, 1, name .. "_down") end
    if frame == last then set_input(field, 0, name .. "_up") end
end

mshvsf_boot_probe_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1

    pulse(coin, 600, 603, "coin_1")
    pulse(coin, 630, 633, "coin_2")
    pulse(start, 690, 693, "start")

    -- Repeated light-punch confirms are exploratory and deterministic. The
    -- low-cadence screenshots establish which pulses map to title skip,
    -- character selection, team selection, and gameplay entry.
    for confirm_frame = 750, 1470, 120 do
        pulse(button1, confirm_frame, confirm_frame + 4,
            "button1_" .. tostring(confirm_frame))
    end

    if frame >= 480 and frame <= 1800 and frame % 60 == 0 then
        screen:snapshot(string.format("mshvsf_boot_probe/frame_%05d.png", frame))
    end

    if frame == 1801 then
        coin:clear_value()
        start:clear_value()
        button1:clear_value()
        events:close()
        machine:exit()
    end
end)
