-- v0.23: Downtown courier route with real pickup bins and delivery addresses.
-- Every job order, interaction radius and paid completion is server-validated.
local Characters=require(script.Parent:WaitForChild("VenueCharacters"))
local Courier={}
Courier.Parcels={"DOCUMENTS","GROCERIES","ELECTRONICS"}
Courier.Destinations={"APARTMENTS","OFFICES","WATERFRONT"}
local bins={}
local destinations={}
local guides={}
local handlers
local function create(folder,name,size,cf,color,material,collides)
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.CFrame=cf;p.Anchored=true
 p.Color=color;p.Material=material or Enum.Material.SmoothPlastic
 p.CanCollide=collides==true;p.CanTouch=false
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth;p.Parent=folder
 return p
end
local function sign(node,title,subtitle)
 local gui=Instance.new("BillboardGui")
 gui.Name="Courier Direction";gui.Size=UDim2.fromOffset(215,64)
 gui.MaxDistance=85;gui.StudsOffsetWorldSpace=Vector3.new(0,3.1,0)
 gui.Parent=node
 local t=Instance.new("TextLabel")
 t.Size=UDim2.fromScale(1,1);t.TextWrapped=true
 t.BackgroundColor3=Color3.fromRGB(32,48,66)
 t.BackgroundTransparency=.1
 t.TextColor3=Color3.fromRGB(236,232,199)
 t.Font=Enum.Font.GothamBold;t.TextSize=14
 t.Text=title.."\n"..subtitle;t.Parent=gui
end
local function prompt(node,verb,displayName,kind,arg)
 local pp=Instance.new("ProximityPrompt")
 pp.Name="Courier "..verb.." "..arg
 pp.ActionText=verb;pp.ObjectText=displayName
 pp.RequiresLineOfSight=false;pp.HoldDuration=.65
 pp.MaxActivationDistance=8;pp.Parent=node
 pp.Triggered:Connect(function(player)
  if handlers and handlers.process then handlers.process(player,kind,arg) end
 end)
end
local function clearPackage(player)
 local char=player.Character
 local prop=char and char:FindFirstChild("Courier Carry Package")
 if prop then prop:Destroy() end
end
function Courier.Clear(player) clearPackage(player) end
function Courier.HasPackage(player,shift)
 local char=player.Character
 local prop=char and char:FindFirstChild("Courier Carry Package")
 return prop~=nil and shift and shift.courierProp==prop and
  prop:GetAttribute("ParcelType")==shift.courierPackage and
  prop:GetAttribute("OwnerUserId")==player.UserId and
  prop:FindFirstChild("Package Body")~=nil
end
local function giveParcel(player,shift,product)
 local char=player.Character
 local grip=char and (char:FindFirstChild("RightHand") or
  char:FindFirstChild("Right Arm"))
 local humanoid=char and char:FindFirstChildOfClass("Humanoid")
 if not grip or not humanoid or humanoid.Health<=0 then return false end
 clearPackage(player)
 local prop=Instance.new("Model")
 prop.Name="Courier Carry Package"
 prop:SetAttribute("ParcelType",product)
 prop:SetAttribute("OwnerUserId",player.UserId)
 local box=Instance.new("Part")
 box.Name="Package Body";box.Size=Vector3.new(1.5,1.15,1.1)
 box.Color=product=="GROCERIES" and Color3.fromRGB(126,166,119) or
  product=="DOCUMENTS" and Color3.fromRGB(209,185,135) or
  Color3.fromRGB(105,155,199)
 box.Material=Enum.Material.Wood
 box.Anchored=false;box.Massless=true
 box.CanCollide=false;box.CanTouch=false;box.CanQuery=false
 box.CFrame=grip.CFrame*CFrame.new(0,-.38,-.77)
 box.Parent=prop;prop.PrimaryPart=box
 local tag=Instance.new("BillboardGui")
 tag.Name="Assigned Package Label";tag.Size=UDim2.fromOffset(130,30)
 tag.StudsOffsetWorldSpace=Vector3.new(0,1,0)
 tag.MaxDistance=28;tag.Parent=box
 local text=Instance.new("TextLabel")
 text.Size=UDim2.fromScale(1,1)
 text.BackgroundColor3=Color3.fromRGB(34,50,69)
 text.TextColor3=Color3.fromRGB(240,232,202)
 text.TextSize=13;text.Font=Enum.Font.GothamBold
 text.Text=product;text.Parent=tag
 prop.Parent=char
 local weld=Instance.new("WeldConstraint")
 weld.Name="Held Package Joint";weld.Part0=grip;weld.Part1=box
 weld.Parent=box
 shift.courierProp=prop
 return true
