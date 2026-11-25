-- Reusable procedural asset kit for any SatisfyForge Roblox map.
-- Original geometry only; no external model IDs, untrusted free models or paid assets.
local Kit={}
local CollectionService=game:GetService("CollectionService")
local function piece(parent,name,size,cf,color,material,collide)
 local p=Instance.new("Part")
 p.Name=name; p.Size=size; p.CFrame=cf; p.Color=color
 p.Material=material or Enum.Material.SmoothPlastic
 p.Anchored=true; p.CanCollide=collide==true
 p.CanTouch=collide==true
 p.CastShadow=true; p.Parent=parent
 return p
end
local function model(parent,name,kind)
 local m=Instance.new("Model"); m.Name=name
 m:SetAttribute("AssetType",kind); m.Parent=parent
 CollectionService:AddTag(m,"RiftWorldAsset")
 return m
end
function Kit.Tree(parent,pos,variant,scale)
 scale=scale or 1; variant=variant or "oak"
 local m=model(parent,"Tree_"..variant,"Tree")
 local trunkColor=Color3.fromRGB(104,72,53)
 local trunk=piece(m,"Trunk",Vector3.new(2.8,14,2.8)*scale,
  CFrame.new(pos+Vector3.new(0,7*scale,0)),trunkColor,Enum.Material.Wood,true)
 m.PrimaryPart=trunk
 if variant=="pine" then
  for layer=1,3 do
   local cone=Instance.new("Part"); cone.Name="Pine Crown"
   cone.Shape=Enum.PartType.Ball
   cone.Size=Vector3.new(13,9,13)*scale
   cone.Position=pos+Vector3.new(0,(12+layer*4)*scale,0)
   cone.Color=Color3.fromRGB(29,110+layer*13,90)
   cone.Material=Enum.Material.Grass; cone.Anchored=true; cone.CanCollide=false
   cone.Parent=m
  end
 elseif variant=="crystal" then
  for i=1,4 do
   local a=i*math.pi/2
   local crown=piece(m,"Prism Branch",Vector3.new(3,13,3)*scale,
    CFrame.new(pos+Vector3.new(math.cos(a)*3*scale,16*scale,math.sin(a)*3*scale))*
     CFrame.Angles(0,a,math.rad(14)),
    Color3.fromRGB(139+15*i,70+20*i,240),Enum.Material.Glass,false)
  end
 else
  for i=1,5 do
   local angle=i*math.pi*2/5
   local leaf=piece(m,"Leaf Crown",Vector3.new(11,10,11)*scale,
    CFrame.new(pos+Vector3.new(math.cos(angle)*4*scale,17*scale,math.sin(angle)*4*scale)),
    Color3.fromRGB(40+i*6,137+i*10,85+i*5),Enum.Material.Grass,false)
   leaf.Shape=Enum.PartType.Ball
  end
 end
 return m
end
function Kit.Grass(parent,pos,color)
 local m=model(parent,"Grass Patch","Grass")
 for i=1,3 do
  local a=i*2.1
  piece(m,"Blade",Vector3.new(.65,2.4,.5),
   CFrame.new(pos+Vector3.new(math.cos(a)*.5,1.2,math.sin(a)*.5))*
    CFrame.Angles(math.sin(a)*.2,0,math.cos(a)*.3),
   color or Color3.fromRGB(69,171,86),Enum.Material.Grass,false)
 end
 return m
end
function Kit.Rock(parent,pos,color,scale)
 local m=model(parent,"Rock Cluster","Rock")
 scale=scale or 1
 for i=1,3 do
  local rock=piece(m,"Boulder",Vector3.new(5+i,3+i,4+i)*scale,
   CFrame.new(pos+Vector3.new(i*2,1.5*scale,i*.6))*
    CFrame.Angles(i*.3,i*.6,i*.15),
   color or Color3.fromRGB(96,106,129),Enum.Material.Slate,true)
  rock.Shape=Enum.PartType.Ball
 end
 return m
