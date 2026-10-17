-- Original, session-only prototype; no paid features or persistence.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local Lighting=game:GetService("Lighting")
local RunService=game:GetService("RunService")
local world=Instance.new("Folder"); world.Name="HyperMutationRushWorld"; world.Parent=workspace
world:SetAttribute("Version","0.2.0")
local palette={Color3.fromRGB(255,82,164),Color3.fromRGB(65,235,255),Color3.fromRGB(255,222,62),Color3.fromRGB(157,92,255),Color3.fromRGB(83,250,134)}
local function part(name,size,pos,color,kind)
 local p=Instance.new("Part"); p.Name=name; p.Anchored=true; p.Size=size; p.Position=pos
 p.Color=color; p.Material=Enum.Material.Neon; p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth; p.Parent=world
 if kind then p.CanCollide=false; p:SetAttribute("Kind",kind) end
 return p
end
local function sign(text,pos,color)
 local p=part("FloatingSign",Vector3.new(1,1,1),pos,color)
 p.Transparency=1; p.CanCollide=false
 local g=Instance.new("BillboardGui"); g.Size=UDim2.fromOffset(320,70)
 g.AlwaysOnTop=true; g.MaxDistance=180; g.Parent=p
 local t=Instance.new("TextLabel"); t.Size=UDim2.fromScale(1,1)
 t.BackgroundTransparency=1; t.Text=text; t.TextScaled=true
 t.TextColor3=color; t.TextStrokeTransparency=.3
 t.Font=Enum.Font.GothamBlack; t.Parent=g
end
Lighting.ClockTime=13.5; Lighting.Brightness=3; Lighting.Ambient=Color3.fromRGB(180,190,222)
local spawn=Instance.new("SpawnLocation"); spawn.Name="Start"; spawn.Neutral=true
spawn.Size=Vector3.new(32,1,28); spawn.Position=Vector3.new(0,0,50)
spawn.Anchored=true; spawn.Color=palette[2]; spawn.Material=Enum.Material.Neon; spawn.Parent=world
part("Track",Vector3.new(34,2,440),Vector3.new(0,-2,-160),Color3.fromRGB(55,68,112))
sign("RUN! COLLECT ORBS! JUMP OVER LASERS!",Vector3.new(0,10,45),palette[3])
for i=1,12 do
 local z=36-i*32; local color=palette[(i-1)%5+1]
 local tile=part("ColorLane",Vector3.new(34,.2,30),Vector3.new(0,-.85,z),color)
 tile.Transparency=.7
 for _,x in ipairs({-16,16}) do
  local rail=part("SideRail",Vector3.new(1.5,5,32),Vector3.new(x,2,z),color)
  rail.CanCollide=true
 end
 local check=part("Checkpoint",Vector3.new(30,8,1.5),Vector3.new(0,4,z+10),color,"Checkpoint")
 check.Transparency=.68; check:SetAttribute("Stage",i)
 if i%2==1 then
  for _,x in ipairs({-9,0,9}) do
   local orb=part("SpeedOrb",Vector3.new(3.5,3.5,3.5),Vector3.new(x,3,z-4),palette[3],"Orb")
   orb.Shape=Enum.PartType.Ball
   local light=Instance.new("PointLight"); light.Color=palette[3]; light.Range=12; light.Parent=orb
  end
 else
  part("JumpLaser",Vector3.new(31,2,2),Vector3.new(0,2,z-4),palette[1],"Hazard")
  sign("JUMP THE LASER!",Vector3.new(0,9,z+2),palette[1])
 end
 if i==4 or i==8 then
  local gate=part("MutationGate",Vector3.new(18,12,2),Vector3.new(0,6,z-10),palette[4],"Mutation")
  gate.Transparency=.55
  sign("FREE MUTATION +3 SPEED",Vector3.new(0,15,z-10),palette[4])
 end
