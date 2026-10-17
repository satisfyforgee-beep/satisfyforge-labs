-- Rift Raiders responsive HUD; no Robux purchase prompts in the prototype.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local TweenService=game:GetService("TweenService")
local player=Players.LocalPlayer
local action=ReplicatedStorage:WaitForChild("RiftRaidersAction")
local event=ReplicatedStorage:WaitForChild("RiftRaidersEvent")
local activitySignal=ReplicatedStorage:WaitForChild("RiftActivitiesSignal")
local world=workspace:WaitForChild("RiftRaidersWorld")
local gui=Instance.new("ScreenGui"); gui.Name="RiftRaidersHUD"
gui.ResetOnSpawn=false; gui.IgnoreGuiInset=false; gui.Parent=player:WaitForChild("PlayerGui")
local function round(object,radius)
 local corner=Instance.new("UICorner"); corner.CornerRadius=UDim.new(0,radius or 12)
 corner.Parent=object
 local stroke=Instance.new("UIStroke"); stroke.Color=Color3.fromRGB(100,151,220)
 stroke.Transparency=.5; stroke.Thickness=1.5; stroke.Parent=object
end
local function text(name,content,size,position,color)
 local label=Instance.new("TextLabel"); label.Name=name; label.Size=size; label.Position=position
 label.BackgroundColor3=Color3.fromRGB(18,24,53); label.BackgroundTransparency=.12
 label.TextColor3=color or Color3.new(1,1,1); label.Font=Enum.Font.GothamBold
 label.TextSize=15; label.Text=content; label.TextWrapped=true
 label.BorderSizePixel=0; label.Parent=gui; round(label,10)
 return label
end
local function button(name,content,size,position,color,parent)
 local b=Instance.new("TextButton"); b.Name=name; b.Size=size; b.Position=position
 b.BackgroundColor3=color; b.TextColor3=Color3.new(1,1,1)
 b.Font=Enum.Font.GothamBlack; b.TextSize=16; b.Text=content
 b.TextWrapped=true; b.BorderSizePixel=0; b.Parent=parent or gui; round(b,12)
 return b
end
local title=text("Title","RIFT RAIDERS  ⚡  CHAOS ISLANDS",
 UDim2.new(.62,0,0,39),UDim2.new(.02,0,0,8),Color3.fromRGB(255,222,97))
local stats=text("Stats","LEVEL 1  |  0 COINS  |  0 SHARDS",
 UDim2.new(.62,0,0,33),UDim2.new(.02,0,0,52),Color3.fromRGB(110,250,236))
local progression=text("Progression","BLASTER 1  |  RIFTS 0  |  XP 0",
 UDim2.new(.62,0,0,29),UDim2.new(.02,0,0,90),Color3.fromRGB(196,168,255))
local phase=text("Surge","CALM | NEXT SURGE: 75s",
 UDim2.new(.32,0,0,34),UDim2.new(.66,0,0,8),Color3.fromRGB(255,154,210))
local missions=text("Missions","MISSIONS: SHARDS 0/8 | DRONES 0/3 | RIFTS 0/1",
 UDim2.new(.96,0,0,34),UDim2.new(.02,0,0,130),Color3.fromRGB(255,221,119))
local hint=text("Hint","EXPLORE PORTALS • DRIVE CARS • HARVEST CROPS • VISIT JAPAN & CASTLES",
 UDim2.new(.96,0,0,32),UDim2.new(.02,0,0,169),Color3.fromRGB(228,239,255))
local resourcesHud=text("ResourceHud","WOOD 0 • METAL 0 • FISH 0 • TOOLKITS 0 • HEAT 0",
 UDim2.new(.64,0,0,31),UDim2.new(.02,0,1,-85),Color3.fromRGB(225,237,214))
resourcesHud.TextSize=12
local toast=text("Toast","",UDim2.new(.82,0,0,55),UDim2.new(.09,0,.68,0),Color3.fromRGB(255,222,99))
toast.Visible=false
local blast=button("Blast","⚡ BLAST",UDim2.fromOffset(112,62),
 UDim2.new(1,-126,1,-88),Color3.fromRGB(239,67,134))
blast.AnchorPoint=Vector2.new(0,0)
local dash=button("Dash","➤ DASH",UDim2.fromOffset(104,57),
 UDim2.new(1,-242,1,-85),Color3.fromRGB(56,178,239))
