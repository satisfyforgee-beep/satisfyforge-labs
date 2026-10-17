-- WORLD ACTIVITIES v0.4: original reusable server-authoritative minigames,
-- resource gathering, crafting and fictional crime jobs. No Robux transactions.
local Players=game:GetService("Players")
local Terrain=workspace.Terrain
local TweenService=game:GetService("TweenService")
local Debris=game:GetService("Debris")
local Kit={}
local sessions={}
local cooldowns={}
local stolen={}
local plotOwners={}
local playerPlots={}
local playerHouses={}
local plotCenters={}
local housingFolder=nil
local stations={}
local activityDefs={}
local function part(parent,name,size,cf,color,material,collide)
 local p=Instance.new("Part"); p.Name=name; p.Size=size; p.CFrame=cf
 p.Anchored=true; p.CanCollide=collide~=false; p.CanTouch=collide~=false
 p.Color=color; p.Material=material or Enum.Material.SmoothPlastic
 p.TopSurface=Enum.SurfaceType.Smooth; p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=parent
 return p
end
local function label(parent,title,pos,color)
 local anchor=part(parent,"Venue Sign",Vector3.new(1,1,1),CFrame.new(pos),color,nil,false)
 anchor.Transparency=1
 local gui=Instance.new("BillboardGui"); gui.Name="VenueLabel"
 gui.Size=UDim2.fromOffset(310,62); gui.MaxDistance=190
 gui.AlwaysOnTop=true; gui.Parent=anchor
 local text=Instance.new("TextLabel"); text.Size=UDim2.fromScale(1,1)
 text.BackgroundTransparency=1; text.Text=title; text.TextScaled=true
 text.Font=Enum.Font.GothamBlack; text.TextColor3=color
 text.TextStrokeTransparency=.2; text.Parent=gui
end
local function within(player,anchor,maxDistance)
 local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
 return root and (root.Position-anchor.Position).Magnitude<=(maxDistance or 18)
end
local function station(parent,id,title,actionText,position,color,callback)
 local base=part(parent,title,Vector3.new(6,6,6),CFrame.new(position),color,Enum.Material.Metal,true)
 base:SetAttribute("ActivityId",id)
 local p=Instance.new("ProximityPrompt")
 p.Name="ActivityPrompt"; p.ActionText=actionText; p.ObjectText=title
 p.HoldDuration=.35; p.MaxActivationDistance=12; p.RequiresLineOfSight=false
 p.Parent=base
 stations[id]=base
 p.Triggered:Connect(function(player)
  if within(player,base,17) then callback(player,id) end
 end)
 return base
end
local function safeResources(s)
 if type(s.resources)~="table" then s.resources={} end
 for _,key in ipairs({"wood","metal","fish","hide","toolkit"}) do
  local n=s.resources[key]
  s.resources[key]=(type(n)=="number" and n==n and n>=0)
   and math.clamp(math.floor(n),0,9999) or 0
 end
 if type(s.jobs)~="table" then s.jobs={} end
 s.jobs.sports=math.clamp(tonumber(s.jobs.sports) or 0,0,100000)
 s.jobs.bankCooldownUntil=math.max(0,tonumber(s.jobs.bankCooldownUntil) or 0)
 s.jobs.carCooldownUntil=math.max(0,tonumber(s.jobs.carCooldownUntil) or 0)
 s.jobs.heists=math.clamp(tonumber(s.jobs.heists) or 0,0,100000)
 s.jobs.houseOwned=s.jobs.houseOwned==true
end
local function cd(player,id,duration)
 cooldowns[player]=cooldowns[player] or {}
 local now=os.clock()
 if now<(cooldowns[player][id] or 0) then return false end
 cooldowns[player][id]=now+duration
 return true
end
local context=nil
local function profile(player)
 local s=context.getProfile(player)
 if s then safeResources(s) end
 return s
end
local function message(player,text) context.tell(player,text) end
local function give(player,coins,xp,shards)
 context.reward(player,coins,xp,shards or 0)
 context.sync(player)
