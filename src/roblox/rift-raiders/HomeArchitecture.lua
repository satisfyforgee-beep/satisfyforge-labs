-- v0.14: walkable upper floors, vertical access, distinct house exteriors.
-- All geometry is authored locally from original Roblox materials and parts.
local House={}
local function part(parent,name,size,cf,material,color,collide)
 local p=Instance.new("Part")
 p.Name=name;p.Anchored=true;p.CanCollide=collide~=false
 p.CanTouch=false;p.Size=size;p.CFrame=cf
 p.Material=material or Enum.Material.WoodPlanks
 p.Color=color or Color3.fromRGB(173,144,106)
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth;p.Parent=parent
 return p
end
local wood=Color3.fromRGB(160,120,83)
local timber=Color3.fromRGB(112,80,55)
local plaster=Color3.fromRGB(227,220,205)
local function prompt(partObj,name,action,fn)
 local p=Instance.new("ProximityPrompt")
 p.Name=name;p.ObjectText=name;p.ActionText=action
 p.MaxActivationDistance=10;p.HoldDuration=.3
 p.RequiresLineOfSight=false;p.Parent=partObj
 p.Triggered:Connect(fn);return p
end
local function buildFloor(m,center,width,floorIndex)
 local y=3+(floorIndex-1)*10
 local length=25
 -- Core x=-3.5..3.5, z=-8..9 is clear for stairs.
 -- Side floors carry upper bedrooms, with landing at the back.
 local sideWidth=(width-8)/2
 for _,side in ipairs({-1,1}) do
  local x=side*(sideWidth/2+3.5)
  part(m,"Walkable Upper Level Floor "..floorIndex,
   Vector3.new(sideWidth,.7,length),
   CFrame.new(center+Vector3.new(x,y,0)),
   Enum.Material.WoodPlanks,wood)
 end
 part(m,"Upper Landing Front "..floorIndex,
  Vector3.new(7.2,.7,4.2),
  CFrame.new(center+Vector3.new(0,y,-10.35)),
  Enum.Material.WoodPlanks,wood)
 part(m,"Upper Landing Rear "..floorIndex,
  Vector3.new(7.2,.7,4.2),
  CFrame.new(center+Vector3.new(0,y,10.35)),
  Enum.Material.WoodPlanks,wood)
 -- Balcony guardrail around the central opening. Deliberately leave stair
 -- opening at back for a walkable connection.
 for _,side in ipairs({-1,1}) do
  local railing=part(m,"Upper Stairwell Railing "..floorIndex,
   Vector3.new(.23,3,16),
   CFrame.new(center+Vector3.new(side*3.55,y+1.65,-1)),
   Enum.Material.Metal,Color3.fromRGB(82,85,83),false)
  for k=1,7 do
   part(m,"Upper Balustrade "..floorIndex,Vector3.new(.17,3,.17),
    CFrame.new(center+Vector3.new(side*3.55,y+1.65,-9.4+k*2.4)),
    Enum.Material.Metal,Color3.fromRGB(112,117,112),false)
  end
 end
 return y
end
local function firstFlight(m,center,baseY)
 -- Each stair tread rises about 0.9 studs. The stairwell is open overhead.
 -- Base interior walkable floor is at y=3.775. Upstairs is y=13.35.
 for i=1,10 do
  local z=-7.6+(i-1)*1.75
  local top=baseY+1+(i-1)*.92
  local tread=part(m,"Walkable Stair Tread "..math.floor(baseY).." "..i,
   Vector3.new(5.4,.45,1.83),
   CFrame.new(center+Vector3.new(0,top-.225,z)),
   Enum.Material.WoodPlanks,wood,true)
  tread:SetAttribute("StairStep",i)
  if i==1 or i==10 then
   for _,side in ipairs({-1,1}) do
    part(m,"Stair Rail Newel",Vector3.new(.24,3.1,.24),
     tread.CFrame*CFrame.new(side*2.8,1.6,0),
     Enum.Material.Metal,Color3.fromRGB(111,113,113),false)
   end
  end
 end