local shield=button("Shield","⬡ SHIELD",UDim2.fromOffset(108,51),
 UDim2.new(1,-126,1,-150),Color3.fromRGB(145,85,231))
local fireButton=button("Fire","FIRE",UDim2.fromOffset(108,56),
 UDim2.new(1,-126,1,-214),Color3.fromRGB(235,169,66))
local carButton=button("Car","SPAWN CAR",UDim2.fromOffset(110,44),
 UDim2.new(1,-118,0,50),Color3.fromRGB(60,148,177))
local flyingCarButton=button("FlyingCar","FLYING CAR",UDim2.fromOffset(110,44),
 UDim2.new(1,-118,0,210),Color3.fromRGB(140,87,218))
local crosshair=Instance.new("TextLabel"); crosshair.Name="Crosshair"
crosshair.Size=UDim2.fromOffset(22,22)
crosshair.Position=UDim2.new(.5,-11,.5,-11)
crosshair.BackgroundTransparency=1; crosshair.Text="+"
crosshair.TextSize=25; crosshair.Font=Enum.Font.GothamBlack
crosshair.TextColor3=Color3.fromRGB(255,246,166); crosshair.Parent=gui
local shopButton=button("ShopToggle","SHOP",UDim2.fromOffset(98,47),
 UDim2.new(.02,0,1,-145),Color3.fromRGB(90,194,128))
local mapButton=button("MapToggle","WORLD",UDim2.fromOffset(98,47),
 UDim2.new(.02,107,1,-145),Color3.fromRGB(87,149,229))
local packButton=button("PackToggle","PACK",UDim2.fromOffset(98,47),
 UDim2.new(.02,0,1,-202),Color3.fromRGB(144,117,86))
blast.Activated:Connect(function() action:FireServer("Blast") end)
dash.Activated:Connect(function() action:FireServer("Dash") end)
shield.Activated:Connect(function() action:FireServer("Shield") end)
carButton.Activated:Connect(function() action:FireServer("SpawnCar") end)
flyingCarButton.Activated:Connect(function() action:FireServer("SpawnFlyingCar") end)
local function fireWeapon()
 local char=player.Character
 local root=char and char:FindFirstChild("HumanoidRootPart")
 local camera=workspace.CurrentCamera
 if not root or not camera then return end
 local equipped=char:FindFirstChildOfClass("Tool")
 local name=equipped and equipped.Name or "Pulse Rifle"
 if name~="Pulse Rifle" and name~="Scatter Blaster" then name="Pulse Rifle" end
 local viewport=camera.ViewportSize
 local ray=camera:ViewportPointToRay(viewport.X*.5,viewport.Y*.5)
 local params=RaycastParams.new()
 params.FilterType=Enum.RaycastFilterType.Exclude
 params.FilterDescendantsInstances={char}
 local result=workspace:Raycast(ray.Origin,ray.Direction*250,params)
 local target=result and result.Position or ray.Origin+ray.Direction*250
 local origin=root.Position+Vector3.new(0,1.8,0)
 local delta=target-origin
 if delta.Magnitude>.1 then action:FireServer("Shoot",delta.Unit,name) end
end
fireButton.Activated:Connect(fireWeapon)
local attached={}
local function bindTool(child)
 if not child:IsA("Tool") or attached[child] then return end
 if child.Name~="Pulse Rifle" and child.Name~="Scatter Blaster" then return end
 attached[child]=true
 child.Activated:Connect(fireWeapon)
 child.Destroying:Connect(function() attached[child]=nil end)
end
local backpack=player:WaitForChild("Backpack")
backpack.ChildAdded:Connect(bindTool)
for _,child in ipairs(backpack:GetChildren()) do bindTool(child) end
local function bindCharacter(char)
 char.ChildAdded:Connect(bindTool)
 for _,child in ipairs(char:GetChildren()) do bindTool(child) end
