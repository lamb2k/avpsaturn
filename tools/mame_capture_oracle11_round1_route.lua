-- ORACLE-11 route-controller, encounter lifecycle and global RNG provenance.
-- Input and completion are supplied by the accepted route-wide player-audio
-- harness. Raw evidence remains private under .deps/mame.
local machine=manager.machine
local maincpu=machine.devices[":maincpu"]
local program=maincpu.spaces["program"]
local opcodes=maincpu.spaces["opcodes"]
local root=assert(os.getenv("AVSP_ORACLE11_ROUTE_ROOT"))
local frame=0
local first,last=1972,15193
local global=0xff8000
local player=0xff8380
local pool,stride,count=0xff9580,0xc0,57
local route=assert(io.open(root.."/route_samples.tsv","w"))
local writes=assert(io.open(root.."/route_writes.tsv","w"))
local life=assert(io.open(root.."/lifecycle_writes.tsv","w"))
local rng=assert(io.open(root.."/route_rng.tsv","w"))
route:write("frame\tg8000\tg8002\tg8004\tg8008\tg800c\tg8010\tg8014\tg8018\tg801a\tg801c\tg81a8\tg81f2\tg8248\tg8278\tg827c\tplayer_active\tplayer_state\tplayer_phase\tplayer_x\tplayer_z\tpopulation\n")
writes:write("frame\taddress\tpc\ta5\ta6\td0\td1\td2\td3\told\tdata\tmask\treturn0\treturn1\treturn2\n")
life:write("frame\tslot\tinner\tpc\ta5\ta6\told_active\told_class\told_type\told_state\told_phase\tdata\tmask\treturn0\treturn1\treturn2\n")
rng:write("frame\tpc\ta5\ta6\towner_kind\towner_class\towner_type\towner_state\towner_phase\tseed\treturn0\treturn1\treturn2\n")
local function u8(a)return program:read_u8(a)end
local function u16(a)return program:read_u16(a)end
local function u32(a)return program:read_u32(a)end
local function s16(v)return v>=0x8000 and v-0x10000 or v end
local function stack()
 local sr=maincpu.state["SR"].value&0xffff
 local sp=(sr&0x2000)~=0 and (maincpu.state["SP"].value&0xffffff) or (maincpu.state["USP"].value&0xffffff)
 return u32(sp)&0xffffff,u32(sp+4)&0xffffff,u32(sp+8)&0xffffff
end
local function actor_base(a)
 if a==player then return a,"player" end
 if a>=pool and a<pool+count*stride and ((a-pool)%stride)==0 then return a,"actor" end
 return nil,"global"
end
local route_counts={}
local function count_writer(address,pc)
 local key=string.format("%06x:%06x",address,pc)
 local row=route_counts[key]
 if row then row.last=frame;row.count=row.count+1
 else route_counts[key]={first=frame,last=frame,count=1} end
end
oracle11_route_writes=program:install_write_tap(global,global+0x2ff,"oracle11_route_writes",function(offset,data,mask)
 if frame<first or frame>last then return end
 local address=offset&0xffffff;local pc=maincpu.state["PC"].value&0xffffff
 count_writer(address,pc)
 -- These fields own the global route state machine, scene/subscene selectors,
 -- camera/route coordinates, withdrawal, load and presentation handshakes.
 -- Record every write so no boundary is inferred from a sampled frame.
 local r0,r1,r2=stack()
 writes:write(string.format("%d\t%06x\t%06x\t%06x\t%06x\t%08x\t%08x\t%08x\t%08x\t%08x\t%08x\t%08x\t%06x\t%06x\t%06x\n",
  frame,address,pc,maincpu.state["A5"].value&0xffffff,maincpu.state["A6"].value&0xffffff,
  maincpu.state["D0"].value&0xffffffff,maincpu.state["D1"].value&0xffffffff,
  maincpu.state["D2"].value&0xffffffff,maincpu.state["D3"].value&0xffffffff,
  u32(address&0xfffffc),data&0xffffffff,mask&0xffffffff,r0,r1,r2))
end)
oracle11_route_lifecycle=program:install_write_tap(pool,pool+count*stride-1,"oracle11_route_lifecycle",function(offset,data,mask)
 if frame<first or frame>last then return end
 local relative=offset-pool;local inner=relative%stride
 if inner>1 then return end
 local b=pool+math.floor(relative/stride)*stride;local r0,r1,r2=stack()
 life:write(string.format("%d\t%06x\t%02x\t%06x\t%06x\t%06x\t%d\t%02x\t%02x\t%d\t%d\t%08x\t%08x\t%06x\t%06x\t%06x\n",
  frame,b,inner,maincpu.state["PC"].value&0xffffff,maincpu.state["A5"].value&0xffffff,
  maincpu.state["A6"].value&0xffffff,u8(b),u8(b+2),u8(b+8),u16(b+4),u16(b+6),
  data&0xffffffff,mask&0xffffffff,r0,r1,r2))
end)
oracle11_route_rng=opcodes:install_read_tap(0x017c5e,0x017c5f,"oracle11_route_rng",function()
 if frame<first or frame>last then return end
 local a6=maincpu.state["A6"].value&0xffffff;local b,kind=actor_base(a6)
 local class,type_,state,phase=0,0,0,0
 if b then class,type_,state,phase=u8(b+2),u8(b+8),u16(b+4),u16(b+6) end
 local r0,r1,r2=stack();rng:write(string.format("%d\t%06x\t%06x\t%06x\t%s\t%02x\t%02x\t%d\t%d\t%04x\t%06x\t%06x\t%06x\n",
  frame,maincpu.state["PC"].value&0xffffff,maincpu.state["A5"].value&0xffffff,a6,kind,
  class,type_,state,phase,u16(0xff81a8),r0,r1,r2))
end)
local function population()
 local n=0
 for i=0,count-1 do if u8(pool+i*stride)~=0 then n=n+1 end end
 return n
end
local function flush_counts()
 local out=assert(io.open(root.."/route_writer_summary.tsv","w"))
 out:write("address\tpc\tfirst_frame\tlast_frame\tcount\n")
 local keys={};for key in pairs(route_counts)do keys[#keys+1]=key end;table.sort(keys)
 for _,key in ipairs(keys)do local a,pc=key:match("([^:]+):([^:]+)");local row=route_counts[key]
  out:write(table.concat({a,pc,row.first,row.last,row.count},"\t").."\n") end
 out:close()
end
oracle11_route_frame=emu.add_machine_frame_notifier(function()
 frame=frame+1
 if frame>=first and frame<=last then route:write(string.format("%d\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%04x\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n",
  frame,u16(global),u16(global+2),u16(global+4),u16(global+8),u16(global+0xc),u16(global+0x10),
  u16(global+0x14),u16(global+0x18),u16(global+0x1a),u16(global+0x1c),u16(0xff81a8),
  u16(0xff81f2),u16(0xff8248),s16(u16(0xff8278)),s16(u16(0xff827c)),u8(player),
  u16(player+4),u16(player+6),s16(u16(player+0x10)),s16(u16(player+0x18)),population())) end
 if frame==18000 then flush_counts();route:close();writes:close();life:close();rng:close() end
end)
dofile("tools/mame_capture_oracle11_player_audio.lua")
