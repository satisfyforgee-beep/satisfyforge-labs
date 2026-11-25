-- Rift Raiders v0.12: usable downtown gardening and produce market.
-- All plots/actions are server-authoritative; purchases use earned coins.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Garden={}
Garden.Crops={
 TOMATO_SEEDS={name="Tomatoes",grow=55,yield=3,value=18,color=Color3.fromRGB(202,60,49)},
 CARROT_SEEDS={name="Carrots",grow=45,yield=4,value=12,color=Color3.fromRGB(237,137,52)},
 STRAWBERRY_SEEDS={name="Strawberries",grow=60,yield=3,value=24,color=Color3.fromRGB(207,54,68)},
 POTATO_SEEDS={name="Potatoes",grow=48,yield=4,value=11,color=Color3.fromRGB(165,119,83)},
 LETTUCE_SEEDS={name="Lettuce",grow=38,yield=3,value=11,color=Color3.fromRGB(109,168,80)},
 PEPPER_SEEDS={name="Bell Peppers",grow=58,yield=3,value=20,color=Color3.fromRGB(219,165,49)},
 CUCUMBER_SEEDS={name="Cucumbers",grow=55,yield=4,value=15,color=Color3.fromRGB(77,142,72)},
 CORN_SEEDS={name="Sweet Corn",grow=80,yield=4,value=22,color=Color3.fromRGB(242,198,74)},
 PUMPKIN_SEEDS={name="Pumpkins",grow=90,yield=2,value=54,color=Color3.fromRGB(222,113,49)},
 SUNFLOWER_SEEDS={name="Sunflowers",grow=60,yield=3,value=15,color=Color3.fromRGB(242,196,60)},
 BLUEBERRY_SEEDS={name="Blueberries",grow=80,yield=4,value=26,color=Color3.fromRGB(75,82,165)},
 ROSE_SEEDS={name="Roses",grow=75,yield=3,value=30,color=Color3.fromRGB(198,68,95)},
 APPLE_TREE_SEEDS={name="Apple Saplings",grow=105,yield=4,value=32,color=Color3.fromRGB(190,70,58)},
 WATERMELON_SEEDS={name="Watermelons",grow=100,yield=2,value=67,color=Color3.fromRGB(80,156,89)},
}
Garden.Order={
 "TOMATO_SEEDS","CARROT_SEEDS","STRAWBERRY_SEEDS","POTATO_SEEDS",
 "LETTUCE_SEEDS","PEPPER_SEEDS","CUCUMBER_SEEDS","CORN_SEEDS",
 "PUMPKIN_SEEDS","SUNFLOWER_SEEDS","BLUEBERRY_SEEDS",
 "ROSE_SEEDS","APPLE_TREE_SEEDS","WATERMELON_SEEDS"
}
local plots={}
local allocated={}
local gardenFolder=nil
local market=nil
local callbacks=nil
local elapsed=0
local function safeInt(value,max)
 return math.clamp(math.floor(tonumber(value) or 0),0,max)
end
function Garden.Normalize(raw)
 raw=type(raw)=="table" and raw or {}
 local crop=type(raw.crop)=="string" and Garden.Crops[raw.crop] and raw.crop or ""
 local now=os.time()
 local planted=safeInt(raw.plantedAt,now)
 if planted<=0 then crop="";planted=0 end
 local inventory={}
 local seeds={}
 for id in pairs(Garden.Crops) do
  local stock=type(raw.seeds)=="table" and raw.seeds[id]
  local quantity=safeInt(stock,99)
  if quantity>0 then seeds[id]=quantity end
  local qty=type(raw.produce)=="table" and raw.produce[id]
  local count=safeInt(qty,500)
  if count>0 then inventory[id]=count end
 end
 return {
  crop=crop,plantedAt=planted,watered=raw.watered==true,
  harvests=safeInt(raw.harvests,100000),
  sales=safeInt(raw.sales,100000),
  produce=inventory,seeds=seeds,
 }
end
local function status(g)
 if not g or g.crop=="" then return "EMPTY" end
 local species=Garden.Crops[g.crop]
 if not species then return "EMPTY" end
 if os.time()-g.plantedAt>=species.grow then
  return g.watered and "READY" or "NEEDS WATER"
 end
 return g.watered and "GROWING" or "DRY"
