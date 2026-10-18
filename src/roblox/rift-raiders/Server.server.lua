-- RIFT RAIDERS: CHAOS ISLANDS. Original, free-to-play multiplayer prototype.
-- All rewards, combat, abilities and progression are validated on the server.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local RunService=game:GetService("RunService")
local Lighting=game:GetService("Lighting")
local DataStoreService=game:GetService("DataStoreService")
local HttpService=game:GetService("HttpService")
local Debris=game:GetService("Debris")
local ServerScriptService=game:GetService("ServerScriptService")
local WorldKit=require(ServerScriptService:WaitForChild("WorldKit"))
local WorldExpansion=require(ServerScriptService:WaitForChild("WorldExpansion"))
local WorldActivities=require(ServerScriptService:WaitForChild("WorldActivities"))
local WorldPolish=require(ServerScriptService:WaitForChild("WorldPolish"))
local Life=require(ServerScriptService:WaitForChild("LifeSimulation"))
local LifeCityVisuals=require(ServerScriptService:WaitForChild("LifeCityVisuals"))
local ModernCityIntegration=require(ServerScriptService:WaitForChild("ModernCityIntegration"))
local DowntownPopulation=require(ServerScriptService:WaitForChild("DowntownPopulation"))
local SuburbanDistrict=require(ServerScriptService:WaitForChild("SuburbanDistrict"))
local Catalog=require(ReplicatedStorage:WaitForChild("PrestigeCatalog"))
local Vehicles=require(ServerScriptService:WaitForChild("VehicleService"))
local Boats=require(ServerScriptService:WaitForChild("BoatService"))
local Persistence=require(ServerScriptService:WaitForChild("DataPersistence"))
local Goals=require(ServerScriptService:WaitForChild("ProgressionGoals"))
local Discovery=require(ServerScriptService:WaitForChild("SuburbanDiscovery"))
local world=Instance.new("Folder"); world.Name="RiftRaidersWorld"; world.Parent=workspace
world:SetAttribute("Version","0.19.0")
world:SetAttribute("Phase","CALM")
world:SetAttribute("SecondsLeft",75)
local palette={Color3.fromRGB(54,232,244),Color3.fromRGB(255,96,164),Color3.fromRGB(171,110,255),Color3.fromRGB(255,209,75),Color3.fromRGB(91,244,149)}
local biomes={
 {id="CYBER",name="Neon Metropolis",center=Vector3.new(180,0,0),color=palette[1]},
 {id="CRYSTAL",name="Prism Wilds",center=Vector3.new(-180,0,0),color=palette[3]},
 {id="VOLCANO",name="Magma Outpost",center=Vector3.new(0,0,180),color=palette[2]},
 {id="SKY",name="Cloud Kingdom",center=Vector3.new(0,0,-180),color=palette[4]},
}
local function part(name,size,pos,color,material,collide)
 local p=Instance.new("Part"); p.Name=name; p.Anchored=true; p.Size=size; p.Position=pos
 p.Material=material or Enum.Material.SmoothPlastic; p.Color=color
 p.CanCollide=collide~=false; p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth; p.Parent=world; return p
end
local function sign(text,pos,color,width)
 local anchor=part("SignAnchor",Vector3.new(1,1,1),pos,color,nil,false)
 anchor.Transparency=1
 local gui=Instance.new("BillboardGui"); gui.Size=UDim2.fromOffset(width or 280,64)
 gui.MaxDistance=160; gui.AlwaysOnTop=true; gui.Parent=anchor
 local label=Instance.new("TextLabel"); label.Size=UDim2.fromScale(1,1)
 label.BackgroundTransparency=1; label.Text=text; label.TextScaled=true
 label.TextColor3=color; label.TextStrokeTransparency=.3
 label.Font=Enum.Font.GothamBlack; label.Parent=gui
 return anchor
end
local function glow(p,color,range)
 local light=Instance.new("PointLight"); light.Color=color; light.Range=range or 14
 light.Brightness=1.2; light.Parent=p
end
Lighting.ClockTime=16; Lighting.Brightness=2.5
Lighting.Ambient=Color3.fromRGB(120,132,179)
local atmosphere=Instance.new("Atmosphere"); atmosphere.Density=.18
atmosphere.Color=Color3.fromRGB(155,176,236); atmosphere.Parent=Lighting
local bloom=Instance.new("BloomEffect"); bloom.Intensity=.22; bloom.Threshold=1.8
bloom.Size=24; bloom.Parent=Lighting
part("Void Floor",Vector3.new(650,2,650),Vector3.new(0,-70,0),Color3.fromRGB(14,13,32),nil,false)
local hub=part("Central Hub",Vector3.new(120,4,120),Vector3.new(0,-1,0),Color3.fromRGB(38,45,85))
local spawn=Instance.new("SpawnLocation"); spawn.Name="RiftRaidersSpawn"
spawn.Neutral=true; spawn.Anchored=true; spawn.Size=Vector3.new(22,1,22)
spawn.Position=Vector3.new(0,2,0); spawn.Material=Enum.Material.Neon
spawn.Color=palette[5]; spawn.Parent=world
sign("RIFT RAIDERS | CHAOS ISLANDS",Vector3.new(0,23,0),palette[4],460)
sign("BLAST DRONES • COLLECT SHARDS • SEAL RIFTS",Vector3.new(0,15,0),palette[1],460)
-- Central arena, tower, rings and colored paths: readable on a small screen.
for i=1,8 do
 local angle=(i-1)*math.pi/4
 local pos=Vector3.new(math.cos(angle)*47,8,math.sin(angle)*47)
 local tower=part("Hub Beacon Pillar",Vector3.new(6,16,6),pos,palette[(i-1)%5+1],Enum.Material.Metal)
 local lamp=part("Hub Beacon Light",Vector3.new(8,2,8),pos+Vector3.new(0,9,0),palette[(i-1)%5+1],Enum.Material.Neon)
 glow(lamp,lamp.Color)