end
local function upstairs(m,center,width,floorIndex)
 local y=3+(floorIndex-1)*10
 local side= floorIndex==2 and 1 or -1
 local roomX=side*(width*.31)
 local c=center+Vector3.new(roomX,y,1.3)
 part(m,"Upper Bedroom Area Rug",Vector3.new(7,.15,7),
  CFrame.new(c+Vector3.new(0,.48,0)),Enum.Material.Fabric,
  Color3.fromRGB(166,139,116),false)
 part(m,"Upper Bedroom Bed Frame",Vector3.new(6,1.1,7.5),
  CFrame.new(c+Vector3.new(0,1.25,3)),Enum.Material.WoodPlanks,timber,true)
 part(m,"Upper Bedroom Mattress",Vector3.new(5.8,.4,7.3),
  CFrame.new(c+Vector3.new(0,1.8,3)),Enum.Material.Fabric,
  Color3.fromRGB(220,226,223),false)
 part(m,"Upper Bedroom Pillow",Vector3.new(3.8,.3,1.3),
  CFrame.new(c+Vector3.new(0,2.17,5.6)),Enum.Material.Fabric,
  Color3.fromRGB(245,242,232),false)
 local desk=part(m,"Upstairs Writing Desk",Vector3.new(4,.5,2.2),
  CFrame.new(c+Vector3.new(0,1.55,-5.1)),Enum.Material.WoodPlanks,wood,true)
 part(m,"Bedroom Books",Vector3.new(1.6,.75,1),
  desk.CFrame*CFrame.new(.9,.65,0),Enum.Material.SmoothPlastic,
  Color3.fromRGB(91,128,167),false)
 local light=part(m,"Upper Sconce",Vector3.new(.8,.8,.4),
  CFrame.new(c+Vector3.new(-1,5.2,8)),
  Enum.Material.Glass,Color3.fromRGB(251,221,180),false)
 local bulb=Instance.new("PointLight")
 bulb.Brightness=.7;bulb.Range=12;bulb.Color=Color3.fromRGB(252,213,155)
 bulb.Parent=light
 return desk
end
local function accessFloor(m,center,floorIndex,totalFloors,player,handlers)
 local y=3+(floorIndex-1)*10
 -- Separate functional lift pads make third storeys accessible when layout
 -- or collision settings interfere with the stairs. Owner-only for now.
 local at=part(m,"Residential Floor Lift "..floorIndex,
  Vector3.new(3.5,.24,3.5),
  CFrame.new(center+Vector3.new(-.5,y+.5,-10)),
  Enum.Material.Metal,Color3.fromRGB(117,145,160),false)
 local light=Instance.new("SurfaceGui")
 light.Face=Enum.NormalId.Top;light.CanvasSize=Vector2.new(230,230);light.Parent=at
 local label=Instance.new("TextLabel")
 label.Size=UDim2.fromScale(1,1);label.BackgroundTransparency=1
 label.Text="FLOOR "..floorIndex;label.Font=Enum.Font.GothamBold
 label.TextScaled=true;label.TextColor3=Color3.fromRGB(255,236,197)
 label.Parent=light
 prompt(at,"Downstairs Access","GO DOWN",function(visitor)
  if visitor~=player then return end
  local state=handlers.getProfile(visitor)
  if not state or not state.life then return end
  local character=visitor.Character
  if character then
   character:PivotTo(CFrame.new(center+Vector3.new(6,y-6,10)))
   handlers.tell(visitor,"RETURNED DOWNSTAIRS.")
  end
 end)
 if floorIndex<totalFloors then
  local upwards=part(m,"Private Third Floor Lift",
   Vector3.new(3.5,.24,3.5),
   CFrame.new(center+Vector3.new(0,y+.55,9.9)),
   Enum.Material.Metal,Color3.fromRGB(113,163,139),false)
  prompt(upwards,"Third Floor Access","GO UP",function(visitor)
   if visitor~=player or not visitor.Character then return end
   local state=handlers.getProfile(visitor)
   if state and state.life then
    visitor.Character:PivotTo(CFrame.new(center+Vector3.new(6,y+14,10)))
    handlers.tell(visitor,"ARRIVED ON THE THIRD FLOOR.")
   end
  end)
 end
 return at