end
player.CharacterAdded:Connect(bindCharacter)
if player.Character then bindCharacter(player.Character) end
local function panel(name,heading)
 local f=Instance.new("Frame"); f.Name=name
 f.Size=UDim2.new(.86,0,.49,0); f.Position=UDim2.new(.07,0,.28,0)
 f.BackgroundColor3=Color3.fromRGB(19,27,61); f.BorderSizePixel=0
 f.Visible=false; f.Parent=gui; round(f,16)
 local header=Instance.new("TextLabel"); header.Size=UDim2.new(1,-55,0,48)
 header.Position=UDim2.fromOffset(12,2); header.BackgroundTransparency=1
 header.Font=Enum.Font.GothamBlack; header.TextSize=20; header.TextColor3=Color3.fromRGB(255,221,110)
 header.Text=heading; header.Parent=f
 local close=button("Close","X",UDim2.fromOffset(43,42),
  UDim2.new(1,-49,0,5),Color3.fromRGB(200,73,113),f)
 close.Activated:Connect(function() f.Visible=false end)
 local scroll=Instance.new("ScrollingFrame"); scroll.Name="Options"
 scroll.Size=UDim2.new(1,-24,1,-64); scroll.Position=UDim2.fromOffset(12,55)
 scroll.BackgroundTransparency=1; scroll.ScrollBarThickness=5
 scroll.BorderSizePixel=0; scroll.Parent=f
 local layout=Instance.new("UIListLayout"); layout.Padding=UDim.new(0,8); layout.Parent=scroll
 layout:GetPropertyChangedSignal("AbsoluteContentSize"):Connect(function()
  scroll.CanvasSize=UDim2.fromOffset(0,layout.AbsoluteContentSize.Y+12)
 end)
 return f,scroll
end
local shop,shopList=panel("ShopPanel","EARNED COIN SHOP")
local map,mapList=panel("MapPanel","EXPLORE 14 WORLD LOCATIONS")
local pack,packList=panel("PackPanel","YOUR RESOURCES & PROGRESS")
local function item(parent,name,content,color,fn)
 local b=button(name,content,UDim2.new(1,-12,0,53),UDim2.fromOffset(0,0),color,parent)
 b.Activated:Connect(fn)
 return b
end
local blasterItem=item(shopList,"Blaster","BLASTER LEVEL UP • COST: 90+ COINS",
 Color3.fromRGB(224,77,133),function() action:FireServer("Buy","BLASTER") end)
local shieldItem=item(shopList,"ShieldUpgrade","SHIELD ABILITY • 150 COINS",
 Color3.fromRGB(126,86,219),function() action:FireServer("Buy","SHIELD") end)
local scatterItem=item(shopList,"ScatterUpgrade","SCATTER BLASTER • 175 COINS",
 Color3.fromRGB(233,120,74),function() action:FireServer("Buy","SCATTER") end)
local petItem=item(shopList,"PetUpgrade","ADOPT RIFTLING PET • 250 COINS",
 Color3.fromRGB(71,172,153),function() action:FireServer("Buy","PET") end)
local places={
 {"HUB","CENTRAL HUB"},{"CYBER","NEON METROPOLIS"},{"CRYSTAL","PRISM WILDS"},
 {"VOLCANO","MAGMA OUTPOST"},{"SKY","CLOUD KINGDOM"},
 {"CASTLE","CASTLE KINGDOM"},{"FARM","HARVEST VALLEY"},
 {"JAPAN","SAKURA JAPAN"},{"ARCTIC","SNOWBOUND NORTH"},
 {"MARINA","OCEAN MARINA"},{"SAFARI","WILDLIFE SAFARI"},
 {"AIRPORT","INTERNATIONAL AIRPORT"},{"SPORTS","WORLD SPORTS COMPLEX"},{"HOMES","HOUSING MEADOWS"},
}
for i,entry in ipairs(places) do
 item(mapList,"Map"..entry[1],entry[2],
  ({Color3.fromRGB(64,177,204),Color3.fromRGB(171,101,219),
    Color3.fromRGB(227,103,143)})[(i-1)%3+1],function()
   action:FireServer("Travel",entry[1]); map.Visible=false
  end)
end
shopButton.Activated:Connect(function()
 map.Visible=false; pack.Visible=false; shop.Visible=not shop.Visible
end)
mapButton.Activated:Connect(function()
 shop.Visible=false; pack.Visible=false; map.Visible=not map.Visible
end)
packButton.Activated:Connect(function()
 shop.Visible=false; map.Visible=false; pack.Visible=not pack.Visible
end)
local packSummary=item(packList,"PackSummary","RESOURCE INVENTORY",
 Color3.fromRGB(66,93,124),function() end)
