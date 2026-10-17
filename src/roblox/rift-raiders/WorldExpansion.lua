-- RIFT RAIDERS: Multiworld Expansion. Original, reusable Roblox models and real terrain.
-- Keep portal destinations server-owned; never accept arbitrary player coordinates.
local Expansion={}
local Players=game:GetService("Players")
local Terrain=workspace.Terrain
local function part(parent,name,size,cf,color,material,collide)
 local p=Instance.new("Part")
 p.Name=name; p.Size=size; p.CFrame=cf; p.Anchored=true
 p.Color=color; p.Material=material or Enum.Material.SmoothPlastic
 p.CanCollide=collide~=false; p.CanTouch=collide~=false
 p.TopSurface=Enum.SurfaceType.Smooth; p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=parent
 return p
end
local function group(parent,name,kind)
 local m=Instance.new("Model"); m.Name=name; m:SetAttribute("AssetType",kind)
 m.Parent=parent
 return m
end
local function label(parent,title,position,color)
 local anchor=part(parent,"Landmark Label",Vector3.new(1,1,1),
  CFrame.new(position),color,Enum.Material.Neon,false)
 anchor.Transparency=1
 local gui=Instance.new("BillboardGui")
 gui.Size=UDim2.fromOffset(280,62); gui.MaxDistance=155
 gui.AlwaysOnTop=true; gui.Parent=anchor
 local text=Instance.new("TextLabel")
 text.Size=UDim2.fromScale(1,1); text.BackgroundTransparency=1
 text.Text=title; text.TextScaled=true; text.Font=Enum.Font.GothamBlack
 text.TextColor3=color; text.TextStrokeTransparency=.2; text.Parent=gui
 return anchor
end
local function prompt(target,action,object,callback)
 local p=Instance.new("ProximityPrompt")
 p.Name="WorldAction"; p.ActionText=action; p.ObjectText=object
 p.HoldDuration=.4; p.MaxActivationDistance=13
 p.RequiresLineOfSight=false; p.Parent=target
 p.Triggered:Connect(function(player)
  local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
  if root and (root.Position-target.Position).Magnitude<=19 then
   callback(player)
  end
 end)
 return p
end
local function tower(parent,position,color)
 local m=group(parent,"Castle Tower","Castle")
 local wall=part(m,"Stone Tower",Vector3.new(18,33,18),
  CFrame.new(position+Vector3.new(0,16.5,0)),Color3.fromRGB(124,131,147),Enum.Material.Cobblestone,true)
 m.PrimaryPart=wall
 part(m,"Roof",Vector3.new(22,4,22),
  CFrame.new(position+Vector3.new(0,35,0)),color,Enum.Material.Slate,true)
 for i=1,4 do
  local a=i*math.pi/2
  part(m,"Battlement",Vector3.new(5,5,5),
   CFrame.new(position+Vector3.new(math.cos(a)*8,39,math.sin(a)*8)),
   Color3.fromRGB(150,153,169),Enum.Material.Cobblestone,true)
 end
 return m
end
local function castle(parent,center)
 local m=group(parent,"Royal Stone Castle","Castle")
 local wallColor=Color3.fromRGB(140,144,159)
 local keep=part(m,"Grand Keep",Vector3.new(39,31,35),
  CFrame.new(center+Vector3.new(0,15.5,0)),wallColor,Enum.Material.Cobblestone,true)
 m.PrimaryPart=keep
 part(m,"Royal Roof",Vector3.new(43,4,39),
  CFrame.new(center+Vector3.new(0,33,0)),Color3.fromRGB(96,72,141),Enum.Material.Slate,true)
 part(m,"Gate",Vector3.new(11,15,1),
  CFrame.new(center+Vector3.new(0,7.5,-18)),Color3.fromRGB(79,59,52),Enum.Material.WoodPlanks,true)
 for _,x in ipairs({-28,28}) do
  for _,z in ipairs({-26,26}) do tower(m,center+Vector3.new(x,0,z),Color3.fromRGB(95,75,160)) end
 end
 for _,x in ipairs({-16,16}) do
  part(m,"Stained Glass",Vector3.new(6,10,.5),
   CFrame.new(center+Vector3.new(x,19,-18)),
   Color3.fromRGB(114,221,255),Enum.Material.Glass,false)
 end
 return m
