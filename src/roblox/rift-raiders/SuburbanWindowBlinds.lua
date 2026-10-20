-- Operate original Suburban house blind slats, never imported Toolbox scripts.
-- Shared, session-only controls. Original slat CFrames are preserved.
local TweenService=game:GetService("TweenService")
local Blinds={}
local entries={}
local keys={}
local tweenInfo=TweenInfo.new(.42,Enum.EasingStyle.Quad,Enum.EasingDirection.InOut)

local function allowed(player,entry)
 if not player or not player.Parent or not entry or not entry.rod.Parent then return false end
 local character=player.Character
 local root=character and character:FindFirstChild("HumanoidRootPart")
 local humanoid=character and character:FindFirstChildOfClass("Humanoid")
 return root~=nil and humanoid~=nil and humanoid.Health>0
  and (root.Position-entry.rod.Position).Magnitude<=11
end

function Blinds.Build(town,options)
 options=options or {}
 table.clear(entries)
 table.clear(keys)
 local total=0
 for _,spec in ipairs({
  {"Suburban Single Story House","ONE"},
  {"Suburban Two Story House","TWO"},
 }) do
  local house=town:FindFirstChild(spec[1])
  if house then
   local windows={}
   for _,node in ipairs(house:GetDescendants()) do
    if node:IsA("Model") and node.Name=="Blinds" then
     local rod=node:FindFirstChild("Raise")
     local slatFolder=node:FindFirstChild("Blinds")
     local slats={}
     if slatFolder and slatFolder:IsA("Folder") then
      for _,part in ipairs(slatFolder:GetChildren()) do
       if part:IsA("BasePart") and tonumber(part.Name) then
        table.insert(slats,part)
       end
      end
     end
     if rod and rod:IsA("BasePart") and #slats>=5 then
      table.sort(slats,function(a,b) return a.Position.Y>b.Position.Y end)
      table.insert(windows,{model=node,rod=rod,slats=slats})
     end
    end
   end
   table.sort(windows,function(a,b)
    if math.abs(a.rod.Position.X-b.rod.Position.X)>.01 then
     return a.rod.Position.X<b.rod.Position.X
    end
    if math.abs(a.rod.Position.Z-b.rod.Position.Z)>.01 then
     return a.rod.Position.Z<b.rod.Position.Z
    end
    return a.rod.Position.Y<b.rod.Position.Y
   end)
   for index,window in ipairs(windows) do
    local key="HOUSE_"..spec[2].."_BLIND_"..index
    local original={}
    local raised={}
    local topY=window.slats[1].Position.Y
    for i,slat in ipairs(window.slats) do
     original[i]=slat.CFrame
     -- Compact the real original slats at the top, preserving orientation.
     raised[i]=slat.CFrame+Vector3.new(0,topY-slat.Position.Y-(i-1)*.10,0)
    end
    local prompt=Instance.new("ProximityPrompt")
    prompt.Name="Original Window Blind "..key
    prompt.ObjectText="Window blinds"
    prompt.ActionText="RAISE BLINDS"
    prompt.MaxActivationDistance=10
    prompt.HoldDuration=.25
    prompt.RequiresLineOfSight=false
    prompt.Parent=window.rod
    entries[key]={rod=window.rod,model=window.model,slats=window.slats,
     original=original,raisedPositions=raised,prompt=prompt,raised=false,lastChange=-math.huge}
    table.insert(keys,key)
    window.model:SetAttribute("OriginalWindowBlindKey",key)
    window.model:SetAttribute("OriginalBlindSlatCount",#window.slats)
    prompt.Triggered:Connect(function(player)
     Blinds.Toggle(player,key,options)
    end)
    total+=1
   end
   house:SetAttribute("FunctionalOriginalWindowBlinds",#windows)
  end
 end
 town:SetAttribute("InteractiveOriginalWindowBlinds",total)
 return total
end

function Blinds.List()
 local out={}
 for i,key in ipairs(keys) do out[i]=key end
 return out
end

function Blinds.Inspect(key)
 local entry=entries[key]
 if not entry then return nil end
 return {rod=entry.rod,model=entry.model,prompt=entry.prompt,
  firstSlat=entry.slats[1],lastSlat=entry.slats[#entry.slats],
  slats=#entry.slats,raised=entry.raised,
  originalCFrame=entry.original[#entry.slats],
  raisedCFrame=entry.raisedPositions[#entry.slats]}
end

function Blinds.Toggle(player,key,options)
 local entry=type(key)=="string" and entries[key]
 if not allowed(player,entry) then return false end
 local now=os.clock()
 if now-entry.lastChange<.65 then return false end
 entry.lastChange=now
 entry.raised=not entry.raised
 local targets=entry.raised and entry.raisedPositions or entry.original
 for i,slat in ipairs(entry.slats) do
  if slat.Parent then
   TweenService:Create(slat,tweenInfo,{CFrame=targets[i]}):Play()
  end
 end
 entry.model:SetAttribute("BlindsRaised",entry.raised)
 entry.prompt.ActionText=entry.raised and "LOWER BLINDS" or "RAISE BLINDS"
 if options and options.tell then
  options.tell(player,entry.raised and "WINDOW BLINDS RAISED" or "WINDOW BLINDS LOWERED")
 end
 return true
end
return Blinds