end
local bridgeData={
 {Vector3.new(90,0,0),Vector3.new(75,2,22)},
 {Vector3.new(-90,0,0),Vector3.new(75,2,22)},
 {Vector3.new(0,0,90),Vector3.new(22,2,75)},
 {Vector3.new(0,0,-90),Vector3.new(22,2,75)},
}
for i,b in ipairs(bridgeData) do
 local walkway=part("Safe Skybridge",b[2],b[1],palette[i],Enum.Material.SmoothPlastic)
 for side=-1,1,2 do
  local railSize=i<=2 and Vector3.new(75,3,2) or Vector3.new(2,3,75)
  local offset=i<=2 and Vector3.new(0,2,side*11) or Vector3.new(side*11,2,0)
  part("Bridge Rail",railSize,b[1]+offset,Color3.fromRGB(31,40,76),Enum.Material.Metal)
 end
end
local shards={}
local drones={}
local beacons={}
-- Co-op Chaos Titan: a shared boss that appears during Rift Surge.
local boss=part("Chaos Titan",Vector3.new(17,17,17),Vector3.new(0,17,0),
 palette[2],Enum.Material.Neon,false)
boss.Shape=Enum.PartType.Ball; boss.Transparency=1; boss.CanTouch=false
boss:SetAttribute("Health",0)
glow(boss,palette[2],35)
local bossActive=false; local bossHP=0; local bossContributors={}
local bossAttackAt=0
for index,biome in ipairs(biomes) do
 local center=biome.center
 local base=part(biome.id.." Island",Vector3.new(115,4,115),center+Vector3.new(0,-1,0),
  Color3.fromRGB(38+index*9,37+index*7,75+index*7))
 sign(biome.name:upper(),center+Vector3.new(0,22,0),biome.color,360)
 for i=1,8 do
  local angle=i*math.pi/4
  local x=math.cos(angle)*42; local z=math.sin(angle)*42
  local height=9+(i%3)*9
  local p=part(biome.id.." Landmark",Vector3.new(9,height,9),
   center+Vector3.new(x,height/2,z),Color3.fromRGB(30,40,74),Enum.Material.Metal)
  local cap=part(biome.id.." Glow Roof",Vector3.new(11,2,11),
   p.Position+Vector3.new(0,height/2+1,0),biome.color,Enum.Material.Neon,false)
  if index==2 then
   local crystal=part("Prism Spire",Vector3.new(5,height+8,5),
    p.Position+Vector3.new(0,7,0),biome.color,Enum.Material.Glass,false)
   crystal.CFrame=crystal.CFrame*CFrame.Angles(0,math.rad(i*30),math.rad(10))
  elseif index==3 then
   local fire=Instance.new("Fire"); fire.Size=7; fire.Heat=5; fire.Parent=cap
  elseif index==4 then
   local cloud=part("Cloud Platform",Vector3.new(16,2,16),
    p.Position+Vector3.new(0,height/2+8,0),Color3.fromRGB(235,239,255),nil,false)
   cloud.Shape=Enum.PartType.Ball
  end
 end
 local beacon=part("Rift Core "..biome.id,Vector3.new(10,13,10),
  center+Vector3.new(0,8,28),biome.color,Enum.Material.Neon,false)
 beacon.Shape=Enum.PartType.Ball; glow(beacon,biome.color,22)
 local prompt=Instance.new("ProximityPrompt"); prompt.ActionText="Seal Rift (12 shards)"
 prompt.ObjectText=biome.name; prompt.HoldDuration=1; prompt.MaxActivationDistance=14
 prompt.RequiresLineOfSight=false; prompt.Parent=beacon
 beacons[beacon]=biome
 sign("SEAL RIFT: 12 SHARDS",beacon.Position+Vector3.new(0,12,0),biome.color,280)
 for i=1,9 do
  local angle=i*math.pi*2/9
  local radius=20+(i%3)*10
  local orb=part("Rift Shard",Vector3.new(4,4,4),
   center+Vector3.new(math.cos(angle)*radius,5,math.sin(angle)*radius),
   palette[(index+i-2)%5+1],Enum.Material.Neon,false)
  orb.Shape=Enum.PartType.Ball; orb:SetAttribute("Biome",biome.id)
  glow(orb,orb.Color,10)
  table.insert(shards,orb)
 end
 for i=1,3 do
  local a=i*math.pi*2/3
  local spawnPos=center+Vector3.new(math.cos(a)*28,6,math.sin(a)*28)
  local drone=part("Rift Drone",Vector3.new(7,7,7),spawnPos,
   biome.color,Enum.Material.Neon,false)
  drone.Shape=Enum.PartType.Ball; drone:SetAttribute("Health",3)
  drone:SetAttribute("Biome",biome.id)
  glow(drone,biome.color)
  drones[drone]={home=spawnPos,health=3,alive=true,attackAt=0}
 end
end
-- Reusable hand-built asset kit populates the islands without external downloads.
WorldKit.Populate(world,biomes)
-- A small physical skill course with a real summit reward.
local sky=biomes[4].center
for i=1,5 do
 part("Cloud Jump "..i,Vector3.new(13,2,13),
  sky+Vector3.new(-27+i*10,4+i*5,-18+((i%2)*10)),
  Color3.fromRGB(228,239,255))