end
local function actionVisual(id,anchor)
 if not anchor or not anchor.Parent then return end
 if id=="football" or id=="baseball" or id=="soccer" then
  local ball=Instance.new("Part"); ball.Name="Sports Shot Visual"
  ball.Shape=Enum.PartType.Ball
  ball.Size=Vector3.new(id=="baseball" and 1.1 or 2.5,
   id=="baseball" and 1.1 or 2.5,id=="baseball" and 1.1 or 2.5)
  ball.Material=Enum.Material.SmoothPlastic
  ball.Color=id=="football" and Color3.fromRGB(127,77,49) or Color3.fromRGB(244,246,242)
  ball.Anchored=true; ball.CanCollide=false; ball.CanTouch=false
  ball.Position=anchor.Position+Vector3.new(0,2,-4); ball.Parent=anchor.Parent
  local endPos=ball.Position+(id=="soccer" and Vector3.new(-33,0,0)
   or id=="football" and Vector3.new(35,0,0) or Vector3.new(0,0,-46))
  local top=endPos+Vector3.new(0,id=="soccer" and 10 or 22,0)
  local rise=TweenService:Create(ball,TweenInfo.new(.55,Enum.EasingStyle.Quad,Enum.EasingDirection.Out),
   {Position=top})
  local fall=TweenService:Create(ball,TweenInfo.new(.55,Enum.EasingStyle.Quad,Enum.EasingDirection.In),
   {Position=endPos})
  rise.Completed:Connect(function()
   if ball.Parent then fall:Play() end
  end)
  rise:Play(); Debris:AddItem(ball,1.4)
 elseif id=="fishing" then
  local splash=part(anchor.Parent,"Fishing Splash",Vector3.new(4,.4,4),
   CFrame.new(anchor.Position+Vector3.new(0,-2,-8)),
   Color3.fromRGB(119,220,255),Enum.Material.Neon,false)
  splash.Shape=Enum.PartType.Ball; splash.Transparency=.25
  TweenService:Create(splash,TweenInfo.new(.65),{
   Size=Vector3.new(9,.4,9),Transparency=1
  }):Play()
  Debris:AddItem(splash,.7)
 end
end
local function updateHeat(player,s,amount)
 s.heat=math.clamp((s.heat or 0)+amount,0,100)
 context.sync(player)
end
function Kit.Start(player,id)
 local def=activityDefs[id]
 local anchor=stations[id]
 local s=profile(player)
 if not def or not anchor or not s or not within(player,anchor,17) then return false end
 local now=os.clock()
 if sessions[player] and now-sessions[player].started<3.8 then
  message(player,"FINISH YOUR CURRENT CHALLENGE FIRST!")
  return false
 end
 if not cd(player,"start_"..id,1.5) then return false end
 if not cd(player,"play_"..id,def.cooldown or 12) then
  message(player,"ACTIVITY RECHARGING!")
  return false
 end
 local delay=1.9+math.random()*0.7
 sessions[player]={id=id,started=now,delay=delay}
 context.signal:FireClient(player,{
  kind="skill",id=id,title=def.title,delay=delay,duration=3.5
 })
 message(player,def.title..": TAP THE ACTION BUTTON WHEN THE METER HITS THE TARGET!")
 return true
end
function Kit.Hit(player,id)
 local session=sessions[player]
 local def=activityDefs[id]
 local anchor=stations[id]
 local s=profile(player)
 if not s or not session or session.id~=id or not def or not anchor then return false end
 sessions[player]=nil
 if not within(player,anchor,19) then return false end
 local delta=math.abs(os.clock()-session.started-session.delay)
 if delta>.58 then
  message(player,"MISSED! TRY AGAIN AFTER THE SHORT COOLDOWN.")
  return false
 end
 actionVisual(id,anchor)
 if id=="football" or id=="baseball" or id=="soccer" then
  s.jobs.sports+=1
  give(player,def.coins,def.xp,0)
  message(player,def.title.." SUCCESS! +"..def.coins.." COINS!")
 elseif id=="fishing" then
  s.resources.fish=math.min(9999,s.resources.fish+2)
  give(player,24,22,0)
  message(player,"CAUGHT 2 FISH! SELL YOUR CATCH AT THE MARKET!")
 elseif id=="hunting" then
  -- Fantasy tracking challenge; no gore, torture or realistic animal injuries.
  s.resources.hide=math.min(9999,s.resources.hide+1)
  give(player,28,24,0)
  message(player,"WILDLIFE TRACKED! +1 CRAFTING HIDE!")
 end
 context.sync(player)
 return true
