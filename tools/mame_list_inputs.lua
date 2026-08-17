print("AVSPU_INPUTS_BEGIN")
for port_tag, port in pairs(manager.machine.ioport.ports) do
    for field_name, field in pairs(port.fields) do
        print(string.format("%s\t%s\t0x%08x", port_tag, field_name, field.mask))
    end
end
print("AVSPU_INPUTS_END")
