-- Original, session-only prototype; no paid features or persistence.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local Lighting=game:GetService("Lighting")
local world=Instance.new("Folder"); world.Name="HyperMutationRushWorld"; world.Parent=workspace
world:SetAttribute("Version","0.1.0")
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
local remote=Instance.new("RemoteEvent"); remote.Name="MutationRushEvent"; remote.Parent=ReplicatedStorage
local action=Instance.new("RemoteEvent"); action.Name="MutationRushAction"; action.Parent=ReplicatedStorage
local sessions={}
local function tell(p,text) remote:FireClient(p,text) end
local function sync(p)
 local s=sessions[p]; if not s then return end
 p:SetAttribute("MRStage",s.stage); p:SetAttribute("MRSpeed",s.speed)
 p:SetAttribute("MRCoins",s.coins); p:SetAttribute("MRMutations",s.mutations)
 p:SetAttribute("MRWins",s.wins)
 local h=p.Character and p.Character:FindFirstChildOfClass("Humanoid")
 if h then h.WalkSpeed=s.speed; h.UseJumpPower=true; h.JumpPower=58 end
end
local function warp(p)
 if p.Character then p.Character:PivotTo(CFrame.new(0,5,50)) end
end
local function init(p)
 sessions[p]={stage=0,speed=18,coins=0,mutations=0,wins=0,used={},lastHit=-10,lastFinish=-10}
 sync(p); p.CharacterAdded:Connect(function() task.wait(.2); sync(p) end)
end
Players.PlayerAdded:Connect(init)
Players.PlayerRemoving:Connect(function(p) sessions[p]=nil end)
for _,p in ipairs(Players:GetPlayers()) do init(p) end
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
action.OnServerEvent:Connect(function(p,kind)
 if kind~="BuySpeed" then return end
 local s=sessions[p]; if not s then return end
 local cost=25+math.floor((s.speed-18)/5)*15
 if s.speed>=48 then tell(p,"MAX SPEED!") return end
 if s.coins<cost then tell(p,"NEED "..cost.." COINS!") return end
 s.coins-=cost; s.speed=math.min(48,s.speed+2); sync(p)
 tell(p,"UPGRADE! +2 SPEED")
end)
print("SF_MUTATION_SERVER_READY v0.1.0")
