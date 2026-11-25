-- v0.7 original procedural architectural detailing for Life City.
-- No Toolbox scripts, third-party meshes, external IDs or unlicensed assets.
-- A polished blockout with masonry, shopfronts, fixtures, landscaping, street furniture.
local Lighting=game:GetService("Lighting")
local Detail={}
local center=Vector3.new(0,0,1600)
local function part(parent,name,size,cf,color,material,collide)
 local p=Instance.new("Part")
 p.Name=name; p.Size=size; p.CFrame=cf; p.Anchored=true
 p.Material=material or Enum.Material.SmoothPlastic
 p.Color=color or Color3.fromRGB(180,180,180)
 p.TopSurface=Enum.SurfaceType.Smooth; p.BottomSurface=Enum.SurfaceType.Smooth
 p.CanCollide=collide==true; p.CanTouch=false
 p.Parent=parent; return p
end
local function beam(parent,name,size,pos,color,material)
 return part(parent,name,size,CFrame.new(pos),color,material,false)
end
local function cylinder(parent,name,size,cf,color,material)
 local p=part(parent,name,size,cf,color,material,false)
 p.Shape=Enum.PartType.Cylinder
 return p
end
local function sphere(parent,name,size,cf,color,material)
 local p=part(parent,name,size,cf,color,material,false)
 p.Shape=Enum.PartType.Ball
 return p
end
local function sign(parent,name,size,pos,color,letters)
 local base=beam(parent,name,size,pos,color,Enum.Material.Metal)
 local face=Instance.new("SurfaceGui"); face.Name="Painted Shop Sign"
 face.Face=Enum.NormalId.Front; face.CanvasSize=Vector2.new(680,140)
 face.LightInfluence=.25; face.Parent=base
 local label=Instance.new("TextLabel")
 label.Size=UDim2.fromScale(1,1)
 label.BackgroundTransparency=1
 label.Text=letters; label.TextScaled=true
 label.Font=Enum.Font.GothamBlack
 label.TextColor3=Color3.fromRGB(246,242,228)
 label.Parent=face
 return base
end
local function light(parent,name,pos,color,range)
 local body=beam(parent,name,Vector3.new(1.1,.4,1.1),
  pos,Color3.fromRGB(242,229,195),Enum.Material.Neon)
 local l=Instance.new("PointLight"); l.Range=range or 15; l.Brightness=.65
 l.Color=color or Color3.fromRGB(255,232,192); l.Shadows=false; l.Parent=body
end
local function tree(parent,pos,index)
 local m=Instance.new("Model"); m.Name="Street Tree "..index; m.Parent=parent
 local trunk=cylinder(m,"Bark",Vector3.new(2,12,2),
  CFrame.new(pos+Vector3.new(0,6.3,0)),Color3.fromRGB(105,83,66),Enum.Material.Wood)
 trunk.CanCollide=true
 for i=1,5 do
  local theta=(i-1)*math.pi*2/5
  local delta=Vector3.new(math.cos(theta)*3,0,math.sin(theta)*3)
  sphere(m,"Leaf Canopy",Vector3.new(9,8,9),
   CFrame.new(pos+Vector3.new(0,15,0)+delta),
   i%2==0 and Color3.fromRGB(61,123,73) or Color3.fromRGB(76,143,86),
   Enum.Material.Grass)
 end
 beam(m,"Mulch Bed",Vector3.new(9,.35,9),
  pos+Vector3.new(0,.2,0),Color3.fromRGB(101,81,63),Enum.Material.Ground)
end
local function bench(parent,pos)
 for _,x in ipairs({-3,3}) do
  beam(parent,"Bench Leg",Vector3.new(.5,2.3,.6),
   pos+Vector3.new(x,1.4,0),Color3.fromRGB(65,72,76),Enum.Material.Metal)
 end
 for _,z in ipairs({-.8,0,.8}) do
  beam(parent,"Wood Bench Seat",Vector3.new(7,.3,.7),
   pos+Vector3.new(0,2.6,z),Color3.fromRGB(125,91,62),Enum.Material.WoodPlanks)
 end
 beam(parent,"Bench Back",Vector3.new(7,2,.35),
  pos+Vector3.new(0,3.6,1.1),Color3.fromRGB(129,97,69),Enum.Material.WoodPlanks)