end
Garden.Status=status
function Garden.ProduceCount(g)
 local total=0
 if g then for _,qty in pairs(g.produce or {}) do total+=qty end end
 return total
end
local function block(parent,name,size,pos,color,material,collides)
 local item=Instance.new("Part")
 item.Name=name;item.Size=size;item.CFrame=CFrame.new(pos)
 item.Anchored=true;item.CanCollide=collides==true;item.CanTouch=false
 item.Material=material or Enum.Material.WoodPlanks
 item.Color=color;item.TopSurface=Enum.SurfaceType.Smooth
 item.BottomSurface=Enum.SurfaceType.Smooth;item.Parent=parent
 return item
end
local function ball(parent,name,size,pos,color,material)
 local item=block(parent,name,size,pos,color,material or Enum.Material.Grass,false)
 item.Shape=Enum.PartType.Ball;return item
end
local function pole(parent,name,size,pos,color,material)
 local item=block(parent,name,size,pos,color,material or Enum.Material.Wood,false)
 item.Shape=Enum.PartType.Cylinder;return item
end
local function prompt(base,action,label,fn)
 local p=Instance.new("ProximityPrompt")
 p.ActionText=action;p.ObjectText=label;p.HoldDuration=.4
 p.MaxActivationDistance=12;p.RequiresLineOfSight=false
 p.Parent=base;p.Triggered:Connect(fn)
 return p
end
local function label(base,title)
 local bill=Instance.new("BillboardGui")
 bill.Name="Garden Plot Label";bill.Size=UDim2.fromOffset(195,65)
 bill.StudsOffsetWorldSpace=Vector3.new(0,4,0)
 bill.MaxDistance=60;bill.AlwaysOnTop=false;bill.Parent=base
 local text=Instance.new("TextLabel")
 text.Name="Text";text.Size=UDim2.fromScale(1,1)
 text.BackgroundColor3=Color3.fromRGB(31,50,43);text.BackgroundTransparency=.12
 text.BorderSizePixel=0;text.Text=title;text.TextScaled=true
 text.TextWrapped=true;text.Font=Enum.Font.GothamBold
 text.TextColor3=Color3.fromRGB(246,237,214);text.Parent=bill
 return text
end
local function planter(index,pos)
 local m=Instance.new("Model")
 m.Name="Raised Garden Bed "..index;m.Parent=gardenFolder
 local frame=block(m,"Garden Cedar Foundation",Vector3.new(12,1,9),
  pos+Vector3.new(0,1,0),Color3.fromRGB(132,96,60),Enum.Material.WoodPlanks,true)
 local soil=block(m,"Organic Garden Soil",Vector3.new(10.4,.65,7.4),
  pos+Vector3.new(0,1.7,0),Color3.fromRGB(100,70,55),Enum.Material.Ground,true)
 for _,x in ipairs({-5.7,5.7}) do
  block(m,"Bed Cedar Border",Vector3.new(.65,1.7,9.6),
   pos+Vector3.new(x,2,0),Color3.fromRGB(156,120,75),Enum.Material.WoodPlanks,true)
 end
 for _,z in ipairs({-4.1,4.1}) do
  block(m,"Bed Cedar Border",Vector3.new(12,1.7,.65),
   pos+Vector3.new(0,2,z),Color3.fromRGB(156,120,75),Enum.Material.WoodPlanks,true)
 end
 local sign=block(m,"Garden Bed Number "..index,Vector3.new(1,.25,1),
  pos+Vector3.new(-4.4,3,3),Color3.fromRGB(180,151,93),Enum.Material.Metal,false)
 local text=label(sign,"PLOT "..index.."\nUNASSIGNED")
 local visible=Instance.new("Model")
 visible.Name="Garden Plants";visible.Parent=m
 local rec={model=m,base=soil,position=pos,label=text,vegetation=visible,owner=nil}
 prompt(soil,"TEND GARDEN","Your Garden Bed",function(player)
  if callbacks and callbacks.process then callbacks.process(player,"GardenWater") end
 end)
 table.insert(plots,rec)