end
local finish=part("FinishPortal",Vector3.new(32,12,2),Vector3.new(0,6,-380),palette[5],"Finish")
finish.Transparency=.3; sign("FINISH! +100 COINS",Vector3.new(0,16,-380),palette[5])
part("FallReset",Vector3.new(150,2,500),Vector3.new(0,-25,-160),palette[1],"Fall").Transparency=1
-- Expansive shared hub: six original districts, each with an activity to explore.
-- Keep the race connected to the hub; multiplayer characters share the same world.
local districts={
 {"Mutation City",Vector3.new(170,0,55),palette[4],"CITY PLAZA + SOCIAL HUB"},
 {"Crystal Caves",Vector3.new(340,0,55),palette[2],"FIND THE CRYSTALS"},
 {"Sky Parkour",Vector3.new(510,0,55),palette[3],"CLIMB THE SKY TOWERS"},
 {"Battle Dome",Vector3.new(-170,0,55),palette[1],"DODGE THE DOME LASERS"},
 {"Treasure Island",Vector3.new(-340,0,55),palette[5],"HUNT THE TREASURE"},
 {"Festival Grounds",Vector3.new(-510,0,55),palette[4],"EXPLORE THE FESTIVAL"},
}
for _,info in ipairs(districts) do
 local name,center,color,headline=info[1],info[2],info[3],info[4]
 local base=part(name.." Platform",Vector3.new(115,2,115),center+Vector3.new(0,-2,0),color)
 base.Material=Enum.Material.SmoothPlastic
 sign(headline,center+Vector3.new(0,15,0),color)
 for n=1,8 do
  local a=(n-1)*math.pi/4
  local pos=center+Vector3.new(math.cos(a)*42,0,math.sin(a)*42)
  local tower=part(name.." Landmark",Vector3.new(9,10+(n%4)*9,9),pos,palette[(n-1)%5+1])
  tower.CanCollide=true
 end
 local bridgeStart=math.min(math.abs(center.X),170)
 local direction=center.X>0 and 1 or -1
 for segment=1,math.floor(math.abs(center.X)/20) do
  local x=direction*(segment*20)
  local walkway=part(name.." Skybridge",Vector3.new(20,1,12),Vector3.new(x,-1,55),color)
  walkway.Material=Enum.Material.SmoothPlastic
 end
end
-- Cooperative collectible scavenger hunt: a shared world, independent player rewards.
local treasurePositions={Vector3.new(340,3,55),Vector3.new(-340,3,55),Vector3.new(510,3,55),Vector3.new(-510,3,55)}
for i,pos in ipairs(treasurePositions) do
 local crystal=part("HiddenTreasure"..i,Vector3.new(5,5,5),pos,palette[(i%5)+1],"Treasure")
 crystal.Shape=Enum.PartType.Ball
 sign("+30 COINS SECRET!",pos+Vector3.new(0,5,0),palette[3])
end
-- Playable activities, not just themed signs. Each reward is checked server-side.
-- Repeating minigames use cooldowns to avoid touch spam and accidental farming.
local function activity(name,kind,pos,color,title,reward,cooldown)
 local trigger=part(name,Vector3.new(11,3,11),pos,color,kind)
 trigger.Shape=Enum.PartType.Cylinder
 trigger:SetAttribute("Reward",reward or 0)
 trigger:SetAttribute("Cooldown",cooldown or 20)
 sign(title,pos+Vector3.new(0,7,0),color)
 return trigger
end
-- City: timed delivery challenge between two glowing pads.
activity("City Delivery Start","DeliveryStart",Vector3.new(130,2,55),palette[2],"DELIVERY RACE! START HERE",0,4)
activity("City Delivery Finish","DeliveryFinish",Vector3.new(207,2,55),palette[5],"DELIVER! +45 COINS",45,8)
-- Caves: find four distinct crystal nodes; each player's progress is independent.
for i,pos in ipairs({
 Vector3.new(318,3,20),Vector3.new(362,3,25),Vector3.new(315,3,88),Vector3.new(364,3,91),
}) do
 activity("Cave Crystal "..i,"CaveCrystal",pos,palette[2],"CRYSTAL +"..(10*i).." COINS",10*i,45)
end
-- Sky parkour: four elevated platforms and a rooftop checkpoint.
for i=1,5 do
 local x=477+i*10
 local y=3+i*6
 local z=55+((i%2==0) and 13 or -13)
 part("Sky Jump Platform "..i,Vector3.new(14,2,14),Vector3.new(x,y,z),palette[(i%5)+1])
end
activity("Sky Summit","SkySummit",Vector3.new(527,37,42),palette[3],"SKY SUMMIT! +80 COINS",80,60)
-- Dome: short survival game. Stay inside for 12 seconds while beams pulse.
activity("Dome Start","DomeStart",Vector3.new(-170,2,55),palette[1],"DODGE SURVIVAL! 12 SECONDS",0,15)
for i=1,4 do
 local laser=part("Dome Hazard "..i,Vector3.new(3,6,75),
  Vector3.new(-205+i*14,3,55),palette[1],"DomeLaser")
 laser.Transparency=.45