end
local summit=part("Cloud Summit",Vector3.new(13,3,13),
 sky+Vector3.new(23,32,-8),palette[4],Enum.Material.Neon,false)
sign("SUMMIT BONUS +80 COINS",summit.Position+Vector3.new(0,7,0),palette[4])
local event=Instance.new("RemoteEvent"); event.Name="RiftRaidersEvent"; event.Parent=ReplicatedStorage
local action=Instance.new("RemoteEvent"); action.Name="RiftRaidersAction"; action.Parent=ReplicatedStorage
local activitySignal=Instance.new("RemoteEvent"); activitySignal.Name="RiftActivitiesSignal"; activitySignal.Parent=ReplicatedStorage
-- Two reusable first-person/third-person sci-fi weapons. The server decides hits.
local ServerStorage=game:GetService("ServerStorage")
local function makeWeapon(name,color,length)
 local tool=Instance.new("Tool"); tool.Name=name
 tool.ToolTip="Aim with camera, tap or click to fire"
 tool.RequiresHandle=true; tool.CanBeDropped=false
 tool.Grip=CFrame.new(0,-.2,-.6)*CFrame.Angles(0,math.rad(90),0)
 local handle=Instance.new("Part"); handle.Name="Handle"
 handle.Size=Vector3.new(1,1.2,3.2); handle.Color=Color3.fromRGB(38,45,63)
 handle.Material=Enum.Material.Metal; handle.CanCollide=false; handle.Massless=true
 handle.Parent=tool
 local barrel=Instance.new("Part"); barrel.Name="Glowing Barrel"
 barrel.Size=Vector3.new(.7,.7,length); barrel.Material=Enum.Material.Neon
 barrel.Color=color; barrel.CanCollide=false; barrel.Massless=true
 barrel.CFrame=handle.CFrame*CFrame.new(0,0,-length*.45)
 barrel.Parent=tool
 local weld=Instance.new("WeldConstraint"); weld.Part0=handle; weld.Part1=barrel; weld.Parent=handle
 tool.Parent=ServerStorage
 return tool
end
local pulseTemplate=makeWeapon("Pulse Rifle",palette[1],4)
local scatterTemplate=makeWeapon("Scatter Blaster",palette[2],2.5)
local function grantWeapon(p,template)
 local backpack=p:FindFirstChildOfClass("Backpack")
 if not backpack then return end
 if backpack:FindFirstChild(template.Name) or (p.Character and p.Character:FindFirstChild(template.Name)) then return end
 template:Clone().Parent=backpack
end
local profiles={}
local store=nil
local saveToken=game.JobId..":"..HttpService:GenerateGUID(false)
local SAVE_SCHEMA=10 -- no profile schema migration in v0.18.
if not RunService:IsStudio() and game.GameId~=0 then
 store=DataStoreService:GetDataStore("RiftRaidersProfiles_v1")
end
world:SetAttribute("StudioSavesIsolated",RunService:IsStudio() and store==nil)
local function cleanInt(n,max)
 return (type(n)=="number" and n==n and n>=0) and math.clamp(math.floor(n),0,max) or 0
end
local function tell(p,msg) event:FireClient(p,tostring(msg)) end
local function applyTrail(p)
 local s=profiles[p]
 local root=p.Character and p.Character:FindFirstChild("HumanoidRootPart")
 if not s or not root or not s.owned.AURORA_TRAIL then return end
 if root:FindFirstChild("AuroraLegendTrail") then return end
 local a=Instance.new("Attachment"); a.Name="AuroraTrailTop"
 a.Position=Vector3.new(0,1,0); a.Parent=root
 local b=Instance.new("Attachment"); b.Name="AuroraTrailBottom"
 b.Position=Vector3.new(0,-1,0); b.Parent=root
 local t=Instance.new("Trail"); t.Name="AuroraLegendTrail"
 t.Attachment0=a; t.Attachment1=b; t.Lifetime=.65
 t.MinLength=.12; t.LightEmission=.8; t.FaceCamera=true
 t.Color=ColorSequence.new(Color3.fromRGB(103,255,218),
  Color3.fromRGB(160,104,255))
 t.Transparency=NumberSequence.new(0.22,1)
 t.Parent=root
end
local function sync(p)
 local s=profiles[p]; if not s then return end
 p:SetAttribute("RRCoins",s.coins); p:SetAttribute("RRShards",s.shards)
 p:SetAttribute("RRLevel",s.level); p:SetAttribute("RRXP",s.xp)
 p:SetAttribute("RRBlaster",s.blaster); p:SetAttribute("RRShield",s.shieldOwned)
 p:SetAttribute("RRPet",s.petOwned); p:SetAttribute("RRSeals",s.seals)
 p:SetAttribute("RRScatter",s.scatterOwned)
 p:SetAttribute("RRQuestShards",s.quest.shards)
 p:SetAttribute("RRQuestDrones",s.quest.drones)
 p:SetAttribute("RRQuestSeals",s.quest.seals)
 local r=s.resources or {}
 p:SetAttribute("RRWood",r.wood or 0); p:SetAttribute("RRMetal",r.metal or 0)
 p:SetAttribute("RRFish",r.fish or 0); p:SetAttribute("RRHide",r.hide or 0)
 p:SetAttribute("RRToolkits",r.toolkit or 0)
 p:SetAttribute("RRHeat",s.heat or 0)
 p:SetAttribute("RRSportsWins",(s.jobs and s.jobs.sports) or 0)
 p:SetAttribute("RRHeists",(s.jobs and s.jobs.heists) or 0)
 p:SetAttribute("RRHouseOwned",(s.jobs and s.jobs.houseOwned) or false)
 for _,item in ipairs(Catalog.Items) do
  p:SetAttribute("RROwn_"..item.id,s.owned[item.id]==true)
 end
 p:SetAttribute("RRActiveVehicleWrap",
  s.owned.PLATINUM_WRAP and "PLATINUM" or
  s.owned.CITY_WRAP and "MIDNIGHT" or "DEFAULT")
 Life.Sync(p)
 Goals.Sync(p)
 Discovery.Sync(p)
 local ls=p:FindFirstChild("leaderstats")
 if ls then
  ls.Level.Value=s.level; ls.Coins.Value=s.coins; ls.Rifts.Value=s.seals
 end
