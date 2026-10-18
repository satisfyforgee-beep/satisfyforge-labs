-- Rift Raiders v0.20: downtown street-level visual pass informed by public
-- Bloxburg city-detailing and Roblox Creator Hub onboarding guidance.
-- Reuses sanitized official Modern City mesh street furniture; original
-- signage, bus stop, traffic signals and wayfinding are our own models.
-- No untrusted third-party scripts or paywalled Marketplace assets.
local CollectionService=game:GetService("CollectionService")
local Streets={}
local DETAIL_TAG="RROptionalStreetscape"
local transitStations={}
function Streets.UseTransit(player,code,tell)
 local stop=transitStations[code]
 if not stop or not stop.button or not stop.button.Parent then return false end
 local character=player.Character
 local humanoid=character and character:FindFirstChildOfClass("Humanoid")
 local root=character and character:FindFirstChild("HumanoidRootPart")
 if not root or not humanoid or humanoid.Health<=0 or
  (root.Position-stop.button.Position).Magnitude>17 then
  return false
 end
 character:PivotTo(CFrame.new(stop.destination))
 if tell then tell(player,"RIFTLIFE TRANSIT • ARRIVED AT "..stop.name:upper()) end
 return true
end
local function part(parent,name,size,cf,color,material,collide)
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.CFrame=cf
 p.Color=color;p.Material=material or Enum.Material.Metal
 p.Anchored=true;p.CanCollide=collide==true;p.CanTouch=false
 p.CanQuery=collide==true;p.CastShadow=collide==true
 p.TopSurface=Enum.SurfaceType.Smooth;p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=parent
 return p
end
local function detail(p)
 if p:IsA("BasePart") then
  p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
  p.CastShadow=false
  CollectionService:AddTag(p,DETAIL_TAG)
 end
end
local function cloneOfficial(folder,source,position,name)
 if not source or not source:IsA("Model") then return nil end
 local clone=source:Clone()
 clone.Name=name
 clone.Parent=folder
 local cf,size=clone:GetBoundingBox()
 local bottom=cf.Position.Y-size.Y*.5
 clone:PivotTo(clone:GetPivot()+
  Vector3.new(position.X-cf.Position.X,position.Y-bottom,position.Z-cf.Position.Z))
 for _,desc in ipairs(clone:GetDescendants()) do
  if desc:IsA("LuaSourceContainer") then
   desc:Destroy()
  elseif desc:IsA("BasePart") then
   desc.Anchored=true;detail(desc)
  elseif desc:IsA("PointLight") or desc:IsA("SpotLight") or
    desc:IsA("SurfaceLight") then
   desc.Shadows=false;desc.Brightness=math.min(desc.Brightness,.35)
  end
 end
 return clone
end
local function billboard(node,main,tag,color)
 local gui=Instance.new("SurfaceGui")
 gui.Name="Premium City Directional Typography"
 gui.Face=Enum.NormalId.Front
 gui.CanvasSize=Vector2.new(720,300)
 gui.LightInfluence=.2;gui.Parent=node
 local back=Instance.new("Frame")
 back.Size=UDim2.fromScale(1,1);back.BorderSizePixel=0
 back.BackgroundColor3=Color3.fromRGB(27,45,47)
 back.Parent=gui
 local accent=Instance.new("Frame")
 accent.BorderSizePixel=0;accent.Size=UDim2.fromScale(.025,1)
 accent.BackgroundColor3=color
 accent.Parent=back
 local title=Instance.new("TextLabel")
 title.Name="City Business Name"
 title.Size=UDim2.new(.91,0,.51,0)
 title.Position=UDim2.fromScale(.065,.08)
 title.BackgroundTransparency=1
 title.Font=Enum.Font.GothamBlack
 title.TextColor3=Color3.fromRGB(250,245,225)
 title.TextScaled=true;title.TextWrapped=true
 title.Text=main;title.Parent=back
 local subtitle=Instance.new("TextLabel")
 subtitle.Name="City Business Description"
 subtitle.Size=UDim2.new(.91,0,.28,0)
 subtitle.Position=UDim2.fromScale(.065,.65)
 subtitle.BackgroundTransparency=1
 subtitle.Font=Enum.Font.GothamBold;subtitle.TextScaled=true
 subtitle.TextColor3=color;subtitle.Text=tag
 subtitle.Parent=back
end
local function prompt(node,action,title,fn)
 local p=Instance.new("ProximityPrompt")
 p.Name="Accessible City "..title
 p.ActionText=action;p.ObjectText=title;p.HoldDuration=.35
 p.MaxActivationDistance=14;p.RequiresLineOfSight=false
 p.Parent=node;p.Triggered:Connect(fn)
