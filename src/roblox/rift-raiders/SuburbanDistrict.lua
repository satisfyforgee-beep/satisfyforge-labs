-- v0.14 Script-free official Roblox Studio Suburban template architecture.
-- Detailed source houses/stores remain actual prefabs, not generated cubes.
local ServerStorage=game:GetService("ServerStorage")
local Suburbs={}
local arrivals=Vector3.new(0,8,3425)
local layout={
 {name="Suburban Single Story House",center=Vector3.new(-200,0,3530)},
 {name="Suburban Two Story House",center=Vector3.new(-25,0,3565)},
 {name="Suburban Convenience Market",center=Vector3.new(215,0,3490)},
 {name="Suburban Gas Station",center=Vector3.new(220,0,3650)},
 {name="Suburban Detailed Garage",center=Vector3.new(25,0,3710)},
 {name="Suburban Playground",center=Vector3.new(-200,0,3710)},
}
local function solid(parent,name,size,pos,color,mat,collision)
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.CFrame=CFrame.new(pos)
 p.Anchored=true;p.CanCollide=collision~=false;p.CanTouch=false
 p.Material=mat or Enum.Material.Concrete;p.Color=color
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth;p.Parent=parent
 return p
end
local function sign(folder,title,position)
 local post=solid(folder,title.." Signboard",Vector3.new(17,5,.4),
  position,Color3.fromRGB(69,81,95),Enum.Material.Metal,false)
 local gui=Instance.new("SurfaceGui")
 gui.Face=Enum.NormalId.Front;gui.CanvasSize=Vector2.new(420,130)
 gui.PixelsPerStud=30;gui.Parent=post
 local label=Instance.new("TextLabel")
 label.Size=UDim2.fromScale(1,1)
 label.Text=title;label.TextScaled=true;label.TextWrapped=true
 label.Font=Enum.Font.GothamBold
 label.TextColor3=Color3.fromRGB(240,233,209)
 label.BackgroundTransparency=1;label.Parent=gui
 return post