end
local function reward(p,coins,xp,shards)
 local s=profiles[p]; if not s then return end
 local boost=world:GetAttribute("Phase")=="SURGE" and 2 or 1
 s.coins=math.min(1000000,s.coins+math.max(0,coins or 0)*boost)
 s.shards=math.min(100000,s.shards+math.max(0,shards or 0))
 s.xp+=math.max(0,xp or 0)
 while s.xp>=80+s.level*25 and s.level<100 do
  s.xp-=80+s.level*25; s.level+=1
  s.coins=math.min(1000000,s.coins+50)
  tell(p,"LEVEL UP! LEVEL "..s.level.." +50 COINS")
 end
 sync(p)
end
Goals.Initialize({getProfile=function(p) return profiles[p] end,
 reward=reward,sync=sync,tell=tell})
-- Seven terrain-based regions, interactive landmarks and server-owned portals.
local newDestinations=WorldExpansion.Build(world,WorldKit,reward,tell,Vehicles.Spawn)
local activityDestinations=WorldActivities.Build(world,{
 getProfile=function(p) return profiles[p] end,
 reward=reward,sync=sync,tell=tell,signal=activitySignal,
 spawnVehicle=Vehicles.Spawn,hasVehicle=Vehicles.HasActive
})
WorldPolish.Build(world,WorldKit)
local lifeDestination=Life.Build(world,{
 getProfile=function(p) return profiles[p] end,
 reward=reward,sync=sync,tell=tell,
 onActivity=function(p,kind,arg) Goals.Record(p,kind,arg) end,
})
LifeCityVisuals.Build(world)
local modernCityDestination=ModernCityIntegration.Build(world,spawn,tell,
 function(player,where) Goals.Record(player,"Travel",where) end)
local importedDowntown=workspace:FindFirstChild("OfficialModernCityDistrict")
if importedDowntown then
 Life.AttachDowntown(importedDowntown)
 DowntownPopulation.Build(world,importedDowntown,{tell=tell})
end
Life.Start()
local function quest(p,kind,n)
 local s=profiles[p]; if not s then return end
 s.quest[kind]=math.min(({shards=8,drones=3,seals=1})[kind],s.quest[kind]+(n or 1))
 if s.quest.shards==8 and s.quest.drones==3 and s.quest.seals==1 then
  s.quest={shards=0,drones=0,seals=0}
  reward(p,250,120,0); tell(p,"MISSION COMPLETE! +250 COINS +120 XP")
 end
 sync(p)
end
-- Serialize saves per player so an older retry cannot overwrite new data.
-- PlayerRemoving releases the lock only after a successful final save.
local function save(p,release)
 local s=profiles[p]
 if not store or not s or not s.loaded then return false end
 local waitSince=os.clock()
 while s.saving do
  if os.clock()-waitSince>25 then
   warn("RiftRaiders save lock wait timed out",p.UserId)
   return false
  end
  task.wait(.1)
 end
 s.saving=true
 local payload={version=10,coins=s.coins,shards=s.shards,level=s.level,xp=s.xp,
  blaster=s.blaster,shieldOwned=s.shieldOwned,petOwned=s.petOwned,
  scatterOwned=s.scatterOwned,seals=s.seals,
  resources={
   wood=cleanInt(s.resources.wood,9999),metal=cleanInt(s.resources.metal,9999),
   fish=cleanInt(s.resources.fish,9999),hide=cleanInt(s.resources.hide,9999),
   toolkit=cleanInt(s.resources.toolkit,9999)
  },
  jobs={
   sports=cleanInt(s.jobs.sports,100000),heists=cleanInt(s.jobs.heists,100000),
   bankCooldownUntil=cleanInt(s.jobs.bankCooldownUntil,9999999999),
   carCooldownUntil=cleanInt(s.jobs.carCooldownUntil,9999999999),
   houseOwned=s.jobs.houseOwned==true
  },
  prestige=Catalog.ValidateOwned(s.owned),
  life=Life.Serialize(s.life),
  goals=Goals.Normalize(s.goals),
  discover=Discovery.Normalize(s.discover)}
 local key="Player_"..p.UserId
 local success,detail=Persistence.Save(store,key,saveToken,payload,
  release==true,SAVE_SCHEMA)
 s.saving=false
 if not success then
  warn("RiftRaiders save could not be verified",p.UserId,detail)
 end
 return success