end
local function planter(parent,pos)
 cylinder(parent,"Stone Planter",Vector3.new(6,1.8,6),
  CFrame.new(pos+Vector3.new(0,1,0)),Color3.fromRGB(150,153,151),Enum.Material.Concrete)
 cylinder(parent,"Planter Soil",Vector3.new(5.5,.2,5.5),
  CFrame.new(pos+Vector3.new(0,2,0)),Color3.fromRGB(87,70,53),Enum.Material.Ground)
 for i=1,5 do
  local angle=i*math.pi*2/5
  local p=pos+Vector3.new(math.cos(angle)*1.7,2.8,math.sin(angle)*1.7)
  sphere(parent,"Garden Shrub",Vector3.new(2.2,2.5,2.2),
   CFrame.new(p),Color3.fromRGB(60+i*4,112+i*3,70),Enum.Material.Grass)
 end
end
local function lampPost(parent,pos)
 local m=Instance.new("Model"); m.Name="City Streetlamp"; m.Parent=parent
 cylinder(m,"Streetlight Pole",Vector3.new(.55,20,.55),
  CFrame.new(pos+Vector3.new(0,10,0)),Color3.fromRGB(65,74,83),Enum.Material.Metal)
 beam(m,"Streetlight Arm",Vector3.new(5,.45,.45),
  pos+Vector3.new(2.4,19.7,0),Color3.fromRGB(65,74,83),Enum.Material.Metal)
 local bulb=beam(m,"Warm Streetlight",Vector3.new(2,.35,1.2),
  pos+Vector3.new(4.7,19.3,0),Color3.fromRGB(252,232,173),Enum.Material.Neon)
 local spot=Instance.new("SpotLight"); spot.Face=Enum.NormalId.Bottom
 spot.Range=28; spot.Angle=95; spot.Brightness=1.2
 spot.Color=Color3.fromRGB(255,230,184); spot.Parent=bulb
end
local function product(parent,category,index,pos)
 local color=({
  TECH=Color3.fromRGB(68,92,115),
  APPAREL=Color3.fromRGB(164,104,127),
  HOME=Color3.fromRGB(161,137,96),
  VEHICLE=Color3.fromRGB(76,119,153),
  PROPERTY=Color3.fromRGB(175,162,139),
  BUSINESS=Color3.fromRGB(106,147,118)
 })[category] or Color3.fromRGB(135,140,146)
 if category=="APPAREL" then
  local mannequin=cylinder(parent,"Clothing Stand",Vector3.new(.7,3,.7),
   CFrame.new(pos+Vector3.new(0,1.6,0)),Color3.fromRGB(103,101,98),Enum.Material.Metal)
  mannequin.CanCollide=false
  local torso=beam(parent,"Displayed Jacket",Vector3.new(2.6,2.2,1),
   pos+Vector3.new(0,3.3,0),color,Enum.Material.Fabric)
  for _,x in ipairs({-1.8,1.8}) do
   beam(parent,"Jacket Sleeve",Vector3.new(.85,2.2,.9),
    pos+Vector3.new(x,3.2,0),color,Enum.Material.Fabric)
  end
 elseif category=="TECH" then
  local screen=beam(parent,"Product Display Screen",Vector3.new(2.9,2.1,.24),
   pos+Vector3.new(0,3,0),Color3.fromRGB(22,35,47),Enum.Material.Metal)
  local display=beam(parent,"Screen Glass",Vector3.new(2.5,1.7,.1),
   screen.Position+Vector3.new(0,0,-.2),Color3.fromRGB(63,137,164),Enum.Material.Glass)
  display.Transparency=.25
  beam(parent,"Device Base",Vector3.new(3.3,.35,2.1),
   pos+Vector3.new(0,1.8,0),color,Enum.Material.Metal)
 elseif category=="VEHICLE" then
  beam(parent,"Model Car Body",Vector3.new(4,1.3,2.1),
   pos+Vector3.new(0,2.6,0),color,Enum.Material.Metal)
  for _,x in ipairs({-1.4,1.4}) do
   for _,z in ipairs({-1.2,1.2}) do
    cylinder(parent,"Showroom Tire",Vector3.new(.5,1.3,1.3),
     CFrame.new(pos+Vector3.new(x,2,z))*CFrame.Angles(0,0,math.pi/2),
     Color3.fromRGB(37,41,45),Enum.Material.Rubber)
   end
  end
 elseif category=="PROPERTY" then
  beam(parent,"Architectural Model House",Vector3.new(3,2,2.8),
   pos+Vector3.new(0,2.7,0),color,Enum.Material.Brick)
  local roof=Instance.new("WedgePart"); roof.Name="Architectural Roof Model"
  roof.Size=Vector3.new(3.4,1.3,3.3)
  roof.CFrame=CFrame.new(pos+Vector3.new(0,4.2,0))
  roof.Anchored=true; roof.CanCollide=false
  roof.Material=Enum.Material.Slate; roof.Color=Color3.fromRGB(79,83,92)
  roof.Parent=parent
 else
  beam(parent,"Product Package",Vector3.new(2.5,2.2,2),
   pos+Vector3.new(0,2.7,0),color,Enum.Material.Wood)
  beam(parent,"Product Label",Vector3.new(1.9,.9,.08),
   pos+Vector3.new(0,2.9,-1.05),
   Color3.fromRGB(238,222,187),Enum.Material.SmoothPlastic)
 end
