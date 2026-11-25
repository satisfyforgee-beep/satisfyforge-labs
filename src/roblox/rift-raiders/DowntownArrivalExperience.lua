-- Rift Raiders v0.19: cinematic first-player impression near authentic city meshes.
-- Original visual assembly uses permitted built-in Studio Modern City trees.
-- No external scripts, paid assets or Robux products.
local Arrivals={}
local function part(parent,name,size,cf,color,material,collidable)
 local p=Instance.new("Part");p.Name=name;p.Size=size;p.CFrame=cf
 p.Anchored=true;p.CanCollide=collidable==true;p.CanTouch=false
 p.Color=color;p.Material=material or Enum.Material.Concrete
 p.TopSurface=Enum.SurfaceType.Smooth;p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=parent;return p
end
local function ball(parent,name,size,cf,color)
 local p=part(parent,name,size,cf,color,Enum.Material.Grass,false)
 p.Shape=Enum.PartType.Ball;return p
end
local function label(parent,node,title,description)
 local ui=Instance.new("SurfaceGui")
 ui.Name="Welcome Plaza Graphic"
 ui.Face=Enum.NormalId.Front;ui.CanvasSize=Vector2.new(1100,700)
 ui.LightInfluence=.25;ui.Parent=node
 local titleText=Instance.new("TextLabel")
 titleText.BackgroundTransparency=1;titleText.Size=UDim2.new(.92,0,.53,0)
 titleText.Position=UDim2.new(.04,0,.07,0);titleText.Text=title
 titleText.Font=Enum.Font.GothamBold;titleText.TextScaled=true
 titleText.TextWrapped=true;titleText.TextColor3=Color3.fromRGB(245,232,199)
 titleText.Parent=ui
 local detail=Instance.new("TextLabel")
 detail.BackgroundTransparency=1;detail.Size=UDim2.new(.94,0,.32,0)
 detail.Position=UDim2.new(.03,0,.6,0);detail.Text=description
 detail.Font=Enum.Font.Gotham;detail.TextScaled=true
 detail.TextWrapped=true;detail.TextColor3=Color3.fromRGB(139,222,191)
 detail.Parent=ui
end
local function prompt(node,action,target,fn)
 local p=Instance.new("ProximityPrompt")
 p.Name="Arrival "..action;p.ActionText=action
 p.ObjectText=target;p.MaxActivationDistance=15
 p.RequiresLineOfSight=false;p.HoldDuration=.25;p.Parent=node
 p.Triggered:Connect(fn)
end
local function plantTree(parent,template,position,name)
 if not template or not template:IsA("Model") then return false end
 local cloned=template:Clone()
 cloned.Name=name;cloned.Parent=parent
 local c,dimensions=cloned:GetBoundingBox()
 local bottom=c.Position.Y-dimensions.Y*.5
 local delta=Vector3.new(position.X-c.Position.X,position.Y-bottom,
  position.Z-c.Position.Z)
 cloned:PivotTo(cloned:GetPivot()+delta)
 for _,p in ipairs(cloned:GetDescendants()) do
  if p:IsA("BasePart") then
   p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
  end
 end
 return true
end
local function planter(parent,position,color)
 part(parent,"City Brick Flowerbed",Vector3.new(8,1.4,5),
  CFrame.new(position+Vector3.new(0,.8,0)),
  Color3.fromRGB(161,115,99),Enum.Material.Brick,false)
 part(parent,"Raised Organic Flowerbed",Vector3.new(7.1,.2,4.2),
  CFrame.new(position+Vector3.new(0,1.53,0)),
  Color3.fromRGB(88,75,59),Enum.Material.Ground,false)
 for i=1,6 do
  local x=(i%3-1)*2.0
  local z=math.floor((i-1)/3)*1.55-.7
  ball(parent,"Flowering Arrival Shrub",Vector3.new(1.25,.85,1.2),
   CFrame.new(position+Vector3.new(x,2.05,z)),
   Color3.fromRGB(72+8*(i%2),137+5*(i%3),78))
  ball(parent,"Garden Bloom",Vector3.new(.55,.4,.55),
   CFrame.new(position+Vector3.new(x,2.5,z)),
   color)
 end
