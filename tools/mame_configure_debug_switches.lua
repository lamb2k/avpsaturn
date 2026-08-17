-- Persist the development hardware type and active-low debug DIPs into an
-- isolated MAME cfg directory.  The real capture is a separate launch, so the
-- game sees these values before its first boot-initialisation instruction.
local machine = manager.machine
local hw_type = machine.ioport.ports[":HW_TYPE"].fields["Hardware"]
local dswa = machine.ioport.ports[":DSWA"].fields
local dswb = machine.ioport.ports[":DSWB"].fields
local frame = 0

hw_type.user_value = 1
dswa["1-1"].user_value = 1
dswb["2-6"].user_value = 0
dswb["2-7"].user_value = 0

debug_switch_config_subscription = emu.add_machine_frame_notifier(function()
    frame = frame + 1
    if frame == 1 then
        print(string.format(
            "DEBUG_SWITCH_CONFIG hw=%02x dswa=%02x dswb=%02x",
            machine.ioport.ports[":HW_TYPE"]:read(),
            machine.ioport.ports[":DSWA"]:read(),
            machine.ioport.ports[":DSWB"]:read()))
        machine:exit()
    end
end)
