-- Render the verified Stage 1 route through MAME's QSound implementation.
-- The caller supplies -wavwrite and 44100 Hz output. This ignored WAV becomes
-- CD audio track 2 in the private Saturn capability image; it is not committed.
local machine = manager.machine
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local left = in0["P1 Left"]
local right = in0["P1 Right"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]
local frame = 0
local base_frame = 4200
local final_frame = 14220
local state_loaded = false

stage1_audio_post_load_subscription = emu.add_machine_post_load_notifier(function()
    frame = 0
    state_loaded = true
    print("AVSPU_STAGE1_AUDIO loaded verified frame-4200 state")
end)

machine:load("avspu_stage1")

stage1_audio_capture_subscription = emu.add_machine_frame_notifier(function()
    if not state_loaded then return end
    frame = frame + 1
    local absolute_frame = base_frame + frame

    if frame == 1 then right:set_value(1) end
    if frame % 45 == 0 then gun:set_value(1) end
    if frame % 45 == 7 then gun:clear_value() end
    if frame % 180 == 0 then attack:set_value(1) end
    if frame % 180 == 8 then attack:clear_value() end
    if frame % 240 == 0 then jump:set_value(1) end
    if frame % 240 == 8 then jump:clear_value() end
    if frame % 600 == 30 then coin:set_value(1) end
    if frame % 600 == 34 then coin:clear_value() end
    if frame % 600 == 90 then start:set_value(1) end
    if frame % 600 == 94 then start:clear_value() end

    if absolute_frame >= final_frame then
        left:clear_value()
        right:clear_value()
        gun:clear_value()
        attack:clear_value()
        jump:clear_value()
        coin:clear_value()
        start:clear_value()
        print("AVSPU_STAGE1_AUDIO captured through Stage Clear")
        machine:exit()
    end
end)