end
local function decorateStore(folder,building,category,pos)
 local trim=Color3.fromRGB(218,214,203)
 local metal=Color3.fromRGB(54,65,77)
 -- Floor-level storefront facade: cornice, corner piers, glazing frames.
 for _,x in ipairs({-16.7,16.7}) do
  beam(folder,"Facade Corner Pilaster",Vector3.new(1.3,15,1.5),
   pos+Vector3.new(x,10,-15.8),trim,Enum.Material.Limestone)
  beam(folder,"Facade Base Stone",Vector3.new(2.4,1.5,2),
   pos+Vector3.new(x,3,-15.8),Color3.fromRGB(155,157,157),Enum.Material.Concrete)
 end
 beam(folder,"Architectural Roof Cornice",Vector3.new(40,1.4,35),
  pos+Vector3.new(0,18.3,0),trim,Enum.Material.Limestone)
 beam(folder,"Second Cornice Shadow",Vector3.new(39,.4,34),
  pos+Vector3.new(0,19.2,0),metal,Enum.Material.Metal)
 sign(folder,"Facade Business Sign",Vector3.new(26,3.8,.6),
  pos+Vector3.new(0,15.6,-16.6),metal,building.Name:upper())
 for _,x in ipairs({-12,12}) do
  beam(folder,"Window Mullion",Vector3.new(.35,8,.6),
   pos+Vector3.new(x,8,-16.1),metal,Enum.Material.Metal)
  beam(folder,"Window Transom",Vector3.new(7,.3,.5),
   pos+Vector3.new(x,10,-16.1),metal,Enum.Material.Metal)
  beam(folder,"Window Sill",Vector3.new(8,.5,1.1),
   pos+Vector3.new(x,4,-16),trim,Enum.Material.Concrete)
 end
 -- Open glazed entrance with doors offset to keep center walkable.
 for _,x in ipairs({-2.8,2.8}) do
  local door=beam(folder,"Open Glass Door",Vector3.new(3.4,8,.25),
   pos+Vector3.new(x,7.3,-13.2),
   Color3.fromRGB(137,192,205),Enum.Material.Glass)
  door.Transparency=.5
  door.CFrame=door.CFrame*CFrame.Angles(0,x<0 and -.7 or .7,0)
  cylinder(folder,"Door Pull",Vector3.new(.2,1.4,.2),
   CFrame.new(pos+Vector3.new(x,7.4,-13.8)),
   Color3.fromRGB(207,198,174),Enum.Material.Metal)
 end
 local awningColor=({
  TECH=Color3.fromRGB(67,108,133),
  APPAREL=Color3.fromRGB(147,86,111),
  HOME=Color3.fromRGB(124,122,87),
  VEHICLE=Color3.fromRGB(59,104,116),
  PROPERTY=Color3.fromRGB(120,119,99),
  BUSINESS=Color3.fromRGB(94,119,100)
 })[category]
 beam(folder,"Striped Store Awning",Vector3.new(30,.45,6),
  pos+Vector3.new(0,12.5,-18),awningColor,Enum.Material.Fabric)
 for i=-6,6 do
  if i%2==0 then
   beam(folder,"Awning Stripe",Vector3.new(2,.08,6),
    pos+Vector3.new(i*2.2,12.76,-18),
    Color3.fromRGB(227,220,199),Enum.Material.Fabric)
  end
 end
 -- Shelves and actual recognizable category-specific display props.
 for _,x in ipairs({-10,0,10}) do
  for _,z in ipairs({-2,10}) do
   local shelf=beam(folder,"Display Shelf",Vector3.new(7,.45,4),
    pos+Vector3.new(x,4.2,z),Color3.fromRGB(121,98,78),Enum.Material.WoodPlanks)
   shelf.CanCollide=true
   product(folder,category,math.floor(x+z),pos+Vector3.new(x,2.6,z))
  end
 end
 for _,x in ipairs({-12,12}) do
  light(folder,"Recessed Ceiling Light",pos+Vector3.new(x,16.2,4),
   Color3.fromRGB(255,232,201),16)
 end
 beam(folder,"Concrete Sidewalk",Vector3.new(39,.55,14),
  pos+Vector3.new(0,2.2,-24),Color3.fromRGB(173,175,169),Enum.Material.Concrete).CanCollide=true
