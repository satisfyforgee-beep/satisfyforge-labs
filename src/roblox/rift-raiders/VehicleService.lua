-- Reusable, server-controlled arcade hovercar service.
-- VehicleSeat supplies keyboard/gamepad/touch throttle and steering.
local RunService=game:GetService("RunService")
local Players=game:GetService("Players")
local ServerStorage=game:GetService("ServerStorage")
local Kit=require(script.Parent:WaitForChild("WorldKit"))
local Expansion=require(script.Parent:WaitForChild("WorldExpansion"))
local LifeCatalog=require(game:GetService("ReplicatedStorage"):WaitForChild("LifeCatalog"))
local VehicleStyles=require(script.Parent:WaitForChild("VehicleStyles"))
local Cars={}
local active={}
local cooldown={}
local function permitted(v)
 if v.Y<2 or v.Y>40 then return false end
 local x,z=v.X,v.Z
 if math.abs(x)<52 and math.abs(z)<52 then return true end
 if math.abs(x)<155 and math.abs(z-1600)<115 then return true end
 if math.abs(x)<135 and math.abs(z-2350)<140 then return true end
 if math.abs(x)<190 and math.abs(z-2785)<125 then return true end
 if math.abs(x-180)<52 and math.abs(z)<52 then return true end
 if math.abs(x+180)<52 and math.abs(z)<52 then return true end
 if math.abs(z-180)<52 and math.abs(x)<52 then return true end
 if math.abs(z+180)<52 and math.abs(x)<52 then return true end
 for _,region in ipairs(Expansion.Worlds) do
  local c=region.center
  if math.abs(x-c.X)<68 and math.abs(z-c.Z)<68 then return true end
 end
 if math.abs(x)<129 and math.abs(z)<9 then return true end
 if math.abs(z)<129 and math.abs(x)<9 then return true end
 return false