end
local function busShelter(folder,tell)
 local anchor=Vector3.new(-48,1.4,2212)
 local base=part(folder,"Urban Transit Curbside",
  Vector3.new(21,.3,9),CFrame.new(anchor),
  Color3.fromRGB(187,177,159),Enum.Material.Concrete,true)
 local mat=Color3.fromRGB(51,67,73)
 for _,x in ipairs({-8.8,8.8}) do
  for _,z in ipairs({-3.4,3.4}) do
   local support=part(folder,"Bus Stop Stainless Stanchion",
    Vector3.new(.35,7.5,.35),
    CFrame.new(anchor+Vector3.new(x,3.7,z)),
    mat,Enum.Material.Metal,true)
  end
 end
 local roof=part(folder,"Urban Transit Tinted Roof",
  Vector3.new(22,.35,10),CFrame.new(anchor+Vector3.new(0,7.45,0)),
  Color3.fromRGB(75,116,130),Enum.Material.Glass,false)
 roof.Transparency=.24
 local glass=part(folder,"Bus Stop Tempered Glass",
  Vector3.new(20,5.7,.22),
  CFrame.new(anchor+Vector3.new(0,3.6,4)),
  Color3.fromRGB(136,183,192),Enum.Material.Glass,false)
 glass.Transparency=.48
 local seat=part(folder,"Bus Stop Cedar Bench",
  Vector3.new(15,.6,2.2),CFrame.new(anchor+Vector3.new(0,2.15,2)),
  Color3.fromRGB(149,121,87),Enum.Material.WoodPlanks,true)
 local board=part(folder,"Transit Neighborhood Destinations",
  Vector3.new(7,4,.6),
  CFrame.new(anchor+Vector3.new(0,5.1,-4)),
  Color3.fromRGB(32,52,55),Enum.Material.Metal,false)
 billboard(board,"RIFTLIFE TRANSIT","WORK • MARKET • HOMES",
  Color3.fromRGB(124,218,177))
 local stops={
  {name="Employment Center",where=Vector3.new(-73,7,2247),
   label="CITY JOBS",x=-7},
  {name="Downtown Community Garden",where=Vector3.new(0,5,2152),
   label="GARDEN",x=0},
  {name="Residential Estates",where=Vector3.new(0,8,2711),
   label="HOMES",x=7},
 }
 for _,stop in ipairs(stops) do
  local screen=part(folder,"Transit Stop "..stop.label,
   Vector3.new(4.8,1.5,.45),
   CFrame.new(anchor+Vector3.new(stop.x,3,-4.6)),
   Color3.fromRGB(52,89,83),Enum.Material.Metal,false)
  transitStations[stop.label]={
   button=screen,destination=stop.where,name=stop.name
  }
  prompt(screen,"RIDE TO "..stop.label,stop.name,function(player)
   Streets.UseTransit(player,stop.label,tell)
  end)
 end
 folder:SetAttribute("TransitStopCount",#stops)
end
local function trafficDetails(folder)
 local asphalt=Color3.fromRGB(69,73,73)
 local curb=Color3.fromRGB(188,180,163)
 for _,x in ipairs({-80,-55,55,80}) do
  for _,z in ipairs({2201,2247}) do
   local piece=part(folder,"Marked Pedestrian Crossing",
    Vector3.new(4.4,.07,1.25),
    CFrame.new(x,.18,z),
    Color3.fromRGB(230,229,212),Enum.Material.Concrete,false)
   detail(piece)
  end
 end
 for _,x in ipairs({-76,-47,47,76}) do
  local post=part(folder,"City Traffic Signal Pole",
   Vector3.new(.43,8,.43),
   CFrame.new(x,4.3,2246),
   Color3.fromRGB(63,75,77),Enum.Material.Metal,false)
  detail(post)
  local head=part(folder,"Pedestrian Signal Housing",
   Vector3.new(2.1,2.9,1.1),
   CFrame.new(x,8,2246),
   Color3.fromRGB(43,48,48),Enum.Material.Metal,false)
  detail(head)
  local walk=part(folder,"Illuminated Walk Signal",
   Vector3.new(1.3,.9,.12),
   head.CFrame*CFrame.new(0,-.7,-.62),
   Color3.fromRGB(66,192,124),Enum.Material.Neon,false)
  detail(walk)
  local stop=part(folder,"Illuminated Stop Signal",
   Vector3.new(1.3,.85,.12),
   head.CFrame*CFrame.new(0,.65,-.62),
   Color3.fromRGB(219,104,70),Enum.Material.Neon,false)
  detail(stop)
 end
 local platform=part(folder,"Street Bicycle Parking",
  Vector3.new(13,.2,6),
  CFrame.new(71,.35,2242),curb,Enum.Material.Concrete,false)
 detail(platform)
 for i=0,3 do
  local rack=part(folder,"Bike Parking Arc "..i,
   Vector3.new(.35,3.3,2.7),
   CFrame.new(66+i*3.2,2.1,2242),
   Color3.fromRGB(161,175,178),Enum.Material.Metal,false)
  detail(rack)
 end
end
local function simpleVenues(folder)
 local places={
  {"CITY LIFE","WORK • CAREERS",Vector3.new(-76,6.4,2241),
   Color3.fromRGB(110,206,184)},
  {"THE BEAN & BREW","ESPRESSO • LATTE • MOCHA",
   Vector3.new(-40,9,2270),Color3.fromRGB(224,177,120)},
  {"MOTOR ROW","CARS • GARAGE",Vector3.new(72,6.4,2241),
   Color3.fromRGB(117,191,231)},
  {"DOWNTOWN NURSERY","GROW • HARVEST",Vector3.new(76,5.5,2180),
   Color3.fromRGB(125,196,121)},
 }
 for _,entry in ipairs(places) do
  local name,subtitle,pos,color=entry[1],entry[2],entry[3],entry[4]
  local sign=part(folder,"Recognizable Venue "..name,
   Vector3.new(13,3.2,.6),CFrame.new(pos),
   Color3.fromRGB(30,51,49),Enum.Material.Metal,false)
  billboard(sign,name,subtitle,color)
  -- Narrow warm wash lights create shopfront character without shadow cost.
  for _,side in ipairs({-1,1}) do
   local lamp=part(folder,"Storefront Brass Wall Sconce",
    Vector3.new(.45,.75,.35),
    sign.CFrame*CFrame.new(side*6.5,0,-.55),
    Color3.fromRGB(181,148,103),Enum.Material.Metal,false)
   detail(lamp)
   local point=Instance.new("PointLight")
   point.Shadows=false;point.Brightness=.35;point.Range=11
   point.Color=Color3.fromRGB(255,215,149)
   point.Parent=lamp
  end
 end
end
function Streets.Build(world,imported,tell)
 if not imported then return nil end
 table.clear(transitStations)
 local old=world:FindFirstChild("Detailed Downtown Streetscape")
 if old then old:Destroy() end
 local folder=Instance.new("Folder")
 folder.Name="Detailed Downtown Streetscape"
 folder.Parent=world
 local assets={
  {"StreetLights",{
    {x=-88,z=2215},{x=-88,z=2249},
    {x=-52,z=2251},{x=63,z=2200},
    {x=84,z=2235},{x=94,z=2254},
  }},
  {"Street_SetDressing",{
    {name="RhododendronVar02",x=-68,z=2205},
    {name="RhododendronVar02",x=-63,z=2240},
    {name="RhododendronVar02",x=65,z=2234},
    {name="RhododendronVar02",x=79,z=2225},
    {name="RhododendronVar02",x=84,z=2189},
    {name="RhododendronVar02",x=-92,z=2228},
    {name="trashCan_a",x=-24,z=2219},
    {name="trashCan_a",x=72,z=2247},
    {name="mailBox",x=-81,z=2208},
    {name="newPaperStand",x=60,z=2234},
    {name="PlanterHanging_Var2",x=-33,z=2262},
    {name="PlanterHanging_Var2",x=41,z=2248},
  }},
 }
 local meshProps=0
 for _,entry in ipairs(assets) do
  local group=imported:FindFirstChild(entry[1],true)
  local children=group and group:GetChildren() or {}
  for i,pos in ipairs(entry[2]) do
   local template
   if pos.name then
    for _,child in ipairs(children) do
     if child.Name==pos.name then template=child;break end
    end
   else
    template=children[(i-1)%math.max(1,#children)+1]
   end
   if template and cloneOfficial(folder,template,
    Vector3.new(pos.x,.55,pos.z),
    "Official Downtown Street Prop "..i.." "..(pos.name or entry[1])) then
    meshProps+=1
   end
  end
 end
 trafficDetails(folder)
 simpleVenues(folder)
 busShelter(folder,tell)
 folder:SetAttribute("OfficialDecorativeMeshModels",meshProps)
 folder:SetAttribute("ZeroExtraHeartbeatLoops",true)
 folder:SetAttribute("TransitAccessible",true)
 folder:SetAttribute("OptimizedLowModeTag",DETAIL_TAG)
 return folder
end
return Streets
