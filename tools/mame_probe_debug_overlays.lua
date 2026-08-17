-- Cold-boot Alien vs Predator with Capcom's retained debug overlays enabled.
--
-- Important: these switches are active-low and are only exposed when the
-- MAME hardware configuration is Development.  Set all four fields before
-- the first emulated frame.  Loading a production-mode save state is invalid
-- because the game caches its master debug enable during boot initialisation.
local machine = manager.machine
local screen = machine.screens[":screen"]
local program = machine.devices[":maincpu"].spaces["program"]
local in0 = machine.ioport.ports[":IN0"].fields
local in2 = machine.ioport.ports[":IN2"].fields
local hw_type = machine.ioport.ports[":HW_TYPE"].fields["Hardware"]
local dswa = machine.ioport.ports[":DSWA"].fields
local dswb = machine.ioport.ports[":DSWB"].fields
local capture_root = os.getenv("AVSP_DEBUG_CAPTURE_ROOT") or
    ".deps/mame/debugoverlay"
local snapshot_root = assert(capture_root:match("([^/\\]+)$"))
local requested_row2 = tonumber(os.getenv("AVSP_DEBUG_ROW2") or "0xc0")
local state_name = os.getenv("AVSP_DEBUG_STATE_NAME")

local DEBUG_ENABLE = 0xff81c7
local DIP_ROW1 = 0xff806c
local DIP_ROW2 = 0xff806d
local DIP_ROW3 = 0xff806e
local PLAYER_HEALTH = 0xff83c1

local coin = in2["Coin 1"]
local start = in2["1 Player Start"]
local right = in0["P1 Right"]
local gun = in0["P1 Button 1"]
local attack = in0["P1 Button 2"]
local jump = in0["P1 Button 3"]

local frame = 0
local final_frame = 4200
local exit_frame = 4220
local software_switches_injected = false
local metadata = assert(io.open(capture_root .. "/samples.tsv", "w"))
metadata:write(
    "frame\tdebug_enable\tdip_row1\tdip_row2\tdip_row3\tplayer_health\tswitch_injected\n")

local function hold_debug_switches()
    -- Hardware: Development (with debug DIP switches) = 1.
    hw_type.user_value = 1
    -- The development master gate uses DSWA bit 0 high (driver label Off).
    -- The two overlay switches use the active-low On value.  The retained
    -- software-switch bytes are injected once below, never forced per frame.
    dswa["1-1"].user_value = 1
    dswb["2-6"].user_value = 0
    dswb["2-7"].user_value = 0
end

local function sample(sample_frame)
    local enable = program:read_u8(DEBUG_ENABLE)
    local row1 = program:read_u8(DIP_ROW1)
    local row2 = program:read_u8(DIP_ROW2)
    local row3 = program:read_u8(DIP_ROW3)
    local health = program:read_u8(PLAYER_HEALTH)
    metadata:write(string.format("%d\t%02x\t%02x\t%02x\t%02x\t%02x\t%d\n",
        sample_frame, enable, row1, row2, row3, health,
        software_switches_injected and 1 or 0))
    metadata:flush()
    screen:snapshot(string.format(
        snapshot_root .. "/coldboot_%05d.png", sample_frame))
    print(string.format(
        "DEBUG_OVERLAY_SAMPLE frame=%d enable=%02x row1=%02x row2=%02x row3=%02x health=%02x hw=%02x dswa=%02x dswb=%02x",
        sample_frame, enable, row1, row2, row3, health,
        machine.ioport.ports[":HW_TYPE"]:read(),
        machine.ioport.ports[":DSWA"]:read(),
        machine.ioport.ports[":DSWB"]:read()))
end

-- Apply at script initialisation, before the first machine-frame notifier.
hold_debug_switches()

debug_overlay_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    hold_debug_switches()

    -- The retail ROM removed the physical-DIP-to-RAM copy routine.  After
    -- startup RAM initialisation, set the retained software-switch bytes once
    -- and let the game's own 0x1434 routine derive DEBUG_ENABLE.  This is not
    -- a per-frame RAM override: any later change is observable in samples.tsv.
    if frame == 1200 then
        program:write_u8(DIP_ROW1, program:read_u8(DIP_ROW1) | 0x01)
        program:write_u8(DIP_ROW2,
            program:read_u8(DIP_ROW2) | requested_row2)
        software_switches_injected = true
        print("DEBUG_OVERLAY_SWITCH_BYTES injected once at frame=1200")
    end

    -- Byte-for-byte input schedule from mame_capture_frontend.lua.
    if frame >= 1200 and frame <= 2400 then
        if (frame - 1200) % 180 == 0 then coin:set_value(1) end
        if (frame - 1200) % 180 == 3 then coin:clear_value() end
        -- With debug master enabled, Start suicides a live player.  The
        -- frontend route only needs its pre-game pulses; stop them before the
        -- Round 1 player object becomes active.
        if frame <= 1980 and (frame - 1200) % 180 == 30 then
            start:set_value(1)
        end
        if frame <= 1983 and (frame - 1200) % 180 == 33 then
            start:clear_value()
        end
    end
    if frame >= 1500 and frame < 4200 then
        if frame % 90 == 0 then gun:set_value(1) end
        if frame % 90 == 5 then gun:clear_value() end
    end

    -- Continue the established deterministic street route once gameplay starts.
    if frame == 2600 then right:set_value(1) end
    if frame >= 2600 and frame < 4200 then
        if frame % 75 == 0 then gun:set_value(1) end
        if frame % 75 == 6 then gun:clear_value() end
        if frame % 310 == 0 then attack:set_value(1) end
        if frame % 310 == 7 then attack:clear_value() end
        if frame % 430 == 0 then jump:set_value(1) end
        if frame % 430 == 7 then jump:clear_value() end
    end

    if frame == 1 or (frame >= 1200 and frame % 30 == 0) then
        sample(frame)
    end

    if frame == final_frame then
        coin:clear_value()
        start:clear_value()
        right:clear_value()
        gun:clear_value()
        attack:clear_value()
        jump:clear_value()
        if state_name then
            machine:save(state_name)
            print("DEBUG_OVERLAY_STATE saved " .. state_name)
        end
    end
    if frame >= exit_frame then
        metadata:close()
        machine:exit()
    end
end)