end
local function barn(parent,center)
 local m=group(parent,"Working Farm Barn","Farm")
 local body=part(m,"Red Barn",Vector3.new(33,19,27),
  CFrame.new(center+Vector3.new(0,9.5,0)),Color3.fromRGB(175,63,66),Enum.Material.WoodPlanks,true)
 m.PrimaryPart=body
 part(m,"Barn Roof",Vector3.new(37,3,31),
  CFrame.new(center+Vector3.new(0,20,0)),Color3.fromRGB(61,69,85),Enum.Material.Metal,true)
 part(m,"Sliding Door",Vector3.new(10,13,.6),
  CFrame.new(center+Vector3.new(0,6.5,-13.8)),Color3.fromRGB(230,217,180),Enum.Material.Wood,true)
 for _,x in ipairs({-12,12}) do
  part(m,"Hay Bale",Vector3.new(7,5,7),
   CFrame.new(center+Vector3.new(x,2.5,-21)),
   Color3.fromRGB(211,171,76),Enum.Material.Grass,true)
 end
 return m
end
local function crop(parent,pos,kind)
 local m=group(parent,"Harvest "..kind,"Crop")
 local dirt=part(m,"Soil",Vector3.new(6,.8,6),
  CFrame.new(pos+Vector3.new(0,.4,0)),Color3.fromRGB(111,76,51),Enum.Material.Ground,true)
 m.PrimaryPart=dirt
 for i=1,4 do
  local x=(i%2)*2.5-1.25; local z=math.floor((i-1)/2)*2.5-1.25
  local plant=part(m,"Growing "..kind,Vector3.new(1.2,3.2,1.2),
   CFrame.new(pos+Vector3.new(x,2.4,z)),
   kind=="Carrot" and Color3.fromRGB(63,175,77) or Color3.fromRGB(208,175,78),
   Enum.Material.Grass,false)
  if kind=="Carrot" then
   part(m,"Carrot",Vector3.new(.8,1.4,.8),
    CFrame.new(pos+Vector3.new(x,1.2,z)),
    Color3.fromRGB(241,125,44),Enum.Material.SmoothPlastic,false)
  end
 end
 return m,dirt
end
local function torii(parent,pos)
 local m=group(parent,"Japanese Torii Gate","Japan")
 local red=Color3.fromRGB(198,56,65)
 for _,x in ipairs({-9,9}) do
  part(m,"Torii Pillar",Vector3.new(2.3,19,2.3),
   CFrame.new(pos+Vector3.new(x,9.5,0)),red,Enum.Material.Wood,true)
 end
 local top=part(m,"Torii Roof Beam",Vector3.new(27,2.6,4),
  CFrame.new(pos+Vector3.new(0,20,0)),Color3.fromRGB(51,52,66),Enum.Material.Wood,true)
 m.PrimaryPart=top
 part(m,"Torii Crossbar",Vector3.new(21,2,2),
  CFrame.new(pos+Vector3.new(0,15,0)),red,Enum.Material.Wood,true)
 return m
end
local function pagoda(parent,pos)
 local m=group(parent,"Five-Level Pagoda","Japan")
 local body=part(m,"Pagoda Center",Vector3.new(18,38,18),
  CFrame.new(pos+Vector3.new(0,19,0)),
  Color3.fromRGB(220,195,164),Enum.Material.WoodPlanks,true)
 m.PrimaryPart=body
 for floor=1,5 do
  local width=29-(floor-1)*3.4
  part(m,"Pagoda Eaves",Vector3.new(width,2.2,width),
   CFrame.new(pos+Vector3.new(0,7.5*floor,0)),
   Color3.fromRGB(51,62,84),Enum.Material.Slate,true)
 end
 return m
end
local function airport(parent,pos)
 local m=group(parent,"Airport Terminal","Airport")
 local terminal=part(m,"Terminal Building",Vector3.new(62,15,30),
  CFrame.new(pos+Vector3.new(0,7.5,0)),
  Color3.fromRGB(144,169,183),Enum.Material.Concrete,true)
 m.PrimaryPart=terminal
 part(m,"Terminal Glass",Vector3.new(56,9,.5),
  CFrame.new(pos+Vector3.new(0,7,-15.3)),
  Color3.fromRGB(102,207,235),Enum.Material.Glass,false)
 part(m,"Terminal Roof",Vector3.new(66,2,34),
  CFrame.new(pos+Vector3.new(0,16,0)),
  Color3.fromRGB(53,72,92),Enum.Material.Metal,true)
 return m
