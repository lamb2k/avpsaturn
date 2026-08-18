-- Bounded full-work-RAM probe for the actor-local collision falsification test.
--
-- Why this exists: the Round 1 debug-overlay capture
-- (tools/mame_capture_round1_debug_overlays.lua) dumps only 0xFF8300..0xFF8FFF
-- and 0xFFA000..0xFFBFFF, so the enemy actor slots BELOW 0xFFA000 are absent.
-- Collision attribution needs every actor that can own an attack box, so this
-- probe replays that route byte-for-byte and dumps the complete work RAM
-- instead, over a bounded frame window, with no screenshots.
--
-- The route is copied verbatim from the overlay capture so the same hit events
-- occur at the same source frames and the two evidence sets are comparable.
--
-- Environment:
--   AVSP_CP_CAPTURE_ROOT  output directory (required)
--   AVSP_CP_STATE_NAME    debug-enabled frame-4200 state (required)
--   AVSP_CP_ROW2          required DIP row-2 bits (required)
--   AVSP_CP_FIRST_FRAME   first source frame to dump (default 4201)
--   AVSP_CP_FINAL_FRAME   last source frame to dump (default 5500)

local machine = manager.machine
local program = machine.devices[":maincpu"].spaces["program"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields

local capture_root = assert(os.getenv("AVSP_CP_CAPTURE_ROOT"))
local state_name = assert(os.getenv("AVSP_CP_STATE_NAME"))
local requested_row2 = tonumber(assert(os.getenv("AVSP_CP_ROW2")))
local first_frame = tonumber(os.getenv("AVSP_CP_FIRST_FRAME") or "4201")
local final_frame = tonumber(os.getenv("AVSP_CP_FINAL_FRAME") or "5500")
local base_frame = 4200

local DEBUG_ENABLE = 0xff81c7
local DIP_ROW1 = 0xff806c
local DIP_ROW2 = 0xff806d
local PLAYER_HEALTH = 0xff83c1
local RAM_FIRST = 0xff8000
local RAM_LAST = 0xffffff
local SAMPLE_SIZE = RAM_LAST - RAM_FIRST + 1

local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local right = in0["P1 Right"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]

local frame = 0
local boot_frames = 0
local state_loaded = false
local sample_index = 0
local metadata = assert(io.open(capture_root .. "/samples.tsv", "w"))
local ram_file = assert(io.open(capture_root .. "/workram.bin", "wb"))
metadata:write(
	"frame\tsample_index\tfile_offset\tdebug_enable\tdip_row1\tdip_row2\tplayer_health\n")

local layout = assert(io.open(capture_root .. "/ram_layout.tsv", "w"))
layout:write("block\tfirst\tsize\toffset_in_sample\n")
layout:write(string.format("workram\t%06x\t%d\t0\n", RAM_FIRST, SAMPLE_SIZE))
layout:write(string.format("sample\t000000\t%d\t0\n", SAMPLE_SIZE))
layout:close()

local function capture(absolute_frame)
	local file_offset = sample_index * SAMPLE_SIZE
	local enable = program:read_u8(DEBUG_ENABLE)
	local row1 = program:read_u8(DIP_ROW1)
	local row2 = program:read_u8(DIP_ROW2)
	local health = program:read_u8(PLAYER_HEALTH)
	if enable == 0 or (row2 & requested_row2) ~= requested_row2 then
		error(string.format(
			"debug flags lost at frame %d: master=%02x row2=%02x",
			absolute_frame, enable, row2))
	end
	ram_file:write(program:read_range(RAM_FIRST, RAM_LAST, 8))
	metadata:write(string.format("%d\t%d\t%d\t%02x\t%02x\t%02x\t%02x\n",
		absolute_frame, sample_index, file_offset, enable, row1, row2, health))
	sample_index = sample_index + 1
end

collision_probe_post_load = emu.add_machine_post_load_notifier(function()
	frame = 0
	state_loaded = true
	print("COLLISION_PROBE loaded " .. state_name)
end)

collision_probe_subscription = emu.add_machine_frame_notifier(function()
	if not state_loaded then
		boot_frames = boot_frames + 1
		if boot_frames == 1 then
			machine:load(state_name)
		end
		if boot_frames > 600 then
			error("debug-enabled frame-4200 state never loaded")
		end
		return
	end

	frame = frame + 1
	local absolute_frame = base_frame + frame
	local health = program:read_u8(PLAYER_HEALTH)

	-- Route copied verbatim from mame_capture_round1_debug_overlays.lua.
	if frame == 1 then right:set_value(1) end
	if frame % 45 == 0 then gun:set_value(1) end
	if frame % 45 == 7 then gun:clear_value() end
	if frame % 180 == 0 then attack:set_value(1) end
	if frame % 180 == 8 then attack:clear_value() end
	if frame % 240 == 0 then jump:set_value(1) end
	if frame % 240 == 8 then jump:clear_value() end

	if frame % 600 == 30 then coin:set_value(1) end
	if frame % 600 == 34 then coin:clear_value() end
	if (health == 0 or health >= 0x80) and frame % 120 == 30 then
		start:set_value(1)
	end
	if frame % 120 == 34 then start:clear_value() end

	if absolute_frame >= first_frame and absolute_frame <= final_frame then
		capture(absolute_frame)
	end
	if absolute_frame > final_frame then
		metadata:close()
		ram_file:close()
		machine:exit()
	end
end)