end
local function init(p)
 local s={coins=0,shards=0,level=1,xp=0,blaster=1,shieldOwned=false,
  petOwned=false,scatterOwned=false,seals=0,quest={shards=0,drones=0,seals=0},
  shardTimes={},beaconTimes={},summitAt=0,lastBlast=0,lastDash=0,lastShield=0,
  shieldUntil=0,travelAt=0,lastShoot=0,loaded=false,pet=nil,
  resources={wood=0,metal=0,fish=0,hide=0,toolkit=0},
  jobs={sports=0,heists=0,bankCooldownUntil=0,carCooldownUntil=0,
   houseOwned=false},owned={},life=Life.Normalize(nil),
  goals=Goals.Normalize(nil),
  discover=Discovery.Normalize(nil),heat=0}
 if store then
  local ok,data=Persistence.Acquire(store,"Player_"..p.UserId,
   saveToken,SAVE_SCHEMA)
  if not ok then
   warn("RiftRaiders player profile unavailable",p.UserId,data)
   p:Kick("Your game progress is still in use or saving. Please rejoin in a moment.")
   return
  end
   if type(data)=="table" and (data.version==nil or data.version==1 or data.version==2 or data.version==3 or data.version==4 or data.version==5 or data.version==6 or data.version==7 or data.version==8 or data.version==9 or data.version==10) then
    s.coins=cleanInt(data.coins,1000000); s.shards=cleanInt(data.shards,100000)
    s.level=math.max(1,cleanInt(data.level,100)); s.xp=cleanInt(data.xp,100000)
    s.blaster=math.clamp(cleanInt(data.blaster,4),1,4)
    s.shieldOwned=data.shieldOwned==true; s.petOwned=data.petOwned==true
    s.scatterOwned=data.scatterOwned==true
    s.seals=cleanInt(data.seals,1000000)
    if type(data.resources)=="table" then
     for _,key in ipairs({"wood","metal","fish","hide","toolkit"}) do
      s.resources[key]=cleanInt(data.resources[key],9999)
     end
    end
    if type(data.jobs)=="table" then
     s.jobs.sports=cleanInt(data.jobs.sports,100000)
     s.jobs.heists=cleanInt(data.jobs.heists,100000)
     s.jobs.bankCooldownUntil=cleanInt(data.jobs.bankCooldownUntil,9999999999)
     s.jobs.carCooldownUntil=cleanInt(data.jobs.carCooldownUntil,9999999999)
     s.jobs.houseOwned=data.jobs.houseOwned==true
    end
    s.owned=Catalog.ValidateOwned(data.prestige)
    s.life=Life.Normalize(data.life)
    s.goals=Goals.Normalize(data.goals)
    s.discover=Discovery.Normalize(data.discover)
   end
  s.loaded=true
 else
  -- Studio tests are local-memory only; NEVER write the live profile store.
  s.loaded=true
 end
 if not p.Parent then
  -- Client disconnected while the atomic load was in flight; free its lease
  -- without overwriting any earned progression.
  if store and s.loaded then
   Persistence.Release(store,"Player_"..p.UserId,saveToken)
  end
  return
 end
 profiles[p]=s
 WorldActivities.PlayerJoined(p)
 Life.PlayerJoined(p)
 local ls=Instance.new("Folder"); ls.Name="leaderstats"; ls.Parent=p
 for _,name in ipairs({"Level","Coins","Rifts"}) do
  local v=Instance.new("IntValue"); v.Name=name; v.Parent=ls
 end
 sync(p)
 task.defer(function()
  -- Players start as ordinary citizens in downtown, not armed adventurers.
  Life.GiveCamera(p)
 end)
 p.CharacterAdded:Connect(function()
  task.wait(.25)
  if profiles[p] then
   sync(p)
   Life.GiveCamera(p)
   applyTrail(p)
  end
 end)
 tell(p,"WELCOME TO RIFTLIFE! EXPLORE DOWNTOWN • WORLD → LIFE CITY FOR JOBS!")
end
Players.PlayerAdded:Connect(init)
Players.PlayerRemoving:Connect(function(p)
 WorldActivities.PlayerRemoving(p)
 save(p,true)
 local s=profiles[p]; if s and s.pet then s.pet:Destroy() end
 profiles[p]=nil
end)
for _,p in ipairs(Players:GetPlayers()) do task.spawn(init,p) end
task.spawn(function()
 -- Small jitter avoids simultaneous DataStore writes across game servers.
 task.wait(70+math.random(0,18))
 while world.Parent do
  for p in pairs(profiles) do task.spawn(save,p,false) end
  task.wait(84+math.random(0,12))
 end
end)
if store then
 game:BindToClose(function()
  local count=0
  local finished=0
  for p in pairs(profiles) do
   count+=1
   task.spawn(function()
    save(p,true)
    finished+=1
   end)
  end
  local started=os.clock()
  while finished<count and os.clock()-started<25 do task.wait(.1) end
 end)
end

local function rootFor(p)
 return p.Character and p.Character:FindFirstChild("HumanoidRootPart")
end
local function spawnPet(p)
 local s=profiles[p]; if not s or not s.petOwned or s.pet then return end
 local pet=part("Riftling Companion",Vector3.new(3.4,3.4,3.4),
  Vector3.new(0,10,0),palette[3],Enum.Material.Neon,false)
 pet.Shape=Enum.PartType.Ball; pet.CanTouch=false; s.pet=pet
 glow(pet,pet.Color,12)