end
function Arrivals.Build(world,imported,tell,onTravel)
 local folder=Instance.new("Folder")
 folder.Name="Downtown First Minute Plaza";folder.Parent=world
 local treeFolder=imported and imported:FindFirstChild("StreetTrees",true)
 local templates=treeFolder and treeFolder:GetChildren() or {}
 local count=0
 -- Frame the road on the first camera view (toward original storefronts).
 for i,position in ipairs({
  Vector3.new(-30,.5,2191),Vector3.new(-39,.5,2229),
  Vector3.new(36,.5,2192),Vector3.new(48,.5,2244),
  Vector3.new(56,.5,2209),
 }) do
  local tree=templates[((i-1)%math.max(1,#templates))+1]
  if tree and plantTree(folder,tree,position,"Imported City Arrival Tree "..i) then
   count+=1
  end
 end
 folder:SetAttribute("ImportedMeshTrees",count)
 -- A low-contrast pedestrian plaza, replacing a blank slab of asphalt in
 -- the start view while preserving road and vehicle collision behavior.
 for xi=0,7 do
  for zi=0,4 do
   local x=17+xi*5.6
   local z=2202+zi*6.2
   part(folder,"Sandstone Plaza Paver",
    Vector3.new(5.35,.16,5.95),
    CFrame.new(x,.34,z),xi%2==zi%2 and
    Color3.fromRGB(148,149,142) or Color3.fromRGB(174,173,162),
    Enum.Material.Concrete,false)
  end
 end
 for _,position in ipairs({
  Vector3.new(21,.3,2183),Vector3.new(50,.3,2177),
  Vector3.new(27,.3,2252),Vector3.new(-29,.3,2247),
 }) do
  planter(folder,position,Color3.fromRGB(203,122,133))
 end
 -- Visible but modest shade/bench seating; none block critical sidewalks.
 for i,z in ipairs({2196,2236}) do
  part(folder,"Plaza Cedar Seat",Vector3.new(9,.8,2.3),
   CFrame.new(32,2.5,z),
   Color3.fromRGB(152,119,86),Enum.Material.WoodPlanks,false)
  part(folder,"Plaza Chair Back",Vector3.new(9,2,.55),
   CFrame.new(32,3.35,z+1),
   Color3.fromRGB(123,102,82),Enum.Material.WoodPlanks,false)
  for _,x in ipairs({28.7,35.3}) do
   part(folder,"Modern Bench Support",Vector3.new(.35,1.7,1.8),
    CFrame.new(x,1.4,z),
    Color3.fromRGB(53,71,72),Enum.Material.Metal,false)
  end
 end
 local fountain=part(folder,"Downtown Welcome Fountain",
  Vector3.new(10,1,10),CFrame.new(55,1,2231),
  Color3.fromRGB(193,187,173),Enum.Material.Concrete,false)
 fountain.Shape=Enum.PartType.Cylinder
 local water=part(folder,"Reflective Fountain Water",
  Vector3.new(8.8,.15,8.8),CFrame.new(55,1.65,2231),
  Color3.fromRGB(99,189,200),Enum.Material.Glass,false)
 water.Shape=Enum.PartType.Cylinder;water.Transparency=.32
 local center=part(folder,"Fountain Center Piece",
  Vector3.new(1,3,1),CFrame.new(55,3.3,2231),
  Color3.fromRGB(191,205,195),Enum.Material.Marble,false)
 center.Shape=Enum.PartType.Cylinder
 local mist=Instance.new("ParticleEmitter")
 mist.Name="Gentle Fountain Spray"
 mist.Texture="rbxasset://textures/particles/sparkles_main.dds"
 mist.Rate=5;mist.Speed=NumberRange.new(1,3)
 mist.Lifetime=NumberRange.new(.4,1)
 mist.SpreadAngle=Vector2.new(35,35)
 mist.Parent=center
 local gate=part(folder,"Welcome to RiftLife City",
  Vector3.new(.8,8,16),
  CFrame.new(-17,7.2,2193)*CFrame.Angles(0,math.rad(90),0),
  Color3.fromRGB(38,69,72),Enum.Material.Metal,false)
 label(folder,gate,"WELCOME TO RIFTLIFE",
  "CITY STORIES • ADVENTURES • FRIENDS")
 local worldBoard=part(folder,"First Minute Explore Kiosk",
  Vector3.new(12,6,.65),
  CFrame.new(39,5,2217),
  Color3.fromRGB(51,76,70),Enum.Material.Metal,false)
 label(folder,worldBoard,"START YOUR STORY",
  "CITY • WORK • SHOPS • GARDEN • TRAVEL")
 prompt(worldBoard,"EXPLORE SUBURBIA","RiftLife Visitor Center",
  function(player)
   if player.Character then
    player.Character:PivotTo(CFrame.new(0,7,3425))
    if tell then tell(player,"WELCOME TO SUBURBIA • EXPLORE MARKET, PARK & CAREERS!") end
    if onTravel then onTravel(player,"SUBURBIA") end
   end
  end)
 -- Welcome neon lines stand out at night with small light pools.
 for _,pos in ipairs({
  Vector3.new(15,4,2200),Vector3.new(60,4,2235),
 }) do
  local lightBase=part(folder,"Welcome Street Light",
   Vector3.new(.45,8,.45),CFrame.new(pos),
   Color3.fromRGB(55,69,73),Enum.Material.Metal,false)
  local lamp=part(folder,"Warm Street Lantern",
   Vector3.new(1.3,.35,2.1),
   CFrame.new(pos+Vector3.new(0,4.3,0)),
   Color3.fromRGB(244,219,169),Enum.Material.Neon,false)
  local point=Instance.new("PointLight")
  point.Color=Color3.fromRGB(246,227,183)
  point.Brightness=.6;point.Range=17;point.Shadows=false
  point.Parent=lamp
 end
 folder:SetAttribute("ArrivalInteractionCount",1)
 folder:SetAttribute("OriginalSourceArt","Official Modern City street trees")
 folder:SetAttribute("WelcomeVisible",true)
 return folder
end
return Arrivals
