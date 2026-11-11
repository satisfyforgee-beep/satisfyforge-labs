-- v0.25: Two real, collision-safe downtown shop shells with entrance openings.
-- Retail and barista workstations remain at their original server-validated
-- positions inside the rooms. No teleport doors or third-party building scripts.
local Stores={}
local function piece(parent,name,size,cf,color,material,collide)
 local node=Instance.new("Part");node.Name=name;node.Size=size
 node.CFrame=cf;node.Color=color;node.Anchored=true
 node.Material=material or Enum.Material.Concrete
 node.CanCollide=collide==true;node.CanTouch=false;node.CanQuery=true
 node.TopSurface=Enum.SurfaceType.Smooth
 node.BottomSurface=Enum.SurfaceType.Smooth;node.Parent=parent
 return node
end
local function lettering(node,title,subtitle)
 local sign=Instance.new("SurfaceGui")
 sign.Name="Storefront Glass Sign";sign.Face=Enum.NormalId.Back
 sign.CanvasSize=Vector2.new(830,300);sign.Parent=node
 local text=Instance.new("TextLabel")
 text.Size=UDim2.fromScale(1,1);text.BackgroundTransparency=1
 text.Text=title.."\n"..subtitle
 text.Font=Enum.Font.GothamBold;text.TextScaled=true
 text.TextColor3=Color3.fromRGB(255,241,209)
 text.TextStrokeTransparency=.3;text.Parent=sign
end
local function accessRamp(model,center,front,floorTop)
 -- Continuous footpath from city asphalt to the actual interior floor.
 local run=12
 local h=floorTop-.25
 local slope=math.atan(h/run)
 local ramp=piece(model,"Continuous Public Entrance Ramp",
  Vector3.new(9,.35,run+.7),
  CFrame.new(center.X,(floorTop+.25)/2,front+run/2-1)*
   CFrame.Angles(slope,0,0),
  Color3.fromRGB(169,169,159),Enum.Material.Concrete,true)
 ramp:SetAttribute("AccessibilityRamp",true)
 local edging=Color3.fromRGB(205,190,156)
 for _,side in ipairs({-1,1}) do
  piece(model,"Ramp Edge Strip",Vector3.new(.35,.35,run+.5),
   ramp.CFrame*CFrame.new(side*4.45,.18,0),
   edging,Enum.Material.Metal,false)
 end
 return ramp
end
local function building(folder,id,center,wide,deep,floorTop,height,doorHalf,trim,brand,sub)
 local model=Instance.new("Model");model.Name=id;model.Parent=folder
 model:SetAttribute("WalkInDoorway",true)
 model:SetAttribute("DoorClearWidth",doorHalf*2)
 local c=Color3.fromRGB(197,194,185)
 local floor=piece(model,"Walkable Indoor Stone Floor",
  Vector3.new(wide,.55,deep),
  CFrame.new(center.X,floorTop-.275,center.Z),
  c,Enum.Material.Concrete,true)
 local wallCenterY=floorTop+height/2
 local front=center.Z+deep/2 -- south, towards arrival streets
 local back=center.Z-deep/2
 for _,side in ipairs({-1,1}) do
  piece(model,"Insulated Brick Side Wall",Vector3.new(.65,height,deep),
   CFrame.new(center.X+side*(wide/2-.325),wallCenterY,center.Z),
   trim,Enum.Material.Brick,true)
 end
 piece(model,"Rear Masonry Wall",Vector3.new(wide,height,.65),
  CFrame.new(center.X,wallCenterY,back+.325),
  trim,Enum.Material.Brick,true)
 local sideWidth=wide/2-doorHalf
 for _,side in ipairs({-1,1}) do
  local x=center.X+side*(doorHalf+sideWidth/2)
  local glass=piece(model,"Full Height Shop Window",Vector3.new(sideWidth,9,.22),
   CFrame.new(x,floorTop+4.5,front+.1),
   Color3.fromRGB(123,177,191),Enum.Material.Glass,true)
  glass.Transparency=.43
  piece(model,"Front Solid Piers",Vector3.new(sideWidth,height-9,.55),
   CFrame.new(x,floorTop+9+(height-9)/2,front),
   trim,Enum.Material.Brick,true)
  piece(model,"Window Frame",Vector3.new(.45,10,.5),
   CFrame.new(center.X+side*(wide/2-.4),floorTop+5,front-.25),
   Color3.fromRGB(53,70,79),Enum.Material.Metal,false)
 end
 -- The central doorway has no collidable glass, door or invisible wall.
 local lintel=piece(model,"Doorway Structural Lintel",
  Vector3.new(doorHalf*2,2,.6),
  CFrame.new(center.X,floorTop+height-1,front),
  trim,Enum.Material.Brick,true)
 local nameplate=piece(model,"Illuminated Business Name",
  Vector3.new(doorHalf*2+4,1.8,.3),
  lintel.CFrame*CFrame.new(0,-.4,-.55),
  Color3.fromRGB(38,51,65),Enum.Material.Metal,false)
 lettering(nameplate,brand,sub)
 for _,side in ipairs({-1,1}) do
  local post=piece(model,"Open Entry Glass Side Light",
   Vector3.new(.55,8,.35),
   CFrame.new(center.X+side*doorHalf,floorTop+4,front),
   Color3.fromRGB(99,142,154),Enum.Material.Glass,false)
  post.Transparency=.45
 end
 piece(model,"Roof and Rain Canopy",Vector3.new(wide+1.3,.65,deep+1.3),
  CFrame.new(center.X,floorTop+height+.32,center.Z),
  Color3.fromRGB(61,75,87),Enum.Material.Slate,true)
 local awning=piece(model,"Entrance Weather Awning",Vector3.new(doorHalf*2+5,.3,5),
  CFrame.new(center.X,floorTop+height-2.6,front-2),
  Color3.fromRGB(122,111,94),Enum.Material.Fabric,false)
 for _,x in ipairs({-wide*.32,wide*.32}) do
  local lamp=piece(model,"Indoor Warm Pendant Light",
   Vector3.new(2,.3,2),
   CFrame.new(center.X+x,floorTop+height-1.2,center.Z+2),
   Color3.fromRGB(247,224,170),Enum.Material.Neon,false)
  local light=Instance.new("PointLight")
  light.Brightness=.65;light.Range=19;light.Shadows=false
  light.Color=Color3.fromRGB(255,222,181);light.Parent=lamp
 end
 local entry=piece(model,"Entrance Threshold",Vector3.new(9,.14,2),
  CFrame.new(center.X,floorTop-.04,front-.7),
  Color3.fromRGB(180,165,139),Enum.Material.Marble,true)
 entry:SetAttribute("WalkableThreshold",true)
 local ramp=accessRamp(model,center,front,floorTop)
 model:SetAttribute("DoorCenter",Vector3.new(center.X,floorTop+3.5,front))
 model:SetAttribute("InsideCenter",Vector3.new(center.X,floorTop+3.5,center.Z+2))
 model:SetAttribute("RampBottom",ramp.Position.Y-math.sin(math.atan((floorTop-.25)/12))*6)
 return model
