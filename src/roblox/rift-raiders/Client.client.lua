-- Rift Raiders responsive HUD; no Robux purchase prompts in the prototype.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local player=Players.LocalPlayer
local action=ReplicatedStorage:WaitForChild("RiftRaidersAction")
local event=ReplicatedStorage:WaitForChild("RiftRaidersEvent")
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
local map,mapList=panel("MapPanel","EXPLORE 12 WORLD LOCATIONS")
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
 {"AIRPORT","INTERNATIONAL AIRPORT"},
}
for i,entry in ipairs(places) do
 item(mapList,"Map"..entry[1],entry[2],
  ({Color3.fromRGB(64,177,204),Color3.fromRGB(171,101,219),
    Color3.fromRGB(227,103,143)})[(i-1)%3+1],function()
   action:FireServer("Travel",entry[1]); map.Visible=false
  end)
end
shopButton.Activated:Connect(function()
 map.Visible=false; shop.Visible=not shop.Visible
end)
mapButton.Activated:Connect(function()
 shop.Visible=false; map.Visible=not map.Visible
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
 "RRShield","RRPet","RRScatter","RRSeals","RRDeliveryTarget","RRQuestShards","RRQuestDrones","RRQuestSeals"}) do
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