end
local marinaDestination=Boats.Build(world)
local suburbanDestination=SuburbanDistrict.Build(world,{
 register=Life.RegisterSuburbanPoint,
 process=Life.Process,
 tell=tell,
})
Discovery.Build(world,{
 getProfile=function(p) return profiles[p] end,
 reward=reward,sync=sync,tell=tell,
})
local destinations={HUB=Vector3.new(0,6,0),WATERFRONT=marinaDestination}
for _,b in ipairs(biomes) do destinations[b.id]=b.center+Vector3.new(0,6,0) end
for id,pos in pairs(newDestinations) do destinations[id]=pos end
for id,pos in pairs(activityDestinations) do destinations[id]=pos end
destinations.LIFE=lifeDestination
destinations.ESTATES=Vector3.new(0,8,2711)
destinations.SUBURBIA=suburbanDestination
if modernCityDestination then destinations.MODERN=modernCityDestination end
local function blast(p)
 local s=profiles[p]; local root=rootFor(p)
 if not s or not root then return end
 local now=os.clock()
 if now-s.lastBlast<.55 then return end
 s.lastBlast=now
 if bossActive and (root.Position-boss.Position).Magnitude<48 then
  bossHP=math.max(0,bossHP-s.blaster)
  boss:SetAttribute("Health",bossHP)
  bossContributors[p]=true
  tell(p,"CHAOS TITAN HIT! "..bossHP.." HP LEFT!")
  if bossHP==0 then
   bossActive=false; boss.Transparency=1
   world:SetAttribute("BossHealth",0)
   for contributor in pairs(bossContributors) do
    if profiles[contributor] then
     reward(contributor,300,120,10)
     tell(contributor,"TITAN DEFEATED! +300 COINS +10 SHARDS!")
    end
   end
   bossContributors={}
  else
   world:SetAttribute("BossHealth",bossHP)
  end
  return
 end
 local target=nil; local best=32
 for drone,d in pairs(drones) do
  if d.alive then
   local delta=drone.Position-root.Position
   local distance=delta.Magnitude
   if distance<best then
    target=drone; best=distance
   end
  end
 end
 if not target then tell(p,"MOVE CLOSER TO A DRONE TO BLAST!"); return end
 local d=drones[target]
 d.health-=s.blaster
 target:SetAttribute("Health",math.max(0,d.health))
 tell(p,"ZAP! DRONE HIT "..s.blaster.." DAMAGE!")
 if d.health<=0 then
  d.alive=false; target.Transparency=1; target.CanTouch=false
  reward(p,30,25,2); quest(p,"drones",1)
  tell(p,"DRONE DEFEATED! +30 COINS +2 SHARDS!")
  task.delay(9,function()
   if target.Parent then
    d.alive=true; d.health=3; target.Position=d.home
    target.Transparency=0; target.CanTouch=true
    target:SetAttribute("Health",3)
   end
  end)
 end
end
-- Long-range pulse and scatter weapons: the client supplies aim, never a hit.
local function shoot(p,aim,weaponName)
 local s=profiles[p]; local root=rootFor(p)
 if not s or not root or typeof(aim)~="Vector3" then return end
 if aim.X~=aim.X or aim.Y~=aim.Y or aim.Z~=aim.Z then return end
 if aim.Magnitude<.9 or aim.Magnitude>1.1 then return end
 if weaponName~="Pulse Rifle" and weaponName~="Scatter Blaster" then return end
 if weaponName=="Scatter Blaster" and not s.scatterOwned then return end
 local backpack=p:FindFirstChildOfClass("Backpack")
 if not ((p.Character and p.Character:FindFirstChild(weaponName)) or
  (backpack and backpack:FindFirstChild(weaponName))) then return end
 local now=os.clock()
 local scatter=weaponName=="Scatter Blaster"
 if now-s.lastShoot<(scatter and .85 or .22) then return end
 s.lastShoot=now
 local origin=root.Position+Vector3.new(0,1.8,0)
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={p.Character}
 params.IgnoreWater=true
 local count=scatter and 4 or 1
 local maxDistance=scatter and 70 or 125
 for i=1,count do
  local spread=scatter and Vector3.new((i-2.5)*.045,((i%2)*2-1)*.035,0) or Vector3.zero
  local direction=(aim+spread).Unit
  local hit=workspace:Raycast(origin,direction*maxDistance,params)
  local endpoint=hit and hit.Position or origin+direction*maxDistance
  local length=(endpoint-origin).Magnitude
  if length>.1 then
   local tracer=Instance.new("Part"); tracer.Name="Pulse Tracer"
   tracer.Size=Vector3.new(.17,.17,length)
   tracer.CFrame=CFrame.lookAt((origin+endpoint)*.5,endpoint)
   tracer.Material=Enum.Material.Neon
   tracer.Color=scatter and palette[2] or palette[1]
   tracer.CanCollide=false; tracer.CanTouch=false; tracer.CanQuery=false
   tracer.Anchored=true; tracer.Parent=world
   Debris:AddItem(tracer,.12)
  end
  local target=hit and hit.Instance
  if target==boss and bossActive then
   bossHP=math.max(0,bossHP-1)
   boss:SetAttribute("Health",bossHP)
   bossContributors[p]=true
   world:SetAttribute("BossHealth",bossHP)
   if bossHP==0 then
    bossActive=false; boss.Transparency=1
    for contributor in pairs(bossContributors) do
     if profiles[contributor] then
      reward(contributor,300,120,10)
      tell(contributor,"TITAN DEFEATED! +300 COINS +10 SHARDS!")
     end
    end
    bossContributors={}
   end
  elseif target and drones[target] and drones[target].alive then
   local d=drones[target]
   d.health-=1
   target:SetAttribute("Health",math.max(0,d.health))
   if d.health<=0 then
    d.alive=false; target.Transparency=1; target.CanTouch=false
    reward(p,30,25,2); quest(p,"drones",1)
    tell(p,"DRONE DOWN! +30 COINS +2 SHARDS!")
    task.delay(9,function()
     if target.Parent then
      d.alive=true; d.health=3; target.Position=d.home
      target.Transparency=0; target.CanTouch=true
      target:SetAttribute("Health",3)
     end
    end)
   end
  end
 end