end
function Cars.Spawn(world,player,kind)
 kind=kind or "car"
 local now=os.clock()
 if cooldown[player] and now-cooldown[player]<8 then return false,"WAIT BEFORE SPAWNING ANOTHER CAR" end
 local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
 if not root or not permitted(root.Position) then return false,"GO TO A SAFE ISLAND TO SPAWN A VEHICLE" end
 if kind=="snowmobile" and (root.Position-Vector3.new(0,root.Position.Y,-520)).Magnitude>75 then
  return false,"SNOWMOBILES ARE AVAILABLE IN SNOWBOUND NORTH!"
 end
 if kind~="car" and kind~="snowmobile" and kind~="flyingcar" and kind~="stolen" then
  return false,"UNKNOWN VEHICLE"
 end
 if kind=="snowmobile" and player:GetAttribute("RROwn_SNOWMOBILE_LICENSE")~=true then
  return false,"EARN THE SNOWMOBILE LICENSE IN THE COIN SHOP FIRST!"
 end
 if kind=="flyingcar" and player:GetAttribute("RROwn_FLIGHT_LICENSE")~=true then
  return false,"EARN THE FLYING CAR LICENSE IN THE COIN SHOP FIRST!"
 end
 cooldown[player]=now
 local previous=active[player]
 if previous and previous.model then previous.model:Destroy() end
 local direction=root.CFrame.LookVector
 local spot=root.Position+direction*17
 if not permitted(spot) then spot=root.Position end
 local cf=CFrame.lookAt(Vector3.new(spot.X,5,spot.Z),
  Vector3.new(spot.X+direction.X,5,spot.Z+direction.Z))
 local m,seat
 local stats
 if kind=="snowmobile" then
  m,seat=Expansion.Prefabs.Snowmobile(world,Vector3.new(spot.X,2,spot.Z),true)
 else
  local tier=player:GetAttribute("RRLifeCarTier")
  local wrap=player:GetAttribute("RRActiveVehicleWrap")
  local ownedPaint=wrap=="PLATINUM" and Color3.fromRGB(205,216,231) or
   wrap=="MIDNIGHT" and Color3.fromRGB(28,36,59) or
   Color3.fromRGB(74,215,245)
  if tier=="SPORTS" then ownedPaint=Color3.fromRGB(222,76,83)
  elseif tier=="SEDAN" then ownedPaint=Color3.fromRGB(111,146,164) end
  m,seat=Kit.Car(world,cf,
   kind=="flyingcar" and Color3.fromRGB(196,94,252) or
   kind=="stolen" and Color3.fromRGB(48,54,69) or ownedPaint,true)
  local choice=kind=="car" and player:GetAttribute("RRLifeSelectedCar") or nil
  stats=choice and LifeCatalog.CarChoices[choice] or nil
  if stats and player:GetAttribute("RRLifeOwn_"..choice)~=true then
   stats=nil;choice=nil
  end
  -- Roblox's own Modern City sedan model replaces the visible primitive car.
  -- We keep the existing server-controlled seat and invisible collision shell
  -- so players cannot gain control by injecting local physics or scripts.
  if kind=="car" or kind=="stolen" then
   local custom=stats and stats.model=="CUSTOM"
   local modelName=stats and stats.model=="RACING" and
    "OfficialRacingCarVisual" or stats and stats.model=="RED" and
    "OfficialRedSedanVisual" or "OfficialSedanVisual"
   local template=custom and nil or ServerStorage:FindFirstChild(modelName)
   if template or custom then
    for _,node in ipairs(m:GetChildren()) do
     if node:IsA("BasePart") and node~=seat then
      node.Transparency=1
      node.CastShadow=false
     end
    end
    if custom then
     local original=VehicleStyles.Build(m,cf,choice)
     if not original then
      warn("Missing custom vehicle shape",choice)
     else
      m:SetAttribute("VisualModel",original:GetAttribute("Silhouette"))
      m:SetAttribute("DetailedPaint","CUSTOM")
      m:SetAttribute("SelectedVehicle",choice)
     end
    else
     local visual=template:Clone()
     visual.Name=modelName=="OfficialRacingCarVisual" and
      "Official Detailed Racing Car Body" or "Official Detailed Sedan Body"
     visual.Parent=m
     for _,node in ipairs(visual:GetDescendants()) do
      if node:IsA("Seat") or node:IsA("VehicleSeat") then
       node:Destroy()
      elseif node:IsA("BasePart") then
       node.Anchored=true; node.CanCollide=false; node.CanTouch=false
       node.CanQuery=false
      elseif node:IsA("LuaSourceContainer") then
       node:Destroy()
      end
     end
     -- Use the actual bumper/headlamp positions to resolve imported model
     -- pivots rather than guessing local +X/-Z orientation or applying 180
     -- degrees to every template. The red Sedan source has a different pivot.
     visual:PivotTo(cf)
     local front=visual:FindFirstChild("bumper_front",true) or
      visual:FindFirstChild("Race Art bumper",true)
     local back=visual:FindFirstChild("bumper_back",true) or
      visual:FindFirstChild("Race Art taillights",true)
     if front and back then
      local actual=front.Position-back.Position
      local desired=cf.LookVector
      local a=Vector3.new(actual.X,0,actual.Z)
      local b=Vector3.new(desired.X,0,desired.Z)
      if a.Magnitude>.1 and b.Magnitude>.1 then
       a=a.Unit;b=b.Unit
       local yaw=math.atan2(a.Z*b.X-a.X*b.Z,a.X*b.X+a.Z*b.Z)
       visual:PivotTo(cf*CFrame.Angles(0,yaw,0))
       visual:SetAttribute("VerifiedFrontAligned",true)
      end
     end
     local visualBox,visualSize=visual:GetBoundingBox()
     local oldBottom=visualBox.Position.Y-visualSize.Y*.5
     local wheelContactY=cf.Position.Y-3.3 -- original Kit.Car wheel height
     visual:PivotTo(visual:GetPivot()+
      Vector3.new(0,wheelContactY-oldBottom,0))
     visual:SetAttribute("VehicleFrontMatchesThrottle",true)
     visual:SetAttribute("WheelsGroundedToChassis",true)
     m:SetAttribute("VisualModel",modelName=="OfficialRacingCarVisual" and
      "Official 29-mesh Racing Car" or "Official Modern City Sedan")
     m:SetAttribute("DetailedPaint",modelName=="OfficialRacingCarVisual" and "RACING" or
      modelName=="OfficialRedSedanVisual" and "RED" or "WHITE")
     m:SetAttribute("SelectedVehicle",choice or "STARTER")
    end
   end
  end
  if kind=="stolen" then m.Name="Mission Getaway Car" end
  if kind=="flyingcar" then
   m.Name="Player Flying Car"
   for _,x in ipairs({-3.5,3.5}) do
    local jet=Instance.new("Part"); jet.Name="Anti-Gravity Thruster"
    jet.Size=Vector3.new(2,1,4)
    jet.CFrame=cf*CFrame.new(x,-2,0)
    jet.Color=Color3.fromRGB(119,246,255); jet.Material=Enum.Material.Neon
    jet.Anchored=true; jet.CanCollide=false; jet.CanTouch=false; jet.Parent=m
   end
  end
 end
 m:SetAttribute("OwnerUserId",player.UserId)
 local speedLimit=kind=="car" and stats and stats.speed or 34
 m:SetAttribute("TopSpeed",speedLimit)
 active[player]={model=m,seat=seat,owner=player,lastOccupied=now,
  speed=0,kind=kind,topSpeed=speedLimit}
 return true,(kind=="snowmobile" and "SNOWMOBILE" or
  kind=="flyingcar" and "FLYING CAR" or
  kind=="stolen" and "MISSION GETAWAY CAR" or "HOVERCAR")..
  " SPAWNED! SIT IN THE DRIVER SEAT TO DRIVE."
