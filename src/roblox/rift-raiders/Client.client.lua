-- Rift Raiders responsive HUD; no Robux purchase prompts in the prototype.
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local TweenService=game:GetService("TweenService")
local Lighting=game:GetService("Lighting")
local RunService=game:GetService("RunService")
local UserInputService=game:GetService("UserInputService")
local player=Players.LocalPlayer
local action=ReplicatedStorage:WaitForChild("RiftRaidersAction")
local event=ReplicatedStorage:WaitForChild("RiftRaidersEvent")
local activitySignal=ReplicatedStorage:WaitForChild("RiftActivitiesSignal")
local world=workspace:WaitForChild("RiftRaidersWorld")
local Catalog=require(ReplicatedStorage:WaitForChild("PrestigeCatalog"))
local LifeCatalog=require(ReplicatedStorage:WaitForChild("LifeCatalog"))
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
 UDim2.new(.29,0,0,30),UDim2.new(.40,0,0,8),Color3.fromRGB(255,222,97))
local stats=text("Stats","LEVEL 1  |  0 COINS  |  0 SHARDS",
 UDim2.new(.29,0,0,27),UDim2.new(.40,0,0,42),Color3.fromRGB(110,250,236))
local progression=text("Progression","BLASTER 1  |  RIFTS 0  |  XP 0",
 UDim2.new(.47,0,0,28),UDim2.new(.02,0,0,78),Color3.fromRGB(196,168,255))
local phase=text("Surge","CALM | NEXT SURGE: 75s",
 UDim2.new(.28,0,0,29),UDim2.new(.70,0,0,8),Color3.fromRGB(255,154,210))
local missions=text("Missions","MISSIONS: SHARDS 0/8 | DRONES 0/3 | RIFTS 0/1",
 UDim2.new(.62,0,0,30),UDim2.new(.02,0,0,111),Color3.fromRGB(255,221,119))
local hint=text("Hint","EXPLORE PORTALS • DRIVE CARS • HARVEST CROPS • VISIT JAPAN & CASTLES",
 UDim2.new(.65,0,0,30),UDim2.new(.18,0,1,-46),Color3.fromRGB(228,239,255))
local resourcesHud=text("ResourceHud","WOOD 0 • METAL 0 • FISH 0 • TOOLKITS 0 • HEAT 0",
 UDim2.new(.48,0,0,27),UDim2.new(.02,0,1,-93),Color3.fromRGB(225,237,214))
resourcesHud.TextSize=12
progression.Visible=false
missions.Visible=false
hint.Visible=false
resourcesHud.Visible=false
local showDetails=false
local detailsButton=button("HUDDetails","DETAILS",
 UDim2.fromOffset(103,35),UDim2.new(1,-114,0,44),
 Color3.fromRGB(55,83,107))
detailsButton.Activated:Connect(function()
 showDetails=not showDetails
 progression.Visible=showDetails
 missions.Visible=showDetails
 resourcesHud.Visible=showDetails
 hint.Visible=showDetails
 detailsButton.Text=showDetails and "HIDE HUD" or "DETAILS"
end)
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
 UDim2.new(1,-118,0,86),Color3.fromRGB(60,148,177))
local flyingCarButton=button("FlyingCar","FLYING CAR",UDim2.fromOffset(110,44),
 UDim2.new(1,-118,0,178),Color3.fromRGB(140,87,218))
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
local qualityButton=button("GraphicsQuality","GRAPHICS: MED",
 UDim2.fromOffset(110,36),UDim2.new(1,-118,0,228),
 Color3.fromRGB(82,117,130))
local lifeButton=button("LifeToggle","LIFE",UDim2.fromOffset(98,47),
 UDim2.new(.02,107,1,-202),Color3.fromRGB(83,149,130))
local packButton=button("PackToggle","PACK",UDim2.fromOffset(98,47),
 UDim2.new(.02,0,1,-202),Color3.fromRGB(144,117,86))
local actionsExpanded=false
local actionsButton=button("ActionsToggle","ACTIONS",
 UDim2.fromOffset(110,38),UDim2.new(1,-118,0,137),
 Color3.fromRGB(98,92,131))
local function showActions()
 for _,control in ipairs({blast,dash,shield,fireButton,flyingCarButton}) do
  control.Visible=actionsExpanded
 end
 crosshair.Visible=actionsExpanded
 actionsButton.Text=actionsExpanded and "HIDE ACTIONS" or "ACTIONS"