end
local function buildHouse(player)
 local slot=playerPlots[player]
 if not slot or not housingFolder then return false end
 if playerHouses[player] then return true end
 local center=plotCenters[slot]
 if not center then return false end
 local m=Instance.new("Model"); m.Name="Player Home "..player.UserId
 m:SetAttribute("OwnerUserId",player.UserId); m:SetAttribute("PlotId",slot)
 m.Parent=housingFolder
 local wood=Color3.fromRGB(185,155,124)
 local trim=Color3.fromRGB(230,218,196)
 local roof=Color3.fromRGB(73,97,121)
 local base=part(m,"Home Floor",Vector3.new(32,1,28),
  CFrame.new(center+Vector3.new(0,2,0)),Color3.fromRGB(165,154,140),
  Enum.Material.WoodPlanks,true)
 m.PrimaryPart=base
 for _,x in ipairs({-16,16}) do
  part(m,"Side Wall",Vector3.new(1,15,28),
   CFrame.new(center+Vector3.new(x,10,0)),wood,Enum.Material.WoodPlanks,true)
  part(m,"House Window",Vector3.new(1.2,5,6),
   CFrame.new(center+Vector3.new(x*1.01,11,-4)),
   Color3.fromRGB(139,213,237),Enum.Material.Glass,false)
 end
 part(m,"Back Wall",Vector3.new(32,15,1),
  CFrame.new(center+Vector3.new(0,10,14)),wood,Enum.Material.WoodPlanks,true)
 for _,x in ipairs({-10,10}) do
  part(m,"Front Wall",Vector3.new(12,15,1),
   CFrame.new(center+Vector3.new(x,10,-14)),wood,Enum.Material.WoodPlanks,true)
 end
 part(m,"Doorway Header",Vector3.new(8,4,1),
  CFrame.new(center+Vector3.new(0,15.5,-14)),wood,Enum.Material.WoodPlanks,true)
 part(m,"House Roof",Vector3.new(37,3,33),
  CFrame.new(center+Vector3.new(0,19,0)),roof,Enum.Material.Slate,true)
 part(m,"Front Porch",Vector3.new(13,1,8),
  CFrame.new(center+Vector3.new(0,2,-18)),trim,Enum.Material.WoodPlanks,true)
 part(m,"Bed",Vector3.new(7,2,11),
  CFrame.new(center+Vector3.new(-9,4,7)),Color3.fromRGB(91,141,180),
  Enum.Material.Fabric,true)
 part(m,"Table",Vector3.new(6,3,5),
  CFrame.new(center+Vector3.new(8,4,5)),Color3.fromRGB(113,80,54),
  Enum.Material.Wood,true)
 label(m,player.DisplayName.."'S HOME",center+Vector3.new(0,26,0),
  Color3.fromRGB(243,220,165))
 playerHouses[player]=m
 return true
end
function Kit.PlayerJoined(player)
 local s=profile(player)
 if not s then return end
 for i=1,#plotCenters do
  if not plotOwners[i] then
   plotOwners[i]=player; playerPlots[player]=i
   player:SetAttribute("RRPlot",i)
   if s.jobs.houseOwned then buildHouse(player) end
   return
  end
 end
 message(player,"ALL HOME PLOTS ARE OCCUPIED ON THIS SERVER.")
