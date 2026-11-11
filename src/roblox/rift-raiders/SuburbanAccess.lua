-- Rift Raiders v0.26: real access to original imported, detailed suburban
-- interiors. Original toolbox scripts stay stripped. Entrances are managed
-- exclusively on the server and opened permanently for the current session,
-- preventing a moving door from closing on a visitor.
local TweenService=game:GetService("TweenService")
local Access={}
local entries={}
local unlocked=0
local serviceOptions

local function permitted(player,entry)
 if not player or not entry or not entry.anchor or
  not entry.anchor.Parent or not player.Parent then return false end
 local character=player.Character
 local root=character and character:FindFirstChild("HumanoidRootPart")
 local humanoid=character and character:FindFirstChildOfClass("Humanoid")
 return root and humanoid and humanoid.Health>0 and
  (root.Position-entry.anchor.Position).Magnitude<=12
end

local function sign(parent,text)
 local gui=Instance.new("BillboardGui")
 gui.Name="Accessible Door Sign"
 gui.Size=UDim2.fromOffset(160,47)
 gui.StudsOffsetWorldSpace=Vector3.new(0,3.6,0)
 gui.MaxDistance=55
 gui.AlwaysOnTop=false
 gui.Parent=parent
 local label=Instance.new("TextLabel")
 label.Size=UDim2.fromScale(1,1)
 label.TextWrapped=true;label.TextSize=12
 label.Font=Enum.Font.GothamBold
 label.BackgroundColor3=Color3.fromRGB(39,61,69)
 label.BackgroundTransparency=.08
 label.TextColor3=Color3.fromRGB(253,237,195)
 label.Text=text.."\nOPEN TO THE PUBLIC"
 label.Parent=gui
 return label
end