end
-- Festival: three color buttons in a sequence. Press red, yellow, green.
local festival={palette[1],palette[3],palette[5]}
for i=1,3 do
 local tile=activity("Festival Button "..i,"FestivalButton",
  Vector3.new(-548+i*19,2,36),festival[i],
  ({"1 RED","2 YELLOW","3 GREEN"})[i],0,2)
 tile:SetAttribute("Step",i)
end
-- Treasure island: a replayable chest with a 90s cooldown.
activity("Treasure Chest","Chest",Vector3.new(-340,3,95),palette[3],
 "OPEN CHEST! +50 COINS",50,90)
-- Shared global event: colorful lightning storm; staying on a district platform is safe.
world:SetAttribute("WorldEvent","CALM")
task.spawn(function()
 while world.Parent do
  task.wait(85)
  world:SetAttribute("WorldEvent","COLOR STORM")
  for i=1,6 do
   Lighting.Ambient=palette[i%5+1]
   task.wait(1)
  end
  Lighting.Ambient=Color3.fromRGB(180,190,222)
  world:SetAttribute("WorldEvent","CALM")
 end
end)
local remote=Instance.new("RemoteEvent"); remote.Name="MutationRushEvent"; remote.Parent=ReplicatedStorage
local action=Instance.new("RemoteEvent"); action.Name="MutationRushAction"; action.Parent=ReplicatedStorage
local sessions={}
local destinations={
 ["RACE"]=Vector3.new(0,5,50),
 ["CITY"]=Vector3.new(170,5,55),
 ["CAVES"]=Vector3.new(340,5,55),
 ["SKY"]=Vector3.new(510,5,55),
 ["DOME"]=Vector3.new(-170,5,55),
 ["TREASURE"]=Vector3.new(-340,5,55),
 ["FESTIVAL"]=Vector3.new(-510,5,55),
}
local function tell(p,text) remote:FireClient(p,text) end
local function sync(p)
 local s=sessions[p]; if not s then return end
 p:SetAttribute("MRStage",s.stage); p:SetAttribute("MRSpeed",s.speed)
 p:SetAttribute("MRCoins",s.coins); p:SetAttribute("MRMutations",s.mutations)
 p:SetAttribute("MRWins",s.wins)
 p:SetAttribute("MRQuest",s.quest)
 local leaderstats=p:FindFirstChild("leaderstats")
 if leaderstats then
  local wins=leaderstats:FindFirstChild("Wins")
  local coins=leaderstats:FindFirstChild("Coins")
  if wins then wins.Value=s.wins end
  if coins then coins.Value=s.coins end
 end
 local h=p.Character and p.Character:FindFirstChildOfClass("Humanoid")
 if h then h.WalkSpeed=s.speed; h.UseJumpPower=true; h.JumpPower=58 end
end
local function warp(p)
 if p.Character then p.Character:PivotTo(CFrame.new(0,5,50)) end
end
local function init(p)
 local leaderstats=Instance.new("Folder"); leaderstats.Name="leaderstats"; leaderstats.Parent=p
 local wins=Instance.new("IntValue"); wins.Name="Wins"; wins.Parent=leaderstats
 local coins=Instance.new("IntValue"); coins.Name="Coins"; coins.Parent=leaderstats
 sessions[p]={stage=0,speed=18,coins=0,mutations=0,wins=0,used={},lastHit=-10,lastFinish=-10,activityTimes={},deliveryAt=nil,festivalStep=0,domeStart=nil,quest=0,questKinds={},pet=nil}
 sync(p); p.CharacterAdded:Connect(function() task.wait(.2); sync(p) end)
end
Players.PlayerAdded:Connect(init)
Players.PlayerRemoving:Connect(function(p)
 local s=sessions[p]
 if s and s.pet then s.pet:Destroy() end
 sessions[p]=nil
end)
for _,p in ipairs(Players:GetPlayers()) do init(p) end
-- Repeatable three-activity quest. Reward comes from server-verified actions only.
local function questProgress(p,kind)
 local s=sessions[p]; if not s then return end
 if s.questKinds[kind] then return end
 s.questKinds[kind]=true
 s.quest+=1
 if s.quest>=3 then
  s.coins=math.min(100000,s.coins+150)
  s.quest=0; s.questKinds={}
  tell(p,"WORLD QUEST COMPLETE! +150 COINS!")
 else
  tell(p,"WORLD QUEST "..s.quest.."/3 ACTIVITIES!")
 end
 sync(p)
