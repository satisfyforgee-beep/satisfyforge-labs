-- v0.10 LIVING DOWNTOWN: R15 citizens and detailed moving traffic.
-- Uses Roblox's own R15 rig generation and the script-free official sedan visual.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local ServerStorage=game:GetService("ServerStorage")

local Population={}
local heartbeatConnection=nil
local citizens={}
local traffic={}

local skins={
 Color3.fromRGB(236,196,159),Color3.fromRGB(195,143,107),
 Color3.fromRGB(128,91,70),Color3.fromRGB(226,174,132),
 Color3.fromRGB(162,112,84),Color3.fromRGB(96,69,55),
}
local shirts={
 Color3.fromRGB(53,91,129),Color3.fromRGB(126,71,92),
 Color3.fromRGB(76,111,84),Color3.fromRGB(111,95,67),
 Color3.fromRGB(64,69,82),Color3.fromRGB(133,98,63),
}
local pants={
 Color3.fromRGB(38,43,52),Color3.fromRGB(54,56,61),
 Color3.fromRGB(42,53,65),Color3.fromRGB(57,49,45),
}
local names={"Alex","Jordan","Morgan","Taylor","Casey","Riley","Avery","Cameron"}
-- Public classic Roblox hair accessories verified in Studio. They cost the
-- player nothing and give the generated R15 citizens recognizable silhouettes.
local hairIds={"63690008","16630147","376548738"}
local dialogues={
 "I am heading to work. The Employment Center is near the front block.",
 "Motor Row is where people shop for vehicles. You still have to earn the coins.",
 "City Tech sells phones and creator gear if you want to build a following.",
 "The community pantry and public benches can help if your needs get low.",
 "Metro Realty handles apartments and homes once you have built up your career.",
 "City Commerce is where business owners collect their simulated revenue.",
 "Police patrol the district. High wanted heat can still get you arrested.",
 "There are more worlds outside downtown through the WORLD menu.",
}

