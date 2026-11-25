-- v0.30: functional original room lighting without importing foreign scripts.
-- The furnished Suburban demo houses are communal showcase spaces, not
-- claimed/privately owned plots. Lighting changes affect all nearby players.
local Rooms={}
local registry={}
local keys={}

local function allowed(player,entry)
 if not entry or not player or not player.Parent or not entry.fixture.Parent then
  return false
 end
 local char=player.Character
 local root=char and char:FindFirstChild("HumanoidRootPart")
 local hum=char and char:FindFirstChildOfClass("Humanoid")
 return root~=nil and hum~=nil and hum.Health>0
  and (root.Position-entry.fixture.Position).Magnitude<=12
end

local function display(name)
 return name:gsub("Lights$",""):gsub("([a-z])([A-Z])","%1 %2")
end

function Rooms.Build(town,options)
 options=options or {}
 table.clear(registry)
 table.clear(keys)
 local count=0
 for _,spec in ipairs({
  {"Suburban Single Story House","ONE"},
  {"Suburban Two Story House","TWO"},
 }) do
  local house=town:FindFirstChild(spec[1])
  if house then
   local groups={}
   for _,node in ipairs(house:GetDescendants()) do
    if node:IsA("Folder") and node.Name~="Lights"
     and node.Name:sub(-6)=="Lights" then
     local lights={}
     for _,child in ipairs(node:GetDescendants()) do
      if child:IsA("PointLight") or child:IsA("SpotLight") or
       child:IsA("SurfaceLight") then
       table.insert(lights,child)
      end
     end
     if #lights>0 then
      local fixture=lights[1].Parent
      if fixture and fixture:IsA("BasePart") then
       table.insert(groups,{folder=node,lights=lights,fixture=fixture})
      end
     end
    end
   end
   table.sort(groups,function(a,b)
    return a.fixture:GetFullName()<b.fixture:GetFullName()
   end)
   for i,group in ipairs(groups) do
    local key="HOUSE_"..spec[2].."_ROOM_"..i
    local fixture=group.fixture
    local label=display(group.folder.Name)
    local prompt=Instance.new("ProximityPrompt")
    prompt.Name="Original Room Light Toggle "..key
    prompt.ActionText="TOGGLE LIGHTS"
    prompt.ObjectText=label
    prompt.MaxActivationDistance=11
    prompt.HoldDuration=.25
    prompt.RequiresLineOfSight=false
    prompt.Parent=fixture
    local entry={
     house=house,fixture=fixture,
     lights=group.lights,room=label,prompt=prompt,
     lastChange=0
    }
    registry[key]=entry
    table.insert(keys,key)
    fixture:SetAttribute("OriginalHouseLightKey",key)
    fixture:SetAttribute("OriginalRoomLightCount",#entry.lights)
    group.folder:SetAttribute("WorkingRoomLightControls",true)
    prompt.Triggered:Connect(function(player)
     Rooms.Toggle(player,key,options)
    end)
    count+=1
   end
   house:SetAttribute("FunctionalOriginalRoomLightGroups",#groups)
  end
 end
 town:SetAttribute("InteractiveFurnishedRoomLightGroups",count)
 return count
end

function Rooms.List()
 local out={}
 for i,key in ipairs(keys) do out[i]=key end
 return out
end

function Rooms.Inspect(key)
 local entry=registry[key]
 if not entry then return nil end
 return {
  room=entry.room,
  fixture=entry.fixture,
  house=entry.house,
  lights=#entry.lights,
  firstLight=entry.lights[1],
  prompt=entry.prompt
 }
end

function Rooms.Toggle(player,key,options)
 local entry=type(key)=="string" and registry[key]
 if not allowed(player,entry) then return false end
 local now=os.clock()
 if now-entry.lastChange<.4 then return false end
 entry.lastChange=now
 local state=not entry.lights[1].Enabled
 for _,light in ipairs(entry.lights) do
  if light.Parent then light.Enabled=state end
 end
 entry.fixture:SetAttribute("OriginalRoomLightsOn",state)
 entry.prompt.ActionText=state and "TURN LIGHTS OFF" or "TURN LIGHTS ON"
 if options and options.tell then
  options.tell(player,entry.room:upper()..
   (state and " LIGHTS ON" or " LIGHTS OFF"))
 end
 return true
end
return Rooms
