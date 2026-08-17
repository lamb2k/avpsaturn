-- Map the CPS2 boot sequence frame by frame without storing images.
--
-- Parity work needs to know exactly which source frame each state begins and
-- ends on, from reset through the Round 1 title. Storing every frame as a PNG
-- would cost roughly a gigabyte, so this records a cheap per-frame screen
-- checksum instead. Equal checksums mean a held frame; a change marks a new
-- unique frame. Boundaries found here tell later captures exactly which narrow
-- windows are worth storing as real pixels.
--
-- The input schedule is byte-identical to tools/mame_capture_frontend.lua so
-- every frame number lines up with the existing frontend evidence.
local machine = manager.machine
local screen = machine.screens[":screen"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local gun = in0["P1 Button 1"]
local capture_root = ".deps/mame/timeline"
local metadata = assert(io.open(capture_root .. "/timeline.tsv", "w"))
metadata:write("frame\tsum1\tsum2\tcoin\tstart\tgun\n")

local frame = 0
local coin_down = 0
local start_down = 0
local gun_down = 0
local last_frame = 2400
local stride = 509
local modulus = 4294967291

-- Fletcher-style checksum over a strided sample of the final screen bitmap.
-- The stride keeps this fast enough to run every frame; it is used only to
-- detect change, never as proof that two frames are identical.
local function checksum(pixels)
    local sum1 = 0
    local sum2 = 0
    local size = #pixels
    for index = 1, size, stride do
        sum1 = (sum1 + string.byte(pixels, index)) % modulus
        sum2 = (sum2 + sum1) % modulus
    end
    return sum1, sum2
end

timeline_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1

    if frame >= 1200 and frame <= 2400 then
        if (frame - 1200) % 180 == 0 then
            coin:set_value(1)
            coin_down = 1
        end
        if (frame - 1200) % 180 == 3 then
            coin:clear_value()
            coin_down = 0
        end
        if (frame - 1200) % 180 == 30 then
            start:set_value(1)
            start_down = 1
        end
        if (frame - 1200) % 180 == 33 then
            start:clear_value()
            start_down = 0
        end
    end

    if frame >= 1500 and frame < 4200 then
        if frame % 90 == 0 then
            gun:set_value(1)
            gun_down = 1
        end
        if frame % 90 == 5 then
            gun:clear_value()
            gun_down = 0
        end
    end

    local pixels = screen:pixels()
    local sum1, sum2 = checksum(pixels)
    metadata:write(string.format("%d\t%d\t%d\t%d\t%d\t%d\n",
        frame, sum1, sum2, coin_down, start_down, gun_down))

    if frame == last_frame then
        coin:clear_value()
        start:clear_value()
        gun:clear_value()
        metadata:close()
        machine:exit()
    end
end)