end
-- Collectible companion, free and earned through normal gameplay.
local function equipPet(p)
 local s=sessions[p]
 if not s or s.pet or s.coins<120 then return end
 s.coins-=120
 local pet=Instance.new("Part"); pet.Name="MutationBuddy"
 pet.Shape=Enum.PartType.Ball; pet.Size=Vector3.new(3,3,3)
 pet.Material=Enum.Material.Neon; pet.Color=palette[4]
 pet.CanCollide=false; pet.CanTouch=false; pet.Anchored=true
 pet.Parent=world; s.pet=pet
 local light=Instance.new("PointLight"); light.Color=palette[4]; light.Range=12; light.Parent=pet
 sync(p); tell(p,"MUTATION BUDDY UNLOCKED! FREE PET!")
end
local petTick=0
RunService.Heartbeat:Connect(function(dt)
 petTick+=dt
 if petTick<.15 then return end
 petTick=0
 for p,s in pairs(sessions) do
  local pet=s.pet
  if pet then
   local root=p.Character and p.Character:FindFirstChild("HumanoidRootPart")
   if root then pet.CFrame=root.CFrame*CFrame.new(3,2,3) end
  end
 end
end)
local function touched(obj,hit)
 local char=hit:FindFirstAncestorOfClass("Model")
 local p=char and Players:GetPlayerFromCharacter(char)
 local s=p and sessions[p]; if not s then return end
 local root=char:FindFirstChild("HumanoidRootPart")
 if not root or (root.Position-obj.Position).Magnitude>18 then return end
 local kind=obj:GetAttribute("Kind"); local now=os.clock()
 if kind=="Checkpoint" then
  local stage=obj:GetAttribute("Stage")
  if stage~=s.stage+1 then return end
  s.stage=stage; s.coins=math.min(100000,s.coins+5)
  tell(p,"CHECKPOINT "..stage.."/12! +5 COINS")
 elseif kind=="Orb" then
  if s.used[obj] then return end
  s.used[obj]=true; s.speed=math.min(48,s.speed+1)
  s.coins=math.min(100000,s.coins+10); tell(p,"+1 SPEED! +10 COINS!")
 elseif kind=="Treasure" then
  if s.used[obj] then return end
  s.used[obj]=true; s.coins=math.min(100000,s.coins+30)
  tell(p,"SECRET TREASURE! +30 COINS!")
  questProgress(p,"Treasure")
 elseif kind=="DeliveryStart" then
  if s.deliveryAt and now-s.deliveryAt<4 then return end
  s.deliveryAt=now
  tell(p,"DELIVERY START! REACH THE GREEN PAD!")
 elseif kind=="DeliveryFinish" then
  if not s.deliveryAt or now-s.deliveryAt>35 then
   tell(p,"START THE DELIVERY FIRST!"); return
  end
  if s.activityTimes.DeliveryFinish and now-s.activityTimes.DeliveryFinish<8 then return end
  s.activityTimes.DeliveryFinish=now; s.deliveryAt=nil
  s.coins=math.min(100000,s.coins+45); tell(p,"DELIVERY COMPLETE! +45 COINS!")
 elseif kind=="CaveCrystal" or kind=="SkySummit" or kind=="Chest" then
  local key=obj.Name
  local cooldown=obj:GetAttribute("Cooldown") or 30
  if s.activityTimes[key] and now-s.activityTimes[key]<cooldown then return end
  if kind=="SkySummit" and root.Position.Y<31 then return end
  s.activityTimes[key]=now
  local bonus=obj:GetAttribute("Reward") or 0
  s.coins=math.min(100000,s.coins+bonus)
  questProgress(p,kind)
  tell(p,(kind=="SkySummit" and "SKY PARKOUR COMPLETE! +" or kind=="Chest" and "CHEST OPENED! +" or "CRYSTAL FOUND! +")..bonus.." COINS!")
 elseif kind=="FestivalButton" then
  local step=obj:GetAttribute("Step")
  if s.activityTimes.Festival and now-s.activityTimes.Festival<30 then return end
  -- Multiple body parts may touch the same pad in one physics step.
  -- Ignore duplicate touches of the current pad instead of resetting the sequence.
  if step==s.festivalStep then return end
  if step~=s.festivalStep+1 then
   s.festivalStep=0; tell(p,"WRONG COLOR! START AT RED!"); return
  end
  s.festivalStep=step
  if step==3 then
   s.festivalStep=0; s.activityTimes.Festival=now
   s.coins=math.min(100000,s.coins+60)
   tell(p,"COLOR COMBO COMPLETE! +60 COINS!")
   questProgress(p,"Festival")
  else
   tell(p,"NICE! NEXT COLOR "..(step+1).."/3")
  end
 elseif kind=="DomeStart" then
  if s.domeStart or (s.activityTimes.Dome and now-s.activityTimes.Dome<20) then return end
  s.domeStart=now
  tell(p,"DOME SURVIVAL! STAY INSIDE FOR 12 SECONDS!")
  task.delay(12,function()
   local active=sessions[p]
   if active~=s or not s.domeStart then return end
   s.domeStart=nil
   local current=p.Character and p.Character:FindFirstChild("HumanoidRootPart")
   if current and (current.Position-Vector3.new(-170,2,55)).Magnitude<51 then
    s.activityTimes.Dome=os.clock()
    s.coins=math.min(100000,s.coins+70); sync(p)
    tell(p,"DOME SURVIVED! +70 COINS!")
    questProgress(p,"Dome")
   else
    tell(p,"DOME FAILED! TRY AGAIN!")
   end
  end)
 elseif kind=="DomeLaser" then
  if not s.domeStart or now-s.lastHit<1.4 then return end
  s.lastHit=now; s.domeStart=nil
  tell(p,"DOME LASER HIT! CHALLENGE FAILED!")
 elseif kind=="Mutation" then
  if s.used[obj] or s.mutations>=8 then return end
  s.used[obj]=true; s.mutations+=1; s.speed=math.min(48,s.speed+3)
  local glow=char:FindFirstChild("MutationAura") or Instance.new("Highlight")
  glow.Name="MutationAura"; glow.FillTransparency=.85; glow.OutlineColor=palette[s.mutations%5+1]; glow.Parent=char
  tell(p,"MUTATION "..s.mutations.."! +3 SPEED!")
 elseif kind=="Hazard" then
  if now-s.lastHit<2 then return end
  s.lastHit=now; s.speed=math.max(16,s.speed-3); tell(p,"LASER HIT! -3 SPEED")
 elseif kind=="Finish" then
  if s.stage<12 or now-s.lastFinish<5 then return end
  s.lastFinish=now; s.wins+=1; s.coins=math.min(100000,s.coins+100)
  s.stage=0; s.used={}; tell(p,"YOU WON! +100 COINS! RUN AGAIN!")
  warp(p)
 elseif kind=="Fall" then warp(p) end
 sync(p)