end
actionsButton.Activated:Connect(function()
 actionsExpanded=not actionsExpanded
 showActions()
end)
showActions()
-- A 2x2 navigation grid leaves the center hotbar clear on desktop and mobile.
for i,control in ipairs({shopButton,mapButton,packButton,lifeButton}) do
 local col=(i-1)%2
 local row=math.floor((i-1)/2)
 control.Position=UDim2.new(.02,col*104,1,-57-row*49)
 control.Size=UDim2.fromOffset(97,43)
end
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
 f.Size=UDim2.new(UserInputService.TouchEnabled and .94 or .7,0,.72,0)
 f.AnchorPoint=Vector2.new(.5,.5); f.Position=UDim2.fromScale(.5,.5)
 local constraint=Instance.new("UISizeConstraint")
 constraint.MaxSize=Vector2.new(760,650)
 constraint.MinSize=Vector2.new(280,240)
 constraint.Parent=f
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
 local layout=Instance.new("UIListLayout"); layout.Padding=UDim.new(0,8)
 layout.SortOrder=Enum.SortOrder.LayoutOrder; layout.Parent=scroll
 layout:GetPropertyChangedSignal("AbsoluteContentSize"):Connect(function()
  scroll.CanvasSize=UDim2.fromOffset(0,layout.AbsoluteContentSize.Y+12)
 end)
 return f,scroll
end
local shop,shopList=panel("ShopPanel","EARNED COIN SHOP + PRESTIGE")
local map,mapList=panel("MapPanel","EXPLORE 19 WORLD LOCATIONS")
local pack,packList=panel("PackPanel","YOUR RESOURCES & PROGRESS")
local lifePanel,lifeList=panel("LifePanel","RIFTLIFE • DOWNTOWN CAREERS & SHOPPING")
local itemOrder=setmetatable({}, {__mode="k"})
local function item(parent,name,content,color,fn)
 local b=button(name,content,UDim2.new(1,-12,0,53),UDim2.fromOffset(0,0),color,parent)
 itemOrder[parent]=(itemOrder[parent] or 0)+1
 b.LayoutOrder=itemOrder[parent]
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
local prestigeItems={}
for _,entry in ipairs(Catalog.Items) do
 prestigeItems[entry.id]=item(shopList,"Prestige_"..entry.id,
  entry.name.." • "..Catalog.PriceText(entry),
  Color3.fromRGB(80,100,132),
  function() action:FireServer("BuyPrestige",entry.id) end)
end
local premiumInfo=item(shopList,"RobuxNotice",
 "ROBUX COSMETICS: NOT FOR SALE YET • ALL ITEMS ABOVE EARNABLE",
 Color3.fromRGB(65,78,102),function() end)
premiumInfo.Active=false
local lifeSummary=item(lifeList,"LifeSummary","CAREER • FOLLOWERS • FINES",
 Color3.fromRGB(67,102,118),function() end)
lifeSummary.Active=false
local lifeHelp=item(lifeList,"LifeHelp",
 "DOWNTOWN: EMPLOYMENT CENTER • REAL STOREFRONTS • WORKPLACES • BUSINESSES",
 Color3.fromRGB(70,89,116),function() end)
lifeHelp.Active=false
local lifeTask=item(lifeList,"LifeTask","NO ACTIVE SHIFT",
 Color3.fromRGB(79,119,101),function() end)
lifeTask.Active=false
local lifeMode="CAREERS"
local careerControls={}
local shopControls={}
local gardenControls={}
local garageControls={}
local updateLifeView
local careerViewButton=item(lifeList,"CareerView","CAREERS • APPLY & WORK",
 Color3.fromRGB(69,112,137),function()
  lifeMode="CAREERS"; updateLifeView()
 end)
local shoppingViewButton=item(lifeList,"ShoppingView","SHOPPING • REAL-WORLD CATALOG",
 Color3.fromRGB(104,94,128),function()
  lifeMode="SHOP"; updateLifeView()
 end)
local gardenViewButton=item(lifeList,"GardenView","GARDEN • PLANT, WATER & HARVEST",
 Color3.fromRGB(80,124,85),function()
  lifeMode="GARDEN"; updateLifeView()
 end)