end
function Courier.ResetAfterRespawn(shift)
 if shift and shift.id=="COURIER" and shift.progress==1 then
  shift.progress=0;shift.courierPickedUp=false;shift.courierProp=nil
  shift.taskAt=0
  return true
 end
 return false
end
local function close(player,node,distance)
 local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
 return root and node and node.Parent and
  (root.Position-node.Position).Magnitude<=(distance or 8)
end
function Courier.Build(world,options)
 handlers=options
 table.clear(bins);table.clear(destinations);table.clear(guides)
 local folder=Instance.new("Folder")
 folder.Name="Downtown Hands-On Delivery Depot";folder.Parent=world
 local base=CFrame.new(36,3,2291)
 create(folder,"Depot Loading Dock",Vector3.new(42,.8,20),
  base*CFrame.new(0,-.65,0),Color3.fromRGB(128,133,129),
  Enum.Material.Concrete,true)
 local header=create(folder,"Rift Express Parcel Dispatch",
  Vector3.new(24,3.5,1),base*CFrame.new(0,7,8),
  Color3.fromRGB(48,75,101),Enum.Material.Metal,false)
 sign(header,"RIFT EXPRESS","PICK UP • DELIVER • GET PAID")
 local packageColors={
  DOCUMENTS=Color3.fromRGB(202,179,121),
  GROCERIES=Color3.fromRGB(128,165,115),
  ELECTRONICS=Color3.fromRGB(103,148,187),
 }
 for i,package in ipairs(Courier.Parcels) do
  -- Separate interactable bins enough that touching a neighboring crate
  -- cannot count as being within the assigned parcel pickup radius.
  local x=(i-2)*14
  local crate=create(folder,"Courier Pickup "..package,
   Vector3.new(7,3.8,4.5),base*CFrame.new(x,1.55,-2),
   Color3.fromRGB(82,93,99),Enum.Material.Metal,true)
  create(folder,package.." Shipping Parcel",Vector3.new(2.8,1.6,2.3),
   crate.CFrame*CFrame.new(0,2.75,0),
   packageColors[package],Enum.Material.Wood,false)
  create(folder,package.." Parcel Label",Vector3.new(2,.06,1),
   crate.CFrame*CFrame.new(0,3.59,0),
   Color3.fromRGB(236,227,198),Enum.Material.SmoothPlastic,false)
  sign(crate,"DISPATCH: "..package,"COLLECT YOUR ASSIGNED PACKAGE")
  prompt(crate,"PICK UP "..package,package.." PARCEL","CourierPickup",package)
  bins[package]=crate
 end
 -- Three grounded customer addresses require a real route through the block;
 -- a distant RemoteEvent alone cannot hand in a parcel.
 for i,place in ipairs(Courier.Destinations) do
  local x=(i-2)*28
  local front=base*CFrame.new(x,0,55)
  local doorstep=create(folder,"Courier Dropoff "..place,
   Vector3.new(8,1.1,7),front*CFrame.new(0,-.05,0),
   Color3.fromRGB(152,158,149),Enum.Material.Concrete,true)
  local doorway=create(folder,place.." Parcel Locker",
   Vector3.new(4.5,6,1.1),front*CFrame.new(0,3.2,2.2),
   Color3.fromRGB(52,72,84),Enum.Material.Metal,true)
  create(folder,place.." Door Panel",Vector3.new(3.1,4,.2),
   doorway.CFrame*CFrame.new(0,-.5,-.68),
   packageColors[Courier.Parcels[i]],Enum.Material.Metal,false)
  sign(doorstep,place.." DELIVERY","DROP OFF THE CORRECT ROUTE")
  prompt(doorstep,"DELIVER TO "..place,place.." DELIVERY","CourierDeliver",place)
  destinations[place]=doorstep
 end
 guides[1]=Characters.Create(folder,"Rift Express Dispatcher",
  base*CFrame.new(15,0,-13),"JORDAN • DISPATCH",
  Color3.fromRGB(71,107,149),function(player)
   if handlers and handlers.process then handlers.process(player,"CourierGuide") end
  end)
 for i,place in ipairs(Courier.Destinations) do
  guides[i+1]=Characters.Create(folder,"Courier Resident "..place,
   base*CFrame.new((i-2)*28+6,0,52),
   place.." • RECEIVER",Color3.fromRGB(125,92,111),function(player)
    if handlers and handlers.process then handlers.process(player,"CourierGuide") end
   end)
 end
 folder:SetAttribute("CourierNPCCount",#guides)
 folder:SetAttribute("CourierParcelTypes",#Courier.Parcels)
 folder:SetAttribute("CourierDestinationTypes",#Courier.Destinations)
 folder:SetAttribute("ServerValidatedDelivery",true)
 folder:SetAttribute("NoBackgroundLoops",true)
 return folder
end
function Courier.Assign(shift)
 if type(shift)~="table" then return nil end
 local parcel=Courier.Parcels[math.random(1,#Courier.Parcels)]
 local destination=Courier.Destinations[math.random(1,#Courier.Destinations)]
 shift.courierPackage=parcel;shift.courierDestination=destination
 shift.courierPickedUp=false
 return parcel,destination
end
function Courier.Process(player,kind,arg,shift)
 if kind=="CourierGuide" then
  local closeToGuide=false
  for _,guide in ipairs(guides) do
   if guide and guide.PrimaryPart and close(player,guide.PrimaryPart,8) then
    closeToGuide=true;break end
  end
  if not closeToGuide or not handlers then return false end
  if shift and shift.id=="COURIER" and shift.courierPackage then
   local words=shift.progress==0 and ("PICK UP "..shift.courierPackage..
    " AT THE DISPATCH DEPOT.") or shift.progress==1 and
    ("BRING "..shift.courierPackage.." TO "..shift.courierDestination..
    ". KEEP YOUR PACKAGE VISIBLE.") or
    "DELIVERY RECEIVED! RETURN TO YOUR WORKPLACE FOR PAY."
   handlers.tell(player,words)
  else handlers.tell(player,"BECOME A COURIER AT CITY JOBS, START A SHIFT, PICK UP A PARCEL, THEN DELIVER IT.") end
  return true
 end
 if not handlers or not shift or shift.id~="COURIER" or
  type(shift.courierPackage)~="string" then return false end
 local now=os.clock()
 if kind=="CourierPickup" then
  if type(arg)~="string" or not bins[arg] or
   not close(player,bins[arg],6) or
   (shift.progress~=0 and not (shift.progress==1 and
    shift.courierPickedUp and not Courier.HasPackage(player,shift))) or
   now-shift.started<1.5 then return false end
  if arg~=shift.courierPackage then
   handlers.tell(player,"WRONG PACKAGE. DISPATCH REQUESTS "..shift.courierPackage..".")
   return false
  end
  if not giveParcel(player,shift,arg) then
   handlers.tell(player,"YOUR CHARACTER MUST BE READY TO HOLD THE PACKAGE.")
   return false
  end
  shift.progress=1;shift.taskAt=now;shift.courierPickedUp=true
  handlers.tell(player,"PARCEL COLLECTED! DELIVER TO "..shift.courierDestination..
   " AT THE LABELED CUSTOMER ADDRESS.")
 elseif kind=="CourierDeliver" then
  if type(arg)~="string" or not destinations[arg] or
   not close(player,destinations[arg],8) or shift.progress~=1 or
   not shift.courierPickedUp then return false end
  if not Courier.HasPackage(player,shift) then
   handlers.tell(player,"YOUR PACKAGE IS MISSING! RETURN TO DISPATCH TO PICK IT UP AGAIN.")
   return false
  end
  if now-shift.taskAt<1.5 then
   handlers.tell(player,"SECURE THE PACKAGE BEFORE DELIVERY.")
   return false
  end
  if arg~=shift.courierDestination then
   handlers.tell(player,"WRONG ADDRESS! CHECK YOUR ROUTE TO "..shift.courierDestination..".")
   return false
  end
  shift.progress=2;shift.taskAt=now
  clearPackage(player);shift.courierProp=nil
  handlers.reward(player,10,4,0)
  handlers.tell(player,"PACKAGE DELIVERED • +10 COIN TIP! RETURN TO THE COURIER WORKPLACE FOR WAGES.")
 else return false end
 handlers.sync(player)
 return true
end
return Courier
