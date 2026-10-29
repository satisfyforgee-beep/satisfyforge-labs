-- v0.13 Home Living: lockable front doors, ownership-validated furniture
-- and equipment used inside physical homes. No Robux or real purchases.
local TweenService=game:GetService("TweenService")
local Home={}
local function piece(parent,name,size,cf,color,material,solid)
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.CFrame=cf
 p.Material=material or Enum.Material.WoodPlanks
 p.Color=color or Color3.fromRGB(149,118,93)
 p.Anchored=true;p.CanCollide=solid==true;p.CanTouch=false
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth;p.Parent=parent
 return p
end
local function device(parent,base,fn,action,name)
 local prompt=Instance.new("ProximityPrompt")
 prompt.Name="Home "..name
 prompt.ActionText=action;prompt.ObjectText=name
 prompt.MaxActivationDistance=10;prompt.HoldDuration=.25
 prompt.RequiresLineOfSight=false;prompt.Parent=base
 prompt.Triggered:Connect(fn)
 return prompt
end
local function inRange(player,part,range)
 local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
 return root and (root.Position-part.Position).Magnitude<(range or 14)
end
local function addLamp(model,location,shade)
 local lamp=piece(model,"Warm Interior Ceiling Lamp",Vector3.new(2,.4,2),
  CFrame.new(location),shade,Enum.Material.Metal,false)
 local light=Instance.new("PointLight")
 light.Brightness=1.5;light.Range=22;light.Shadows=true
 light.Color=Color3.fromRGB(255,222,173);light.Parent=lamp
 local globe=piece(model,"Frosted Lamp Diffuser",Vector3.new(1.25,.5,1.25),
  CFrame.new(location-Vector3.new(0,.4,0)),
  Color3.fromRGB(250,234,205),Enum.Material.Glass,false)
 globe.Transparency=.16
end
local function sofaUpgrade(model,center,width)
 local pos=center+Vector3.new(-width*.25,5,-2)
 local base=piece(model,"Purchased Couch Cushions",Vector3.new(8,1.25,3),
  CFrame.new(pos+Vector3.new(0,.55,-.1)),
  Color3.fromRGB(81,112,129),Enum.Material.Fabric,true)
 for _,x in ipairs({-2.55,0,2.55}) do
  piece(model,"Upholstered Sofa Cushion",Vector3.new(2.1,.4,2.25),
   CFrame.new(pos+Vector3.new(x,1.22,-.15)),
   Color3.fromRGB(100,131,144),Enum.Material.Fabric,false)
 end
 for _,x in ipairs({-4.0,4.0}) do
  piece(model,"Sofa Armrest",Vector3.new(.8,2.05,3),
   CFrame.new(pos+Vector3.new(x,1,-.1)),
   Color3.fromRGB(86,111,125),Enum.Material.Fabric,true)
 end
 return base
