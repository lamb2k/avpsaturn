-- Capture the verified cold-boot route densely enough to reconstruct the
-- menu, character-select, and Round 1 transitions rather than shipping only
-- three key stills. This mirrors the input schedule in mame_capture_stage1.lua.
local machine = manager.machine
local screen = machine.screens[":screen"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local gun = in0["P1 Button 1"]
local capture_root = ".deps/mame/frontend"
local metadata = assert(io.open(capture_root .. "/samples.tsv", "w"))
metadata:write("frame\tcoin\tstart\tgun\n")

local frame = 0
local coin_down = 0
local start_down = 0
local gun_down = 0
local first_frame = 1320
local last_frame = 2160
local cadence = 2

local function write_palette(sample_frame)
    local palette = machine.palettes[":palette"]
    local file = assert(io.open(string.format(
        capture_root .. "/palette_%04d.tsv", sample_frame), "w"))
    file:write("index\targb\n")
    for index = 0, palette.entries - 1 do
        file:write(string.format("%04x\t%08x\n",
            index, palette:pen_color(index)))
    end
    file:close()
end

local function write_screen_pixels(sample_frame)
    local pixels, width, height = screen:pixels()
    assert(width == 384 and height == 224,
        "frontend indexed screen dimensions changed")
    local file = assert(io.open(string.format(
        capture_root .. "/pixels_%04d.bin", sample_frame), "wb"))
    file:write(pixels)
    file:close()
end

frontend_capture_subscription = emu.add_machine_frame_notifier(function()
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

    if frame >= first_frame and frame <= last_frame and
        (frame - first_frame) % cadence == 0 then
        screen:snapshot(string.format(
            "frontend/frontend_%04d.png", frame))
        write_screen_pixels(frame)
        write_palette(frame)
        metadata:write(string.format("%d\t%d\t%d\t%d\n",
            frame, coin_down, start_down, gun_down))
    end

    if frame == last_frame + 2 then
        coin:clear_value()
        start:clear_value()
        gun:clear_value()
        metadata:close()
        machine:exit()
    end
end)