local boatViewButton=item(lifeList,"BoatView","MARINA • LAUNCH YOUR BOATS",
 Color3.fromRGB(66,114,151),function()
  lifeMode="BOATS"; updateLifeView()
 end)
local garageViewButton=item(lifeList,"GarageView","GARAGE • SELECT YOUR DETAILED CAR",
 Color3.fromRGB(106,110,146),function()
  lifeMode="GARAGE"; updateLifeView()
 end)
local homeViewButton=item(lifeList,"HomeView","MY HOME • FURNITURE & SECURITY",
 Color3.fromRGB(110,118,101),function()
  lifeMode="HOME"; updateLifeView()
 end)
local careerHeading=item(lifeList,"CareerHeading","AVAILABLE REAL-WORLD CAREERS",
 Color3.fromRGB(83,112,145),function() end)
careerHeading.Active=false; table.insert(careerControls,careerHeading)
for _,career in ipairs(LifeCatalog.Careers) do
 local listing=item(lifeList,"Career_"..career.id,
  career.name.." • "..career.wage.." COINS/SHIFT • LEVEL "..career.level..
  " • APPLY AT EMPLOYMENT CENTER",
  Color3.fromRGB(60,83,107),function()
   action:FireServer("LifeAction","Career",career.id)
  end)
 table.insert(careerControls,listing)
end
local creatorButton=item(lifeList,"CreatorPublish",
 "RECORD CONTENT • CREATOR CAREER + PHONE + EQUIPPED CAMERA",
 Color3.fromRGB(127,80,141),function()
  action:FireServer("LifeAction","Publish")
 end)
table.insert(careerControls,creatorButton)
local collectButton=item(lifeList,"BusinessCollect",
 "COLLECT BUSINESS INCOME • VISIT CITY COMMERCE",
 Color3.fromRGB(86,131,93),function()
  action:FireServer("LifeAction","BusinessCollect")
 end)
table.insert(shopControls,collectButton)
local shopCategories={"ALL","GARDEN","APPAREL","TECH","HOME","VEHICLE","PROPERTY","BUSINESS"}
local shopCategoryIndex=1
local categoryButton
categoryButton=item(lifeList,"LifeCategory","CATEGORY: ALL • TAP TO FILTER",
 Color3.fromRGB(81,92,122),function()
  shopCategoryIndex=shopCategoryIndex%#shopCategories+1
  updateLifeView()
 end)
table.insert(shopControls,categoryButton)
-- Keep the category filter at the top of Shopping, ahead of revenue collection.
local collectOrder=collectButton.LayoutOrder
collectButton.LayoutOrder=categoryButton.LayoutOrder
categoryButton.LayoutOrder=collectOrder
local lifeItems={}
for _,entry in ipairs(LifeCatalog.Items) do
 local control=item(lifeList,"LifeItem_"..entry.id,
  entry.name.." | "..entry.price.." coins | Level "..entry.level,
  Color3.fromRGB(88,105,129),function()
   action:FireServer("LifeAction","Buy",entry.id)
  end)
 lifeItems[entry.id]=control
 table.insert(shopControls,control)
end
local boatControls={}
local boatHelp=item(lifeList,"BoatHelp",
 "TRAVEL TO WATERFRONT • BUY A VESSEL AT THE VEHICLE DEALER • LAUNCH AT DOCK",
 Color3.fromRGB(58,94,133),function() end)
boatHelp.Active=false;table.insert(boatControls,boatHelp)
for _,id in ipairs({"KAYAK","FISHING_BOAT","JET_SKI","PONTOON",
 "SPEEDBOAT","SAILBOAT","CABIN_CRUISER","YACHT","LUXURY_YACHT"}) do
 local entry=LifeCatalog.ById[id]
 local control=item(lifeList,"Launch_"..id,
  "LAUNCH "..entry.name:upper().." • REQUIRES OWNERSHIP",
  Color3.fromRGB(66,116,151),function()
   action:FireServer("SpawnBoat",id)
  end)
 table.insert(boatControls,control)
end
local homeControls={}
local homeInfo=item(lifeList,"HomeStatus","BUY A HOME TO UNLOCK YOUR ESTATE.",
 Color3.fromRGB(94,109,100),function() end)