end
local function updatePlants(rec,g)
 rec.vegetation:ClearAllChildren()
 if not g or g.crop=="" then return end
 local species=Garden.Crops[g.crop]
 if not species then return end
 local stage=status(g)
 local fully=(stage=="READY" or stage=="NEEDS WATER")
 local age=math.max(0,os.time()-g.plantedAt)
 local grown=fully and 1 or math.clamp(age/species.grow,.1,.82)
 local height=(species.name=="Sweet Corn" or species.name=="Sunflowers") and 8 or 4.5
 if species.name=="Apple Saplings" then height=9 end
 for i=1,4 do
  local x=i%2==0 and 2.65 or -2.65
  local z=i<=2 and -1.6 or 1.6
  local center=rec.position+Vector3.new(x,2,z)
  local size=math.max(.9,height*grown)
  local stalk=pole(rec.vegetation,"Crop Stem "..i,Vector3.new(.35,size,.35),
   center+Vector3.new(0,size*.5,0),Color3.fromRGB(75,127,61))
  for j=1,3 do
   local radius=math.max(.7,1.15*grown)
   ball(rec.vegetation,"Natural Leaf "..j,Vector3.new(radius*1.5,.25,radius),
    center+Vector3.new(j%2==0 and -.9 or .9,1+j*size*.17,j==1 and .7 or -.5),
    Color3.fromRGB(70+6*j,138+2*j,72),Enum.Material.Grass)
  end
  if fully then
   for j=1,2 do
    local fruitSize=(species.name=="Pumpkins" or species.name=="Watermelons") and 2 or
     (species.name=="Tomatoes" or species.name=="Bell Peppers") and 1.1 or .8
    local y=(species.name=="Potatoes" or species.name=="Carrots") and 2.25 or (2.2+size*.6)
    ball(rec.vegetation,"Ripe "..species.name.." "..j,
     Vector3.new(fruitSize,fruitSize,fruitSize),
     center+Vector3.new(j==1 and -.6 or .7,y-center.Y,
      j==1 and -.4 or .4),species.color,Enum.Material.SmoothPlastic)
   end
  end
 end
end
function Garden.SyncPlayer(player,g)
 local rec=allocated[player]
 player:SetAttribute("RRLifeGardenPlot",rec and rec.model.Name or "WAIT FOR PLOT")
 player:SetAttribute("RRLifeGardenCrop",g and g.crop or "")
 player:SetAttribute("RRLifeGardenStatus",status(g))
 player:SetAttribute("RRLifeGardenHarvests",g and g.harvests or 0)
 player:SetAttribute("RRLifeGardenProduce",Garden.ProduceCount(g))
 for id in pairs(Garden.Crops) do
  player:SetAttribute("RRLifeSeed_"..id,g and g.seeds[id] or 0)
 end
end
local function refresh(player)
 local rec=allocated[player]
 local state=callbacks and callbacks.getProfile(player)
 local g=state and state.life and state.life.garden
 if rec then
  local description=g and g.crop~="" and Garden.Crops[g.crop].name or "UNPLANTED"
  rec.label.Text=player.DisplayName.."\n"..description..": "..status(g)
  rec.base:SetAttribute("OwnerUserId",player.UserId)
  rec.base:SetAttribute("Crop",g and g.crop or "")
  rec.base:SetAttribute("Stage",status(g))
  updatePlants(rec,g)
 end
 Garden.SyncPlayer(player,g)
end
local function decorativeTool(player,name,kind)
 local backpack=player:FindFirstChildOfClass("Backpack")
 if not backpack or backpack:FindFirstChild(name) or
  (player.Character and player.Character:FindFirstChild(name)) then return end
 local tool=Instance.new("Tool")
 tool.Name=name;tool.CanBeDropped=false;tool.RequiresHandle=true
 tool.ToolTip=kind=="CAN" and "Water your garden with the bed prompt" or
  "Use the Garden menu to plant seeds at your raised bed"
 local handle=Instance.new("Part")
 handle.Name="Handle";handle.Size=Vector3.new(.45,2.3,.45)
 handle.Material=Enum.Material.Wood;handle.Color=Color3.fromRGB(126,89,61)
 handle.CanCollide=false;handle.Massless=true
 handle.Parent=tool
 local function element(name,size,offset,color,shape)
  local p=Instance.new("Part");p.Name=name;p.Size=size
  p.Shape=shape or Enum.PartType.Block
  p.Color=color;p.Material=Enum.Material.Metal
  p.CanCollide=false;p.Massless=true;p.CFrame=handle.CFrame*CFrame.new(offset)
  p.Parent=tool
  local weld=Instance.new("WeldConstraint")
  weld.Part0=handle;weld.Part1=p;weld.Parent=p
 end
 if kind=="CAN" then
  element("Watering Can Metal Body",Vector3.new(1.3,1.7,1.3),
   Vector3.new(0,-.45,0),Color3.fromRGB(77,148,179),Enum.PartType.Cylinder)
  element("Watering Spout",Vector3.new(1.6,.45,.45),
   Vector3.new(1.25,-.75,0),Color3.fromRGB(87,157,187),
   Enum.PartType.Cylinder)
  element("Pouring Head",Vector3.new(.35,.75,.75),
   Vector3.new(2,-.75,0),Color3.fromRGB(111,168,193),
   Enum.PartType.Cylinder)
 else
  element("Trowel Steel Blade",Vector3.new(.85,1.9,.25),
   Vector3.new(0,-1.7,0),Color3.fromRGB(156,164,168))
 end
 tool.Parent=backpack
