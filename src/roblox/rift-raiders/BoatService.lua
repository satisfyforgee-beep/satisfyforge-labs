-- Rift Raiders v0.12 | First navigable earned-coin watercraft.
-- Watercraft are original modular Roblox geometry, not imported photoreal meshes.
-- All spawning and travel are validated on the server; no Robux payments.
local RunService=game:GetService("RunService")
local Players=game:GetService("Players")
local Boat={}
Boat.Vessels={
 KAYAK={name="Kayak",speed=13,length=14,beam=3,level=2},
 FISHING_BOAT={name="Fishing Boat",speed=21,length=24,beam=10,level=8},
 JET_SKI={name="Jet Ski",speed=45,length=12,beam=4,level=10},
 PONTOON={name="Pontoon",speed=20,length=32,beam=15,level=14},
 SAILBOAT={name="Sailboat",speed=23,length=34,beam=12,level=14},
 SPEEDBOAT={name="Speedboat",speed=53,length=28,beam=10,level=16},
 CABIN_CRUISER={name="Cabin Cruiser",speed=34,length=39,beam=13,level=25},
 YACHT={name="Luxury Yacht",speed=27,length=48,beam=17,level=24},
 LUXURY_YACHT={name="Superyacht",speed=33,length=65,beam=22,level=45},
}
local active={}
local cooldown={}
local region=Vector3.new(760,0,520)
local pier=Vector3.new(610,3,520)
local dockPart=nil
local dockFolder=nil
local elapsed=0
local function part(parent,name,size,cf,color,material,solid)
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.CFrame=cf;p.Color=color
 p.Anchored=true;p.CanCollide=solid==true;p.CanTouch=false
 p.Material=material or Enum.Material.SmoothPlastic
 p.TopSurface=Enum.SurfaceType.Smooth;p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=parent
 return p
end
local function modelHull(parent,cf,vehicle)
 local b=vehicle.beam;local length=vehicle.length
 local main=part(parent,"Marine Hull",Vector3.new(b,2.9,length*.72),
  cf*CFrame.new(0,-1,3),Color3.fromRGB(234,239,237),
  Enum.Material.SmoothPlastic,true)
 main.Shape=Enum.PartType.Cylinder
 main.CFrame=main.CFrame*CFrame.Angles(0,0,math.pi*.5)
 -- Strong rub rail, tapered forward bow and a nonslip deck.
 local nose=Instance.new("WedgePart")
 nose.Name="Sloped Boat Bow";nose.Size=Vector3.new(b,3,length*.32)
 nose.CFrame=cf*CFrame.new(0,-.65,-length*.35)*CFrame.Angles(0,math.pi,0)
 nose.Color=Color3.fromRGB(231,234,229);nose.Material=Enum.Material.SmoothPlastic
 nose.Anchored=true;nose.CanCollide=true;nose.Parent=parent
 part(parent,"Nonslip Marine Deck",Vector3.new(b-.6,.45,length*.67),
  cf*CFrame.new(0,.05,2.6),Color3.fromRGB(191,207,210),
  Enum.Material.Concrete,true)
 for _,side in ipairs({-1,1}) do
  part(parent,"Hull Rub Rail",Vector3.new(.33,.4,length*.7),
   cf*CFrame.new(side*b*.49,-.15,2.5),
   Color3.fromRGB(58,80,103),Enum.Material.Metal,false)
 end
 if vehicle.length>=28 then
  part(parent,"Captain Console",Vector3.new(3,2.5,2),
   cf*CFrame.new(1,1.55,0),Color3.fromRGB(65,80,94),Enum.Material.Metal,true)
  local glass=part(parent,"Windshield",Vector3.new(b*.58,3,.3),
   cf*CFrame.new(0,3,-3)*CFrame.Angles(math.rad(-20),0,0),
   Color3.fromRGB(106,177,195),Enum.Material.Glass,false)
  glass.Transparency=.33
 end
 if vehicle.length>=35 then
  local cabin=part(parent,"Marine Cabin Walls",
   Vector3.new(b*.68,5,length*.22),cf*CFrame.new(0,3,8),
   Color3.fromRGB(236,232,216),Enum.Material.SmoothPlastic,true)
  local roof=part(parent,"Marine Cabin Roof",Vector3.new(b*.76,.5,length*.27),
   cf*CFrame.new(0,6,8),Color3.fromRGB(83,111,134),
   Enum.Material.Metal,true)
  for _,side in ipairs({-1,1}) do
   local window=part(parent,"Cabin Window",Vector3.new(.15,2,4),
    cf*CFrame.new(side*b*.345,3.7,8),
    Color3.fromRGB(70,132,158),Enum.Material.Glass,false)
   window.Transparency=.2
  end
 end
 if vehicle.length>=48 then
  part(parent,"Upper Sun Deck",Vector3.new(b*.66,.45,length*.3),
   cf*CFrame.new(0,6.5,7),Color3.fromRGB(220,218,209),
   Enum.Material.WoodPlanks,true)
  for _,side in ipairs({-1,1}) do
   part(parent,"Yacht Sun Deck Railing",Vector3.new(.18,2.3,length*.33),
    cf*CFrame.new(side*b*.35,7.7,7),
    Color3.fromRGB(191,204,210),Enum.Material.Metal,false)
  end
 end
 if vehicle.length<20 then
  part(parent,"Personal Watercraft Cowling",Vector3.new(b*.9,1.1,length*.4),
   cf*CFrame.new(0,.85,-1),Color3.fromRGB(61,130,164),Enum.Material.Metal,true)
 end
 local motor=part(parent,"Outboard Engine",Vector3.new(2.6,2.8,2.8),
  cf*CFrame.new(0,-.6,length*.49),Color3.fromRGB(52,65,77),
  Enum.Material.Metal,false)
 for _,side in ipairs({-1,1}) do
  local navigation=part(parent,"Marine Navigation Light",Vector3.new(.55,.55,.55),
   cf*CFrame.new(side*b*.4,2,-length*.28),
   side==-1 and Color3.fromRGB(224,78,70) or
   Color3.fromRGB(80,207,120),Enum.Material.Neon,false)
  navigation.Shape=Enum.PartType.Ball
 end
 return main