end
function Kit.Perform(player,id)
 local anchor=stations[id]
 local s=profile(player)
 if not anchor or not s or not within(player,anchor,17) then return false end
 local r=s.resources
 if string.sub(id,1,11)=="gather_wood" then
  if not cd(player,id,18) then message(player,"TREES ARE REGROWING!"); return false end
  r.wood=math.min(9999,r.wood+2)
  give(player,8,10); message(player,"+2 WOOD +8 COINS")
 elseif string.sub(id,1,12)=="gather_metal" then
  if not cd(player,id,18) then message(player,"SCRAP IS REPLENISHING!"); return false end
  r.metal=math.min(9999,r.metal+2)
  give(player,8,10); message(player,"+2 METAL +8 COINS")
 elseif id=="craft_toolkit" then
  if r.wood<2 or r.metal<3 then
   message(player,"TOOLKIT NEEDS 2 WOOD + 3 METAL!"); return false
  end
  r.wood-=2; r.metal-=3; r.toolkit=math.min(9999,r.toolkit+1)
  context.sync(player); message(player,"CRAFTED A TOOLKIT!")
 elseif id=="sell_fish" then
  if r.fish<1 then message(player,"CATCH FISH AT THE MARINA FIRST!"); return false end
  local amount=math.min(10,r.fish)
  r.fish-=amount; give(player,amount*18,amount*2)
  message(player,"SOLD "..amount.." FISH FOR "..(amount*18).." COINS!")
 elseif id=="build_house" then
  if s.jobs.houseOwned then message(player,"YOU ALREADY OWN A HOME!"); return false end
  if s.level<2 then message(player,"HOME BUILDING UNLOCKS AT LEVEL 2!"); return false end
  if not playerPlots[player] then message(player,"NO FREE HOME PLOTS THIS SERVER!"); return false end
  if r.wood<8 or r.metal<6 then
   message(player,"HOUSE NEEDS 8 WOOD + 6 METAL!"); return false
  end
  r.wood-=8; r.metal-=6; s.jobs.houseOwned=true
  buildHouse(player)
  give(player,0,100)
  message(player,"HOME BUILT! VISIT YOUR PERSONAL PLOT!")
 elseif id=="bank_heist" then
  if s.level<3 then message(player,"BANK JOB UNLOCKS AT LEVEL 3!"); return false end
  if (s.heat or 0)>45 then message(player,"TOO MUCH HEAT! WAIT FOR THE ALERT TO CLEAR!"); return false end
  if r.toolkit<1 then message(player,"CRAFT A TOOLKIT AT THE HUB WORKSHOP!"); return false end
  if os.time()<s.jobs.bankCooldownUntil then
   message(player,"THE BANK IS ON LOCKDOWN!"); return false
  end
  r.toolkit-=1
  s.jobs.bankCooldownUntil=os.time()+300
  s.jobs.heists+=1
  updateHeat(player,s,75)
  give(player,250,145,3)
  message(player,"VAULT HEIST COMPLETE! +250 COINS • WANTED LEVEL HIGH!")
 elseif id=="steal_car" then
  if s.level<2 then message(player,"VEHICLE MISSION UNLOCKS AT LEVEL 2!"); return false end
  if r.toolkit<1 then message(player,"NEED A CRAFTED TOOLKIT TO HOTWIRE!"); return false end
  if os.time()<s.jobs.carCooldownUntil then message(player,"GARAGE SECURITY ALERT!"); return false end
  if (s.heat or 0)>70 then message(player,"LOSE YOUR WANTED LEVEL FIRST!"); return false end
  local ok,reason=context.spawnVehicle(context.world,player,"stolen")
  if not ok then message(player,reason); return false end
  r.toolkit-=1; s.jobs.carCooldownUntil=os.time()+180
  stolen[player]=true
  updateHeat(player,s,40)
  message(player,"FICTIONAL CAR HEIST! DRIVE TO THE CHOP SHOP!")
 elseif id=="chop_shop" then
  if not stolen[player] then message(player,"NO MISSION CAR TO SELL!"); return false end
  local carPosition=context.hasVehicle(player,"stolen")
  local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
  if not carPosition or not root or (carPosition-root.Position).Magnitude>45 then
   message(player,"BRING YOUR MISSION GETAWAY CAR TO THE CHOP SHOP!"); return false
  end
  stolen[player]=nil
  updateHeat(player,s,20)
  give(player,110,65)
  message(player,"CAR DELIVERY COMPLETE! +110 COINS!")
 else
  return false
 end
 context.sync(player)
 return true