end
local function plane(parent,pos)
 local m=group(parent,"Passenger Jet Display","Airplane")
 local body=part(m,"Fuselage",Vector3.new(9,8,55),
  CFrame.new(pos+Vector3.new(0,10,0)),
  Color3.fromRGB(226,235,241),Enum.Material.Metal,true)
 m.PrimaryPart=body
 part(m,"Main Wings",Vector3.new(57,1.5,13),
  CFrame.new(pos+Vector3.new(0,10,0)),
  Color3.fromRGB(164,191,213),Enum.Material.Metal,true)
 part(m,"Tail Fin",Vector3.new(2,14,8),
  CFrame.new(pos+Vector3.new(0,17,23)),
  Color3.fromRGB(52,142,211),Enum.Material.Metal,true)
 for _,x in ipairs({-14,14}) do
  part(m,"Jet Engine",Vector3.new(5,5,10),
   CFrame.new(pos+Vector3.new(x,7,2)),
   Color3.fromRGB(57,72,93),Enum.Material.Metal,true)
 end
 return m
end
local function snowmobile(parent,pos,drivable)
 local m=group(parent,"Snowmobile Display","Snowmobile")
 local body=part(m,"Snowmobile Body",Vector3.new(5,2.5,11),
  CFrame.new(pos+Vector3.new(0,3,0)),
  Color3.fromRGB(236,84,91),Enum.Material.Metal,true)
 m.PrimaryPart=body
 part(m,"Snow Track",Vector3.new(4,1.3,8),
  CFrame.new(pos+Vector3.new(0,1,1)),
  Color3.fromRGB(41,46,61),Enum.Material.Rubber,true)
 for _,x in ipairs({-2.3,2.3}) do
  part(m,"Front Ski",Vector3.new(.6,.7,8),
   CFrame.new(pos+Vector3.new(x,.5,-4)),
   Color3.fromRGB(36,48,63),Enum.Material.Metal,true)
 end
 part(m,"Windshield",Vector3.new(4,3,.4),
  CFrame.new(pos+Vector3.new(0,5,-2.5)),
  Color3.fromRGB(143,222,243),Enum.Material.Glass,false)
 if drivable then
  local seat=Instance.new("VehicleSeat"); seat.Name="DriverSeat"
  seat.Size=Vector3.new(2,1,2)
  seat.CFrame=CFrame.new(pos+Vector3.new(0,5.2,1))
  seat.Anchored=true; seat.CanCollide=false
  seat.Color=Color3.fromRGB(34,41,59); seat.Parent=m
  m.Name="Player Snowmobile"; m:SetAttribute("Drivable",true)
  return m,seat
 end
 return m
end
local function boat(parent,pos)
 local m=group(parent,"Marina Motorboat Display","Boat")
 local hull=part(m,"Boat Hull",Vector3.new(11,4,24),
  CFrame.new(pos+Vector3.new(0,2,0)),
  Color3.fromRGB(238,239,227),Enum.Material.SmoothPlastic,true)
 m.PrimaryPart=hull
 part(m,"Boat Cabin",Vector3.new(9,5,9),
  CFrame.new(pos+Vector3.new(0,6,3)),
  Color3.fromRGB(63,135,189),Enum.Material.Glass,false)
 part(m,"Motor",Vector3.new(4,4,4),
  CFrame.new(pos+Vector3.new(0,1.5,13)),
  Color3.fromRGB(38,50,65),Enum.Material.Metal,true)
 return m
