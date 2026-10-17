-- Reusable, server-controlled arcade hovercar service.
-- VehicleSeat supplies keyboard/gamepad/touch throttle and steering.
local RunService=game:GetService("RunService")
local Players=game:GetService("Players")
local Kit=require(script.Parent:WaitForChild("WorldKit"))
local Cars={}
local active={}
local cooldown={}
local function permitted(v)
 if v.Y<2 or v.Y>40 then return false end
 local x,z=v.X,v.Z
 if math.abs(x)<52 and math.abs(z)<52 then return true end
 if math.abs(x-180)<52 and math.abs(z)<52 then return true end
 if math.abs(x+180)<52 and math.abs(z)<52 then return true end
 if math.abs(z-180)<52 and math.abs(x)<52 then return true end
 if math.abs(z+180)<52 and math.abs(x)<52 then return true end
 if math.abs(x)<129 and math.abs(z)<9 then return true end
 if math.abs(z)<129 and math.abs(x)<9 then return true end
 return false
end
function Cars.Spawn(world,player)
 local now=os.clock()
 if cooldown[player] and now-cooldown[player]<8 then return false,"WAIT BEFORE SPAWNING ANOTHER CAR" end
 local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
 if not root or not permitted(root.Position) then return false,"GO TO A SAFE ISLAND TO SPAWN A CAR" end
 cooldown[player]=now
 local previous=active[player]
 if previous and previous.model then previous.model:Destroy() end
 local direction=root.CFrame.LookVector
 local spot=root.Position+direction*17
 if not permitted(spot) then spot=root.Position end
 local cf=CFrame.lookAt(Vector3.new(spot.X,5,spot.Z),
  Vector3.new(spot.X+direction.X,5,spot.Z+direction.Z))
 local m,seat=Kit.Car(world,cf,Color3.fromRGB(74,215,245),true)
 m:SetAttribute("OwnerUserId",player.UserId)
 active[player]={model=m,seat=seat,owner=player,lastOccupied=now,speed=0}
 return true,"HOVERCAR SPAWNED! SIT IN THE DRIVER SEAT TO DRIVE."
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
   if driver and hum.Health>0 then
    car.lastOccupied=os.clock()
    local throttle=math.clamp(seat.ThrottleFloat,-1,1)
    local steer=math.clamp(seat.SteerFloat,-1,1)
    car.speed+=(throttle*34-car.speed)*math.min(1,step*3)
    if math.abs(throttle)<.03 then car.speed*=math.max(0,1-step*2) end
    local current=m:GetPivot()
    local yaw=-steer*step*1.7*math.clamp(math.abs(car.speed)/20,.25,1)
    local turn=current*CFrame.Angles(0,yaw,0)
    local displacement=turn.LookVector*car.speed*step
    local target=turn+Vector3.new(displacement.X,0,displacement.Z)
    if permitted(target.Position) then
     m:PivotTo(target)
    else
     car.speed=0
    end
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
