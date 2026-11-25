-- Original lightweight world atmosphere and ambient NPC behavior.
-- NPCs are decorative route-following pedestrians/traffic, not full pathfinding AI.
local Lighting=game:GetService("Lighting")
local RunService=game:GetService("RunService")
local TweenService=game:GetService("TweenService")
local Terrain=workspace.Terrain
local Polish={}
local function piece(parent,name,size,cf,color,material,collide)
 local p=Instance.new("Part")
 p.Name=name; p.Size=size; p.CFrame=cf; p.Color=color
 p.Material=material or Enum.Material.SmoothPlastic
 p.Anchored=true; p.CanCollide=collide==true; p.CanTouch=false
 p.CastShadow=true; p.Parent=parent
 return p
end
local function pedestrian(parent,id,center,waypoints)
 local colors={
  Color3.fromRGB(72,130,180),Color3.fromRGB(198,116,73),
  Color3.fromRGB(92,155,109),Color3.fromRGB(158,101,166),
  Color3.fromRGB(183,168,89),Color3.fromRGB(82,94,126)
 }
 local m=Instance.new("Model"); m.Name="Ambient Pedestrian "..id
 m:SetAttribute("NPCType","AmbientCitizen")
 m:SetAttribute("Behavior","Walking")
 m.Parent=parent
 local cf=CFrame.new(center+Vector3.new(0,3,0))
 local body=piece(m,"Torso",Vector3.new(2.1,3,1.2),cf,
  colors[(id-1)%#colors+1],Enum.Material.Fabric,false)
 m.PrimaryPart=body
 local skin=({Color3.fromRGB(219,170,131),Color3.fromRGB(124,91,69),
  Color3.fromRGB(178,123,95),Color3.fromRGB(236,200,161)})[(id-1)%4+1]
 piece(m,"Head",Vector3.new(1.6,1.6,1.6),cf*CFrame.new(0,2.3,0),
  skin,Enum.Material.SmoothPlastic,false).Shape=Enum.PartType.Ball
 piece(m,"Hair",Vector3.new(1.7,.45,1.65),cf*CFrame.new(0,3.05,0),
  Color3.fromRGB(40+id*11,34+id*8,35+id*7),Enum.Material.SmoothPlastic,false)
 local arms,legs={},{}
 for _,side in ipairs({-1,1}) do
  arms[side]=piece(m,"Arm",Vector3.new(.75,2.7,.85),
   cf*CFrame.new(side*1.5,0,0),skin,Enum.Material.SmoothPlastic,false)
  legs[side]=piece(m,"Leg",Vector3.new(.9,2.8,1),
   cf*CFrame.new(side*.56,-2.8,0),
   Color3.fromRGB(42,49,63),Enum.Material.Fabric,false)
 end
 local data={model=m,body=body,arms=arms,legs=legs,waypoints=waypoints,
  next=2,position=waypoints[1],wait=0,speed=5.5+(id%4),
  distance=0,seed=id*1.2}
 return data
end
function Polish.Build(world,kit)
 local folder=Instance.new("Folder"); folder.Name="Living World Atmosphere"
 folder.Parent=world
 local clouds=Terrain:FindFirstChildOfClass("Clouds")
 if not clouds then clouds=Instance.new("Clouds"); clouds.Parent=Terrain end
 clouds.Name="Dynamic Weather Clouds"; clouds.Cover=.25
 clouds.Density=.42; clouds.Color=Color3.fromRGB(240,241,250)
 local atmosphere=Lighting:FindFirstChildOfClass("Atmosphere")
 if not atmosphere then atmosphere=Instance.new("Atmosphere"); atmosphere.Parent=Lighting end
 atmosphere.Density=.19; atmosphere.Offset=.1; atmosphere.Haze=1.3
 atmosphere.Glare=.18
 Lighting.GlobalShadows=true
 Lighting.Brightness=2.3
 Lighting.EnvironmentDiffuseScale=.5
 Lighting.EnvironmentSpecularScale=.6
 Lighting.ExposureCompensation=-.1
 pcall(function() Lighting.LightingStyle=Enum.LightingStyle.Realistic end)
 local grading=Lighting:FindFirstChild("RiftNaturalColorGrade")
 if not grading then
  grading=Instance.new("ColorCorrectionEffect"); grading.Name="RiftNaturalColorGrade"
  grading.Parent=Lighting
 end
 grading.Brightness=.015; grading.Contrast=.08
 grading.Saturation=-.04; grading.TintColor=Color3.fromRGB(251,248,241)
 local rays=Lighting:FindFirstChild("RiftSunRays")
 if not rays then
  rays=Instance.new("SunRaysEffect"); rays.Name="RiftSunRays"; rays.Parent=Lighting
 end
 rays.Intensity=.055; rays.Spread=.75
 local people={}
 for i=1,6 do
  local c=Vector3.new(180,0,0)
  local x=-32+((i-1)%3)*32
  local z=(i<=3 and 22 or -20)
  local a=c+Vector3.new(x,0,z)
  local b=c+Vector3.new(x+11,0,z)
  local d=c+Vector3.new(x+11,0,z+7)
  table.insert(people,pedestrian(folder,i,a,{a,b,d,a}))
 end
 for i=1,4 do
  local c=Vector3.new(0,0,1260)
  local x=-125+(i-1)*80
  local a=c+Vector3.new(x,0,-6)
  local b=c+Vector3.new(x+32,0,-6)
  table.insert(people,pedestrian(folder,i+6,a,{a,b,a}))
 end
 -- Life City citizens move between storefronts, workplaces and the public plaza.
 for i=1,8 do
  local x=-135+(i-1)*36
  local start=Vector3.new(x,3,1566)
  local store=Vector3.new(x+8,3,1546)
  local plaza=Vector3.new(x+16,3,1608)
  local work=Vector3.new(x+4,3,1662)
  table.insert(people,pedestrian(folder,i+10,start,
   {start,store,plaza,work,plaza,start}))
 end
 local traffic={}
 local roadCenter=Vector3.new(180,2.3,0)
 for _,z in ipairs({-39,39}) do
  piece(folder,"City Ring Road",Vector3.new(92,.6,12),
   CFrame.new(roadCenter+Vector3.new(0,0,z)),
   Color3.fromRGB(52,57,65),Enum.Material.Asphalt,true)
 end
 for _,x in ipairs({-39,39}) do
  piece(folder,"City Ring Road",Vector3.new(12,.6,88),
   CFrame.new(roadCenter+Vector3.new(x,0,0)),
   Color3.fromRGB(52,57,65),Enum.Material.Asphalt,true)
 end
 for i=1,2 do
  local c=Vector3.new(180,0,0)
  local waypoints={
   c+Vector3.new(-39,5,-39),c+Vector3.new(39,5,-39),
   c+Vector3.new(39,5,39),c+Vector3.new(-39,5,39)
  }
  local start=i==1 and 1 or 3
  local car=kit.Car(folder,CFrame.new(waypoints[start]),
   i==1 and Color3.fromRGB(135,150,161) or Color3.fromRGB(189,98,77),false)
  car.Name="Ambient City Traffic "..i
  car:SetAttribute("NPCType","Traffic")
  for _,desc in ipairs(car:GetDescendants()) do
   if desc:IsA("BasePart") then desc.CanCollide=false; desc.CanTouch=false end
  end
  table.insert(traffic,{model=car,waypoints=waypoints,next=start%4+1,
   position=waypoints[start],speed=14+i*3,wait=0})
 end
 -- Two more lightweight NPC cars drive the Life City boulevard.
 for i=1,2 do
  local start=Vector3.new(i==1 and -135 or 135,5,1600+(i==1 and -4 or 4))
  local finish=Vector3.new(i==1 and 135 or -135,5,1600+(i==1 and -4 or 4))
  local car=kit.Car(folder,CFrame.new(start),
   i==1 and Color3.fromRGB(71,102,122) or Color3.fromRGB(176,140,105),false)
  car.Name="Life City Traffic "..i
  car:SetAttribute("NPCType","Traffic")
  for _,desc in ipairs(car:GetDescendants()) do
   if desc:IsA("BasePart") then desc.CanCollide=false; desc.CanTouch=false end
  end
  table.insert(traffic,{model=car,waypoints={start,finish},next=2,
   position=start,speed=11+i*2,wait=0})
 end
 local weatherStates={"CLEAR","CLOUDY","RAIN","MIST"}
 local weatherIndex=1
 world:SetAttribute("Weather",weatherStates[weatherIndex])
 world:SetAttribute("TimeOfDay","DAY")
 local function setWeather(index)
  local state=weatherStates[index]
  world:SetAttribute("Weather",state)
  local cover=state=="CLEAR" and .18 or state=="CLOUDY" and .57
   or state=="RAIN" and .85 or .7
  local density=state=="MIST" and .38 or state=="RAIN" and .27 or .19
  TweenService:Create(clouds,TweenInfo.new(5),{Cover=cover}):Play()
  TweenService:Create(atmosphere,TweenInfo.new(5),{
   Density=density,Haze=state=="MIST" and 2.9 or 1.3
  }):Play()
  TweenService:Create(grading,TweenInfo.new(5),{
   Saturation=state=="RAIN" and -.22 or -.04,
   Brightness=state=="RAIN" and -.05 or .015
  }):Play()
 end
 task.spawn(function()
  while world.Parent do
   task.wait(115)
   weatherIndex=weatherIndex%#weatherStates+1
   setWeather(weatherIndex)
  end
 end)
 task.spawn(function()
  local time=8
  while world.Parent do
   task.wait(1)
   time=(time+.025)%24
   Lighting.ClockTime=time
   local night=time>=19 or time<6
   world:SetAttribute("TimeOfDay",night and "NIGHT" or "DAY")
   Lighting.OutdoorAmbient=night and Color3.fromRGB(52,68,92)
    or Color3.fromRGB(122,131,148)
  end
 end)
 local accumulator=0
 RunService.Heartbeat:Connect(function(dt)
  if not world.Parent then return end
  accumulator+=dt
  if accumulator<.14 then return end
  local step=math.min(accumulator,.2); accumulator=0
  local now=os.clock()
  for _,npc in ipairs(people) do
   if npc.wait>now then continue end
   local goal=npc.waypoints[npc.next]
   local delta=goal-npc.position
   if delta.Magnitude<1 then
    npc.wait=now+1+(npc.seed%3)
    npc.next=npc.next%#npc.waypoints+1
    npc.model:SetAttribute("Behavior","Waiting")
   else
    npc.model:SetAttribute("Behavior","Walking")
    local direction=delta.Unit
    npc.position+=direction*math.min(delta.Magnitude,step*npc.speed)
    local cf=CFrame.lookAt(npc.position+Vector3.new(0,3,0),
     npc.position+Vector3.new(0,3,0)+direction)
    npc.model:PivotTo(cf)
    local stride=math.sin(now*8+npc.seed)*.55
    for _,side in ipairs({-1,1}) do
     npc.arms[side].CFrame=cf*CFrame.new(side*1.5,0,0)*
      CFrame.Angles(side*stride,0,0)
     npc.legs[side].CFrame=cf*CFrame.new(side*.56,-2.8,0)*
      CFrame.Angles(-side*stride,0,0)
    end
   end
  end
  for _,car in ipairs(traffic) do
   if car.wait>now then continue end
   local goal=car.waypoints[car.next]
   local delta=goal-car.position
   if delta.Magnitude<1 then
    car.wait=now+1.2
    car.next=car.next%#car.waypoints+1
   else
    local direction=delta.Unit
    car.position+=direction*math.min(delta.Magnitude,car.speed*step)
    car.model:PivotTo(CFrame.lookAt(car.position,car.position+direction))
   end
  end
 end)
 return folder
end
return Polish