end
for _,shard in ipairs(shards) do
 shard.Touched:Connect(function(hit)
  local char=hit:FindFirstAncestorOfClass("Model")
  local p=char and Players:GetPlayerFromCharacter(char)
  local s=p and profiles[p]; local root=p and rootFor(p)
  if not s or not root or (root.Position-shard.Position).Magnitude>14 then return end
  local now=os.clock()
  if s.shardTimes[shard] and now-s.shardTimes[shard]<25 then return end
  s.shardTimes[shard]=now
  reward(p,5,8,1); quest(p,"shards",1)
  tell(p,"+1 RIFT SHARD • +5 COINS")
 end)
end
for beacon,biome in pairs(beacons) do
 local prompt=beacon:FindFirstChildOfClass("ProximityPrompt")
 prompt.Triggered:Connect(function(p)
  local s=profiles[p]; local root=rootFor(p)
  if not s or not root or (root.Position-beacon.Position).Magnitude>17 then return end
  local now=os.clock()
  if s.beaconTimes[beacon] and now-s.beaconTimes[beacon]<50 then
   tell(p,"THIS RIFT NEEDS TIME TO RECHARGE!"); return
  end
  if s.shards<12 then tell(p,"NEED 12 SHARDS TO SEAL THIS RIFT!"); return end
  s.shards-=12; s.beaconTimes[beacon]=now; s.seals+=1
  reward(p,75,80,0); quest(p,"seals",1)
  tell(p,"RIFT SEALED! "..biome.name:upper().." +75 COINS!")
 end)