end
local function decorateJobTask(folder,target)
 local job=target:GetAttribute("Job")
 local step=target:GetAttribute("Step")
 local pos=target.Position
 local m=Instance.new("Model")
 m.Name="Workplace Props "..job.." "..step
 m.Parent=folder
 local function box(name,size,offset,color,material)
  return beam(m,name,size,pos+offset,color,material)
 end
 local function tube(name,size,offset,color)
  return cylinder(m,name,size,CFrame.new(pos+offset),color,Enum.Material.Metal)
 end
 if job=="FIREFIGHTER" then
  if step==2 then
   local flame=box("Training Fire",Vector3.new(3,3,2),
    Vector3.new(0,3,0),Color3.fromRGB(232,99,43),Enum.Material.Neon)
   local fire=Instance.new("Fire"); fire.Heat=4; fire.Size=5; fire.Parent=flame
  else
   tube("Fire Hose Reel",Vector3.new(1.3,4,4),
    Vector3.new(0,2.6,0),Color3.fromRGB(181,55,48))
  end
 elseif job=="PARAMEDIC" or job=="VETERINARIAN" then
  box("Medical Examination Bed",Vector3.new(7,1,3.5),
   Vector3.new(0,3.1,0),Color3.fromRGB(229,235,228),Enum.Material.Fabric)
  box("Medical Cabinet",Vector3.new(2,3,1),
   Vector3.new(-3,3,0),Color3.fromRGB(152,179,177),Enum.Material.Metal)
 elseif job=="BARISTA" or job=="CHEF" then
  box("Kitchen Worktop",Vector3.new(7,.5,3),
   Vector3.new(0,3.1,0),Color3.fromRGB(189,193,188),Enum.Material.Marble)
  for x=-2,2,2 do
   tube("Kitchen Cup or Pot",Vector3.new(1.2,1.2,1.2),
    Vector3.new(x,4,0),Color3.fromRGB(221,225,217))
  end
 elseif job=="MECHANIC" then
  box("Vehicle Engine Block",Vector3.new(5,2,3),
   Vector3.new(0,3.2,0),Color3.fromRGB(76,88,98),Enum.Material.Metal)
  for x=-1,1 do
   tube("Engine Piston",Vector3.new(1,1.6,1.6),
    Vector3.new(x*1.3,4.6,0),Color3.fromRGB(144,153,157))
  end
 elseif job=="POLICE" then
  box("Police Dispatch Terminal",Vector3.new(3.2,2.3,.3),
   Vector3.new(0,4.3,0),Color3.fromRGB(44,77,111),Enum.Material.Glass)
 elseif job=="CONSTRUCTION" then
  for x=-2,2,2 do
   box("Stacked Bricks",Vector3.new(2,1.3,3),
    Vector3.new(x,3.3,0),Color3.fromRGB(164,112,85),Enum.Material.Brick)
  end
 elseif job=="FARMER" then
  for x=-2,2,2 do
   sphere(m,"Produce Harvest",Vector3.new(1.7,1.7,1.7),
    CFrame.new(pos+Vector3.new(x,3.2,0)),
    Color3.fromRGB(122,174,65),Enum.Material.Grass)
  end
 elseif job=="SANITATION" then
  for x=-2,2,2 do
   tube("Recycling Bin",Vector3.new(2.1,3,2.1),
    Vector3.new(x,3.1,0),Color3.fromRGB(74,146,110))
  end
 elseif job=="ELECTRICIAN" then
  box("Electrical Breaker Panel",Vector3.new(4,4,.8),
   Vector3.new(0,4.1,0),Color3.fromRGB(143,151,151),Enum.Material.Metal)
  for x=-1,1 do
   box("Circuit Breaker",Vector3.new(.6,.6,.2),
    Vector3.new(x,4.3,-.5),Color3.fromRGB(55,62,66),Enum.Material.Metal)
  end
 elseif job=="PLUMBER" then
  for x=-2,2,2 do
   tube("Pipe Fitting",Vector3.new(1.4,3,1.4),
    Vector3.new(x,3.5,0),Color3.fromRGB(169,172,173))
  end
 elseif job=="PHOTOGRAPHER" or job=="CREATOR" then
  box("Camera on Tripod",Vector3.new(2,1.4,1.2),
   Vector3.new(0,5,0),Color3.fromRGB(39,45,56),Enum.Material.Metal)
  for x=-2,2,2 do
   tube("Studio Tripod",Vector3.new(.25,4,.25),
    Vector3.new(x,3,0),Color3.fromRGB(80,86,90))
  end
 elseif job=="PILOT" then
  box("Flight Simulator Console",Vector3.new(6,2.5,2),
   Vector3.new(0,3.8,0),Color3.fromRGB(46,66,88),Enum.Material.Metal)
  box("Cockpit Display",Vector3.new(4,1.6,.15),
   Vector3.new(0,4.3,-1.1),Color3.fromRGB(56,145,184),Enum.Material.Glass)
 elseif job=="MUSICIAN" then
  box("Performance Speaker",Vector3.new(3,4,2),
   Vector3.new(0,4,0),Color3.fromRGB(49,51,60),Enum.Material.Metal)
  for y=-1,1,2 do
   cylinder(m,"Speaker Cone",Vector3.new(.3,1.2,1.2),
    CFrame.new(pos+Vector3.new(0,4+y,-1.1))*CFrame.Angles(0,0,math.pi/2),
    Color3.fromRGB(101,105,112),Enum.Material.Rubber)
  end
 elseif job=="TEACHER" then
  box("Classroom Whiteboard",Vector3.new(6,3,.2),
   Vector3.new(0,5,0),Color3.fromRGB(234,234,224),Enum.Material.SmoothPlastic)
 elseif job=="REAL_ESTATE_AGENT" then
  box("Home Staging Display",Vector3.new(5,2.5,3),
   Vector3.new(0,4,0),Color3.fromRGB(193,168,132),Enum.Material.Wood)
 else
  box("Workplace Parcel",Vector3.new(3,2,3),
   Vector3.new(0,3,0),Color3.fromRGB(164,130,96),Enum.Material.Wood)
 end