packSummary.Active=false
local packGuide=item(packList,"PackGuide",
 "WOOD AT FARM + METAL IN CITY • BUILD HOME IN HOUSING MEADOWS",
 Color3.fromRGB(80,105,135),function() end)
packGuide.Active=false
local packJobs=item(packList,"PackJobs",
 "SPORTS IN SPORTS WORLD • FISH AT MARINA • HUNT/TRACK AT SAFARI",
 Color3.fromRGB(80,105,135),function() end)
packJobs.Active=false
local packCrime=item(packList,"PackCrime",
 "LEVEL 2: NPC CAR JOB • LEVEL 3: BANK VAULT • HEAT COOLS DOWN",
 Color3.fromRGB(113,81,109),function() end)
packCrime.Active=false
local skill=Instance.new("Frame")
skill.Name="SkillChallenge"; skill.AnchorPoint=Vector2.new(.5,.5)
skill.Size=UDim2.new(.84,0,0,145); skill.Position=UDim2.new(.5,0,.43,0)
skill.BackgroundColor3=Color3.fromRGB(17,31,51); skill.BorderSizePixel=0
skill.Visible=false; skill.Parent=gui; round(skill,16)
local skillTitle=Instance.new("TextLabel"); skillTitle.Name="ChallengeTitle"
skillTitle.Size=UDim2.new(1,-20,0,34); skillTitle.Position=UDim2.fromOffset(10,5)
skillTitle.BackgroundTransparency=1; skillTitle.Font=Enum.Font.GothamBlack
skillTitle.TextSize=18; skillTitle.TextColor3=Color3.fromRGB(250,235,185)
skillTitle.Text="TIME YOUR ACTION"; skillTitle.Parent=skill
local meter=Instance.new("Frame"); meter.Name="TimingMeter"
meter.Size=UDim2.new(1,-40,0,23); meter.Position=UDim2.fromOffset(20,45)
meter.BackgroundColor3=Color3.fromRGB(66,85,110); meter.BorderSizePixel=0
meter.Parent=skill; round(meter,5)
local target=Instance.new("Frame"); target.Name="SuccessZone"
target.Size=UDim2.new(.11,0,1,0); target.BackgroundColor3=Color3.fromRGB(99,243,149)
target.BorderSizePixel=0; target.Parent=meter
local marker=Instance.new("Frame"); marker.Name="MovingMarker"
marker.Size=UDim2.fromOffset(6,28); marker.Position=UDim2.new(0,0,0,-2)
marker.BackgroundColor3=Color3.fromRGB(255,241,163)
marker.BorderSizePixel=0; marker.Parent=meter
local skillHit=button("SkillHit","HIT / KICK / CAST",UDim2.new(.85,0,0,53),
 UDim2.new(.075,0,0,79),Color3.fromRGB(54,158,198),skill)