end
function Cars.HasActive(player,kind)
 local car=active[player]
 return car~=nil and car.kind==kind and car.model~=nil and car.model.Parent~=nil
  and car.model:GetPivot().Position or nil
end
local elapsed=0
RunService.Heartbeat:Connect(function(dt)
 elapsed+=dt
 if elapsed<.06 then return end
 local step=math.min(elapsed,.12); elapsed=0
 for owner,car in pairs(active) do
  local m,seat=car.model,car.seat
  if not owner.Parent or not m.Parent then
   if m.Parent then m:Destroy() end
   active[owner]=nil
  else
   local hum=seat.Occupant
   local driver=hum and Players:GetPlayerFromCharacter(hum.Parent)
   if driver==owner and hum.Health>0 then
    car.lastOccupied=os.clock()
    local throttle=math.clamp(seat.ThrottleFloat,-1,1)
    local steer=math.clamp(seat.SteerFloat,-1,1)
    car.speed+=(throttle*(car.topSpeed or 34)-car.speed)*math.min(1,step*3)
    if math.abs(throttle)<.03 then car.speed*=math.max(0,1-step*2) end
    local current=m:GetPivot()
    local yaw=-steer*step*1.7*math.clamp(math.abs(car.speed)/20,.25,1)
    local turn=current*CFrame.Angles(0,yaw,0)
    local displacement=turn.LookVector*car.speed*step
    local climb=car.kind=="flyingcar" and math.clamp(21-current.Position.Y,-step*12,step*12) or 0
    local target=turn+Vector3.new(displacement.X,climb,displacement.Z)
    if permitted(target.Position) then
     m:PivotTo(target)
    else
     car.speed=0
    end
   elseif driver and driver~=owner then
    -- Other players cannot remotely take over someone else's paid personal car.
    hum.Sit=false
    car.speed=0
   elseif os.clock()-car.lastOccupied>240 then
    m:Destroy(); active[owner]=nil
   end
  end
 end
end)
Players.PlayerRemoving:Connect(function(p)
 local car=active[p]
 if car and car.model then car.model:Destroy() end
 active[p]=nil; cooldown[p]=nil
end)
return Cars