end
for _,obj in ipairs(world:GetDescendants()) do
 if obj:IsA("BasePart") and obj:GetAttribute("Kind") then
  obj.Touched:Connect(function(hit) touched(obj,hit) end)
 end
end
action.OnServerEvent:Connect(function(p,kind,...)
 local s=sessions[p]; if not s then return end
 if kind=="Travel" then
  local destination=select(1,...)
  -- All destinations are a server-owned allowlist, never a client position.
  if type(destination)~="string" or not destinations[destination] then return end
  local now=os.clock()
  if s.lastTravel and now-s.lastTravel<1.5 then return end
  s.lastTravel=now
  if p.Character then p.Character:PivotTo(CFrame.new(destinations[destination])) end
  tell(p,"ARRIVED: "..destination.."!")
  return
 end
 if kind=="BuyPet" then equipPet(p); return end
 if kind~="BuySpeed" then return end
 local cost=25+math.floor((s.speed-18)/5)*15
 if s.speed>=48 then tell(p,"MAX SPEED!") return end
 if s.coins<cost then tell(p,"NEED "..cost.." COINS!") return end
 s.coins-=cost; s.speed=math.min(48,s.speed+2); sync(p)
 tell(p,"UPGRADE! +2 SPEED")
end)
print("SF_MUTATION_SERVER_READY v0.2.0")
