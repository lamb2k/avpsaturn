-- Watch the CPS2 object write buffer for one street-alien actor's five-slot
-- emission, on stock MAME 0.289 (stock debugger + frame notifier).
--
-- Loads a frame-4200 anchor state and runs only the short window that covers
-- the two target source frames, so the instrumented (debugger) run stays small
-- and fast. The anchor state is produced separately by
-- tools/mame_save_replay_state.lua (a fast, debugger-free cold boot); do NOT
-- point this watcher at avspu_stage1_debug_hitboxes, whose debug master leaves
-- the street alien idle.
--
-- SOURCE-FRAME MAPPING. The anchor state is saved in the notifier for source
-- frame AVP_OE_STATE_FRAME, so the first frame emulated after the load is
-- source frame AVP_OE_STATE_FRAME + 1, and notifier call k (k >= 2) ends
-- source frame AVP_OE_STATE_FRAME + k - 1. Verified byte-for-byte against the
-- oracle route's own work-RAM dumps (.deps/mame/enemy_actions/workram_*.bin).
--
-- POST-ANCHOR ROUTE. The oracle fixture was captured by
-- tools/mame_capture_enemy_actions.lua, whose route does not stop at the anchor
-- frame: it presses P1 Left over a short window and holds the P1 health byte
-- for the whole observation window. Replaying the anchor state without that
-- tail is a DIFFERENT route (the player never turns, so the scroll origin and
-- the alien's approach diverge). The tail is replayed here, is fully
-- parameterized, and carries no expected object values.
--
-- Installs exactly N word write watchpoints (N = AVP_OE_WORDS) at the object
-- list base plus one bank-select watchpoint. Each object write logs
-- addr/data/pc and the emitter's data registers (a0,a1,a4,a5,a6) to error.log.
-- Post-frame workram is dumped every frame in the window; both the logical
-- write buffer (0x708000..0x709FFF) and the ACTIVE/display object share are
-- dumped every frame in the window. The oracle instrument
-- (mame_capture_enemy_actions.lua) sampled the ACTIVE share, so objact_*.bin is
-- the like-for-like comparison surface and objbuf_*.bin is the writer view.
-- Dumps are named by SOURCE frame.
--
-- Scenario parameters via environment:
--   AVP_OE_STATE         anchor state name (required)
--   AVP_OE_STATE_FRAME   source frame of the anchor state (default 4200)
--   AVP_OE_FRAME_A       first target source frame (default 4214)
--   AVP_OE_FRAME_B       second target source frame (default 4253)
--   AVP_OE_OBJ_BASE      object list base address (default 0x7080A0)
--   AVP_OE_WORDS         object words to watch (default 20)
--   AVP_OE_BANK_REG      bank-select register (default 0x8040E0)
--   AVP_OE_ACTOR         actor base address (default 0xFFA000)
--   AVP_OE_RAWDIR        raw output dir (default .deps/mame/object_emission)
--   AVP_OE_TAIL_HOLD_ADDR   byte address held every frame (default FF83C1)
--   AVP_OE_TAIL_HOLD_VALUE  byte value written there (default 65)
--   AVP_OE_TAIL_DIR         P1 direction pressed after the anchor
--                           (default Left; empty string disables)
--   AVP_OE_TAIL_DIR_ON      source frame the direction goes down (default 4201)
--   AVP_OE_TAIL_DIR_OFF     source frame the direction is released (default 4210)

local machine = manager.machine
local debugger = assert(machine.debugger)
local program = machine.devices[":maincpu"].spaces["program"]

local state_name = os.getenv("AVP_OE_STATE")
local state_frame = tonumber(os.getenv("AVP_OE_STATE_FRAME") or "", 10) or 4200
local frame_a = tonumber(os.getenv("AVP_OE_FRAME_A") or "", 10) or 4214
local frame_b = tonumber(os.getenv("AVP_OE_FRAME_B") or "", 10) or 4253
local obj_base = tonumber(os.getenv("AVP_OE_OBJ_BASE") or "", 16) or 0x7080A0
local word_count = tonumber(os.getenv("AVP_OE_WORDS") or "", 10) or 20
local bank_reg = tonumber(os.getenv("AVP_OE_BANK_REG") or "", 16) or 0x8040E0
local actor_base = tonumber(os.getenv("AVP_OE_ACTOR") or "", 16) or 0xFFA000
local raw_dir = os.getenv("AVP_OE_RAWDIR") or ".deps/mame/object_emission"
local hold_addr = tonumber(os.getenv("AVP_OE_TAIL_HOLD_ADDR") or "", 16) or 0xFF83C1
local hold_value = tonumber(os.getenv("AVP_OE_TAIL_HOLD_VALUE") or "", 16) or 0x65
local tail_dir = os.getenv("AVP_OE_TAIL_DIR") or "Left"
local tail_dir_on = tonumber(os.getenv("AVP_OE_TAIL_DIR_ON") or "", 10) or 4201
local tail_dir_off = tonumber(os.getenv("AVP_OE_TAIL_DIR_OFF") or "", 10) or 4210

if not state_name then
	error("AVP_OE_STATE is required")
end
if word_count % 2 ~= 0 then
	error("AVP_OE_WORDS must be even")
end
if word_count + 1 > 34 then
	error("AVP_OE_WORDS + 1 bank watchpoint must stay under the 34 ceiling")
end
if frame_a <= state_frame or frame_b <= frame_a then
	error("Require state_frame < AVP_OE_FRAME_A < AVP_OE_FRAME_B")
end

-- Notifier call k ends source frame state_frame + k - 1, so the call that ends
-- source frame f is k = f - state_frame + 1.
local function call_for(source) return source - state_frame + 1 end
local wp_first_call = call_for(frame_a - 2)     -- install so watchpoints are live at A
local dump_first_call = call_for(frame_a - 1)
local dump_last_call = call_for(frame_b + 1)
local wp_last_call = call_for(frame_b + 2)

local in0 = machine.ioport.ports[":IN0"].fields
local dir_field = nil
if tail_dir ~= "" then
	dir_field = in0["P1 " .. tail_dir]
	if not dir_field then
		error("AVP_OE_TAIL_DIR names no P1 field: " .. tail_dir)
	end
end

local debug = nil   -- lazy; only needed once watchpoints install
local wp_installed = false
local function install_watchpoints()
	if wp_installed then return end
	wp_installed = true
	debug = assert(machine.devices[":maincpu"].debug)
	for i = 0, word_count - 1 do
		local action = string.format(
			'logerror "AVP_OE_OBJ addr=%%08X data=%%08X pc=%%08X a0=%%08X a1=%%08X a4=%%08X a5=%%08X a6=%%08X\\n",wpaddr,wpdata,pc,a0,a1,a4,a5,a6 ; g',
			obj_base + i * 2)
		debug:wpset(program, "w", obj_base + i * 2, 2, nil, action)
	end
	local bank_action = string.format(
		'logerror "AVP_OE_BANK addr=%%08X data=%%08X pc=%%08X a5=%%08X\\n",wpaddr,wpdata,pc,a5 ; g',
		bank_reg)
	debug:wpset(program, "w", bank_reg, 2, nil, bank_action)
end

local bank = 1
program:install_write_tap(bank_reg, bank_reg + 1, "avp_oe_bank", function(offset, data, mask)
	bank = data & 1
end)

local function be16(b, off)
	-- MAME read_range returns a 1-based Lua string; offset is 0-based.
	return (b:byte(off + 1) << 8) | b:byte(off + 2)
end
local function be32(b, off)
	return (b:byte(off + 1) << 24) | (b:byte(off + 2) << 16)
		| (b:byte(off + 3) << 8) | b:byte(off + 4)
end
local function dump(name, data)
	local f = assert(io.open(raw_dir .. "/" .. name, "wb"))
	f:write(data)
	f:close()
end
local function dump_share(name, share)
	local f = assert(io.open(raw_dir .. "/" .. name, "wb"))
	for offset = 0, share.size - 2, 2 do
		local w = share:read_u16(offset)
		f:write(string.char((w >> 8) & 0xff, w & 0xff))
	end
	f:close()
end

local frame = 0   -- notifier call count (1 = the call that requests the load)
oe_subscription = emu.add_machine_frame_notifier(function()
	frame = frame + 1
	if frame == 1 then
		machine:load(state_name)
		return
	end
	local source = state_frame + frame - 1

	-- Post-anchor route tail of the oracle instrument, replayed verbatim.
	if dir_field then
		if source == tail_dir_on then dir_field:set_value(1) end
		if source == tail_dir_off then dir_field:clear_value() end
	end
	program:write_u8(hold_addr, hold_value)

	if frame == wp_first_call then
		install_watchpoints()
	end
	if frame >= dump_first_call and frame <= dump_last_call then
		local wram = program:read_range(0xff8000, 0xffffff, 8)
		dump(string.format("workram_%05d.bin", source), wram)
		-- The logical write buffer (what the emitter just wrote through
		-- 0x708000) and the ACTIVE/display share (what the oracle instrument
		-- sampled) are both dumped: the alien's list offset is run-dependent
		-- and the two banks hold different lists, so the comparison surface
		-- must be stated, not assumed.
		dump(string.format("objbuf_%05d.bin", source),
			program:read_range(0x708000, 0x709fff, 8))
		local active = (bank == 0) and machine.memory.shares[":objram1"]
			or machine.memory.shares[":objram2"]
		dump_share(string.format("objact_%05d.bin", source), active)
		local ao = actor_base - 0xff8000
		print(string.format(
			"AVP_OE_MARKER source=%d bank=%d anim=%08x type=%d facing=%d p50=%08x X=%d Y=%d",
			source, bank, be32(wram, ao + 0x1c),
			(be16(wram, ao + 0x08) >> 8) & 0xff, (be16(wram, ao + 0x0f) >> 8) & 0xff,
			be32(wram, ao + 0x50), be16(wram, ao + 0x10), be16(wram, ao + 0x14)))
	end
	if frame == wp_last_call then
		for i = 0, word_count do
			local addr = (i < word_count) and (obj_base + i * 2) or bank_reg
			debug:wpdel(program, addr)
		end
		if dir_field then dir_field:clear_value() end
		machine:exit()
	end
end)

debugger.execution_state = "run"