local currentSkill=nil
local challengeSeq=0
local activeTween=nil
activitySignal.OnClientEvent:Connect(function(payload)
 if type(payload)~="table" or payload.kind~="skill" or type(payload.id)~="string" then return end
 challengeSeq+=1
 local seq=challengeSeq
 currentSkill=payload.id
 skillTitle.Text=tostring(payload.title or "SKILL CHALLENGE")
 skillHit.Text="TAP WHEN MARKER REACHES GREEN!"
 skill.Visible=true
 local duration=math.clamp(tonumber(payload.duration) or 3.5,2,5)
 local delay=math.clamp(tonumber(payload.delay) or 2,0,duration)
 target.Position=UDim2.new(math.clamp(delay/duration-.055,0,.89),0,0,0)
 marker.Position=UDim2.new(0,0,0,-2)
 if activeTween then activeTween:Cancel() end
 activeTween=TweenService:Create(marker,TweenInfo.new(duration,Enum.EasingStyle.Linear),
  {Position=UDim2.new(1,-6,0,-2)})
 activeTween:Play()
 task.delay(duration+.3,function()
  if challengeSeq==seq then skill.Visible=false; currentSkill=nil end
 end)
end)
skillHit.Activated:Connect(function()
 if not currentSkill then return end
 local id=currentSkill
 currentSkill=nil; skill.Visible=false
 if activeTween then activeTween:Cancel() end
 action:FireServer("ActivityHit",id)
end)
local seq=0
event.OnClientEvent:Connect(function(message)
 seq+=1; local current=seq
 toast.Text=tostring(message); toast.Visible=true
 task.delay(2.7,function() if current==seq then toast.Visible=false end end)
end)
local function update()
 local target=player:GetAttribute("RRDeliveryTarget")
 hint.Text=(type(target)=="string" and target~="" and
  ("COURIER JOB: DELIVER TO "..target:upper()) or
  "EXPLORE PORTALS • DRIVE CARS • HARVEST CROPS • VISIT JAPAN & CASTLES")
 local coins=player:GetAttribute("RRCoins") or 0
 local shards=player:GetAttribute("RRShards") or 0
 local level=player:GetAttribute("RRLevel") or 1
 local xp=player:GetAttribute("RRXP") or 0
 local blasterLevel=player:GetAttribute("RRBlaster") or 1
 local seals=player:GetAttribute("RRSeals") or 0
 stats.Text="LEVEL "..level.."  |  "..coins.." COINS  |  "..shards.." SHARDS"
 resourcesHud.Text="WOOD "..(player:GetAttribute("RRWood") or 0)..
  " • METAL "..(player:GetAttribute("RRMetal") or 0)..
  " • FISH "..(player:GetAttribute("RRFish") or 0)..
  " • TOOLS "..(player:GetAttribute("RRToolkits") or 0)..
  " • HEAT "..(player:GetAttribute("RRHeat") or 0)
 packSummary.Text="WOOD "..(player:GetAttribute("RRWood") or 0)..
  " • METAL "..(player:GetAttribute("RRMetal") or 0)..
  " • FISH "..(player:GetAttribute("RRFish") or 0)..
  " • HIDES "..(player:GetAttribute("RRHide") or 0)..
  " • TOOLKITS "..(player:GetAttribute("RRToolkits") or 0)..
  " • SPORTS WINS "..(player:GetAttribute("RRSportsWins") or 0)..
  " • HEISTS "..(player:GetAttribute("RRHeists") or 0)..
  " • HOME "..(player:GetAttribute("RRHouseOwned") and "BUILT" or "NOT BUILT")
 progression.Text="BLASTER "..blasterLevel.."  |  RIFTS "..seals.."  |  XP "..xp
 missions.Text="MISSIONS: SHARDS "..(player:GetAttribute("RRQuestShards") or 0)..
  "/8  •  DRONES "..(player:GetAttribute("RRQuestDrones") or 0)..
  "/3  •  RIFTS "..(player:GetAttribute("RRQuestSeals") or 0).."/1"
 blasterItem.Text=blasterLevel>=4 and "BLASTER MAXED" or
  "BLASTER LEVEL "..(blasterLevel+1).." • "..(blasterLevel*90).." COINS"
 shieldItem.Text=player:GetAttribute("RRShield") and "SHIELD OWNED • USE SHIELD BUTTON" or
  "UNLOCK SHIELD • 150 COINS"
 scatterItem.Text=player:GetAttribute("RRScatter") and "SCATTER BLASTER OWNED" or
  "UNLOCK SCATTER BLASTER • 175 COINS"
 petItem.Text=player:GetAttribute("RRPet") and "RIFTLING PET OWNED" or
  "ADOPT RIFTLING PET • 250 COINS"
end
for _,name in ipairs({"RRCoins","RRShards","RRLevel","RRXP","RRBlaster",
 "RRShield","RRPet","RRScatter","RRSeals","RRDeliveryTarget","RRQuestShards",
 "RRWood","RRMetal","RRFish","RRHide","RRToolkits","RRHeat","RRSportsWins","RRHeists","RRHouseOwned","RRQuestDrones","RRQuestSeals"}) do
 player:GetAttributeChangedSignal(name):Connect(update)
end
local function phaseUpdate()
 local current=world:GetAttribute("Phase") or "CALM"
 phase.Text=current.." | "..(world:GetAttribute("SecondsLeft") or 0).."s"..
  (current=="SURGE" and (" TITAN HP: "..(world:GetAttribute("BossHealth") or 0)) or " TO SURGE")
end
world:GetAttributeChangedSignal("Phase"):Connect(phaseUpdate)
world:GetAttributeChangedSignal("SecondsLeft"):Connect(phaseUpdate)
world:GetAttributeChangedSignal("BossHealth"):Connect(phaseUpdate)
update(); phaseUpdate()
print("SF_RIFT_RAIDERS_CLIENT_READY")
