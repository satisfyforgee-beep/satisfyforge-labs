local StudioTestService=game:GetService("StudioTestService")
local ServerScriptService=game:GetService("ServerScriptService")
local StarterPlayer=game:GetService("StarterPlayer")
print("SF_RIFT_MP_BEGIN")
local server=Instance.new("Script"); server.Name="RiftMultiplayerServerHarness"
server.Source=[==[
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local StudioTestService=game:GetService("StudioTestService")
local function waitFor(fn,seconds)
 local untilAt=os.clock()+seconds
 while os.clock()<untilAt do
  local ok,result=pcall(fn)
  if ok and result then return result end
  task.wait(.1)
 end
 return nil
end
local function fail(message)
 warn("SF_RIFT_MP_FAIL "..message)
 StudioTestService:EndTest("FAIL:"..message)
end
local clients=waitFor(function()
 local ps=Players:GetPlayers()
 if #ps>=2 and ps[1]:GetAttribute("RRLevel") and ps[2]:GetAttribute("RRLevel") then return ps end
end,45)
if not clients then fail("players_not_ready") return end
local a,b=clients[1],clients[2]
local channel=Instance.new("RemoteEvent"); channel.Name="RiftMPProbe"; channel.Parent=ReplicatedStorage
local acknowledgments={}
channel.OnServerEvent:Connect(function(p,id)
 acknowledgments[p]=acknowledgments[p] or {}
 acknowledgments[p][id]=true
end)
local function request(p,id,kind,arg,extra)
 channel:FireClient(p,id,kind,arg,extra)
 return waitFor(function() return acknowledgments[p] and acknowledgments[p][id] end,6)
end
local rootA=waitFor(function() return a.Character and a.Character:FindFirstChild("HumanoidRootPart") end,6)
local rootB=waitFor(function() return b.Character and b.Character:FindFirstChild("HumanoidRootPart") end,6)
if not rootA or not rootB then fail("character_missing") return end
if not request(a,"travel","Travel","CYBER") then fail("no_travel_ack") return end
if not waitFor(function() return (rootA.Position-Vector3.new(180,6,0)).Magnitude<12 end,4) then fail("travel_missing") return end
if (rootB.Position-Vector3.new(180,6,0)).Magnitude<20 then fail("cross_player_travel") return end
print("SF_RIFT_MP_CHECK travel_isolated PASS")
task.wait(2)
if not request(a,"bad","Travel","HACKED") then fail("no_bad_ack") return end
task.wait(.3)
if (rootA.Position-Vector3.new(180,6,0)).Magnitude>28 then fail("invalid_travel") return end
print("SF_RIFT_MP_CHECK travel_allowlist PASS")
if not request(a,"shop","Buy","PET") then fail("no_shop_ack") return end
task.wait(.3)
if a:GetAttribute("RRPet") or a:GetAttribute("RRCoins")~=0 then fail("free_pet") return end
print("SF_RIFT_MP_CHECK no_free_purchases PASS")
local world=workspace:WaitForChild("RiftRaidersWorld")
local rifle=waitFor(function()
 local pack=a:FindFirstChildOfClass("Backpack")
 return pack and pack:FindFirstChild("Pulse Rifle")
end,5)
if not rifle then fail("starter_weapon_missing") return end
if not request(a,"car","SpawnCar") then fail("spawn_car_no_ack") return end
local car=waitFor(function()
 for _,item in ipairs(world:GetChildren()) do
  if item.Name=="Player Hovercar" and item:GetAttribute("OwnerUserId")==a.UserId then return item end
 end
end,5)
if not car or not car:FindFirstChild("DriverSeat") then fail("drivable_car_missing") return end
local seat=car.DriverSeat
local humanoid=a.Character and a.Character:FindFirstChildOfClass("Humanoid")
if not humanoid then fail("car_humanoid_missing") return end
a.Character:PivotTo(CFrame.new(seat.Position+Vector3.new(0,3,0)))
seat:Sit(humanoid)
if not waitFor(function() return seat.Occupant==humanoid end,3) then fail("car_seat_not_usable") return end
local beforeCar=car:GetPivot().Position
seat.ThrottleFloat=1
task.wait(.55)
local moved=(car:GetPivot().Position-beforeCar).Magnitude
print("SF_RIFT_MP_CAR_DRIVE_DISTANCE "..string.format("%.2f",moved))
if moved<.4 then fail("car_did_not_move") return end
humanoid.Sit=false
car:Destroy()
task.wait(.4)
print("SF_RIFT_MP_CHECK player_car_and_seat PASS")
local shard=nil
for _,item in ipairs(world:GetChildren()) do
 if item.Name=="Rift Shard" and item:GetAttribute("Biome")=="CYBER" then shard=item; break end
end
if not shard then fail("shard_missing") return end
a.Character:PivotTo(CFrame.new(shard.Position))
if not waitFor(function() return (a:GetAttribute("RRShards") or 0)>=1 end,4) then fail("shard_not_collected") return end
if b:GetAttribute("RRShards")~=0 then fail("shared_shards") return end
local amount=a:GetAttribute("RRShards")
a.Character:PivotTo(CFrame.new(shard.Position+Vector3.new(0,10,0)))
task.wait(.3)
a.Character:PivotTo(CFrame.new(shard.Position))
task.wait(.5)
if a:GetAttribute("RRShards")~=amount then fail("shard_cooldown_bypass") return end
print("SF_RIFT_MP_CHECK shards_independent_and_cooldown PASS")
if not request(a,"blast","Blast") then fail("blast_no_ack") return end
print("SF_RIFT_MP_CHECK remote_blast_accepted PASS")
local drone=nil
for _,item in ipairs(world:GetChildren()) do
 if item.Name=="Rift Drone" and item:GetAttribute("Biome")=="CYBER" then drone=item; break end
end
if not drone then fail("drone_missing") return end
a.Character:PivotTo(CFrame.new(drone.Position+Vector3.new(0,0,14)))
task.wait(.2)
local aim=(drone.Position-(rootA.Position+Vector3.new(0,1.8,0))).Unit
if not request(a,"gun","Shoot",aim,"Pulse Rifle") then fail("shoot_no_ack") return end
if not waitFor(function() return (drone:GetAttribute("Health") or 3)<3 end,3) then fail("gun_no_damage") return end
print("SF_RIFT_MP_CHECK server_ray_weapon PASS")
print("SF_RIFT_MP_SERVER_PASS players=2")
StudioTestService:EndTest("PASS:rift_multiplayer")
]==]
server.Parent=ServerScriptService
local client=Instance.new("LocalScript"); client.Name="RiftMultiplayerClientHarness"
client.Source=[==[
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local channel=ReplicatedStorage:WaitForChild("RiftMPProbe",20)
local action=ReplicatedStorage:WaitForChild("RiftRaidersAction",20)
channel.OnClientEvent:Connect(function(id,kind,arg,extra)
 action:FireServer(kind,arg,extra)
 task.wait(.15)
 channel:FireServer(id)
end)
]==]
client.Parent=StarterPlayer:WaitForChild("StarterPlayerScripts")
local ok,result=pcall(function()
 return StudioTestService:ExecuteMultiplayerTestAsync(2,"rift-multiplayer")
end)
print("SF_RIFT_MP_RESULT ok="..tostring(ok).." result="..tostring(result))
if not ok or result~="PASS:rift_multiplayer" then error("rift multiplayer test failed: "..tostring(result)) end
print("SF_RIFT_MP_PASS")