end
local function homeDoor(model,center,player,handlers)
 local hinge=CFrame.new(center+Vector3.new(-2.7,7.05,-13.95))
 local shut=hinge*CFrame.new(2.7,0,0)
 local open=hinge*CFrame.Angles(0,math.rad(104),0)*CFrame.new(2.7,0,0)
 local door=piece(model,"Security Entrance Door",Vector3.new(5.25,7.65,.45),
  shut,Color3.fromRGB(95,83,77),Enum.Material.WoodPlanks,true)
 local handle=piece(model,"Front Door Handle",Vector3.new(.5,.5,.5),
  shut*CFrame.new(1.7,-.1,-.45),Color3.fromRGB(183,165,121),
  Enum.Material.Metal,false)
 local lockPanel=piece(model,"Door Smart Lock",Vector3.new(.75,1,.22),
  CFrame.new(center+Vector3.new(3.7,7.2,-13.65)),
  Color3.fromRGB(50,65,69),Enum.Material.Metal,false)
 local lockLight=piece(model,"Door Lock Indicator",Vector3.new(.28,.28,.16),
  lockPanel.CFrame*CFrame.new(0,.2,-.18),
  Color3.fromRGB(209,70,61),Enum.Material.Neon,false)
 local busy=false;local opened=false
 local function change(openNow)
  if busy then return end
  busy=true;opened=openNow
  if openNow then door.CanCollide=false end
  local tween=TweenService:Create(door,TweenInfo.new(.65,Enum.EasingStyle.Sine),
   {CFrame=openNow and open or shut})
  local hTween=TweenService:Create(handle,
   TweenInfo.new(.65,Enum.EasingStyle.Sine),
   {CFrame=(openNow and open or shut)*CFrame.new(1.7,-.1,-.45)})
  tween:Play();hTween:Play();tween.Completed:Wait()
  if door.Parent then door.CanCollide=not openNow end
  busy=false
 end
 local function ownerProfile()
  local state=handlers.getProfile(player)
  return state and state.life or nil
 end
 local prompt=device(model,door,function(visitor)
  if not inRange(visitor,door,12) then return end
  local owner=ownerProfile()
  if not owner then return end
  if visitor~=player and owner.homeLocked then
   handlers.tell(visitor,"THIS HOME IS LOCKED • ASK THE OWNER TO UNLOCK IT.")
   return
  end
  if busy then return end
  change(not opened)
  handlers.tell(visitor,opened and "HOME DOOR OPENED." or "HOME DOOR CLOSED.")
 end,"OPEN / CLOSE","Front Door")
 local lockPrompt=device(model,lockPanel,function(visitor)
  if visitor~=player or not inRange(visitor,lockPanel,12) then return end
  local state=ownerProfile()
  if not state then return end
  state.homeLocked=not state.homeLocked
  if state.homeLocked and opened and not busy then change(false) end
  lockLight.Color=state.homeLocked and Color3.fromRGB(209,70,61)
   or Color3.fromRGB(90,196,114)
  lockPanel:SetAttribute("Locked",state.homeLocked)
  handlers.sync(player)
  handlers.tell(player,state.homeLocked and
   "YOUR HOME IS LOCKED TO VISITORS." or "YOUR HOME IS OPEN TO VISITORS.")
 end,"LOCK / UNLOCK","Owner Home Security")
 local state=ownerProfile()
 lockPanel:SetAttribute("Locked",not state or state.homeLocked)
 if state and not state.homeLocked then
  lockLight.Color=Color3.fromRGB(90,196,114)
 end
 door:SetAttribute("OwnerUserId",player.UserId)
 return door,lockPanel