end
function Stores.Build(world)
 local existing=world:FindFirstChild("Real Walk-In Downtown Shops")
 if existing then existing:Destroy() end
 local folder=Instance.new("Folder")
 folder.Name="Real Walk-In Downtown Shops";folder.Parent=world
 -- Move the two earlier services out of overlapping skyscraper collision
 -- geometry into an accessible side street, keeping station-to-station
 -- gameplay and owner-validated server rules identical.
 local plaza=piece(folder,"Arcade Continuous Outdoor Stone Plaza",
  Vector3.new(121,.35,104),
  CFrame.new(-59,-.12,2117),
  Color3.fromRGB(155,152,146),Enum.Material.Concrete,true)
 plaza:SetAttribute("PedestrianPublicGround",true)
 piece(folder,"Downtown-to-Market Walkway",
  Vector3.new(16,.3,105),
  CFrame.new(-15,.03,2200),
  Color3.fromRGB(178,176,165),Enum.Material.Concrete,true)
 for i=0,12 do
  local walkwayMark=piece(folder,"Arcade Pavement Joint "..i,
   Vector3.new(16,.05,.17),
   CFrame.new(-15,.21,2150+i*8),
   Color3.fromRGB(121,122,118),Enum.Material.Concrete,false)
  walkwayMark.CastShadow=false
 end
 for _,x in ipairs({-110,-5}) do
  for _,z in ipairs({2094,2142}) do
   local lamp=piece(folder,"Neighborhood Entrance Lamppost",
    Vector3.new(.55,9,.55),CFrame.new(x,4.6,z),
    Color3.fromRGB(61,75,81),Enum.Material.Metal,true)
   local lantern=piece(folder,"Warm Pedestrian Street Lantern",
    Vector3.new(2,1.1,2),CFrame.new(x,9.3,z),
    Color3.fromRGB(255,226,168),Enum.Material.Glass,false)
   local point=Instance.new("PointLight");point.Brightness=.65
   point.Range=20;point.Shadows=false;point.Parent=lantern
  end
 end
 local district=piece(folder,"Arcade Destination Sign",
  Vector3.new(14,5,.6),CFrame.new(-15,7,2151),
  Color3.fromRGB(41,68,72),Enum.Material.Metal,false)
 lettering(district,"MARKET & CAFE","OPEN STOREFRONTS AHEAD")
 -- Existing workstations remain server-validated, now behind open entries.
 local retail=building(folder,"Accessible Corner Market",
  Vector3.new(-72,0,2125),40,37,2.775,13.5,5.5,
  Color3.fromRGB(130,115,105),"THE CORNER MARKET","SHOP • SCAN • STOCK")
 local cafe=building(folder,"Accessible Bean and Brew",
  Vector3.new(-36,0,2119),31,22,3.55,11.3,5,
  Color3.fromRGB(151,121,102),"BEAN & BREW","COFFEE • BAKERY")
 -- Human-scale furnishings, deliberately kept away from entry lanes.
 for _,data in ipairs({
  {c=Vector3.new(-72,0,2125),wide=40,floor=2.775},
  {c=Vector3.new(-36,0,2119),wide=31,floor=3.55},
 }) do
  for _,s in ipairs({-1,1}) do
   local x=data.c.X+s*(data.wide/2-2)
   piece(folder,"Wall Mounted Brochure Shelf",Vector3.new(2.1,.3,3.2),
    CFrame.new(x,data.floor+3.5,data.c.Z+1),
    Color3.fromRGB(124,91,69),Enum.Material.WoodPlanks,false)
   piece(folder,"Community Noticeboard",Vector3.new(2,.9,.17),
    CFrame.new(x,data.floor+5.4,data.c.Z+1),
    Color3.fromRGB(223,211,179),Enum.Material.Wood,false)
  end
 end
 folder:SetAttribute("OutsideFoundationExtended",true)
 folder:SetAttribute("WalkInShopCount",2)
 folder:SetAttribute("TeleportEntranceCount",0)
 folder:SetAttribute("BuiltForPhysicalWalking",true)
 return folder
end
return Stores