end
local function sports(parent,center)
 local turf=Color3.fromRGB(56,134,83)
 Terrain:FillBlock(CFrame.new(center+Vector3.new(0,-4,0)),
  Vector3.new(280,12,225),Enum.Material.Grass)
 local plaza=part(parent,"Sports Plaza",Vector3.new(30,1,30),
  CFrame.new(center+Vector3.new(0,2.5,0)),Color3.fromRGB(195,205,212),Enum.Material.Concrete,true)
 label(parent,"WORLD SPORTS COMPLEX",center+Vector3.new(0,26,0),Color3.fromRGB(255,233,138))
 local pitch=part(parent,"Soccer Pitch",Vector3.new(83,1,52),
  CFrame.new(center+Vector3.new(-75,2,34)),turf,Enum.Material.Grass,true)
 for _,x in ipairs({-113,-37}) do
  part(parent,"Soccer Goal Crossbar",Vector3.new(2,1,19),
   CFrame.new(x,8,center.Z+34),Color3.fromRGB(242,245,249),Enum.Material.Metal,false)
  for _,z in ipairs({-9,9}) do
   part(parent,"Soccer Goal Post",Vector3.new(2,11,1),
    CFrame.new(x,7,center.Z+34+z),Color3.fromRGB(242,245,249),Enum.Material.Metal,false)
  end
 end
 station(parent,"soccer","Soccer Penalty Challenge","KICK",center+Vector3.new(-75,6,34),
  Color3.fromRGB(66,193,124),Kit.Start)
 local football=part(parent,"Football Field",Vector3.new(85,1,48),
  CFrame.new(center+Vector3.new(75,2,34)),Color3.fromRGB(48,115,68),Enum.Material.Grass,true)
 for j=0,10 do
  part(parent,"Football Yard Line",Vector3.new(.5,.1,47),
   CFrame.new(center+Vector3.new(33+j*8.3,2.6,34)),
   Color3.fromRGB(244,245,226),Enum.Material.SmoothPlastic,false)
 end
 for _,x in ipairs({34,116}) do
  part(parent,"Football Goal Crossbar",Vector3.new(1,1,19),
   CFrame.new(center+Vector3.new(x,14,34)),
   Color3.fromRGB(247,208,85),Enum.Material.Metal,false)
  for _,z in ipairs({-9,9}) do
   part(parent,"Football Upright",Vector3.new(1,10,1),
    CFrame.new(center+Vector3.new(x,19,34+z)),
    Color3.fromRGB(247,208,85),Enum.Material.Metal,false)
  end
 end
 station(parent,"football","Football Field Goal","KICK",center+Vector3.new(75,6,34),
  Color3.fromRGB(244,183,76),Kit.Start)
 local diamond=part(parent,"Baseball Diamond",Vector3.new(65,1,65),
  CFrame.new(center+Vector3.new(0,2,-65)),
  Color3.fromRGB(175,126,86),Enum.Material.Ground,true)
 diamond.CFrame=diamond.CFrame*CFrame.Angles(0,math.rad(45),0)
 for _,offset in ipairs({
  Vector3.new(0,3,-87),Vector3.new(-21,3,-65),
  Vector3.new(0,3,-43),Vector3.new(21,3,-65)
 }) do
  part(parent,"Baseball Base",Vector3.new(4,.3,4),
   CFrame.new(center+offset),Color3.fromRGB(248,248,242),Enum.Material.SmoothPlastic,true)
 end
 station(parent,"baseball","Baseball Batting Cage","SWING",center+Vector3.new(0,6,-65),
  Color3.fromRGB(226,115,80),Kit.Start)
 for _,x in ipairs({-122,122}) do
  for i=1,5 do
   part(parent,"Stadium Bleacher",Vector3.new(9,2,65),
    CFrame.new(center+Vector3.new(x,3+i*2,35)),
    Color3.fromRGB(92,111,137),Enum.Material.Metal,true)
  end
 end
 for _,pos in ipairs({
  Vector3.new(-112,3,-90),Vector3.new(112,3,-90),
  Vector3.new(-112,3,90),Vector3.new(112,3,90)
 }) do
  local pole=part(parent,"Stadium Floodlight Pole",Vector3.new(2,30,2),
   CFrame.new(center+pos+Vector3.new(0,15,0)),
   Color3.fromRGB(82,99,118),Enum.Material.Metal,true)
  local light=part(parent,"Stadium Floodlight",Vector3.new(10,3,3),
   CFrame.new(center+pos+Vector3.new(0,31,0)),
   Color3.fromRGB(241,246,221),Enum.Material.Neon,false)
  local point=Instance.new("PointLight"); point.Range=55; point.Brightness=1.2; point.Parent=light
 end
 return plaza