end
function Garden.GiveTools(player,life)
 if not life or not life.owned then return end
 if life.owned.GARDEN_TROWEL then decorativeTool(player,"Garden Trowel","TROWEL") end
 if life.owned.WATERING_CAN then decorativeTool(player,"Watering Can","CAN") end
end
function Garden.PlayerJoined(player)
 if allocated[player] then return end
 for _,rec in ipairs(plots) do
  if not rec.owner then
   rec.owner=player;allocated[player]=rec;refresh(player)
   break
  end
 end
end
function Garden.PlayerRemoving(player)
 local rec=allocated[player]
 if rec then
  rec.owner=nil;rec.label.Text="GARDEN BED\nAVAILABLE"
  rec.base:SetAttribute("OwnerUserId",0)
  rec.base:SetAttribute("Crop","");rec.base:SetAttribute("Stage","EMPTY")
  rec.vegetation:ClearAllChildren()
 end
 allocated[player]=nil
end
function Garden.PlotFor(player)
 return allocated[player] and allocated[player].base or nil
end
local function nearby(player,node,maxdist)
 local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
 return root and node and (root.Position-node.Position).Magnitude<(maxdist or 16)
end
function Garden.Process(player,kind,arg,s)
 if not callbacks or not s or not s.life then return false end
 local life=s.life;local g=life.garden
 local rec=allocated[player]
 if not rec then callbacks.tell(player,"ALL GARDEN PLOTS ARE OCCUPIED RIGHT NOW.");return false end
 local isAtPlot=nearby(player,rec.base,19)
 if kind=="GardenPlant" then
  if type(arg)~="string" or not Garden.Crops[arg] then return false end
  if not isAtPlot then callbacks.tell(player,"VISIT YOUR ASSIGNED RAISED BED IN THE DOWNTOWN COMMUNITY GARDEN.");return false end
  if g.crop~="" then callbacks.tell(player,"HARVEST YOUR EXISTING CROP FIRST.");return false end
  if not life.owned.GARDEN_TROWEL or (g.seeds[arg] or 0)<=0 then
   callbacks.tell(player,"BUY A GARDEN TROWEL AND A FRESH SEED PACK AT THE NURSERY FIRST.");return false
  end
  g.seeds[arg]-=1
  g.crop=arg;g.plantedAt=os.time();g.watered=false
  callbacks.tell(player,"PLANTED "..Garden.Crops[arg].name.."! WATER YOUR GARDEN TO GROW.")
 elseif kind=="GardenWater" then
  if not isAtPlot or g.crop=="" then return false end
  if not life.owned.WATERING_CAN then
   callbacks.tell(player,"BUY A WATERING CAN AT THE GARDEN NURSERY.");return false
  end
  if g.watered then callbacks.tell(player,"THIS CROP IS ALREADY WATERED.");return false end
  g.watered=true;callbacks.tell(player,"WATERED "..Garden.Crops[g.crop].name.." • COME BACK WHEN RIPE!")
 elseif kind=="GardenHarvest" then
  if not isAtPlot or g.crop=="" or status(g)~="READY" then
   callbacks.tell(player,"THE CROP MUST GROW AND BE WATERED BEFORE HARVEST.");return false
  end
  local species=Garden.Crops[g.crop]
  local amount=species.yield+(life.owned.GARDEN_FERTILIZER and 1 or 0)
  g.produce[g.crop]=math.min(500,(g.produce[g.crop] or 0)+amount)
  g.crop="";g.plantedAt=0;g.watered=false;g.harvests+=1
  callbacks.reward(player,0,8,0)
  callbacks.tell(player,"HARVESTED "..amount.." "..species.name.."! SELL AT THE FARM MARKET.")
 elseif kind=="GardenSell" then
  if not nearby(player,market,23) then return false end
  local total=0
  for id,n in pairs(g.produce) do
   local crop=Garden.Crops[id]
   if crop then total+=n*crop.value end
  end
  if total<=0 then callbacks.tell(player,"GROW AND HARVEST SOMETHING FIRST.");return false end
  g.produce={};g.sales+=1
  callbacks.reward(player,total,10,0)
  callbacks.tell(player,"SOLD YOUR HARVEST FOR "..total.." EARNED COINS!")
 else
  return false
 end
 refresh(player)
 return true
