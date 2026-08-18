-- Cold-boot the verified Stage-1 street route and save the frame-4200 state
-- WITHOUT any debugger/watchpoint overhead, so the cold boot runs at full
-- speed. The resulting state avspu_stage1_replay4200 is the authoritative
-- frame-4200 anchor for the street-alien object-emission capture.
--
-- The debug-MASTER state avspu_stage1_debug_hitboxes cannot serve this role:
-- DEBUG_ENABLE=0x01 leaves the street alien idle (X=1333, anim 0x12D8xx). This
-- debug-OFF route reaches the engaging pose (X=1181/1292, anim
-- 0x12EC04/0x12E8EC at source frames 4214/4253).
--
-- Environment:
--   AVSP_REPLAY_STATE  state name to save (default avspu_stage1_replay4200)

local machine = manager.machine
local program = machine.devices[":maincpu"].spaces["program"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields

local state_name = os.getenv("AVSP_REPLAY_STATE") or "avspu_stage1_replay4200"
local anchor_frame = 4200

local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local left = in0["P1 Left"]
local right = in0["P1 Right"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]

local function clear_inputs()
	left:clear_value(); right:clear_value(); coin:clear_value()
	start:clear_value(); gun:clear_value(); attack:clear_value(); jump:clear_value()
end

local frame = 0

-- Byte-for-byte route from the proven enemy-actions replay through 4200.
local function replay_inputs()
	if frame >= 1200 and frame <= 2400 then
		if (frame - 1200) % 180 == 0 then coin:set_value(1) end
		if (frame - 1200) % 180 == 3 then coin:clear_value() end
		if (frame - 1200) % 180 == 30 then start:set_value(1) end
		if (frame - 1200) % 180 == 33 then start:clear_value() end
	end
	if frame >= 1500 and frame < anchor_frame then
		if frame % 90 == 0 then gun:set_value(1) end
		if frame % 90 == 5 then gun:clear_value() end
	end
	if frame == 2600 then right:set_value(1) end
	if frame >= 2600 and frame < anchor_frame then
		if frame % 75 == 0 then gun:set_value(1) end
		if frame % 75 == 6 then gun:clear_value() end
		if frame % 310 == 0 then attack:set_value(1) end
		if frame % 310 == 7 then attack:clear_value() end
		if frame % 430 == 0 then jump:set_value(1) end
		if frame % 430 == 7 then jump:clear_value() end
	end
	if frame == anchor_frame then clear_inputs() end
	if frame == anchor_frame + 1 then left:set_value(1) end
	if frame == anchor_frame + 10 then left:clear_value() end
	if frame >= anchor_frame then program:write_u8(0xff83c1, 0x65) end
end

replay_save_subscription = emu.add_machine_frame_notifier(function()
	frame = frame + 1
	replay_inputs()
	if frame == anchor_frame then
		machine:save(state_name)
	end
	if frame == anchor_frame + 10 then
		clear_inputs()
		machine:exit()
	end
end)