end
function Suburbs.Build(world,options)
 options=options or {}
 local source=ServerStorage:WaitForChild("OfficialSuburbanArchitecture")
 local folder=Instance.new("Folder")
 folder.Name="Official Detailed Suburban Town";folder.Parent=world
 local terrain=workspace.Terrain
 terrain:FillBlock(CFrame.new(0,-6,3600),
  Vector3.new(760,13,510),Enum.Material.Grass)
 for _,z in ipairs({3435,3610}) do
  solid(folder,"Neighborhood Asphalt Boulevard",
   Vector3.new(730,.65,22),Vector3.new(0,1.05,z),
   Color3.fromRGB(73,76,79),Enum.Material.Asphalt,true)
  for x=-342,342,38 do
   solid(folder,"Road Center Lane Paint",
    Vector3.new(14,.1,.4),Vector3.new(x,1.42,z),
    Color3.fromRGB(223,207,149),Enum.Material.Concrete,false)
  end
 end
 for _,x in ipairs({-315,80}) do
  solid(folder,"Suburban Cross Avenue",
   Vector3.new(17,.7,310),Vector3.new(x,1,3570),
   Color3.fromRGB(75,79,83),Enum.Material.Asphalt,true)
 end
 local imported=0
 local countParts=0
 for _,asset in ipairs(layout) do
  local sample=source:FindFirstChild(asset.name)
  if not sample then warn("Missing official suburban prefab",asset.name) continue end
  local clone=sample:Clone()
  -- Roblox's Playground template is a Folder containing many 3D models.
  -- Wrap it into a Model so it supports precise bounding-box relocation.
  if not clone:IsA("Model") then
   local wrapper=Instance.new("Model")
   wrapper.Name=clone.Name
   for _,child in ipairs(clone:GetChildren()) do
    child.Parent=wrapper
   end
   clone:Destroy()
   clone=wrapper
  end
  clone.Parent=folder
  local box,sz=clone:GetBoundingBox()
  local offset=Vector3.new(asset.center.X-box.Position.X,
   2.05-(box.Position.Y-sz.Y*.5),
   asset.center.Z-box.Position.Z)
  clone:PivotTo(clone:GetPivot()+offset)
  local pieces=0
  for _,node in ipairs(clone:GetDescendants()) do
   if node:IsA("LuaSourceContainer") then
    node:Destroy()
   elseif node:IsA("BasePart") then
    node.Anchored=true
    node.CanTouch=false
    pieces+=1
   end
  end
  clone:SetAttribute("OfficialTemplate",true)
  clone:SetAttribute("OriginalVisiblePieces",pieces)
  clone:SetAttribute("EnvironmentalPrefab",true)
  imported+=1;countParts+=pieces
 end
 local arrival=solid(folder,"Suburban Community Arrival",
  Vector3.new(20,.5,15),Vector3.new(0,1.65,3425),
  Color3.fromRGB(154,153,144),Enum.Material.Concrete,true)
 sign(folder,"RIFTLIFE SUBURBAN DISTRICT",Vector3.new(0,11,3407))
 sign(folder,"SHOPS • GAS STATION • HOMES",
  Vector3.new(15,8,3461))
 -- Real, server-validated economic/gameplay points near detailed prefabs.
 -- No imported Toolbox or template scripts are executed.
 local activityFolder=Instance.new("Folder")
 activityFolder.Name="Working Suburban Services"
 activityFolder.Parent=folder
 local function station(name,position,title,details)
  local node=solid(activityFolder,name,Vector3.new(5,4,.7),position,
   Color3.fromRGB(70,83,88),Enum.Material.Metal,false)
  node.CanQuery=false
  local gui=Instance.new("SurfaceGui")
  gui.Name="Official Suburb Service Sign"
  gui.Face=Enum.NormalId.Front
  gui.CanvasSize=Vector2.new(620,350)
  gui.Parent=node
  local headline=Instance.new("TextLabel")
  headline.Size=UDim2.fromScale(1,.59)
  headline.BackgroundTransparency=1;headline.Text=title
  headline.TextScaled=true;headline.TextWrapped=true
  headline.Font=Enum.Font.GothamBold
  headline.TextColor3=Color3.fromRGB(247,239,215)
  headline.Parent=gui
  local sub=Instance.new("TextLabel")
  sub.Position=UDim2.fromScale(0,.59)
  sub.Size=UDim2.fromScale(1,.39)
  sub.BackgroundTransparency=1;sub.Text=details
  sub.TextScaled=true;sub.TextWrapped=true
  sub.Font=Enum.Font.Gotham
  sub.TextColor3=Color3.fromRGB(142,215,208)
  sub.Parent=gui
  return node
 end
 local function activate(node,text,what,callback)
  local prompt=Instance.new("ProximityPrompt")
  prompt.Name="Suburban "..what.." Prompt"
  prompt.ActionText=text
  prompt.ObjectText=what
  prompt.HoldDuration=.3;prompt.MaxActivationDistance=13
  prompt.RequiresLineOfSight=false
  prompt.Parent=node
  prompt.Triggered:Connect(callback)
 end
 local registered=0
 local function register(kind,id,node,step)
  if options.register and options.register(kind,id,node,step) then
   registered+=1
  end
 end
 local market=station("Official Suburban Market Checkout",
  Vector3.new(208,5,3447),"MARKET","GROCERIES • GARDEN • HOME")
 for _,category in ipairs({"HOME","GARDEN","TECH"}) do
  register("STORE",category,market)
 end
 register("SNACK","MARKET",market)
 activate(market,"BROWSE STORE","Convenience Market",function(player)
  if options.tell then
   options.tell(player,"OPEN LIFE → SHOPPING • HOME, GARDEN OR TECH • USE EARNED COINS.")
  end
 end)
 activate(market,"BUY SNACK • 15 COINS","Convenience Market Snack",function(player)
  if options.process then options.process(player,"BuySnack","MARKET") end
 end)
 local garage=station("Official Suburban Auto Garage Checkout",
  Vector3.new(22,5,3668),"AUTO REPAIR","CAR DEALER • WORK SHIFTS")
 register("STORE","VEHICLE",garage)
 activate(garage,"SHOP VEHICLES","Suburban Motor Garage",function(player)
  if options.tell then
   options.tell(player,"OPEN LIFE → SHOPPING → VEHICLE OR LIFE → GARAGE.")
  end
 end)
 local roadside=station("Official Suburban Gas Station Kiosk",
  Vector3.new(214,5,3617),"ROADSIDE STOP","CARS • SNACKS • COURIERS")
 register("STORE","VEHICLE",roadside)
 register("SNACK","MARKET",roadside)
 activate(roadside,"BROWSE AUTO","Suburban Gas Station",function(player)
  if options.tell then options.tell(player,"OPEN LIFE → GARAGE OR SHOPPING → VEHICLE.") end
 end)
 activate(roadside,"BUY SNACK • 15 COINS","Roadside Snacks",function(player)
  if options.process then options.process(player,"BuySnack","MARKET") end
 end)
 local park=station("Suburban Play Park Rest Station",
  Vector3.new(-191,5,3676),"PLAYGROUND","TAKE A BREAK")
 register("REST","PUBLIC",park)
 activate(park,"REST","Suburban Public Park",function(player)
  if options.process then options.process(player,"Rest","PUBLIC") end
 end)
 local careers={
  {id="RETAIL",name="Market Retail",at=Vector3.new(182,5,3452)},
  {id="MECHANIC",name="Vehicle Mechanic",at=Vector3.new(4,5,3679)},
  {id="COURIER",name="Roadside Courier",at=Vector3.new(191,5,3618)},
  {id="SECURITY_GUARD",name="Store Security",at=Vector3.new(232,5,3454)},
 }
 for _,entry in ipairs(careers) do
  local id=entry.id
  local site=station("Suburban Worksite "..id,entry.at,
   entry.name:upper(),"HIRE • SHIFT • 2 TASKS")
  register("CAREER",id,site)
  register("WORK",id,site)
  activate(site,"APPLY FOR JOB",entry.name,function(player)
   if options.process then options.process(player,"Career",id) end
  end)
  activate(site,"START / FINISH SHIFT",entry.name,function(player)
   if options.process then options.process(player,"Work",id) end
  end)
  for step=1,2 do
   local offset=step==1 and -8 or 8
   local task=station("Suburban Work Task "..id.." "..step,
    entry.at+Vector3.new(offset,0,0),
    step==1 and "TASK 1" or "TASK 2",
    step==1 and "PREPARE WORK" or "COMPLETE SERVICE")
   register("TASK",id,task,step)
   activate(task,step==1 and "PREPARE" or "COMPLETE",
    entry.name.." Task "..step,function(player)
    if options.process then options.process(player,"Task",id,step) end
   end)
  end
 end
 folder:SetAttribute("ActiveSuburbanWorkplaces",#careers)
 folder:SetAttribute("ServerValidatedServicePoints",registered)
 folder:SetAttribute("EnvironmentOnly",false)
 folder:SetAttribute("OfficialPrefabCount",imported)
 folder:SetAttribute("DetailedSourceParts",countParts)
 folder:SetAttribute("GeometryOrigin","Official Roblox Studio Suburban")
 return arrivals
end
return Suburbs