homeInfo.Active=false;table.insert(homeControls,homeInfo)
local goHome=item(lifeList,"VisitMyHome","VISIT MY PERSONAL HOME LOT",
 Color3.fromRGB(91,137,110),function()
  action:FireServer("LifeAction","GoHome")
 end)
table.insert(homeControls,goHome)
local homeHelp=item(lifeList,"HomeGuide",
 "PURCHASE FRIDGE, TV, GAME CONSOLE, BED, COUCH & FURNISHINGS IN LIFE SHOPPING."..
 " VISIT YOUR HOME AND USE REAL APPLIANCES. KEYPAD CONTROLS GUEST ACCESS.",
 Color3.fromRGB(94,105,120),function() end)
homeHelp.Active=false;table.insert(homeControls,homeHelp)
local garageInfo=item(lifeList,"GarageInfo",
 "10 EARNABLE VEHICLES • OFFICIAL RACE CAR, SEDANS, AND SUV/PICKUP • VISIT DEALER",
 Color3.fromRGB(96,103,132),function() end)
garageInfo.Active=false;table.insert(garageControls,garageInfo)
local garageButtons={}
for _,id in ipairs(LifeCatalog.DrivableCars) do
 local choice=LifeCatalog.CarChoices[id]
 local control=item(lifeList,"GarageCar_"..id,choice.name:upper()..
  " • TOP SPEED "..choice.speed.." • SELECT AT DEALER",
  Color3.fromRGB(97,110,139),function()
   action:FireServer("LifeAction","SelectCar",id)
  end)
 garageButtons[id]=control;table.insert(garageControls,control)
end
local garageTip=item(lifeList,"GarageTip",
 "SELECT A PURCHASED CAR AT MOTOR ROW, THEN USE THE CAR BUTTON. OTHER VEHICLES NEED FUTURE MODELS.",
 Color3.fromRGB(88,95,119),function() end)
garageTip.Active=false;table.insert(garageControls,garageTip)
local gardenStatus=item(lifeList,"GardenStatus",
 "VISIT DOWNTOWN COMMUNITY GARDEN • BUY A TROWEL, CAN & SEEDS",
 Color3.fromRGB(85,115,77),function() end)
gardenStatus.Active=false
table.insert(gardenControls,gardenStatus)
local gardenWater=item(lifeList,"GardenWater","WATER YOUR CROPS • NEEDS WATERING CAN",
 Color3.fromRGB(57,124,157),function()
  action:FireServer("LifeAction","GardenWater")
 end)
table.insert(gardenControls,gardenWater)
local gardenHarvest=item(lifeList,"GardenHarvest","HARVEST RIPE VEGETABLES",
 Color3.fromRGB(104,150,75),function()
  action:FireServer("LifeAction","GardenHarvest")
 end)
table.insert(gardenControls,gardenHarvest)
local gardenSell=item(lifeList,"GardenSell","SELL PRODUCE • DOWNTOWN FARM MARKET",
 Color3.fromRGB(142,118,75),function()
  action:FireServer("LifeAction","GardenSell")
 end)
table.insert(gardenControls,gardenSell)
local gardenPlantControls={}
for _,id in ipairs({
 "TOMATO_SEEDS","CARROT_SEEDS","STRAWBERRY_SEEDS","POTATO_SEEDS",
 "LETTUCE_SEEDS","PEPPER_SEEDS","CUCUMBER_SEEDS","CORN_SEEDS",
 "PUMPKIN_SEEDS","SUNFLOWER_SEEDS","BLUEBERRY_SEEDS",
 "ROSE_SEEDS","APPLE_TREE_SEEDS","WATERMELON_SEEDS"
}) do
 local seed=LifeCatalog.ById[id]
 local control=item(lifeList,"Plant_"..id,"PLANT "..seed.name:upper(),
  Color3.fromRGB(84,125,82),function()
   action:FireServer("LifeAction","GardenPlant",id)
  end)
 gardenPlantControls[id]=control
 table.insert(gardenControls,control)