end
local function spawnModel(player,id,cf)
 local vessel=Boat.Vessels[id]
 local m=Instance.new("Model")
 m.Name=player.DisplayName.."'s "..vessel.name
 m:SetAttribute("OwnerUserId",player.UserId)
 m:SetAttribute("VesselType",id)
 m:SetAttribute("SpeedLimit",vessel.speed)
 m.Parent=dockFolder
 local hull=modelHull(m,cf,vessel)
 local seat=Instance.new("VehicleSeat")
 seat.Name="Boat Driver Seat";seat.Size=Vector3.new(2,1.1,2)
 seat.CFrame=cf*CFrame.new(0,2,1.8)
 seat.Color=Color3.fromRGB(69,85,103);seat.Material=Enum.Material.Fabric
 seat.Anchored=true;seat.CanCollide=true;seat.Parent=m
 m.PrimaryPart=hull
 local foam=Instance.new("ParticleEmitter")
 foam.Name="Boat Wake";foam.Enabled=false
 foam.Texture="rbxasset://textures/particles/sparkles_main.dds"
 foam.Rate=17;foam.Lifetime=NumberRange.new(.3,.7)
 foam.Speed=NumberRange.new(1,3)
 foam.SpreadAngle=Vector2.new(15,15)
 foam.Parent=hull
 return m,seat,foam
end
local function inSea(pos)
 return pos.X>=605 and pos.X<=920 and
  pos.Z>=332 and pos.Z<=710 and pos.Y>=-2 and pos.Y<=18
end
function Boat.Spawn(player,id)
 if type(id)~="string" or not Boat.Vessels[id] then
  return false,"CHOOSE AN AVAILABLE BOAT TYPE."
 end
 local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
 if not root or (root.Position-pier).Magnitude>100 then
  return false,"VISIT THE OCEAN MARINA BOAT LAUNCH TO SPAWN A BOAT."
 end
 if player:GetAttribute("RRLifeOwn_"..id)~=true then
  return false,"BUY THIS BOAT WITH EARNED COINS AT THE VEHICLE DEALER FIRST."
 end
 local now=os.clock()
 if now-(cooldown[player] or -1000)<7 then
  return false,"WAIT BEFORE LAUNCHING ANOTHER VESSEL."
 end
 cooldown[player]=now
 local previous=active[player]
 if previous and previous.model then previous.model:Destroy() end
 local spot=Vector3.new(650,1.2,520)
 local cf=CFrame.lookAt(spot,spot+Vector3.new(0,0,-1))
 local m,seat,wake=spawnModel(player,id,cf)
 active[player]={model=m,seat=seat,position=spot,speed=0,kind=id,
  wake=wake,lastOccupied=now}
 return true,Boat.Vessels[id].name:upper().." LAUNCHED! USE THE DRIVER SEAT TO STEER."