end
local function bank(parent,pos)
 local m=group(parent,"City Bank","Bank")
 local base=part(m,"Bank Building",Vector3.new(39,20,29),
  CFrame.new(pos+Vector3.new(0,10,0)),
  Color3.fromRGB(191,196,203),Enum.Material.Concrete,true)
 m.PrimaryPart=base
 part(m,"Bank Roof",Vector3.new(43,3,33),
  CFrame.new(pos+Vector3.new(0,21.5,0)),
  Color3.fromRGB(66,84,113),Enum.Material.Slate,true)
 for _,x in ipairs({-13,-6,6,13}) do
  part(m,"Bank Column",Vector3.new(2,18,2),
   CFrame.new(pos+Vector3.new(x,9,-16)),
   Color3.fromRGB(238,237,219),Enum.Material.Marble,true)
 end
 part(m,"Vault Door",Vector3.new(9,11,.6),
  CFrame.new(pos+Vector3.new(0,5.5,-14.9)),
  Color3.fromRGB(75,91,108),Enum.Material.Metal,true)
 return m
end
local function animal(parent,pos,species)
 local m=group(parent,species.." Animal","Animal")
 local fur=species=="Deer" and Color3.fromRGB(151,100,70) or
  species=="Cow" and Color3.fromRGB(221,217,208) or Color3.fromRGB(179,147,100)
 local body=part(m,"Animal Body",Vector3.new(5,3.5,8),
  CFrame.new(pos+Vector3.new(0,4,0)),fur,Enum.Material.SmoothPlastic,true)
 m.PrimaryPart=body
 part(m,"Head",Vector3.new(3.5,3.5,3.5),
  CFrame.new(pos+Vector3.new(0,5.4,-4.3)),fur,Enum.Material.SmoothPlastic,false)
 for _,x in ipairs({-1.7,1.7}) do
  for _,z in ipairs({-2.5,2.5}) do
   part(m,"Leg",Vector3.new(1.1,2.5,1.1),
    CFrame.new(pos+Vector3.new(x,1.3,z)),fur,Enum.Material.SmoothPlastic,true)
  end
 end
 for _,x in ipairs({-1,1}) do
  part(m,"Eye",Vector3.new(.45,.45,.45),
   CFrame.new(pos+Vector3.new(x,5.9,-6.1)),
   Color3.fromRGB(22,28,33),Enum.Material.SmoothPlastic,false)
 end
 return m,body
end
local function jetpack(parent,pos)
 local m=group(parent,"Jetpack Station","Jetpack")
 local body=part(m,"Jetpack Core",Vector3.new(5,8,2),
  CFrame.new(pos+Vector3.new(0,4,0)),
  Color3.fromRGB(53,75,116),Enum.Material.Metal,true)
 m.PrimaryPart=body
 for _,x in ipairs({-3,3}) do
  part(m,"Thruster",Vector3.new(2,6,2),
   CFrame.new(pos+Vector3.new(x,3,0)),
   Color3.fromRGB(73,210,255),Enum.Material.Neon,false)
 end
 return m,body
end
local function portal(parent,pos,color,name)
 local m=group(parent,"Portal to "..name,"Portal")
 local frame=part(m,"Portal Frame",Vector3.new(8,12,2),
  CFrame.new(pos+Vector3.new(0,6,0)),color,Enum.Material.Neon,false)
 frame.Transparency=.55; m.PrimaryPart=frame
 part(m,"Portal Base",Vector3.new(12,1,7),
  CFrame.new(pos+Vector3.new(0,.5,0)),color,Enum.Material.Metal,true)
 local particle=Instance.new("ParticleEmitter")
 particle.Rate=6; particle.Lifetime=NumberRange.new(.5,1)
 particle.Speed=NumberRange.new(1,2); particle.Parent=frame
 return m,frame