local function safeDescription(index)
 local d=Instance.new("HumanoidDescription")
 local skin=skins[(index-1)%#skins+1]
 local top=shirts[(index-1)%#shirts+1]
 local bottom=pants[(index-1)%#pants+1]
 d.HeadColor=skin; d.LeftArmColor=skin; d.RightArmColor=skin
 d.TorsoColor=top; d.LeftLegColor=bottom; d.RightLegColor=bottom
 d.HeightScale=.96+(index%4)*.025
 d.WidthScale=.92+(index%3)*.035
 d.DepthScale=.94+(index%2)*.04
 d.HeadScale=.98; d.BodyTypeScale=.28; d.ProportionScale=.18
 d.HairAccessory=hairIds[(index-1)%#hairIds+1]
 return d
end

local function walkAnimation(humanoid)
 local animator=humanoid:FindFirstChildOfClass("Animator")
 if not animator then animator=Instance.new("Animator"); animator.Parent=humanoid end
 local animation=Instance.new("Animation")
 animation.Name="Downtown Walk Animation"
 animation.AnimationId="rbxassetid://507777826" -- Roblox R15 walk
 local ok,track=pcall(function() return animator:LoadAnimation(animation) end)
 if ok and track then
  track.Name="Downtown Walk"
  track.Looped=true
  track.Priority=Enum.AnimationPriority.Movement
  track:Play(.2,1,1)
  return track
 end
 animation:Destroy()
 return nil
end

local function citizen(parent,index,start,route,tellPlayer,world)
 local description=safeDescription(index)
 local ok,model=pcall(function()
  return Players:CreateHumanoidModelFromDescription(description,Enum.HumanoidRigType.R15)
 end)
 description:Destroy()
 if not ok or not model then return nil end
 model.Name="Downtown Citizen "..index
 model:SetAttribute("NPCType","R15Citizen")
 model:SetAttribute("CitizenName",names[(index-1)%#names+1])
 model:SetAttribute("Behavior","Walking")
 model:SetAttribute("RecoveryMode","RerouteWithoutTeleport")
 model:SetAttribute("WaypointRecoveryCount",0)
 model.Parent=parent
 local humanoid=model:FindFirstChildOfClass("Humanoid")
 local root=model:FindFirstChild("HumanoidRootPart")
 if not humanoid or not root then model:Destroy(); return nil end
 humanoid.DisplayDistanceType=Enum.HumanoidDisplayDistanceType.None
 humanoid.HealthDisplayType=Enum.HumanoidHealthDisplayType.AlwaysOff
 humanoid.WalkSpeed=7.4+(index%4)*.65
 humanoid.AutoRotate=true
 humanoid.BreakJointsOnDeath=false
 root.CanCollide=false
 local talkAnchor=model:FindFirstChild("UpperTorso") or model:FindFirstChild("Head")
 if talkAnchor then
  local talk=Instance.new("ProximityPrompt")
  talk.Name="Talk to Citizen"
  talk.ActionText="TALK"
  talk.ObjectText=model:GetAttribute("CitizenName")
  talk.HoldDuration=.25; talk.MaxActivationDistance=9
  talk.RequiresLineOfSight=false; talk.Parent=talkAnchor
  talk.Triggered:Connect(function(player)
   if tellPlayer then tellPlayer(player,model:GetAttribute("CitizenName")..": "..dialogues[index]) end
   if world then
    world:SetAttribute("DowntownConversations",(world:GetAttribute("DowntownConversations") or 0)+1)
   end
  end)
 end
 pcall(function() root:SetNetworkOwner(nil) end)
 model:PivotTo(CFrame.new(start+Vector3.new(0,3.2,0)))
 local track=walkAnimation(humanoid)
 local state={model=model,humanoid=humanoid,root=root,route=route,index=2,walkTrack=track}
 table.insert(citizens,state)
 task.spawn(function()
  while model.Parent and humanoid.Health>0 do
   local target=route[state.index]
   humanoid:MoveTo(target)
   local reached=humanoid.MoveToFinished:Wait()
   if model.Parent and humanoid.Health>0 then
    -- Physically teleporting a visible NPC to its next route point looked
    -- like broken physics. Reroute after a stall; never snap through walls.
    if not reached and (root.Position-target).Magnitude>24 then
     model:SetAttribute("WaypointRecoveryCount",
      (model:GetAttribute("WaypointRecoveryCount") or 0)+1)
    end
    state.index=state.index%#route+1
    task.wait(.35+(index%3)*.2)
   end
  end
 end)
 return model
end

local function makeTrafficSedan(parent,index,startIndex,route)
 local template=ServerStorage:FindFirstChild("OfficialSedanVisual")
 if not template then return nil end
 local m=template:Clone()
 m.Name="Downtown Traffic Sedan "..index
 m:SetAttribute("NPCType","DetailedTraffic")
 m:SetAttribute("VisualModel","Official Modern City Sedan")
 m:SetAttribute("DistanceTravelled",0)
 m.Parent=parent
 for _,node in ipairs(m:GetDescendants()) do
  if node:IsA("LuaSourceContainer") then
   node:Destroy()
  elseif node:IsA("BasePart") then
   node.Anchored=true; node.CanCollide=false; node.CanTouch=false
   node.CanQuery=false
  end
 end
 local pos=route[startIndex]
 local nextIndex=startIndex%#route+1
 local direction=(route[nextIndex]-pos).Unit
 -- Official white sedan headlights and front bumper are at local -Z.
 -- Rotating this by 180 degrees made traffic visibly drive in reverse.
 m:PivotTo(CFrame.lookAt(pos,pos+direction))
 -- The template pivot is not at the wheel contact patch. Ground the mesh
 -- against the actual ~1.1-stud downtown asphalt, not a hardcoded pivot Y.
 local box,dimensions=m:GetBoundingBox()
 local wheelBottom=box.Position.Y-dimensions.Y*.5
 local grounded=pos+Vector3.new(0,1.1-wheelBottom,0)
 m:PivotTo(CFrame.lookAt(grounded,grounded+direction))
 m:SetAttribute("GroundedRoadHeight",1.1)
 m:SetAttribute("ForwardFacingTraffic",true)
 m:SetAttribute("SteeringMode","ProgressiveYaw")
 m:SetAttribute("DynamicFacingChecked",false)
 local state={model=m,position=grounded,heading=direction,route=route,
  index=nextIndex,speed=18+index*1.5,distance=0,lastAttribute=0}
 table.insert(traffic,state)
 return m
end

function Population.Build(world,cityModel,options)
 options=options or {}
 if heartbeatConnection then heartbeatConnection:Disconnect(); heartbeatConnection=nil end
 citizens={}; traffic={}
 local old=world:FindFirstChild("Living Modern Downtown")
 if old then old:Destroy() end
 local folder=Instance.new("Folder")
 folder.Name="Living Modern Downtown"
 folder.Parent=world
 folder:SetAttribute("CitizenCount",8)
 folder:SetAttribute("TrafficCount",4)
 folder:SetAttribute("RigType","R15")
 folder:SetAttribute("TrafficVisual","Official Modern City Sedan")

 -- Two citizens cross the welcome block immediately so downtown feels alive
 -- from the first camera view instead of only at the far perimeter.
 local frontA=Vector3.new(-32,0,2238)
 local frontB=Vector3.new(32,0,2238)
 local rightA=Vector3.new(108,0,2260)
 local rightB=Vector3.new(108,0,2460)
 local backA=Vector3.new(85,0,2472)
 local backB=Vector3.new(-85,0,2472)
 local leftA=Vector3.new(-108,0,2460)
 local leftB=Vector3.new(-108,0,2260)
 local pedestrianRoutes={
  {frontA,frontB,frontA},
  {frontB,frontA,frontB},
  {rightA,rightB,rightA},
  {rightB,rightA,rightB},
  {backA,backB,backA},
  {backB,backA,backB},
  {leftA,leftB,leftA},
  {leftB,leftA,leftB},
 }
 world:SetAttribute("DowntownConversations",0)
 for i,route in ipairs(pedestrianRoutes) do
  citizen(folder,i,route[1],route,options.tell,world)
 end

 -- Keep the front traffic lane behind the third-person camera at spawn.
 -- This prevents a non-colliding sedan from visually passing through the camera.
 local roadRoute={
  Vector3.new(-128,4.5,2200),Vector3.new(128,4.5,2200),
  Vector3.new(128,4.5,2502),Vector3.new(-128,4.5,2502),
 }
 for i=1,4 do makeTrafficSedan(folder,i,i,roadRoute) end

 if cityModel then
  cityModel:SetAttribute("LivingDowntownIntegrated",true)
  cityModel:SetAttribute("DetailedCitizenCount",#citizens)
  cityModel:SetAttribute("DetailedTrafficCount",#traffic)
 end
 world:SetAttribute("DowntownTrafficDistance",0)
 local elapsed=0
 heartbeatConnection=RunService.Heartbeat:Connect(function(dt)
  if not world.Parent or not folder.Parent then return end
  elapsed+=dt
  if elapsed<.09 then return end
  local step=math.min(elapsed,.14); elapsed=0
  local totalDistance=0
  for _,car in ipairs(traffic) do
   local m=car.model
   if m and m.Parent then
    local routeGoal=car.route[car.index]
    local goal=Vector3.new(routeGoal.X,car.position.Y,routeGoal.Z)
    local delta=goal-car.position
    if delta.Magnitude<2.2 then
     car.index=car.index%#car.route+1
     routeGoal=car.route[car.index]
     goal=Vector3.new(routeGoal.X,car.position.Y,routeGoal.Z)
     delta=goal-car.position
    end
    if delta.Magnitude>.01 then
     local direction=delta.Unit
     -- Ease off the throttle while approaching an intersection corner,
     -- then blend the visual car yaw toward the new street direction.
     local cornerSlow=math.clamp(delta.Magnitude/18,.55,1)
     local amount=math.min(delta.Magnitude,car.speed*step*cornerSlow)
     car.position+=direction*amount
     car.distance+=amount
     local eased=car.heading:Lerp(direction,math.clamp(step*3.6,0,1))
     car.heading=eased.Magnitude>.01 and eased.Unit or direction
     -- CRITICAL: the sedan headlights are at local -Z. The old movement
     -- update mistakenly added CFrame.Angles(0,math.pi,0), reversing every
     -- sedan after spawn even though the initial orientation was correct.
     local cf=CFrame.lookAt(car.position,car.position+car.heading)
     m:PivotTo(cf)
     if car.distance-car.lastAttribute>=6 then
      car.lastAttribute=car.distance
      m:SetAttribute("DistanceTravelled",math.floor(car.distance))
      m:SetAttribute("DynamicFacingChecked",true)
      m:SetAttribute("ForwardTravelHeadingDot",
       math.floor(car.heading:Dot(direction)*100)/100)
     end
    end
    totalDistance+=car.distance
   end
  end
  world:SetAttribute("DowntownTrafficDistance",math.floor(totalDistance))
 end)
 return {folder=folder,citizens=#citizens,traffic=#traffic}
end

return Population