end
summit.Touched:Connect(function(hit)
 local char=hit:FindFirstAncestorOfClass("Model")
 local p=char and Players:GetPlayerFromCharacter(char)
 local s=p and profiles[p]; local root=p and rootFor(p)
 if not s or not root or (root.Position-summit.Position).Magnitude>15 then return end
 if root.Position.Y<26 then return end
 local now=os.clock()
 if now-s.summitAt<60 then return end
 s.summitAt=now
 reward(p,80,65,3)
 tell(p,"SKY SUMMIT! +80 COINS +3 SHARDS!")
end)
action.OnServerEvent:Connect(function(p,kind,arg,extra)
 local s=profiles[p]; local root=rootFor(p)
 if not s or not root or type(kind)~="string" then return end
 local now=os.clock()
 if kind=="LifeAction" then
  if type(arg)=="string" and #arg<=24 then Life.Process(p,arg,extra) end
  return
 end
 if Life.IsJailed(p) then
  tell(p,"SERVE YOUR IN-GAME JAIL SENTENCE BEFORE TAKING ACTION.")
  return
 end
 if kind=="SpawnBoat" then
  local ok,message=Boats.Spawn(p,arg)
  tell(p,message)
  return
 end
 if kind=="ActivityHit" then
  if type(arg)=="string" and #arg<32 then WorldActivities.Hit(p,arg) end
  return
 end
 if kind=="Blast" then blast(p); return end
 if kind=="Shoot" then shoot(p,arg,extra); return end
 if kind=="SpawnCar" or kind=="SpawnSnowmobile" or kind=="SpawnFlyingCar" then
  local vehicleKind=kind=="SpawnSnowmobile" and "snowmobile" or
   kind=="SpawnFlyingCar" and "flyingcar" or "car"
  local ok,message=Vehicles.Spawn(world,p,vehicleKind)
  tell(p,message)
  return
 end
 if kind=="Dash" then
  if now-s.lastDash<6 then return end
  s.lastDash=now
  local direction=root.CFrame.LookVector
  root.AssemblyLinearVelocity=Vector3.new(direction.X*72,18,direction.Z*72)
  tell(p,"DASH!")
 elseif kind=="Shield" then
  if not s.shieldOwned then tell(p,"UNLOCK SHIELD IN SHOP FOR 150 COINS!"); return end
  if now-s.lastShield<20 then return end
  s.lastShield=now; s.shieldUntil=now+6
  local char=p.Character
  if char then
   local old=char:FindFirstChild("RiftShield")
   if old then old:Destroy() end
   local force=Instance.new("ForceField"); force.Name="RiftShield"
   force.Parent=char
   task.delay(6,function() if force.Parent then force:Destroy() end end)
  end
  tell(p,"SHIELD ACTIVE FOR 6 SECONDS!")
 elseif kind=="Travel" then
  if type(arg)~="string" or not destinations[arg] then return end
  if now-s.travelAt<2 then return end
  s.travelAt=now
  p.Character:PivotTo(CFrame.new(destinations[arg]))
  if arg=="MODERN" or arg=="LIFE" then
   -- Keep realistic life-simulation zones free of the fantasy rifle hotbar.
   for _,container in ipairs({p.Character,p:FindFirstChildOfClass("Backpack")}) do
    if container then
     for _,name in ipairs({"Pulse Rifle","Scatter Blaster"}) do
      local tool=container:FindFirstChild(name)
      if tool then tool:Destroy() end
     end
    end
   end
  else
   grantWeapon(p,pulseTemplate)
   if s.scatterOwned then grantWeapon(p,scatterTemplate) end
  end
  tell(p,"ARRIVED: "..arg)
  Goals.Record(p,"Travel",arg)
 elseif kind=="BuyPrestige" then
  if type(arg)~="string" then return end
  local item=Catalog.ById[arg]
  if not item then return end
  if s.owned[item.id] then tell(p,"ALREADY OWNED: "..item.name); return end
  if s.level<item.level then
   tell(p,item.name.." UNLOCKS AT LEVEL "..item.level); return
  end
  if s.coins<item.coins then
   tell(p,"EARN "..(item.coins-s.coins).." MORE COINS FOR "..item.name); return
  end
  local wood=item.wood or 0; local metal=item.metal or 0
  if s.resources.wood<wood or s.resources.metal<metal then
   tell(p,"NEED "..wood.." WOOD AND "..metal.." METAL"); return
  end
  s.coins-=item.coins
  s.resources.wood-=wood; s.resources.metal-=metal
  s.owned[item.id]=true
  sync(p)
  WorldActivities.RefreshHouse(p)
  applyTrail(p)
  tell(p,"PRESTIGE UNLOCKED: "..item.name.."!")
  return
 elseif kind=="Buy" then
  if arg=="BLASTER" then
   if s.blaster>=4 then tell(p,"BLASTER MAX LEVEL!"); return end
   local cost=s.blaster*90
   if s.coins<cost then tell(p,"NEED "..cost.." COINS!"); return end
   s.coins-=cost; s.blaster+=1
   tell(p,"BLASTER UPGRADED TO LEVEL "..s.blaster.."!")
  elseif arg=="SHIELD" then
   if s.shieldOwned then tell(p,"SHIELD ALREADY OWNED!"); return end
   if s.coins<150 then tell(p,"NEED 150 COINS!"); return end
   s.coins-=150; s.shieldOwned=true
   tell(p,"SHIELD UNLOCKED! PRESS SHIELD TO ACTIVATE!")
  elseif arg=="SCATTER" then
   if s.scatterOwned then tell(p,"SCATTER BLASTER ALREADY OWNED!"); return end
   if s.coins<175 then tell(p,"NEED 175 COINS!"); return end
   s.coins-=175; s.scatterOwned=true
   grantWeapon(p,scatterTemplate)
   tell(p,"SCATTER BLASTER UNLOCKED! EQUIP IT FROM BACKPACK!")
  elseif arg=="PET" then
   if s.petOwned then tell(p,"RIFTLING ALREADY OWNED!"); return end
   if s.coins<250 then tell(p,"NEED 250 COINS!"); return end
   s.coins-=250; s.petOwned=true; spawnPet(p)
   tell(p,"YOU ADOPTED A RIFTLING!")
  else return end
  sync(p)
 end
end)
local tickAccum=0
RunService.Heartbeat:Connect(function(dt)
 tickAccum+=dt
 if tickAccum<.18 then return end
 local step=math.min(tickAccum,.3); tickAccum=0
 for drone,d in pairs(drones) do
  if d.alive then
   local closest=nil; local best=52
   for p,s in pairs(profiles) do
    local root=rootFor(p)
    local hum=p.Character and p.Character:FindFirstChildOfClass("Humanoid")
    if root and hum and hum.Health>0 then
     local dist=(root.Position-drone.Position).Magnitude
     if dist<best then closest=p; best=dist end
    end
   end
   if closest then
    local root=rootFor(closest)
    local delta=root.Position-drone.Position
    if delta.Magnitude>4 then
     local nextPos=drone.Position+delta.Unit*math.min(delta.Magnitude,step*13)
     drone.Position=Vector3.new(nextPos.X,d.home.Y,nextPos.Z)
    elseif os.clock()-d.attackAt>2.2 then
     d.attackAt=os.clock()
     local s=profiles[closest]
     if s and os.clock()>s.shieldUntil then
      local hum=closest.Character and closest.Character:FindFirstChildOfClass("Humanoid")
      if hum then hum:TakeDamage(8) end
      tell(closest,"DRONE HIT! BLAST OR DASH TO ESCAPE!")
     end
    end
   else
    drone.Position=drone.Position:Lerp(d.home,.07)
   end
  end
 end
 if bossActive then
  boss.CFrame=boss.CFrame*CFrame.Angles(0,step*.5,0)
  if os.clock()-bossAttackAt>2.4 then
   bossAttackAt=os.clock()
   for p,s in pairs(profiles) do
    local root=rootFor(p)
    if root and (root.Position-boss.Position).Magnitude<24 and os.clock()>s.shieldUntil then
     local hum=p.Character and p.Character:FindFirstChildOfClass("Humanoid")
     if hum then hum:TakeDamage(10) end
     tell(p,"CHAOS TITAN SHOCKWAVE! DASH AWAY!")
    end
   end
  end
 end
 for p,s in pairs(profiles) do
  if s.petOwned and not s.pet then spawnPet(p) end
  local root=rootFor(p)
  if root and s.pet then s.pet.CFrame=root.CFrame*CFrame.new(3,3,3) end
 end
end)
task.spawn(function()
 while world.Parent do
  for remaining=75,0,-1 do
   world:SetAttribute("Phase","CALM")
   world:SetAttribute("SecondsLeft",remaining)
   task.wait(1)
  end
  world:SetAttribute("Phase","SURGE")
  bossHP=26; bossActive=true; bossContributors={}
  boss.Transparency=0; boss:SetAttribute("Health",bossHP)
  world:SetAttribute("BossHealth",bossHP)
  for _,p in ipairs(Players:GetPlayers()) do
   tell(p,"RIFT SURGE! DOUBLE COINS! DEFEAT THE CHAOS TITAN AT HUB!")
  end
  -- Do not tint the entire realistic downtown purple during fantasy surges.
  Lighting.Ambient=Color3.fromRGB(120,132,179)
  for remaining=25,0,-1 do
   world:SetAttribute("SecondsLeft",remaining)
   task.wait(1)
  end
  bossActive=false; bossHP=0; bossContributors={}
  boss.Transparency=1; boss:SetAttribute("Health",0)
  world:SetAttribute("BossHealth",0)
  Lighting.Ambient=Color3.fromRGB(120,132,179)
 end
end)
print("SF_RIFT_RAIDERS_SERVER_READY v0.19.0")