end
Expansion.Prefabs={
 Castle=castle,Barn=barn,Crop=crop,Torii=torii,Pagoda=pagoda,
 Airport=airport,Plane=plane,Snowmobile=snowmobile,Boat=boat,
 Bank=bank,Animal=animal,Jetpack=jetpack,Portal=portal,
}
Expansion.Worlds={
 {id="CASTLE",name="Castle Kingdom",center=Vector3.new(520,0,0),ground=Enum.Material.Grass,color=Color3.fromRGB(177,136,255)},
 {id="FARM",name="Harvest Valley",center=Vector3.new(-520,0,0),ground=Enum.Material.Grass,color=Color3.fromRGB(116,213,93)},
 {id="JAPAN",name="Sakura Japan",center=Vector3.new(0,0,520),ground=Enum.Material.Grass,color=Color3.fromRGB(255,141,191)},
 {id="ARCTIC",name="Snowbound North",center=Vector3.new(0,0,-520),ground=Enum.Material.Snow,color=Color3.fromRGB(134,215,255)},
 {id="MARINA",name="Ocean Marina",center=Vector3.new(520,0,520),ground=Enum.Material.Sand,color=Color3.fromRGB(69,211,221)},
 {id="SAFARI",name="Wildlife Safari",center=Vector3.new(-520,0,-520),ground=Enum.Material.Grass,color=Color3.fromRGB(241,185,87)},
 {id="AIRPORT",name="International Airport",center=Vector3.new(-520,0,520),ground=Enum.Material.Ground,color=Color3.fromRGB(185,214,246)},
}
function Expansion.Build(world,kit,reward,tell,spawnVehicle)
 local folder=Instance.new("Folder"); folder.Name="Seven New Worlds"; folder.Parent=world
 local destinations={}
 local cooldown={}
 local deliveries={}
 local deliveryCompletedAt={}
 local rng=Random.new(71245)
 local function earn(id,player,coins,xp)
  cooldown[player]=cooldown[player] or {}
  local last=cooldown[player][id] or -math.huge
  if os.clock()-last<35 then tell(player,"COME BACK AFTER THIS ACTIVITY RECHARGES!"); return end
  cooldown[player][id]=os.clock()
  reward(player,coins,xp,0)
  tell(player,"ACTIVITY COMPLETE! +"..coins.." COINS!")
 end
 Players.PlayerRemoving:Connect(function(p)
  cooldown[p]=nil; deliveries[p]=nil; deliveryCompletedAt[p]=nil
 end)
 for i,region in ipairs(Expansion.Worlds) do
  local c=region.center
  local area=Instance.new("Folder"); area.Name=region.name; area.Parent=folder
  area:SetAttribute("WorldId",region.id)
  area:SetAttribute("Biome",region.name)
  -- True Roblox Terrain, not flat plastic tiles. Material supports sculpting in Studio.
  if region.id=="MARINA" then
   Terrain:FillBlock(CFrame.new(c+Vector3.new(0,-9,0)),
    Vector3.new(300,12,300),Enum.Material.Water)
   Terrain:FillBlock(CFrame.new(c+Vector3.new(0,-4,0)),
    Vector3.new(145,12,145),Enum.Material.Sand)
  else
   Terrain:FillBlock(CFrame.new(c+Vector3.new(0,-4,0)),
    Vector3.new(170,12,170),region.ground)
   for j=1,5 do
    local a=j*1.2566
    Terrain:FillBall(c+Vector3.new(math.cos(a)*76,-5,math.sin(a)*76),
     18,region.ground)
   end
  end
  local floor=part(area,"Walkable Arrival Plaza",Vector3.new(28,1,28),
   CFrame.new(c+Vector3.new(0,2.5,0)),region.color,Enum.Material.SmoothPlastic,true)
  floor.Transparency=.25
  label(area,region.name:upper(),c+Vector3.new(0,29,0),region.color)
  destinations[region.id]=c+Vector3.new(0,8,0)
  local deliveryPoint=part(area,"Interworld Delivery Point",Vector3.new(5,5,5),
   CFrame.new(c+Vector3.new(-20,4,13)),
   Color3.fromRGB(244,199,74),Enum.Material.Neon,false)
  prompt(deliveryPoint,"DELIVER","Interworld Courier",function(p)
   if deliveries[p]~=region.id then
    tell(p,"ACCEPT A DELIVERY FROM THE CENTRAL HUB FIRST!")
    return
   end
   deliveries[p]=nil
   deliveryCompletedAt[p]=os.clock()
   p:SetAttribute("RRDeliveryTarget","")
   p:SetAttribute("RRDeliveries",(p:GetAttribute("RRDeliveries") or 0)+1)
   reward(p,40,45,2)
   tell(p,"DELIVERY COMPLETE! +40 COINS +2 SHARDS!")
  end)
  local hubAngle=(i-1)*math.pi*2/#Expansion.Worlds
  local hubPos=Vector3.new(math.cos(hubAngle)*37,2,math.sin(hubAngle)*37)
  local _,hubFrame=portal(area,hubPos,region.color,region.name)
  prompt(hubFrame,"TRAVEL",region.name,function(p)
   local root=p.Character and p.Character:FindFirstChild("HumanoidRootPart")
   if root and (root.Position-hubFrame.Position).Magnitude<19 then
    p.Character:PivotTo(CFrame.new(destinations[region.id]))
    tell(p,"WELCOME TO "..region.name:upper())
   end
  end)
  local _,returnFrame=portal(area,c+Vector3.new(0,2,36),region.color,"Central Hub")
  prompt(returnFrame,"RETURN","Central Hub",function(p)
   p.Character:PivotTo(CFrame.new(0,8,0))
   tell(p,"BACK AT THE CENTRAL HUB!")
  end)
  for j=1,11 do
   local a=j*2.39996
   local radius=45+(j%3)*9
   local pos=c+Vector3.new(math.cos(a)*radius,2,math.sin(a)*radius)
   if region.id=="ARCTIC" then
    kit.Tree(area,pos,"pine",.7)
   elseif region.id=="JAPAN" then
    kit.Tree(area,pos,"oak",.6)
   elseif region.id=="MARINA" or region.id=="AIRPORT" then
    if j%2==0 then kit.Lamp(area,pos,region.color) end
   else
    kit.Tree(area,pos,"oak",.55)
   end
  end
  for j=1,12 do
   local x=rng:NextNumber(-67,67); local z=rng:NextNumber(-67,67)
   if x*x+z*z>32*32 then
    if region.id=="ARCTIC" then
     kit.Rock(area,c+Vector3.new(x,2,z),Color3.fromRGB(202,222,239),.6)
    elseif region.id~="AIRPORT" and region.id~="MARINA" then
     kit.Grass(area,c+Vector3.new(x,2,z))
    end
   end
  end
  if region.id=="CASTLE" then
   castle(area,c+Vector3.new(0,2,-36))
   local relic=part(area,"Royal Relic",Vector3.new(4,6,4),
    CFrame.new(c+Vector3.new(32,6,-24)),region.color,Enum.Material.Neon,false)
   prompt(relic,"FIND RELIC","Castle Quest",function(p) earn("relic",p,22,24) end)
  elseif region.id=="FARM" then
   barn(area,c+Vector3.new(-33,2,-25))
   for j=1,12 do
    local x=(j%4)*9-14; local z=math.floor((j-1)/4)*9+10
    local _,soil=crop(area,c+Vector3.new(x,2,z),j%2==0 and "Wheat" or "Carrot")
    prompt(soil,"HARVEST","Farm Crops",function(p) earn("crop_"..j,p,8,8) end)
   end
   local cow,body=animal(area,c+Vector3.new(34,2,-25),"Cow")
   prompt(body,"FEED","Friendly Cow",function(p) earn("cow",p,10,10) end)
  elseif region.id=="JAPAN" then
   torii(area,c+Vector3.new(0,2,-33))
   pagoda(area,c+Vector3.new(0,2,34))
   for j=1,5 do
    local lantern=kit.Lamp(area,c+Vector3.new(-45+j*15,2,-9),region.color)
    if j==3 then
     prompt(lantern.PrimaryPart,"LIGHT","Sakura Lantern",function(p) earn("lantern",p,14,14) end)
    end
   end
  elseif region.id=="ARCTIC" then
   for j=1,4 do
    local display=snowmobile(area,c+Vector3.new(-36+j*17,2,-28))
    prompt(display.PrimaryPart,"RIDE","Spawn Snowmobile",function(p)
     if not spawnVehicle then return end
     local ok,message=spawnVehicle(world,p,"snowmobile")
     tell(p,message)
    end)
   end
   local pack,core=jetpack(area,c+Vector3.new(32,2,28))
   prompt(core,"ACTIVATE","Jetpack Launch",function(p)
    local root=p.Character and p.Character:FindFirstChild("HumanoidRootPart")
    if not root then return end
    local k="jetpack"
    cooldown[p]=cooldown[p] or {}
    if os.clock()-(cooldown[p][k] or -math.huge)<12 then
     tell(p,"JETPACK RECHARGING!"); return
    end
    cooldown[p][k]=os.clock()
    local attachment=Instance.new("Attachment"); attachment.Name="JetpackAttachment"
    attachment.Parent=root
    local lift=Instance.new("VectorForce")
    lift.Name="JetpackLift"; lift.Attachment0=attachment
    lift.RelativeTo=Enum.ActuatorRelativeTo.World
    lift.ApplyAtCenterOfMass=true
    lift.Force=Vector3.new(0,root.AssemblyMass*workspace.Gravity*1.25,0)
    lift.Parent=root
    root.AssemblyLinearVelocity=Vector3.new(root.AssemblyLinearVelocity.X,25,root.AssemblyLinearVelocity.Z)
    tell(p,"JETPACK LIFT ACTIVE FOR 3 SECONDS!")
    task.delay(3,function()
     if lift.Parent then lift:Destroy() end
     if attachment.Parent then attachment:Destroy() end
    end)
   end)
  elseif region.id=="MARINA" then
   local dock=part(area,"Marina Dock",Vector3.new(20,2,110),
    CFrame.new(c+Vector3.new(0,1,85)),
    Color3.fromRGB(129,95,70),Enum.Material.WoodPlanks,true)
   boat(area,c+Vector3.new(23,-1,113))
   boat(area,c+Vector3.new(-23,-1,105))
   local fishing=part(area,"Fishing Pier Marker",Vector3.new(5,3,5),
    CFrame.new(c+Vector3.new(0,4,115)),region.color,Enum.Material.Neon,false)
   prompt(fishing,"FISH","Ocean Fishing",function(p) earn("fishing",p,18,20) end)
  elseif region.id=="SAFARI" then
   local deer,body=animal(area,c+Vector3.new(22,2,-21),"Deer")
   prompt(body,"FEED","Friendly Deer",function(p) earn("deer",p,12,12) end)
   for j=1,4 do
    animal(area,c+Vector3.new(-35+j*14,2,29),j%2==0 and "Cow" or "Deer")
   end
   kit.Pond(area,c+Vector3.new(-30,2,-32))
  elseif region.id=="AIRPORT" then
   airport(area,c+Vector3.new(0,2,-35))
   local runway=part(area,"Airport Runway",Vector3.new(120,1,28),
    CFrame.new(c+Vector3.new(0,2,44)),
    Color3.fromRGB(41,48,58),Enum.Material.Asphalt,true)
   plane(area,c+Vector3.new(38,2,41))
   local bag=part(area,"Luggage Cart",Vector3.new(6,5,7),
    CFrame.new(c+Vector3.new(-32,4,12)),
    Color3.fromRGB(232,170,66),Enum.Material.Metal,true)
   prompt(bag,"DELIVER","Airport Luggage",function(p) earn("luggage",p,16,18) end)
  end
 end
 -- Cross-world courier missions turn exploration into a replayable gameplay loop.
 local dispatch=part(folder,"Courier Dispatch Terminal",Vector3.new(8,8,6),
  CFrame.new(0,6,23),Color3.fromRGB(244,190,69),Enum.Material.Metal,true)
 prompt(dispatch,"TAKE JOB","Interworld Courier",function(p)
  if deliveries[p] then
   tell(p,"CURRENT DELIVERY: "..tostring(p:GetAttribute("RRDeliveryTarget")))
   return
  end
  if os.clock()-(deliveryCompletedAt[p] or -math.huge)<25 then
   tell(p,"NEW COURIER JOB AVAILABLE SOON!")
   return
  end
  local count=p:GetAttribute("RRDeliveries") or 0
  local nextRegion=Expansion.Worlds[(count+p.UserId%7)%#Expansion.Worlds+1]
  deliveries[p]=nextRegion.id
  p:SetAttribute("RRDeliveryTarget",nextRegion.name)
  tell(p,"COURIER JOB: DELIVER PACKAGE TO "..nextRegion.name:upper())
 end)
 -- A bank belongs in the metropolitan island rather than an isolated world.
 local bankFolder=Instance.new("Folder"); bankFolder.Name="Metropolis Bank"; bankFolder.Parent=folder
 bank(bankFolder,Vector3.new(180+31,2,31))
 local atm=part(bankFolder,"Bank ATM",Vector3.new(4,7,3),
  CFrame.new(180+31,5,31-17),Color3.fromRGB(64,144,179),Enum.Material.Metal,true)
 prompt(atm,"COLLECT BANK PAYOUT","Bank ATM",function(p) earn("bank",p,12,12) end)
 return destinations
end
return Expansion