end
function Kit.Lamp(parent,pos,color)
 local m=model(parent,"Street Lamp","StreetLight")
 local pole=piece(m,"Pole",Vector3.new(1.1,16,1.1),
  CFrame.new(pos+Vector3.new(0,8,0)),Color3.fromRGB(46,57,78),Enum.Material.Metal,true)
 m.PrimaryPart=pole
 local light=piece(m,"Lamp Head",Vector3.new(4,1.5,4),
  CFrame.new(pos+Vector3.new(0,16,0)),color or Color3.fromRGB(67,235,255),Enum.Material.Neon,false)
 local point=Instance.new("PointLight"); point.Color=light.Color
 point.Brightness=1.4; point.Range=23; point.Parent=light
 return m
end
function Kit.Crate(parent,pos,color)
 local m=model(parent,"Supply Crate","Crate")
 local box=piece(m,"Box",Vector3.new(7,6,7),CFrame.new(pos+Vector3.new(0,3,0)),
  Color3.fromRGB(90,72,62),Enum.Material.WoodPlanks,true)
 m.PrimaryPart=box
 for _,x in ipairs({-3.6,3.6}) do
  piece(m,"Metal Strap",Vector3.new(.6,6.5,7.6),
   CFrame.new(pos+Vector3.new(x,3,0)),color or Color3.fromRGB(241,171,66),Enum.Material.Metal,false)
 end
 return m
end
function Kit.Road(parent,pos,size)
 local m=model(parent,"Road Segment","Road")
 local road=piece(m,"Asphalt",size,CFrame.new(pos),
  Color3.fromRGB(29,34,48),Enum.Material.Asphalt,true)
 m.PrimaryPart=road
 local longX=size.X>size.Z
 for offset=-1,1,2 do
  local stripeSize=longX and Vector3.new(6,.13,.6) or Vector3.new(.6,.13,6)
  local stripeOffset=longX and Vector3.new(offset*size.X*.25,size.Y/2+.1,0)
   or Vector3.new(0,size.Y/2+.1,offset*size.Z*.25)
  piece(m,"Road Stripe",stripeSize,CFrame.new(pos+stripeOffset),
   Color3.fromRGB(255,214,95),Enum.Material.Neon,false)
 end
 return m
end
function Kit.Car(parent,cf,paint,drivable)
 local m=model(parent,drivable and "Player Hovercar" or "Parked Future Car",
  drivable and "Vehicle" or "CarProp")
 local body=piece(m,"Chassis",Vector3.new(11,2.2,18),
  cf,paint or Color3.fromRGB(62,203,230),Enum.Material.Metal,true)
 m.PrimaryPart=body
 local cockpit=piece(m,"Cabin",Vector3.new(9,3.5,8),
  cf*CFrame.new(0,2.5,1.8),Color3.fromRGB(30,51,78),Enum.Material.Glass,false)
 local seat=Instance.new("VehicleSeat"); seat.Name="DriverSeat"
 seat.Size=Vector3.new(2,1,2); seat.CFrame=cf*CFrame.new(0,2.5,1.8)
 seat.Color=Color3.fromRGB(30,38,56); seat.Material=Enum.Material.SmoothPlastic
 seat.Anchored=true; seat.CanCollide=false; seat.Parent=m
 seat.HeadsUpDisplay=true; seat.MaxSpeed=40; seat.Torque=8; seat.TurnSpeed=2
 local function wheel(x,z)
  local w=piece(m,"Wheel",Vector3.new(4,2.5,4),
   cf*CFrame.new(x,-1.3,z)*CFrame.Angles(0,0,math.pi/2),
   Color3.fromRGB(24,29,44),Enum.Material.Rubber,true)
  w.Shape=Enum.PartType.Cylinder
  local hub=piece(m,"Wheel Glow",Vector3.new(4.2,.3,4.2),
   cf*CFrame.new(x*1.02,-1.3,z)*CFrame.Angles(0,0,math.pi/2),
   Color3.fromRGB(93,224,255),Enum.Material.Neon,false)
  hub.Shape=Enum.PartType.Cylinder
 end
 for _,x in ipairs({-5.1,5.1}) do
  for _,z in ipairs({-5.8,5.8}) do wheel(x,z) end
 end
 for _,x in ipairs({-3.4,3.4}) do
  piece(m,"Headlight",Vector3.new(2,1,.3),
   cf*CFrame.new(x,.4,-9.2),Color3.fromRGB(244,247,255),Enum.Material.Neon,false)
  piece(m,"Tail Light",Vector3.new(2,1,.3),
   cf*CFrame.new(x,.4,9.2),Color3.fromRGB(255,69,101),Enum.Material.Neon,false)
 end
 if drivable then
  -- Arcade handling: server moves an anchored model only while its real
  -- VehicleSeat is occupied. PivotTo moves the seat and attached rider.
  m:SetAttribute("Drivable",true)
 else
  seat.Disabled=true
 end
 return m,seat