end
function Boat.Build(world)
 local Terrain=workspace.Terrain
 Terrain:FillBlock(CFrame.new(730,-9,520),Vector3.new(450,12,400),
  Enum.Material.Water)
 local folder=Instance.new("Folder");folder.Name="Navigable Ocean Marina";folder.Parent=world
 dockFolder=folder
 for i=0,5 do
  part(folder,"Marina Plank "..i,Vector3.new(15,.8,13),
   CFrame.new(583+i*9,2.7,520),
   Color3.fromRGB(157,114,78),Enum.Material.WoodPlanks,true)
 end
 for _,z in ipairs({-6,6}) do
  for x=578,638,12 do
   part(folder,"Marine Dock Post",Vector3.new(1.3,7,1.3),
    CFrame.new(x,.3,520+z),
    Color3.fromRGB(112,85,69),Enum.Material.Wood,true)
  end
 end
 dockPart=part(folder,"Public Marina Boat Launch",Vector3.new(7,4,4),
  CFrame.new(600,6.1,520),Color3.fromRGB(54,106,134),
  Enum.Material.Metal,true)
 local p=Instance.new("ProximityPrompt")
 p.Name="Boat Launch Prompt";p.ActionText="LAUNCH OWNED BOAT"
 p.ObjectText="MARINA • SELECT YOUR BOAT IN LIFE MENU"
 p.MaxActivationDistance=14;p.HoldDuration=.3;p.Parent=dockPart
 p.Triggered:Connect(function(player)
  for _,id in ipairs({"FISHING_BOAT","JET_SKI","PONTOON","SPEEDBOAT",
   "SAILBOAT","CABIN_CRUISER","YACHT","LUXURY_YACHT","KAYAK"}) do
   if player:GetAttribute("RRLifeOwn_"..id) then
    Boat.Spawn(player,id)
    break
   end
  end
 end)
 folder:SetAttribute("BoatModels",9)
 elapsed=0
 RunService.Heartbeat:Connect(function(dt)
  elapsed+=dt
  if elapsed<.06 then return end
  local step=math.min(elapsed,.12);elapsed=0
  for player,boat in pairs(active) do
   if not player.Parent or not boat.model or not boat.model.Parent then
    if boat.model then boat.model:Destroy() end
    active[player]=nil
   else
    local hum=boat.seat.Occupant
    local driver=hum and Players:GetPlayerFromCharacter(hum.Parent)
    if driver==player and hum.Health>0 then
     boat.lastOccupied=os.clock()
     local v=Boat.Vessels[boat.kind]
     local throttle=math.clamp(boat.seat.ThrottleFloat,-1,1)
     local turn=math.clamp(boat.seat.SteerFloat,-1,1)
     local goal=throttle*v.speed
     boat.speed+=(goal-boat.speed)*math.min(1,step*1.4)
     if math.abs(throttle)<.05 then boat.speed*=math.max(0,1-step*.7) end
     local cf=boat.model:GetPivot()
     local yaw=-turn*step*1.1*math.clamp(math.abs(boat.speed)/18,.2,1)
     local rot=cf*CFrame.Angles(0,yaw,0)
     local nextPos=rot.Position+rot.LookVector*boat.speed*step
     if inSea(nextPos) then
      nextPos=Vector3.new(nextPos.X,1.2,nextPos.Z)
      boat.model:PivotTo(rot-rot.Position+nextPos)
      boat.wake.Enabled=math.abs(boat.speed)>5
     else
      boat.speed=0;boat.wake.Enabled=false
     end
    elseif os.clock()-boat.lastOccupied>300 then
     boat.model:Destroy();active[player]=nil
    end
   end
  end
 end)
 Players.PlayerRemoving:Connect(function(player)
  local boat=active[player]
  if boat and boat.model then boat.model:Destroy() end
  active[player]=nil;cooldown[player]=nil
 end)
 return Vector3.new(600,8,520)
end
return Boat
