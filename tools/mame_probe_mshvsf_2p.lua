-- Low-cadence probe for a deterministic two-player MSHvSF route. Four credits
-- start both sides; repeated light-punch confirms establish the exact frontend
-- schedule before the high-cadence vertical-slice capture is updated.
local machine = manager.machine
local screen = machine.screens[":screen"]
local maincpu = machine.devices[":maincpu"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start1 = in2["1 Player Start"]
local start2 = in2["2 Players Start"]
local button1 = in0["P1 Button 1"]
local button2 = in0["P2 Button 1"]
local frame = 0
local capture_root = ".deps/mame/mshvsf_boot_probe_2p"
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

mshvsf_boot_probe_2p_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1

    for coin_frame = 600, 690, 30 do
        pulse(coin, coin_frame, coin_frame + 3,
            "coin_" .. tostring(math.floor((coin_frame - 600) / 30) + 1))
    end
    pulse(start1, 720, 723, "start_p1")
    pulse(start2, 750, 753, "start_p2")

    for confirm_frame = 810, 1770, 120 do
        pulse(button1, confirm_frame, confirm_frame + 4,
            "p1_button1_" .. tostring(confirm_frame))
        pulse(button2, confirm_frame + 15, confirm_frame + 19,
            "p2_button1_" .. tostring(confirm_frame + 15))
    end

    if frame >= 480 and frame <= 2220 and frame % 60 == 0 then
        screen:snapshot(string.format("mshvsf_boot_probe_2p/frame_%05d.png", frame))
    end

    if frame == 2221 then
        coin:clear_value()
        start1:clear_value()
        start2:clear_value()
        button1:clear_value()
        button2:clear_value()
        events:close()
        machine:exit()
    end
end)