end
function Home.Furnish(model,center,width,floors,player,owned,handlers)
 -- All interactions use the server-held original owner, never a client-supplied user id.
 addLamp(model,center+Vector3.new(0,12,0),Color3.fromRGB(94,85,76))
 if floors>=2 then
  addLamp(model,center+Vector3.new(0,21,0),Color3.fromRGB(95,88,81))
 end
 homeDoor(model,center,player,handlers)
 local function restore(node,needs,cooldown,notice)
  local clock=-1000
  device(model,node,function(visitor)
   if visitor~=player or not inRange(visitor,node,12) then return end
   local state=handlers.getProfile(player)
   if not state or not state.life then return end
   local now=os.clock()
   if now-clock<cooldown then
    handlers.tell(player,"FINISH USING THIS APPLIANCE BEFORE TRYING AGAIN.")
    return
   end
   clock=now
   for k,n in pairs(needs) do
    state.life.needs[k]=math.min(100,state.life.needs[k]+n)
   end
   handlers.sync(player)
   handlers.tell(player,notice)
  end,"USE","Your "..node.Name)
 end
 if owned.COUCH or owned.FURNITURE then
  sofaUpgrade(model,center,width)
 end
 if owned.SMART_TV or owned.GAME_CONSOLE or owned.HOME_PROJECTOR then
  local tv=piece(model,"Wall Mounted Smart TV",
   Vector3.new(8.1,4.1,.38),
   CFrame.new(center+Vector3.new(-width*.25,8.2,-10.75)),
   Color3.fromRGB(19,25,31),Enum.Material.Glass,false)
  local screen=piece(model,"Home TV Display",
   Vector3.new(7.6,3.65,.16),
   tv.CFrame*CFrame.new(0,0,-.28),
   Color3.fromRGB(67,125,157),Enum.Material.Glass,false)
  screen.Transparency=.12
  restore(tv,{fun=24},35,"WATCHED TELEVISION • FUN +24!")
  if owned.GAME_CONSOLE then
   local console=piece(model,"Game Console Dock",Vector3.new(2.1,.45,1.6),
    CFrame.new(center+Vector3.new(-width*.25,5,-10)),
    Color3.fromRGB(36,45,56),Enum.Material.Metal,false)
   restore(console,{fun=43},45,"PLAYED VIDEO GAMES • FUN +43!")
  end
 end
 if owned.FRIDGE or owned.KITCHEN_APPLIANCES then
  local fridge=piece(model,"Home Refrigerator",Vector3.new(2.6,6,2.4),
   CFrame.new(center+Vector3.new(width*.43,7,10)),
   Color3.fromRGB(203,215,219),Enum.Material.Metal,true)
  piece(model,"Freezer Door",Vector3.new(2.45,2.1,.16),
   fridge.CFrame*CFrame.new(0,1.55,-1.24),
   Color3.fromRGB(188,203,209),Enum.Material.Metal,false)
  piece(model,"Fridge Handle",Vector3.new(.18,1.2,.2),
   fridge.CFrame*CFrame.new(-.85,.7,-1.38),
   Color3.fromRGB(62,68,75),Enum.Material.Metal,false)
  restore(fridge,{hunger=40},60,"ATE A MEAL FROM THE FRIDGE • HUNGER +40!")
 end
 if owned.DINING_TABLE then
  local spot=center+Vector3.new(width*.28,5.1,-7.2)
  local top=piece(model,"Purchased Dining Table",Vector3.new(6.6,.55,3.4),
   CFrame.new(spot),Color3.fromRGB(124,85,62),Enum.Material.WoodPlanks,true)
  for _,x in ipairs({-2.5,2.5}) do
   for _,z in ipairs({-1,1}) do
    piece(model,"Dining Table Leg",Vector3.new(.45,1.3,.45),
     top.CFrame*CFrame.new(x,-.8,z),
     Color3.fromRGB(103,74,55),Enum.Material.Wood,true)
   end
  end
  for _,z in ipairs({-3,3}) do
   piece(model,"Dining Chair",Vector3.new(2,1,1.7),
    CFrame.new(spot+Vector3.new(0,-.45,z)),
    Color3.fromRGB(158,122,85),Enum.Material.Wood,true)
  end
 end
 if owned.BOOKSHELF then
  local base=piece(model,"Oak Bookcase",Vector3.new(4.2,7,.9),
   CFrame.new(center+Vector3.new(-width*.43,7.5,2)),
   Color3.fromRGB(109,81,58),Enum.Material.Wood,true)
  for _,y in ipairs({-1.8,-.3,1.2,2.6}) do
   piece(model,"Library Shelf",Vector3.new(4,.15,.94),
    base.CFrame*CFrame.new(0,y,0),
    Color3.fromRGB(165,124,81),Enum.Material.Wood,false)
  end
  restore(base,{fun=12},40,"READ A BOOK • FUN +12!")
 end
 if owned.WASHER_DRYER then
  local washer=piece(model,"Home Washing Machine",Vector3.new(3.2,3,2.7),
   CFrame.new(center+Vector3.new(-width*.34,5.5,6.1)),
   Color3.fromRGB(211,219,225),Enum.Material.Metal,true)
  local drum=piece(model,"Laundry Washer Window",Vector3.new(1.6,1.6,.16),
   washer.CFrame*CFrame.new(0,0,-1.45),
   Color3.fromRGB(95,155,184),Enum.Material.Glass,false)
  drum.Shape=Enum.PartType.Ball
  restore(washer,{hygiene=30},50,"CLEANED CLOTHES • HYGIENE +30!")
 end
 if owned.KING_BED or owned.BED_SET then
  local mattress=piece(model,"Purchased King Mattress",Vector3.new(7.8,.65,9.8),
   CFrame.new(center+Vector3.new(width*.25,5.6,4)),
   Color3.fromRGB(235,227,215),Enum.Material.Fabric,true)
  piece(model,"Bedspread",Vector3.new(7.9,.18,5),
   mattress.CFrame*CFrame.new(0,.45,-1.8),
   Color3.fromRGB(134,156,164),Enum.Material.Fabric,false)
 end
 if owned.BABY_CRIB then
  local crib=piece(model,"Nursery Crib Base",Vector3.new(3.5,.65,5),
   CFrame.new(center+Vector3.new(width*.38,4.7,-5)),
   Color3.fromRGB(217,214,194),Enum.Material.Wood,true)
  for _,side in ipairs({-1,1}) do
   for i=1,6 do
    piece(model,"Nursery Safety Rail",Vector3.new(.17,2.7,.17),
     crib.CFrame*CFrame.new(side*1.63,1.5,-2.2+i*.63),
     Color3.fromRGB(230,226,206),Enum.Material.Wood,false)
   end
  end
 end
 if owned.PET_BED or owned.DOG_HOUSE or owned.CAT_TREE then
  local dogBed=piece(model,"Companion Pet Cushion",Vector3.new(3,.4,2.9),
   CFrame.new(center+Vector3.new(-width*.37,4.1,4.2)),
   Color3.fromRGB(162,117,91),Enum.Material.Fabric,false)
 end
 if owned.WORKSTATION or owned.DESKTOP_PC or owned.LAPTOP then
  local desk=piece(model,"Creator Work Desk",Vector3.new(4,.5,2.2),
   CFrame.new(center+Vector3.new(width*.37,6.1,-.4)),
   Color3.fromRGB(133,102,79),Enum.Material.Wood,true)
  local screen=piece(model,"Home Computer Monitor",Vector3.new(2.3,1.5,.3),
   desk.CFrame*CFrame.new(0,1.1,.2),
   Color3.fromRGB(52,78,99),Enum.Material.Glass,false)
  restore(desk,{fun=20},40,"WORKED ON YOUR COMPUTER • FUN +20!")
 end
 -- More purchases appear as equipment in owned homes rather than
 -- remaining permanent inventory checkmarks.
 if owned.ROBOT_VACUUM then
  local robot=piece(model,"Robotic Vacuum",Vector3.new(1.8,.55,1.8),
   CFrame.new(center+Vector3.new(-width*.3,4.2,6)),
   Color3.fromRGB(60,75,83),Enum.Material.Metal,false)
  robot.Shape=Enum.PartType.Cylinder
  piece(model,"Vacuum Status Light",Vector3.new(.3,.1,.3),
   robot.CFrame*CFrame.new(0,.29,0),
   Color3.fromRGB(72,201,161),Enum.Material.Neon,false)
  restore(robot,{hygiene=15},60,"ROBOT VACUUM CLEANED THE HOUSE • HYGIENE +15!")
 end
 if owned.SECURITY_CAMERA then
  local camera=piece(model,"Exterior Home Security Camera",
   Vector3.new(1.15,.7,1.4),
   CFrame.new(center+Vector3.new(-width*.33,11.1,-13.6))*
    CFrame.Angles(0,math.rad(30),0),
   Color3.fromRGB(212,212,212),Enum.Material.Metal,false)
  piece(model,"Security Camera Lens",Vector3.new(.4,.4,.14),
   camera.CFrame*CFrame.new(0,0,-.77),
   Color3.fromRGB(43,71,101),Enum.Material.Glass,false)
  device(model,camera,function(visitor)
   if visitor~=player or not inRange(visitor,camera,13) then return end
   local state=handlers.getProfile(player)
   if not state or not state.life then return end
   handlers.tell(player,
    "HOME SECURITY CAMERA INSTALLED. HOUSE IS "..
     (state.life.homeLocked and "LOCKED." or "OPEN TO GUESTS."))
  end,"CHECK","Home Security Camera")
 end
 if owned.BBQ_GRILL then
  local grill=piece(model,"Backyard Barbecue Grill",Vector3.new(4,2,2.6),
   CFrame.new(center+Vector3.new(width*.28,5,19)),
   Color3.fromRGB(79,81,82),Enum.Material.Metal,true)
  piece(model,"Barbecue Stainless Steel Hood",Vector3.new(4,.8,2.6),
   grill.CFrame*CFrame.new(0,1.35,0),
   Color3.fromRGB(126,132,135),Enum.Material.Metal,false)
  restore(grill,{hunger=35,fun=10},50,"COOKED A MEAL ON THE GRILL • HUNGER +35!")
 end
 if owned.HOT_TUB then
  local hot=piece(model,"Private Hot Tub",Vector3.new(7.7,2.2,6),
   CFrame.new(center+Vector3.new(-width*.28,4.2,20)),
   Color3.fromRGB(121,130,133),Enum.Material.Concrete,true)
  local spa=piece(model,"Spa Bubbles Surface",Vector3.new(6.6,.15,4.85),
   hot.CFrame*CFrame.new(0,1.2,0),
   Color3.fromRGB(89,178,201),Enum.Material.Glass,false)
  spa.Transparency=.35
  restore(hot,{fun=35,energy=18},65,
   "RELAXED IN HOT TUB • FUN +35 • ENERGY +18!")
 end
 if owned.PATIO_FURNITURE then
  local patio=piece(model,"Patio Dining Table",Vector3.new(4,.4,4),
   CFrame.new(center+Vector3.new(width*.3,4.75,23)),
   Color3.fromRGB(159,118,75),Enum.Material.WoodPlanks,true)
  for _,x in ipairs({-1,1}) do
   local chair=piece(model,"Patio Chair",Vector3.new(1.4,.9,1.4),
    patio.CFrame*CFrame.new(x*3,-.3,0),
    Color3.fromRGB(111,129,124),Enum.Material.WoodPlanks,true)
  end
  restore(patio,{fun=12},50,"RELAXED ON THE PATIO • FUN +12!")
 end
 if owned.TOOL_CABINET then
  local cabinet=piece(model,"Garage Mechanics Tool Chest",
   Vector3.new(3.8,3.5,2),
   CFrame.new(center+Vector3.new(width*.25,4.6,-20)),
   Color3.fromRGB(164,49,51),Enum.Material.Metal,true)
  for y=-1,1 do
   piece(model,"Mechanics Drawer Pull",Vector3.new(2.8,.16,.17),
    cabinet.CFrame*CFrame.new(0,y,-1.07),
    Color3.fromRGB(215,210,196),Enum.Material.Metal,false)
  end
  restore(cabinet,{fun=10},45,"ORGANIZED GARAGE TOOLS • FUN +10!")
 end
 if owned.CAT_TREE then
  local cat=piece(model,"Owned Cat Tower",Vector3.new(2.8,5.5,2.8),
   CFrame.new(center+Vector3.new(width*.36,6.6,-5)),
   Color3.fromRGB(157,133,110),Enum.Material.WoodPlanks,true)
  for _,height in ipairs({-1.8,.5,2.4}) do
   piece(model,"Pet Tree Platform",Vector3.new(3.8,.35,3),
    cat.CFrame*CFrame.new(0,height,0),
    Color3.fromRGB(176,140,102),Enum.Material.Fabric,false)
  end
  restore(cat,{fun=12},55,"SPENT TIME WITH YOUR CAT'S TOYS • FUN +12!")
 end
 if owned.DOG_HOUSE then
  local dog=piece(model,"Backyard Dog House",Vector3.new(4,3.4,4.1),
   CFrame.new(center+Vector3.new(-width*.37,4.6,20)),
   Color3.fromRGB(148,104,73),Enum.Material.WoodPlanks,true)
  piece(model,"Pet Shelter Roof",Vector3.new(5,.5,4.9),
   dog.CFrame*CFrame.new(0,2.1,0),
   Color3.fromRGB(67,75,81),Enum.Material.Slate,false)
  restore(dog,{fun=14},55,"PLAYED WITH PET IN THE GARDEN • FUN +14!")
 end
 model:SetAttribute("FurniturePieces",#model:GetDescendants())
end
return Home
