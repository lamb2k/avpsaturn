-- Enable Alien vs Predator's own built-in debug overlays.
--
-- The retail ROM still contains Capcom's development tools. Two of them matter
-- for functional parity: hitbox display and stage-collision display. The port
-- currently infers hit windows indirectly, by watching health values change
-- across captured frames. These overlays draw the real boxes, which turns
-- collision from something inferred into something read.
--
-- Flags documented by the sudden-desu.net teardown of the game:
--   0xff81c7  byte, non-zero enables the debug tools at all
--   0xff806c  cached debug DIP row 1: bit0 entity spawner/info, bit1 entity
--             monitor, bit2 player monitor
--   0xff806d  cached debug DIP row 2: bit6 stage collision, bit7 hitboxes
--   0xff806e  cached debug DIP row 3: bit2 extended entity info
--
-- Writing those RAM bytes directly does not work: the game re-caches them from
-- the physical switch inputs every frame, so the writes are overwritten before
-- anything is drawn. MAME exposes the switches as real ioport fields
-- (:DSWA 1-1, :DSWB 2-6, :DSWB 2-7), so drive those instead and let the game
-- populate its own cache.
local machine = manager.machine
local screen = machine.screens[":screen"]
local program = machine.devices[":maincpu"].spaces["program"]
local capture_root = ".deps/mame/debugoverlay"

local DEBUG_ENABLE = 0xff81c7
local DIP_ROW1 = 0xff806c
local DIP_ROW2 = 0xff806d
local DIP_ROW3 = 0xff806e

local ROW2_STAGE_COLLISION = 0x40
local ROW2_HITBOXES = 0x80
local ROW3_EXTENDED_ENTITY_INFO = 0x04

local dswa = machine.ioport.ports[":DSWA"].fields
local dswb = machine.ioport.ports[":DSWB"].fields
local dswc = machine.ioport.ports[":DSWC"].fields

local state_loaded = false
local frame = 0
local boot_frames = 0
local LAST_SAMPLE = 240

local function finish()
    machine:exit()
end

debug_overlay_post_load = emu.add_machine_post_load_notifier(function()
    if state_loaded then return end
    frame = 0
    state_loaded = true
end)

debug_overlay_subscription = emu.add_machine_frame_notifier(function()
    if not state_loaded then
        boot_frames = boot_frames + 1
        if boot_frames > 600 then
            print("DEBUG_OVERLAY_ERROR state never loaded")
            finish()
        end
        return
    end
    frame = frame + 1

    dswa["1-1"]:set_value(1)
    dswb["2-7"]:set_value(1)
    dswb["2-6"]:set_value(1)

    if frame % 30 == 0 then
        screen:snapshot(string.format("debugoverlay/dbg_%05d.png", frame))
        print(string.format("DEBUG_OVERLAY_SAMPLE frame=%d enable=%02x row2=%02x",
            frame, program:read_u8(DEBUG_ENABLE), program:read_u8(DIP_ROW2)))
    end

    if frame >= LAST_SAMPLE then finish() end
end)

machine:load("avspu_stage1_boss_12660")