end
function Kit.Build(world,options)
 context=options
 context.world=world
 local area=Instance.new("Folder"); area.Name="Sports and Life Activities"; area.Parent=world
 local center=Vector3.new(0,0,900)
 sports(area,center)
 local homeCenter=Vector3.new(0,0,1260)
 housingFolder=Instance.new("Folder")
 housingFolder.Name="Player Housing Neighborhood"; housingFolder.Parent=area
 Terrain:FillBlock(CFrame.new(homeCenter+Vector3.new(0,-4,0)),
  Vector3.new(420,12,300),Enum.Material.Grass)
 local homeRoad=part(housingFolder,"Neighborhood Road",Vector3.new(370,1,14),
  CFrame.new(homeCenter+Vector3.new(0,2.4,0)),
  Color3.fromRGB(71,77,84),Enum.Material.Asphalt,true)
 label(housingFolder,"HOUSING MEADOWS • BUILD YOUR HOME",
  homeCenter+Vector3.new(0,29,0),Color3.fromRGB(251,225,177))
 for _,z in ipairs({-95,0,95}) do
  for _,x in ipairs({-150,-50,50,150}) do
   local spot=homeCenter+Vector3.new(x,0,z)
   table.insert(plotCenters,spot)
   local tile=part(housingFolder,"Home Plot "..#plotCenters,
    Vector3.new(42,1,42),CFrame.new(spot+Vector3.new(0,2.3,0)),
    Color3.fromRGB(111,159,96),Enum.Material.Grass,true)
   tile:SetAttribute("PlotId",#plotCenters)
  end
 end
 station(area,"build_house","Housing Construction Office","BUILD HOME",
  homeCenter+Vector3.new(0,5,26),Color3.fromRGB(177,133,88),Kit.Perform)
 activityDefs={
  football={title="FOOTBALL FIELD GOAL",coins=35,xp=32,cooldown=14},
  baseball={title="BASEBALL HOME RUN",coins=32,xp=30,cooldown=14},
  soccer={title="SOCCER PENALTY KICK",coins=33,xp=30,cooldown=14},
  fishing={title="FISHING CAST",coins=24,xp=22,cooldown=15},
  hunting={title="WILDLIFE TRACKING HUNT",coins=28,xp=24,cooldown=20},
 }
 station(area,"gather_wood","Lumber Camp","GATHER WOOD",
  Vector3.new(-520+40,5,0-12),Color3.fromRGB(153,104,57),Kit.Perform)
 for i=2,5 do
  station(area,"gather_wood_"..i,"Lumber Stand "..i,"GATHER WOOD",
   Vector3.new(-520+32+i*9,5,-24),
   Color3.fromRGB(142,102,59),Kit.Perform)
 end
 station(area,"gather_metal","Metropolis Scrap Yard","SALVAGE METAL",
  Vector3.new(180-29,5,-24),Color3.fromRGB(102,144,165),Kit.Perform)
 station(area,"gather_metal_alt","Salvage Yard Overflow","SALVAGE METAL",
  Vector3.new(180-31,5,-35),Color3.fromRGB(98,140,160),Kit.Perform)
 station(area,"gather_metal_alt2","Salvage Yard South","SALVAGE METAL",
  Vector3.new(180-21,5,-38),Color3.fromRGB(92,133,156),Kit.Perform)
 for i=3,4 do
  station(area,"gather_metal_alt"..i,"Scrap Depot "..i,"SALVAGE METAL",
   Vector3.new(180+5+i*6,5,-34),
   Color3.fromRGB(90,136,157),Kit.Perform)
 end
 station(area,"craft_toolkit","Hub Workshop","CRAFT TOOLKIT",
  Vector3.new(-23,5,17),Color3.fromRGB(212,158,84),Kit.Perform)
 station(area,"sell_fish","Marina Fish Market","SELL FISH",
  Vector3.new(520-22,5,520+28),Color3.fromRGB(79,173,196),Kit.Perform)
 station(area,"fishing","Fishing Challenge Pier","CAST LINE",
  Vector3.new(520+7,6,520+116),Color3.fromRGB(66,172,215),Kit.Start)
 station(area,"hunting","Safari Wildlife Tracking","TRACK GAME",
  Vector3.new(-520+22,5,-520-22),Color3.fromRGB(164,134,76),Kit.Start)
 station(area,"bank_heist","Bank Vault Mission","OPEN VAULT",
  Vector3.new(180+31,6,31-19),Color3.fromRGB(220,100,91),Kit.Perform)
 station(area,"steal_car","NPC Vehicle Depot","HOTWIRE NPC CAR",
  Vector3.new(180-27,5,29),Color3.fromRGB(179,109,206),Kit.Perform)
 station(area,"chop_shop","Chop Shop Delivery","DELIVER MISSION CAR",
  Vector3.new(180-39,5,45),Color3.fromRGB(198,158,87),Kit.Perform)
 -- Low-poly physical details, all original and reusable.
 for i=1,4 do
  part(area,"Lumber Logs",Vector3.new(2,2,12),
   CFrame.new(Vector3.new(-520+31+i*3,3,-22)),
   Color3.fromRGB(129,83,52),Enum.Material.Wood,true)
  part(area,"Scrap Metal Stack",Vector3.new(4,1+i,6),
   CFrame.new(Vector3.new(180-38+i*3,3+i*.5,-25)),
   Color3.fromRGB(92,105,123),Enum.Material.CorrodedMetal,true)
 end
 part(area,"Crafting Workbench",Vector3.new(11,2,5),
  CFrame.new(-23,2,25),Color3.fromRGB(145,103,68),Enum.Material.WoodPlanks,true)
 for i=1,3 do
  part(area,"Fish Market Crate",Vector3.new(5,4,5),
   CFrame.new(Vector3.new(520-31+i*5,4,520+37)),
   Color3.fromRGB(165,119,72),Enum.Material.WoodPlanks,true)
 end
 part(area,"Vault Security Light",Vector3.new(9,1,1),
  CFrame.new(211,11,11),Color3.fromRGB(255,75,83),Enum.Material.Neon,false)
 label(area,"SPORTS: FOOTBALL • BASEBALL • SOCCER",
  center+Vector3.new(0,18,18),Color3.fromRGB(249,242,198))
 label(area,"BANK HEIST • REQUIRES LEVEL 3 + TOOLKIT",
  Vector3.new(211,20,12),Color3.fromRGB(241,127,108))
 -- Server-only heat decay; no realistic death or gore.
 task.spawn(function()
  while world.Parent do
   task.wait(5)
   for _,player in ipairs(Players:GetPlayers()) do
    local s=profile(player)
    if s and (s.heat or 0)>0 then
     s.heat=math.max(0,s.heat-3)
     context.sync(player)
    end
   end
  end
 end)
 return {SPORTS=center+Vector3.new(0,8,0),HOMES=homeCenter+Vector3.new(0,8,0)}
end
function Kit.PlayerRemoving(player)
 sessions[player]=nil; cooldowns[player]=nil; stolen[player]=nil
 local slot=playerPlots[player]
 if slot then plotOwners[slot]=nil; playerPlots[player]=nil end
 if playerHouses[player] then playerHouses[player]:Destroy(); playerHouses[player]=nil end
end
function Kit.GetStation(id)
 return stations[id]
end
return Kit