end
function Detail.Build(world)
 local folder=Instance.new("Folder"); folder.Name="Life City Architectural Details"
 folder.Parent=world
 local stores={
  {"TECH","Creator Technology Store",-112,-65},
  {"APPAREL","Clothing Boutique",-62,-65},
  {"HOME","Home Supply Store",-12,-65},
  {"VEHICLE","Vehicle and Marine Dealer",38,-65},
  {"PROPERTY","Real Estate Agency",88,-65},
  {"BUSINESS","Business Licensing Office",138,-65},
 }
 for _,row in ipairs(stores) do
  local category,name,x,z=unpack(row)
  local building=world:FindFirstChild(name,true)
  if building then
   decorateStore(folder,building,category,center+Vector3.new(x,0,z))
  end
 end
 -- City block landscaping and street furniture with actual collision where needed.
 for i,x in ipairs({-148,-100,-52,-4,44,92,148}) do
  -- This offset is relative to center.Z=1600, not an absolute world Z.
 -- Earlier 1538 accidentally placed this tree row at Z=3138.
 local z=-62
  tree(folder,center+Vector3.new(x,3,z),i)
 end
 for _,x in ipairs({-135,-35,65,145}) do
  lampPost(folder,center+Vector3.new(x,3,17))
 end
 for _,x in ipairs({-135,-15,100}) do
  bench(folder,center+Vector3.new(x,3,-22))
 end
 for _,x in ipairs({-145,15,145}) do
  planter(folder,center+Vector3.new(x,3,36))
 end
 -- Pavement crossings, stop lines, sidewalk curb cuts and parking stalls.
 for _,x in ipairs({-90,90}) do
  for z=-10,10,4 do
   beam(folder,"Zebra Crossing Paint",Vector3.new(3,.09,2.5),
    center+Vector3.new(x,3.05,z),Color3.fromRGB(238,234,219))
  end
 end
 for i=-6,6 do
  local x=i*22
  beam(folder,"Parking Space Line",Vector3.new(.25,.1,16),
   center+Vector3.new(x,3.1,40),Color3.fromRGB(237,232,205))
 end
 for _,z in ipairs({-12,12}) do
  beam(folder,"Raised Sidewalk Curb",Vector3.new(328,.7,1),
   center+Vector3.new(0,3,z),Color3.fromRGB(184,185,181),Enum.Material.Concrete)
 end
 -- Career workstations show props for their particular profession, not bare buttons.
 for _,node in ipairs(world:GetDescendants()) do
  if node:IsA("BasePart") and node:GetAttribute("Job") and
   node:GetAttribute("Step") then
   decorateJobTask(folder,node)
  end
 end
 -- Public garden and pedestrian plaza for the job and home district.
 for _,x in ipairs({-150,-75,0,75,150}) do
  for _,z in ipairs({90,205}) do
   tree(folder,center+Vector3.new(x,3,z),math.floor(x+z))
  end
 end
 -- Curved architectural shapes using cylinders, spheres and wedge roofs.
 local plaza=beam(folder,"Employment Plaza",Vector3.new(90,.4,42),
  center+Vector3.new(-95,2.9,67),
  Color3.fromRGB(174,170,157),Enum.Material.Cobblestone)
 plaza.CanCollide=true
 local fountain=cylinder(folder,"Public Fountain Basin",Vector3.new(13,1.4,13),
  CFrame.new(center+Vector3.new(-30,3.8,105)),
  Color3.fromRGB(153,166,172),Enum.Material.Concrete)
 fountain.CanCollide=true
 cylinder(folder,"Fountain Pool",Vector3.new(11,.3,11),
  CFrame.new(center+Vector3.new(-30,4.65,105)),
  Color3.fromRGB(85,172,204),Enum.Material.Glass)
 local plume=part(folder,"Fountain Water Jet",Vector3.new(.9,7,.9),
  CFrame.new(center+Vector3.new(-30,8,105)),
  Color3.fromRGB(144,220,243),Enum.Material.Glass,false)
 plume.Transparency=.45
 local particles=Instance.new("ParticleEmitter")
 particles.Texture="rbxasset://textures/particles/sparkles_main.dds"
 particles.Rate=7; particles.Lifetime=NumberRange.new(.7,1.2)
 particles.Speed=NumberRange.new(2,5); particles.SpreadAngle=Vector2.new(15,15)
 particles.Parent=plume
 return folder
end
return Detail
