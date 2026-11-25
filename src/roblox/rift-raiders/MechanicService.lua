-- v0.21: The Pit Stop mechanic career. A genuinely interactive car
-- service loop with a randomized fault, inspection, correct repair selection,
-- tip and ordinary career paycheck. All rewards and proximity checks are
-- server authoritative; the display car is script-free official Racing art.
local ServerStorage=game:GetService("ServerStorage")
local Mechanic={}
local Faults={"BRAKES","BATTERY","TIRES"}
Mechanic.Faults=Faults
local stations={}
local handlers
local function piece(folder,name,size,cf,color,material,collision)
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.CFrame=cf;p.Anchored=true
 p.CanCollide=collision==true;p.CanTouch=false
 p.Color=color;p.Material=material or Enum.Material.Metal
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth;p.Parent=folder
 return p
end
local function billboard(base,title,sub)
 local gui=Instance.new("BillboardGui")
 gui.Name="Pit Stop Sign"
 gui.Size=UDim2.fromOffset(215,62)
 gui.StudsOffsetWorldSpace=Vector3.new(0,3.2,0)
 gui.MaxDistance=70;gui.Parent=base
 local text=Instance.new("TextLabel")
 text.Size=UDim2.fromScale(1,1)
 text.BackgroundColor3=Color3.fromRGB(35,46,54)
 text.BackgroundTransparency=.05;text.TextWrapped=true
 text.TextColor3=Color3.fromRGB(249,225,179)
 text.TextSize=14;text.Font=Enum.Font.GothamBold
 text.Text=title.."\n"..sub;text.Parent=gui
end
local function prompt(base,action,thing,callback)
 local p=Instance.new("ProximityPrompt")
 p.Name="Mechanic "..thing
 p.ActionText=action;p.ObjectText=thing;p.HoldDuration=.55
 p.MaxActivationDistance=12
 p.RequiresLineOfSight=false
 p.Parent=base;p.Triggered:Connect(callback)
end
local function near(player,node,distance)
 local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
 return root and node and node.Parent and
  (root.Position-node.Position).Magnitude<=(distance or 12)
