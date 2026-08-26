-- ORACLE-11 Round 1 boss phase and boss-clear orchestration provenance.
-- The accepted player-audio harness supplies deterministic completion input.
local machine=manager.machine
local cpu=machine.devices[":maincpu"]
local program=cpu.spaces["program"]
local opcodes=cpu.spaces["opcodes"]
local root=assert(os.getenv("AVSP_ORACLE11_BOSS_ROOT"))
local variant=assert(os.getenv("AVSP_ORACLE11_BOSS_VARIANT"))
assert(variant=="baseline" or variant=="suppress-clear-writer")
local frame=0
local first,last=5200,15193
local boss,presentation=0xffa3c0,0xffd180
local samples=assert(io.open(root.."/boss_samples.tsv","w"))
local writes=assert(io.open(root.."/boss_writes.tsv","w"))
local rng=assert(io.open(root.."/boss_rng.tsv","w"))
local clear=assert(io.open(root.."/clear_writes.tsv","w"))
samples:write("frame\trecord\tactive\tclass\ttype\tstate\tphase\tfacing\tx\ty\tz\tanim\ttimer\thealth\tg81f2\tg8008\n")
writes:write("frame\trecord\toffset\tpc\ta5\ta6\told\tdata\tmask\treturn0\treturn1\treturn2\n")
rng:write("frame\trecord\tpc\tstate\tphase\tseed\treturn0\treturn1\treturn2\n")
clear:write("frame\tpc\ta6\tstate\tphase\told\tdata\tmask\tsuppressed\treturn0\treturn1\treturn2\n")
local function u8(a)return program:read_u8(a)end
local function u16(a)return program:read_u16(a)end
local function u32(a)return program:read_u32(a)end
local function s16(v)return v>=0x8000 and v-0x10000 or v end
local function stack()
 local sr=cpu.state["SR"].value&0xffff
 local sp=(sr&0x2000)~=0 and (cpu.state["SP"].value&0xffffff) or (cpu.state["USP"].value&0xffffff)
 return u32(sp)&0xffffff,u32(sp+4)&0xffffff,u32(sp+8)&0xffffff
end
local function name(a6)
 if a6==boss then return "boss" end
 if a6==presentation then return "presentation" end
 return nil
end
local function install_record_tap(base,label)
 return program:install_write_tap(base,base+0xbf,"oracle11_boss_"..label,function(offset,data,mask)
  if frame<first or frame>last then return end
  local r0,r1,r2=stack()
  writes:write(string.format("%d\t%s\t%02x\t%06x\t%06x\t%06x\t%08x\t%08x\t%08x\t%06x\t%06x\t%06x\n",
   frame,label,(offset-base)&0xff,cpu.state["PC"].value&0xffffff,cpu.state["A5"].value&0xffffff,
   cpu.state["A6"].value&0xffffff,u32(offset&0xfffffc),data&0xffffffff,mask&0xffffffff,r0,r1,r2))
 end)
end
oracle11_boss_actor_write=install_record_tap(boss,"boss")
oracle11_boss_presentation_write=install_record_tap(presentation,"presentation")
oracle11_boss_rng=opcodes:install_read_tap(0x017c5e,0x017c5f,"oracle11_boss_rng",function(offset,data,mask)
 if frame<first or frame>last then return data end
 local a6=cpu.state["A6"].value&0xffffff;local label=name(a6)
 if label then local r0,r1,r2=stack();rng:write(string.format("%d\t%s\t%06x\t%d\t%d\t%04x\t%06x\t%06x\t%06x\n",
  frame,label,cpu.state["PC"].value&0xffffff,u16(a6+4),u16(a6+6),u16(0xff81a8),r0,r1,r2)) end
 return data
end)
oracle11_boss_clear=program:install_write_tap(0xff81f2,0xff81f3,"oracle11_boss_clear",function(offset,data,mask)
 if frame<first or frame>last then return end
 local pc=cpu.state["PC"].value&0xffffff;local a6=cpu.state["A6"].value&0xffffff
 local suppress=variant=="suppress-clear-writer" and pc==0x028ea2
 local r0,r1,r2=stack();clear:write(string.format("%d\t%06x\t%06x\t%d\t%d\t%08x\t%08x\t%08x\t%d\t%06x\t%06x\t%06x\n",
  frame,pc,a6,u16(a6+4),u16(a6+6),u32(offset&0xfffffc),data&0xffffffff,mask&0xffffffff,suppress and 1 or 0,r0,r1,r2))
 if suppress then return 0 end
end)
local function emit(label,b)
 samples:write(string.format("%d\t%s\t%d\t%02x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%08x\t%d\t%d\t%04x\t%04x\n",
  frame,label,u8(b),u8(b+2),u8(b+8),u16(b+4),u16(b+6),u8(b+0x0f),s16(u16(b+0x10)),
  s16(u16(b+0x14)),s16(u16(b+0x18)),u32(b+0x1c),u16(b+0x2a),s16(u16(b+0x40)),
  u16(0xff81f2),u16(0xff8008)))
end
oracle11_boss_frame=emu.add_machine_frame_notifier(function()
 frame=frame+1
 if frame>=first and frame<=last then emit("boss",boss);emit("presentation",presentation)end
 if frame==18000 then samples:close();writes:close();rng:close();clear:close()end
end)
dofile("tools/mame_capture_oracle11_player_audio.lua")