end
updateLifeView=function()
 local careers=lifeMode=="CAREERS"
 local shopping=lifeMode=="SHOP"
 local gardening=lifeMode=="GARDEN"
 local boating=lifeMode=="BOATS"
 local garage=lifeMode=="GARAGE"
 local atHome=lifeMode=="HOME"
 for _,control in ipairs(homeControls) do control.Visible=atHome end
 for _,control in ipairs(garageControls) do control.Visible=garage end
 for _,control in ipairs(boatControls) do control.Visible=boating end
 for _,control in ipairs(careerControls) do control.Visible=careers end
 for _,control in ipairs(gardenControls) do control.Visible=gardening end
 local category=shopCategories[shopCategoryIndex]
 collectButton.Visible=shopping
 categoryButton.Visible=shopping
 categoryButton.Text="CATEGORY: "..category.." • TAP TO FILTER"
 for _,entry in ipairs(LifeCatalog.Items) do
  local control=lifeItems[entry.id]
  control.Visible=shopping and (category=="ALL" or entry.category==category)
 end
 for id,control in pairs(gardenPlantControls) do
  control.Visible=gardening
  local remaining=player:GetAttribute("RRLifeSeed_"..id) or 0
  control.Text="PLANT "..LifeCatalog.ById[id].name:upper()..
   " • "..remaining.." SEEDS LEFT"
  control.BackgroundColor3=remaining>0 and
   Color3.fromRGB(69,133,90) or Color3.fromRGB(88,96,95)
 end
 gardenStatus.Text="YOUR PLOT: "..(player:GetAttribute("RRLifeGardenPlot") or "WAIT FOR PLOT")..
  " • CROP: "..(player:GetAttribute("RRLifeGardenCrop") or "NONE")..
  " • "..(player:GetAttribute("RRLifeGardenStatus") or "EMPTY")..
  " • STORED HARVEST: "..(player:GetAttribute("RRLifeGardenProduce") or 0)..
  " • TOTAL HARVESTS: "..(player:GetAttribute("RRLifeGardenHarvests") or 0)
 careerViewButton.BackgroundColor3=careers and Color3.fromRGB(49,124,112) or Color3.fromRGB(69,88,102)
 shoppingViewButton.BackgroundColor3=shopping and Color3.fromRGB(104,94,128) or Color3.fromRGB(69,88,102)
 gardenViewButton.BackgroundColor3=gardening and Color3.fromRGB(76,142,81) or Color3.fromRGB(69,88,102)
 boatViewButton.BackgroundColor3=boating and Color3.fromRGB(66,132,171) or Color3.fromRGB(69,88,102)
 garageViewButton.BackgroundColor3=garage and Color3.fromRGB(131,119,161) or Color3.fromRGB(69,88,102)
 homeViewButton.BackgroundColor3=atHome and Color3.fromRGB(123,147,114) or Color3.fromRGB(69,88,102)
 homeInfo.Text="HOME LOT: "..tostring(player:GetAttribute("RRLifeHomePlot") or 0)..
  " • SECURITY "..(player:GetAttribute("RRLifeHomeLocked") and "LOCKED" or "UNLOCKED")..
  " • FUN "..tostring(player:GetAttribute("RRLifeFun") or 100)..
  " • VISIT WORLD → ESTATES TO SEE THE NEIGHBORHOOD"
 local selected=player:GetAttribute("RRLifeSelectedCar") or ""
 for id,control in pairs(garageButtons) do
  local owned=player:GetAttribute("RRLifeOwn_"..id)==true
  control.Text=LifeCatalog.CarChoices[id].name.." • "..
   LifeCatalog.CarChoices[id].speed.." SPEED • "..
   (selected==id and "YOUR CURRENT CAR" or owned and "SELECT OWNED CAR" or "BUY FIRST")
  control.BackgroundColor3=selected==id and Color3.fromRGB(62,138,109) or
   owned and Color3.fromRGB(95,111,144) or Color3.fromRGB(62,70,78)
 end
 lifeList.CanvasPosition=Vector2.zero