end
function Mechanic.Build(world,options)
 handlers=options
 table.clear(stations)
 local folder=Instance.new("Folder")
 folder.Name="Pit Stop Detailed Mechanic Bay"
 folder.Parent=world
 local center=CFrame.new(104,3,2292)
 local floor=piece(folder,"Concrete Service Bay",
  Vector3.new(40,.65,27),center*CFrame.new(0,-1,0),
  Color3.fromRGB(120,123,115),Enum.Material.Concrete,true)
 for _,x in ipairs({-17,17}) do
  piece(folder,"Safety Stripe",Vector3.new(1.1,.09,18),
   center*CFrame.new(x,.06,0),Color3.fromRGB(228,195,69),
   Enum.Material.SmoothPlastic,false)
 end
 for _,x in ipairs({-10,10}) do
  piece(folder,"Hydraulic Lift Rail",Vector3.new(1.1,1.1,18),
   center*CFrame.new(x,1.3,0),Color3.fromRGB(71,90,101),
   Enum.Material.Metal,true)
  piece(folder,"Hydraulic Lift Steel Post",Vector3.new(1.1,8,1.1),
   center*CFrame.new(x,4.5,-7),
   Color3.fromRGB(113,138,145),Enum.Material.Metal,true)
  piece(folder,"Garage Work Light",Vector3.new(2.6,.35,4),
   center*CFrame.new(x,8.4,-7),Color3.fromRGB(246,224,183),
   Enum.Material.Neon,false)
 end
 local display=ServerStorage:FindFirstChild("OfficialRacingCarVisual")
 if display then
  local official=display:Clone()
  official.Name="Official Racing Service Demo Car"
  official.Parent=folder
  official:PivotTo(center*CFrame.new(0,3.1,0)*CFrame.Angles(0,math.pi,0))
  for _,node in ipairs(official:GetDescendants()) do
   if node:IsA("LuaSourceContainer") then
    node:Destroy()
   elseif node:IsA("BasePart") then
    node.Anchored=true;node.CanTouch=false;node.CanCollide=false
    node.CanQuery=false
   end
  end
  local count=0
  for _,node in ipairs(official:GetDescendants()) do
   if node:IsA("MeshPart") then count+=1 end
  end
  folder:SetAttribute("OfficialDetailedCarMeshes",count)
 end
 local sign=piece(folder,"Auto Garage Service Sign",
  Vector3.new(15,4,.55),center*CFrame.new(0,8,12),
  Color3.fromRGB(33,55,67),Enum.Material.Metal,false)
 billboard(sign,"THE PIT STOP","INSPECT • REPAIR • EARN")
 local diagnostic=piece(folder,"Fault Diagnostic Tablet",
  Vector3.new(3.8,2.7,1.4),
  center*CFrame.new(-17,2,1),
  Color3.fromRGB(61,94,112),Enum.Material.Metal,false)
 billboard(diagnostic,"SCAN CAR","IDENTIFY CUSTOMER FAULT")
 prompt(diagnostic,"RUN DIAGNOSTIC","Vehicle Inspection",function(p)
  if handlers and handlers.process then
   handlers.process(p,"MechanicInspect")
  end
 end)
 stations.INSPECT=diagnostic
 local colors={
  BRAKES=Color3.fromRGB(174,90,83),
  BATTERY=Color3.fromRGB(80,146,176),
  TIRES=Color3.fromRGB(143,148,92),
 }
 for index,fault in ipairs(Faults) do
  local x= -13+(index-1)*13
  local work=piece(folder,"Repair Station "..fault,
   Vector3.new(7,2.5,3),center*CFrame.new(x,1,18),
   colors[fault],Enum.Material.Metal,true)
  billboard(work,fault.." REPAIR","USE WHEN DIAGNOSTIC MATCHES")
  prompt(work,"REPAIR "..fault,fault.." REPAIR STATION",function(p)
   if handlers and handlers.process then
    handlers.process(p,"MechanicRepair",fault)
   end
  end)
  if fault=="TIRES" then
   for j=1,2 do
    local tire=piece(folder,"Realistic Garage Tire "..j,
     Vector3.new(2.2,.8,2.2),
     center*CFrame.new(x+2.1*(j-1),2.5,15)*
     CFrame.Angles(0,0,math.rad(90)),
     Color3.fromRGB(37,41,46),Enum.Material.Rubber,false)
    tire.Shape=Enum.PartType.Cylinder
   end
  elseif fault=="BATTERY" then
   piece(folder,"Replacement Automotive Battery",
    Vector3.new(2,1.5,1.25),
    center*CFrame.new(x,3.05,16),
    Color3.fromRGB(50,57,65),Enum.Material.SmoothPlastic,false)
  else
   piece(folder,"Brake Service Steel Rotor",
    Vector3.new(1.8,.35,1.8),
    center*CFrame.new(x,3.1,16)*CFrame.Angles(0,0,math.rad(90)),
    Color3.fromRGB(176,182,180),Enum.Material.Metal,false).Shape=
    Enum.PartType.Cylinder
  end
  stations[fault]=work
 end
 folder:SetAttribute("MechanicFaultTypes",#Faults)
 folder:SetAttribute("RequiresRealInspection",true)
 folder:SetAttribute("NoBackgroundLoops",true)
 return folder
end
function Mechanic.Assign(shift)
 if type(shift)~="table" then return nil end
 local fault=Faults[math.random(1,#Faults)]
 shift.mechanicFault=fault
 shift.mechanicScanned=false
 return fault
end
function Mechanic.Process(player,kind,arg,shift)
 if not handlers or not shift or shift.id~="MECHANIC" or
  type(shift.mechanicFault)~="string" then return false end
 local now=os.clock()
 if kind=="MechanicInspect" then
  if not near(player,stations.INSPECT,11) or shift.progress~=0 or
   now-shift.started<1.5 then return false end
  shift.progress=1;shift.taskAt=now;shift.mechanicScanned=true
  handlers.tell(player,"DIAGNOSIS: "..shift.mechanicFault..
   ". SELECT THE CORRECT REPAIR WORKBENCH!")
 elseif kind=="MechanicRepair" then
  if type(arg)~="string" or not stations[arg] or
   not near(player,stations[arg],10) or
   shift.progress~=1 or not shift.mechanicScanned then return false end
  if now-shift.taskAt<1.5 then
   handlers.tell(player,"REVIEW THE DIAGNOSTIC AND PREPARE YOUR TOOLS FIRST.")
   return false
  end
  if arg~=shift.mechanicFault then
   handlers.tell(player,"INCORRECT REPAIR. THE PROBLEM IS "..shift.mechanicFault..
    " • TRY THAT BENCH.")
   return false
  end
  shift.progress=2;shift.taskAt=now
  handlers.reward(player,18,6,0)
  handlers.tell(player,"REPAIR COMPLETE • +18 COIN TIP! RETURN TO THE MECHANIC WORKPLACE FOR WAGES.")
 else return false end
 handlers.sync(player)
 return true
end
return Mechanic