end
function Garden.Build(world,options)
 callbacks=options
 if gardenFolder then gardenFolder:Destroy() end
 gardenFolder=Instance.new("Folder")
 gardenFolder.Name="Downtown Community Garden";gardenFolder.Parent=world
 table.clear(plots);table.clear(allocated)
 block(gardenFolder,"Community Garden Grass Lawn",Vector3.new(180,.4,55),
  Vector3.new(0,.1,2168),Color3.fromRGB(78,125,73),Enum.Material.Grass,true)
 for index=1,16 do
  local col=(index-1)%8
  local row=math.floor((index-1)/8)
  planter(index,Vector3.new(-70+col*20,1.5,2160+row*18))
 end
 local stand=block(gardenFolder,"Downtown Farm Produce Market",Vector3.new(14,4,6),
  Vector3.new(90,4,2185),Color3.fromRGB(122,85,53),Enum.Material.WoodPlanks,true)
 market=stand
 -- Original market stall: canopy, produce baskets and visible harvests.
 for _,x in ipairs({-6,6}) do
  block(gardenFolder,"Produce Market Canopy Post",Vector3.new(.5,8,.5),
   Vector3.new(90+x,8,2185),
   Color3.fromRGB(135,113,82),Enum.Material.Wood,true)
 end
 block(gardenFolder,"Outdoor Farm Market Awning",Vector3.new(18,.6,9),
  Vector3.new(90,12.3,2185),Color3.fromRGB(92,153,95),
  Enum.Material.Fabric,false)
 for idx,x in ipairs({-4,0,4}) do
  block(gardenFolder,"Fresh Market Basket",Vector3.new(3,1,3),
   Vector3.new(90+x,6.5,2185),Color3.fromRGB(155,121,72),
   Enum.Material.WoodPlanks,false)
  for j=1,4 do
   ball(gardenFolder,"Market Organic Produce",
    Vector3.new(.75,.75,.75),
    Vector3.new(90+x+(j%2)*1,7.2,2185+math.floor(j/3)*1),
    idx==1 and Color3.fromRGB(210,68,62) or
    idx==2 and Color3.fromRGB(223,137,53) or
    Color3.fromRGB(80,161,78),Enum.Material.SmoothPlastic)
  end
 end
 label(stand,"FARM MARKET\nSELL YOUR PRODUCE")
 prompt(stand,"SELL HARVEST","Downtown Produce Market",function(player)
  if callbacks and callbacks.process then callbacks.process(player,"GardenSell") end
 end)
 gardenFolder:SetAttribute("GardenBedCount",#plots)
 gardenFolder:SetAttribute("CropVarieties",#Garden.Order)
 local lastStages={}
 elapsed=0
 RunService.Heartbeat:Connect(function(dt)
  if not gardenFolder or not gardenFolder.Parent then return end
  elapsed+=dt
  if elapsed<5 then return end
  elapsed=0
  for p,rec in pairs(allocated) do
   local s=callbacks.getProfile(p)
   local g=s and s.life and s.life.garden
   local stage=status(g)
   if lastStages[p]~=stage then
    lastStages[p]=stage
    refresh(p)
   end
  end
 end)
 Players.PlayerRemoving:Connect(function(p)
  lastStages[p]=nil
 end)
 return gardenFolder
end
return Garden