end
updateLifeView()
local places={
 {"MODERN","MODERN DOWNTOWN • REAL 3D CITY"},
 {"WATERFRONT","WATERFRONT • OWNED BOATS & YACHTS"},
 {"ESTATES","RESIDENTIAL ESTATES • YOUR HOME"},
 {"SUBURBIA","SUBURBAN SHOWCASE • DETAILED HOMES & STORES"},
 {"HUB","CENTRAL HUB"},{"CYBER","NEON METROPOLIS"},{"CRYSTAL","PRISM WILDS"},
 {"VOLCANO","MAGMA OUTPOST"},{"SKY","CLOUD KINGDOM"},
 {"CASTLE","CASTLE KINGDOM"},{"FARM","HARVEST VALLEY"},
 {"JAPAN","SAKURA JAPAN"},{"ARCTIC","SNOWBOUND NORTH"},
 {"MARINA","OCEAN MARINA"},{"SAFARI","WILDLIFE SAFARI"},
 {"AIRPORT","INTERNATIONAL AIRPORT"},{"SPORTS","WORLD SPORTS COMPLEX"},{"HOMES","HOUSING MEADOWS"},
 {"LIFE","LIFE CITY • CAREERS, STORES & POLICE"},
}
for i,entry in ipairs(places) do
 item(mapList,"Map"..entry[1],entry[2],
  ({Color3.fromRGB(64,177,204),Color3.fromRGB(171,101,219),
    Color3.fromRGB(227,103,143)})[(i-1)%3+1],function()
   action:FireServer("Travel",entry[1]); map.Visible=false
  end)