end
function Kit.Bush(parent,pos,color)
 local m=model(parent,"Flowering Bush","Bush")
 for i=1,3 do
  local p=piece(m,"Foliage",Vector3.new(5,3.5,5),
   CFrame.new(pos+Vector3.new((i-2)*2.1,2,math.sin(i)*1.5)),
   color or Color3.fromRGB(65,165,95),Enum.Material.Grass,false)
  p.Shape=Enum.PartType.Ball
 end
 return m
end
function Kit.Flower(parent,pos,color)
 local m=model(parent,"Wild Flower","Flower")
 piece(m,"Stem",Vector3.new(.25,2,.25),
  CFrame.new(pos+Vector3.new(0,1,0)),Color3.fromRGB(57,161,73),Enum.Material.Grass,false)
 local head=piece(m,"Bloom",Vector3.new(1.6,1.6,1.6),
  CFrame.new(pos+Vector3.new(0,2.2,0)),color or Color3.fromRGB(255,131,190),
  Enum.Material.SmoothPlastic,false)
 head.Shape=Enum.PartType.Ball
 return m
end
function Kit.Bench(parent,pos,color)
 local m=model(parent,"Park Bench","Bench")
 local seat=piece(m,"Seat",Vector3.new(9,.8,3),
  CFrame.new(pos+Vector3.new(0,2.4,0)),color or Color3.fromRGB(135,91,61),
  Enum.Material.WoodPlanks,true)
 m.PrimaryPart=seat
 piece(m,"Backrest",Vector3.new(9,3,.8),
  CFrame.new(pos+Vector3.new(0,4,-1.2)),seat.Color,Enum.Material.WoodPlanks,true)
 for _,x in ipairs({-3.4,3.4}) do
  piece(m,"Bench Leg",Vector3.new(.8,2.4,.8),
   CFrame.new(pos+Vector3.new(x,1.2,0)),Color3.fromRGB(43,49,67),Enum.Material.Metal,true)
 end
 return m
end
function Kit.Fence(parent,pos,length,color)
 local m=model(parent,"Fence","Fence")
 length=math.max(8,length or 24)
 for i=0,math.floor(length/6) do
  local x=-length/2+i*6
  piece(m,"Fence Post",Vector3.new(.8,5,.8),
   CFrame.new(pos+Vector3.new(x,2.5,0)),
   color or Color3.fromRGB(102,81,70),Enum.Material.Wood,true)
 end
 for _,height in ipairs({1.6,3.5}) do
  piece(m,"Fence Rail",Vector3.new(length,.6,.65),
   CFrame.new(pos+Vector3.new(0,height,0)),
   color or Color3.fromRGB(102,81,70),Enum.Material.Wood,true)
 end
 return m