local function attachDoor(building,key,door,name,kind)

 if not door or not door:IsA("Model") then
  warn("Cannot wire official suburban doorway",key)
  return false
 end
 local base=door:FindFirstChild("Base",true)
 if not base or not base:IsA("BasePart") then
  warn("No original imported door base",key)
  return false
 end
 local anchor=Instance.new("Part")
 anchor.Name="Accessible "..name.." Entrance"
 anchor.Size=Vector3.new(.3,.3,.3)
 anchor.CFrame=base.CFrame
 anchor.Anchored=true;anchor.Transparency=1
 anchor.CanCollide=false;anchor.CanTouch=false;anchor.CanQuery=false
 anchor.Parent=building

 local prompt=Instance.new("ProximityPrompt")
 prompt.Name="Open Original Building "..key
 prompt.ObjectText=name
 prompt.ActionText="OPEN DOOR"
 prompt.HoldDuration=.35
 prompt.MaxActivationDistance=10
 prompt.RequiresLineOfSight=false
 prompt.Parent=anchor

 local doorFrame,extents=door:GetBoundingBox()
 local delta
 if kind=="BAY" then
  delta=Vector3.new(0,11,0)
 elseif extents.X>extents.Z then
  delta=Vector3.new(extents.X+1.5,0,0)
 else
  delta=Vector3.new(0,0,extents.Z+1.5)
 end
 entries[key]={
  anchor=anchor,door=door,building=building,delta=delta,
  name=name,kind=kind,open=false,parts={}
 }
 local entry=entries[key]
 for _,obj in ipairs(door:GetDescendants()) do
  if obj:IsA("BasePart") then
   obj.Anchored=true
   table.insert(entry.parts,obj)
  end
 end
 entry.initialCF=base.CFrame
 entry.initialPosition=base.Position
 entry.threshold=doorFrame.Position
 entry.boundingWidth=kind=="BAY" and extents.X or math.max(extents.X,extents.Z)
 anchor:SetAttribute("DoorAccessKey",key)
 anchor:SetAttribute("PhysicalDoorway",true)
 anchor:SetAttribute("OpeningPanelCount",#entry.parts)
 door:SetAttribute("RestoredSecureEntry",true)
 building:SetAttribute("HasServerOperatedEntry",true)
 sign(anchor,name:upper())
 prompt.Triggered:Connect(function(player)
  Access.Open(player,key)
 end)
 return true
end

local function add(building,key,doorName,name,kind)
 local container=building:FindFirstChild(doorName,true)
 local door=container and container:FindFirstChild("Door")
 return attachDoor(building,key,door,name,kind)
end

function Access.Open(player,key)
 local entry=type(key)=="string" and entries[key]
 if not permitted(player,entry) then return false end
 if entry.open then
  if serviceOptions and serviceOptions.tell then
   serviceOptions.tell(player,entry.name:upper().." IS ALREADY OPEN. WALK INSIDE!")
  end
  return true
 end
 entry.open=true
 entry.anchor:SetAttribute("IsOpen",true)
 entry.door:SetAttribute("IsOpen",true)
 entry.building:SetAttribute("OpenedAccessibleEntrance",true)
 unlocked+=1
 local tweens={}
 for _,obj in ipairs(entry.parts) do
  if obj.Parent then
   local target=obj.CFrame+entry.delta
   obj.CanCollide=false
   obj.CanTouch=false
   obj.CanQuery=false
   local tween=TweenService:Create(obj,
    TweenInfo.new(.65,Enum.EasingStyle.Quint,Enum.EasingDirection.Out),
    {CFrame=target})
   table.insert(tweens,tween)
  end
 end
 for _,tween in ipairs(tweens) do tween:Play() end
 local prompt=entry.anchor:FindFirstChildOfClass("ProximityPrompt")
 if prompt then prompt.ActionText="DOOR OPEN" end
 if serviceOptions and serviceOptions.tell then
  serviceOptions.tell(player,entry.name:upper()..
   " UNLOCKED • WALK THROUGH THE ACTUAL IMPORTED ENTRANCE!")
 end
 return true
end
function Access.Inspect(key)
 local e=entries[key]
 if not e then return nil end
 return {
  key=key,position=e.anchor.Position,name=e.name,
  threshold=e.threshold,
  opened=e.open,pieces=#e.parts,delta=e.delta,
  door=e.door,anchor=e.anchor,building=e.building,
  firstPanel=e.parts[1],originalPanelCF=e.initialCF
 }
end
function Access.Count()
 local count=0
 for _ in pairs(entries) do count+=1 end
 return count,unlocked
end
function Access.Build(folder,options)
 serviceOptions=options or {}
 table.clear(entries);unlocked=0
 local registered=0
 local function addFor(buildingName,key,doorName,name,kind)
  local b=folder:FindFirstChild(buildingName)
  if b and add(b,key,doorName,name,kind) then registered+=1 end
 end
 addFor("Suburban Single Story House","HOUSE_ONE",
  "Front Doorway","Single Story Home","SWING")
 addFor("Suburban Two Story House","HOUSE_TWO",
  "Front Doorway","Two Story Home","SWING")
 addFor("Suburban Convenience Market","MARKET",
  "Doorway","Convenience Market","SWING")
 addFor("Suburban Detailed Garage","GARAGE_PEDESTRIAN",
  "Doorway","Auto Garage Side Door","SWING")
 local garage=folder:FindFirstChild("Suburban Detailed Garage")
 if garage then
  local bays={}
  for _,desc in ipairs(garage:GetDescendants()) do
   if desc:IsA("Folder") and desc.Name=="PhysicsGarageDoor" and
    desc:FindFirstChild("Door") then
    table.insert(bays,desc)
   end
  end
  table.sort(bays,function(a,b)
   return a.Door:GetPivot().Position.X<b.Door:GetPivot().Position.X
  end)
  for i,bay in ipairs(bays) do
   local key="GARAGE_BAY_"..i
   local node=bay:FindFirstChild("Door")
   local base=node and node:FindFirstChild("Base",true)
   if base and attachDoor(garage,key,node,"Garage Bay "..i,"BAY") then
    registered+=1
   end
  end
 end
 folder:SetAttribute("RestoredSuburbanEntrances",registered)
 folder:SetAttribute("SuburbanDoorController","ServerProximity")
 return registered
end
return Access