end
shopButton.Activated:Connect(function()
 map.Visible=false; pack.Visible=false; lifePanel.Visible=false; shop.Visible=not shop.Visible
end)
mapButton.Activated:Connect(function()
 shop.Visible=false; pack.Visible=false; lifePanel.Visible=false; map.Visible=not map.Visible
end)
packButton.Activated:Connect(function()
 shop.Visible=false; map.Visible=false; lifePanel.Visible=false; pack.Visible=not pack.Visible
end)
lifeButton.Activated:Connect(function()
 shop.Visible=false; map.Visible=false; pack.Visible=false
 lifePanel.Visible=not lifePanel.Visible
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
 if lifeMode=="HOME" then
  homeInfo.Text="HOME LOT: "..tostring(player:GetAttribute("RRLifeHomePlot") or 0)..
   " • SECURITY "..(player:GetAttribute("RRLifeHomeLocked") and "LOCKED" or "UNLOCKED")..
   " • FUN "..tostring(player:GetAttribute("RRLifeFun") or 100)..
   " • VISIT WORLD → ESTATES TO SEE THE NEIGHBORHOOD"
 elseif lifeMode=="GARAGE" then
  local selected=player:GetAttribute("RRLifeSelectedCar") or ""
  for id,control in pairs(garageButtons) do
   local owned=player:GetAttribute("RRLifeOwn_"..id)==true
   control.Text=LifeCatalog.CarChoices[id].name.." • "..
    LifeCatalog.CarChoices[id].speed.." SPEED • "..
    (selected==id and "YOUR CURRENT CAR" or owned and
     "SELECT OWNED CAR" or "BUY FIRST")
  end
 end
 local target=player:GetAttribute("RRDeliveryTarget")
 hint.Text=(type(target)=="string" and target~="" and
  ("COURIER JOB: DELIVER TO "..target:upper()) or
  "EXPLORE PORTALS • DRIVE CARS • HARVEST CROPS • VISIT JAPAN & CASTLES")
 local coins=player:GetAttribute("RRCoins") or 0
 local level=player:GetAttribute("RRLevel") or 1
 if lifeMode=="GARDEN" then
  gardenStatus.Text="PLOT: "..(player:GetAttribute("RRLifeGardenPlot") or "WAIT FOR PLOT")..
   " • "..(player:GetAttribute("RRLifeGardenCrop") or "NO CROPS")..
   " • "..(player:GetAttribute("RRLifeGardenStatus") or "EMPTY")..
   " • PRODUCE: "..(player:GetAttribute("RRLifeGardenProduce") or 0)..
   " • HARVESTS: "..(player:GetAttribute("RRLifeGardenHarvests") or 0)
 end
 local career=player:GetAttribute("RRLifeCareer") or "UNEMPLOYED"
 local shift=player:GetAttribute("RRLifeShift") or ""
 lifeTask.Text=shift~="" and
  ("WORK SHIFT: "..shift.." • TASK "..(player:GetAttribute("RRLifeTaskStep") or 0)..
  "/2 • "..(player:GetAttribute("RRLifeTaskName") or "")) or
  "FIND A JOB AT THE DOWNTOWN EMPLOYMENT CENTER"
 lifeSummary.Text="CAREER: "..career..
  " • FOLLOWERS: "..(player:GetAttribute("RRLifeFollowers") or 0)..
  " • POSTS: "..(player:GetAttribute("RRLifeUploads") or 0)..
  " • FINES: "..(player:GetAttribute("RRLifeFines") or 0)..
  " • ARRESTS: "..(player:GetAttribute("RRLifeArrests") or 0)..
  (player:GetAttribute("RRLifeJailed") and " • IN JAIL" or "")
 lifeHelp.Text="HUNGER "..(player:GetAttribute("RRLifeHunger") or 100)..
  " • ENERGY "..(player:GetAttribute("RRLifeEnergy") or 100)..
  " • HYGIENE "..(player:GetAttribute("RRLifeHygiene") or 100)..
  " • FUN "..(player:GetAttribute("RRLifeFun") or 100)..
  " • HOME "..(player:GetAttribute("RRLifeHomeLocked") and "LOCKED" or "UNLOCKED")..
  " • FREE MEALS AND REST AT THE COMMUNITY PARK • HOME BED & SINK"
 for _,entry in ipairs(LifeCatalog.Items) do
  local owned=player:GetAttribute("RRLifeOwn_"..entry.id)==true
  local seedStock=player:GetAttribute("RRLifeSeed_"..entry.id)
  local seedPacket=type(seedStock)=="number"
  local available=owned and "OWNED" or
   (level<entry.level and "LEVEL LOCKED" or
    coins<entry.price and "SAVE UP" or "BUY AT STORE")
  if seedPacket then
   available="BUY +3 PLANTINGS • IN BAG: "..seedStock
   if level<entry.level then available="LEVEL LOCKED" end
  end
  lifeItems[entry.id].Text=entry.name.." • "..entry.price.." COINS"..
   " • LV "..entry.level.." • "..available..
   " • "..(LifeCatalog.ShopLocations[entry.category] or "")
  lifeItems[entry.id].BackgroundColor3=owned and not seedPacket and Color3.fromRGB(49,107,91)
   or Color3.fromRGB(88,105,129)
 end
 local shards=player:GetAttribute("RRShards") or 0
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
 for _,entry in ipairs(Catalog.Items) do
  local owned=player:GetAttribute("RROwn_"..entry.id)==true
  local enoughLevel=level>=entry.level
  local status=owned and "OWNED" or
   (not enoughLevel and ("LOCKED UNTIL LEVEL "..entry.level)) or
   (coins<entry.coins and "KEEP EARNING COINS") or "AVAILABLE TO EARN"
  prestigeItems[entry.id].Text=entry.name.." | "..Catalog.PriceText(entry)..
   " | "..status
  prestigeItems[entry.id].BackgroundColor3=owned and Color3.fromRGB(49,112,88)
   or enoughLevel and Color3.fromRGB(90,102,137)
   or Color3.fromRGB(59,68,82)
 end
end
for _,name in ipairs({"RRCoins","RRShards","RRLevel","RRXP","RRBlaster",
 "RRShield","RRPet","RRScatter","RRSeals","RRDeliveryTarget","RRQuestShards",
 "RRWood","RRMetal","RRFish","RRHide","RRToolkits","RRHeat","RRSportsWins","RRHeists","RRHouseOwned","RRQuestDrones","RRQuestSeals",
 "RROwn_CITY_WRAP","RROwn_ESTATE_ROOF","RROwn_PLATINUM_WRAP",
 "RROwn_HOME_GARAGE","RROwn_AURORA_TRAIL",
 "RROwn_SNOWMOBILE_LICENSE","RROwn_JETPACK_LICENSE","RROwn_FLIGHT_LICENSE",
 "RRLifeCareer","RRLifeFollowers","RRLifeUploads","RRLifeFines",
 "RRLifeArrests","RRLifeJailed","RRLifeReputation","RRLifeShifts",
 "RRLifeShift","RRLifeTaskStep","RRLifeTaskName",
 "RRLifeHunger","RRLifeEnergy","RRLifeHygiene",
 "RRLifeFun","RRLifeHomeLocked","RRLifeHomePlot","RRLifeSelectedCar",
 "RRLifeGardenPlot","RRLifeGardenCrop","RRLifeGardenStatus",
 "RRLifeGardenHarvests","RRLifeGardenProduce"}) do
 player:GetAttributeChangedSignal(name):Connect(update)
end
for _,entry in ipairs(LifeCatalog.Items) do
 player:GetAttributeChangedSignal("RRLifeOwn_"..entry.id):Connect(update)
 if entry.category=="GARDEN" then
  player:GetAttributeChangedSignal("RRLifeSeed_"..entry.id):Connect(update)
 end
end
task.spawn(function()
 while gui.Parent do
  task.wait(2)
  local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
  if root and root.Position.Z>2200 and root.Position.Z<2550 then
   phase.Visible=false
   title.Text="RIFTLIFE • DOWNTOWN"
   hint.Text="EXPLORE REAL CITY STREETS • WALK TO LIFE CITY JOBS • DRIVE & EXPLORE"
  elseif root and root.Position.Z>1430 and root.Position.Z<1930 then
   phase.Visible=false
   title.Text="RIFTLIFE • CAREERS"
   local shift=player:GetAttribute("RRLifeShift") or ""
   hint.Text=shift~="" and
    ("ON SHIFT: "..shift.." • "..(player:GetAttribute("RRLifeTaskName") or "")) or
    "LIFE CITY • FIND WORK • EARN WAGES • BUY A HOME • RUN A BUSINESS"
  else
   phase.Visible=true
   title.Text="RIFT RAIDERS • ADVENTURE"
  end
 end
end)
local function phaseUpdate()
 local current=world:GetAttribute("Phase") or "CALM"
 phase.Text=current.." | "..(world:GetAttribute("SecondsLeft") or 0).."s"..
  " | "..(world:GetAttribute("Weather") or "CLEAR")..
  (current=="SURGE" and (" TITAN HP: "..(world:GetAttribute("BossHealth") or 0)) or " TO SURGE")
end
world:GetAttributeChangedSignal("Phase"):Connect(phaseUpdate)
world:GetAttributeChangedSignal("SecondsLeft"):Connect(phaseUpdate)
world:GetAttributeChangedSignal("BossHealth"):Connect(phaseUpdate)
world:GetAttributeChangedSignal("Weather"):Connect(phaseUpdate)
local qualityModes={"LOW","MED","HIGH"}
local qualityIndex=2
local rainStreaks={}
for i=1,22 do
 local streak=Instance.new("Part")
 streak.Name="LocalRainStreak"
 streak.Size=Vector3.new(.09,3.5,.09)
 streak.Color=Color3.fromRGB(175,207,241)
 streak.Material=Enum.Material.Glass
 streak.Transparency=.35
 streak.Anchored=true; streak.CanCollide=false; streak.CanTouch=false
 streak.CanQuery=false; streak.CastShadow=false
 streak.Parent=workspace
 streak.LocalTransparencyModifier=1
 table.insert(rainStreaks,streak)
end
local function applyGraphics()
 local quality=qualityModes[qualityIndex]
 qualityButton.Text="GRAPHICS: "..quality
 for _,effect in ipairs(Lighting:GetChildren()) do
  if effect:IsA("BloomEffect") or effect:IsA("SunRaysEffect") or
   effect:IsA("ColorCorrectionEffect") then
   effect.Enabled=quality~="LOW" and
    (quality=="HIGH" or not effect:IsA("SunRaysEffect"))
  end
 end
 local clouds=workspace.Terrain:FindFirstChildOfClass("Clouds")
 if clouds then clouds.Enabled=quality~="LOW" end
 Lighting.GlobalShadows=quality~="LOW"
end
qualityButton.Activated:Connect(function()
 qualityIndex=qualityIndex%#qualityModes+1
 applyGraphics()
end)
task.defer(applyGraphics)
local rainAccum=0
RunService.Heartbeat:Connect(function(dt)
 rainAccum+=dt
 if rainAccum<.085 then return end
 rainAccum=0
 local count=qualityIndex==3 and 22 or qualityIndex==2 and 8 or 0
 local raining=world:GetAttribute("Weather")=="RAIN"
 local camera=workspace.CurrentCamera
 for i,streak in ipairs(rainStreaks) do
  local show=raining and i<=count and camera~=nil
  streak.LocalTransparencyModifier=show and 0 or 1
  if show then
   streak.CFrame=CFrame.new(camera.CFrame.Position+
    Vector3.new(math.random(-28,28),math.random(-7,22),math.random(-25,25)))*
    CFrame.Angles(0,0,math.rad(10))
  end
 end
end)
update(); phaseUpdate()
print("SF_RIFT_RAIDERS_CLIENT_READY")