end
function Kit.House(parent,pos,color)
 local m=model(parent,"Modular House","Building")
 local foundation=piece(m,"House Base",Vector3.new(16,12,14),
  CFrame.new(pos+Vector3.new(0,6,0)),
  color or Color3.fromRGB(79,116,155),Enum.Material.Concrete,true)
 m.PrimaryPart=foundation
 local roof=piece(m,"Roof",Vector3.new(19,2,17),
  CFrame.new(pos+Vector3.new(0,13,0)),Color3.fromRGB(50,59,90),Enum.Material.Metal,true)
 piece(m,"Door",Vector3.new(3,6,.4),
  CFrame.new(pos+Vector3.new(0,3,-7.3)),
  Color3.fromRGB(44,47,66),Enum.Material.Wood,true)
 for _,x in ipairs({-5,5}) do
  piece(m,"Window",Vector3.new(3,3,.3),
   CFrame.new(pos+Vector3.new(x,8,-7.3)),
   Color3.fromRGB(119,236,255),Enum.Material.Glass,false)
 end
 return m
end
function Kit.Pond(parent,pos)
 local m=model(parent,"Crystal Pond","WaterFeature")
 local rim=piece(m,"Pond Rim",Vector3.new(21,.4,15),
  CFrame.new(pos+Vector3.new(0,.1,0)),
  Color3.fromRGB(87,112,140),Enum.Material.Slate,true)
 m.PrimaryPart=rim
 local water=piece(m,"Water Surface",Vector3.new(18,.15,12),
  CFrame.new(pos+Vector3.new(0,.35,0)),
  Color3.fromRGB(77,177,217),Enum.Material.Glass,false)
 water.Transparency=.3
 return m
end
function Kit.Populate(parent,biomes)
 local rng=Random.new(424242)
 local folder=Instance.new("Folder"); folder.Name="ReusableWorldKit"; folder.Parent=parent
 folder:SetAttribute("AssetLibrary","Trees,Grass,Rocks,Lamps,Crates,Roads,Cars,Bushes,Flowers,Benches,Fences,Buildings,Ponds")
 for index,biome in ipairs(biomes) do
  local area=Instance.new("Folder"); area.Name=biome.id.." Scenery"; area.Parent=folder
  local c=biome.center
  for i=1,9 do
   local angle=i*2.399
   local radius=36+(i%3)*6
   local p=c+Vector3.new(math.cos(angle)*radius,1,math.sin(angle)*radius)
   if index==1 then
    Kit.Lamp(area,p,Color3.fromRGB(74,223,252))
   elseif index==2 then
    Kit.Tree(area,p,"crystal",.7)
   elseif index==3 then
    Kit.Rock(area,p,Color3.fromRGB(94,65,67),.75)
   else
    Kit.Tree(area,p,"pine",.65)
   end
  end
  Kit.Bench(area,c+Vector3.new(24,1,-20),biome.color)
  Kit.Fence(area,c+Vector3.new(-30,1,-51),24,biome.color)
  for i=1,5 do
   Kit.Bush(area,c+Vector3.new(-46+i*14,1,49),biome.color)
  end
  if index==1 then
   Kit.House(area,c+Vector3.new(-38,1,26),Color3.fromRGB(85,128,164))
   Kit.House(area,c+Vector3.new(38,1,26),Color3.fromRGB(130,91,169))
   Kit.Road(area,c+Vector3.new(0,1,-42),Vector3.new(90,.35,12))
   for i=1,3 do
    Kit.Car(area,CFrame.new(c+Vector3.new(-33+i*20,4,-42)),
     Color3.fromRGB(85+i*35,99+i*25,225-i*30),false)
   end
  else
   if index==2 then Kit.Pond(area,c+Vector3.new(-33,1,-35)) end
   for i=1,45 do
    local x=rng:NextNumber(-52,52); local z=rng:NextNumber(-52,52)
    if x*x+z*z>24*24 then
     if i%7==0 then
      Kit.Flower(area,c+Vector3.new(x,1,z),biome.color)
     end
     Kit.Grass(area,c+Vector3.new(x,1,z),
      index==3 and Color3.fromRGB(217,101,64) or
       index==2 and Color3.fromRGB(159,113,225) or Color3.fromRGB(85,174,119))
    end
   end
  end
  for i=1,4 do
   Kit.Crate(area,c+Vector3.new(-44+i*17,1,43),biome.color)
  end
 end
 return folder
end
return Kit
