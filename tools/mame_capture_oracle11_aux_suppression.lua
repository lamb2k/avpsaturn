-- One real full-route class/type suppression control.
local machine=manager.machine;local cpu=machine.devices[":maincpu"];local program=cpu.spaces["program"]
local root=assert(os.getenv("AVSP_ORACLE11_AUX_SUPPRESS_ROOT"));local target_type=assert(tonumber(os.getenv("AVSP_ORACLE11_AUX_SUPPRESS_TYPE")))
local target_class=assert(tonumber(os.getenv("AVSP_ORACLE11_AUX_SUPPRESS_CLASS")));local frame,count,first=0,0,nil
local pools={{type=16,base=0xffa480,stride=0x80,count=20},{type=20,base=0xffae80,stride=0x80,count=16},{type=24,base=0xffb680,stride=0x80,count=32}}
local out=assert(io.open(root.."/suppression.tsv","w"));out:write("type\tclass\tsuppression_count\tfirst_frame\n")
oracle11_aux_suppress_frame=emu.add_machine_frame_notifier(function()frame=frame+1;for _,p in ipairs(pools)do if p.type==target_type then for i=0,p.count-1 do local b=p.base+i*p.stride;if program:read_u8(b)~=0 and program:read_u8(b+2)==target_class and program:read_u8(b+8)==target_type then program:write_u8(b,0);count=count+1;if not first then first=frame end end end end end;if frame==18000 then out:write(string.format("%d\t%02x\t%d\t%d\n",target_type,target_class,count,first or 0));out:close()end end)
dofile("tools/mame_capture_oracle11_player_audio.lua")