end
local function facade(m,center,width,height,tier,owned)
 local color=tier=="FARMHOUSE" and Color3.fromRGB(235,237,226)
  or tier=="BEACH_HOUSE" and Color3.fromRGB(183,220,229)
  or tier=="LAKE_CABIN" and Color3.fromRGB(134,108,80)
  or tier=="VILLA" and Color3.fromRGB(232,214,185)
  or tier=="PENTHOUSE" and Color3.fromRGB(158,183,197)
  or tier=="PRIVATE_ISLAND" and Color3.fromRGB(233,222,206)
  or Color3.fromRGB(189,191,186)
 local trimMaterial=tier=="LAKE_CABIN" and Enum.Material.WoodPlanks
  or Enum.Material.Concrete
 for floor=1,height/10 do
  local level=5+(floor-1)*10
  for _,x in ipairs({-width*.30,width*.30}) do
   local outline=part(m,"Exterior Window Surround",Vector3.new(6.8,5.7,.45),
    CFrame.new(center+Vector3.new(x,level+1,-13.55)),
    trimMaterial,color,false)
   local glass=part(m,"Front Pane Glass",Vector3.new(5.5,4.6,.13),
    outline.CFrame*CFrame.new(0,0,-.3),Enum.Material.Glass,
    Color3.fromRGB(84,154,184),false)
   glass.Transparency=.29
   part(m,"Window Mullion",Vector3.new(.17,4.7,.3),
    glass.CFrame*CFrame.new(0,0,-.1),Enum.Material.Metal,
    Color3.fromRGB(73,91,99),false)
  end
 end
 if tier=="BEACH_HOUSE" or tier=="VILLA" or tier=="PRIVATE_ISLAND" then
  part(m,"Private Garden Patio",Vector3.new(26,.4,11),
   CFrame.new(center+Vector3.new(0,2.55,23)),
   Enum.Material.Concrete,Color3.fromRGB(213,197,173),true)
  if owned.SWIMMING_POOL then
   local pool=part(m,"Owned Garden Swimming Pool",Vector3.new(15,.2,7),
    CFrame.new(center+Vector3.new(0,2.84,23)),
    Enum.Material.Glass,Color3.fromRGB(78,179,203),false)
   pool.Transparency=.28
   local outer=part(m,"Swimming Pool Coping",Vector3.new(17,.3,9),
    pool.CFrame*CFrame.new(0,-.25,0),
    Enum.Material.Limestone,Color3.fromRGB(225,213,190),false)
  end
 end
 if tier=="FARMHOUSE" or tier=="STARTER_HOME" then
  for _,x in ipairs({-width*.38,width*.38}) do
   local planter=part(m,"Front Flower Trough",Vector3.new(4,1.2,3),
    CFrame.new(center+Vector3.new(x,3.5,-18)),
    Enum.Material.WoodPlanks,timber,true)
   for k=1,3 do
    local flower=part(m,"Front Flowering Shrub",Vector3.new(1.1,1.1,1.1),
     planter.CFrame*CFrame.new(-1.2+k*.65,1.1,0),
     Enum.Material.Grass,Color3.fromRGB(66,146,73),false)
    flower.Shape=Enum.PartType.Ball
   end
  end
 end
 if owned.SWIMMING_POOL and not
  (tier=="BEACH_HOUSE" or tier=="VILLA" or tier=="PRIVATE_ISLAND") then
  local pool=part(m,"Owned Garden Swimming Pool",Vector3.new(14,.2,7),
   CFrame.new(center+Vector3.new(0,2.84,23)),Enum.Material.Glass,
   Color3.fromRGB(84,173,196),false)
  pool.Transparency=.24
  part(m,"Swimming Pool Coping",Vector3.new(15,.3,8),
   pool.CFrame*CFrame.new(0,-.24,0),Enum.Material.Limestone,
   Color3.fromRGB(216,212,201),false)
 end
 if owned.SOLAR_PANEL then
  for x=-1,1 do
   part(m,"Owned Rooftop Solar Panel",Vector3.new(4,.15,7),
    CFrame.new(center+Vector3.new(x*4,8+height,0))*
     CFrame.Angles(math.rad(18),0,0),
    Enum.Material.Glass,Color3.fromRGB(35,64,97),false)
  end
 end
end
function House.Build(model,center,width,floors,tier,player,owned,handlers)
 if floors>=2 then
  for f=2,floors do
   buildFloor(model,center,width,f)
   if f==2 then firstFlight(model,center,3.78) end
   upstairs(model,center,width,f)
   accessFloor(model,center,f,floors,player,handlers)
  end
  local ground=part(model,"Ground Floor Lift",Vector3.new(3.5,.25,3.5),
   CFrame.new(center+Vector3.new(-.5,4.05,-10)),
   Enum.Material.Metal,Color3.fromRGB(106,128,150),false)
  prompt(ground,"Upper Floor Lift","GO UP",function(visitor)
   if visitor~=player or not visitor.Character then return end
   local state=handlers.getProfile(visitor)
   if not state or not state.life then return end
   visitor.Character:PivotTo(CFrame.new(center+Vector3.new(6,17,10)))
   handlers.tell(visitor,"ARRIVED IN YOUR UPSTAIRS BEDROOM.")
  end)
 end
 facade(model,center,width,floors*10,tier,owned)
 model:SetAttribute("ReachableUpperFloors",math.max(0,floors-1))
end
return House
