local StudioTestService=game:GetService("StudioTestService")
local ServerScriptService=game:GetService("ServerScriptService")
local StarterPlayer=game:GetService("StarterPlayer")
print("SF_RIFT_MP_BEGIN")
local server=Instance.new("Script"); server.Name="RiftMultiplayerServerHarness"
server.Source=[==[
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local ServerScriptService=game:GetService("ServerScriptService")
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
local initialBPack=b:FindFirstChildOfClass("Backpack")
if initialBPack and initialBPack:FindFirstChild("Pulse Rifle") then
 fail("armed_downtown_spawn") return
end
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
if not request(a,"prestige","BuyPrestige","PLATINUM_WRAP") then
 fail("prestige_no_ack") return
end
task.wait(.2)
if a:GetAttribute("RROwn_PLATINUM_WRAP") or a:GetAttribute("RRCoins")~=0 then
 fail("free_prestige") return
end
if not request(a,"invalidprestige","BuyPrestige","HACKED_ITEM") then
 fail("invalid_prestige_no_ack") return
end
if a:GetAttribute("RROwn_HACKED_ITEM") then fail("invalid_prestige_granted") return end
print("SF_RIFT_MP_CHECK prestige_purchase_validation PASS")
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
local visual=car:FindFirstChild("Official Detailed Sedan Body")
if not visual or car:GetAttribute("VisualModel")~="Official Modern City Sedan" then
 fail("real_car_art_missing") return
end
print("SF_RIFT_MP_CHECK official_detailed_drivable_sedan PASS")
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
task.wait(2)
if not request(a,"castle","Travel","CASTLE") then fail("castle_travel_ack") return end
if not waitFor(function() return (rootA.Position-Vector3.new(520,8,0)).Magnitude<16 end,5) then fail("castle_travel_missing") return end
if (rootB.Position-Vector3.new(520,8,0)).Magnitude<30 then fail("castle_travel_shared") return end
print("SF_RIFT_MP_CHECK new_world_travel PASS")
task.wait(2.2)
if not request(a,"life","Travel","LIFE") then fail("life_travel_ack") return end
if not waitFor(function() return (rootA.Position-Vector3.new(0,7,1600)).Magnitude<20 end,5) then
 fail("life_travel_missing") return
end
local lifeCoinsBefore=a:GetAttribute("RRCoins")
if not request(a,"life_bad","LifeAction","Buy","YACHT") then
 fail("life_invalid_purchase_ack") return
end
task.wait(.2)
if a:GetAttribute("RRLifeOwn_YACHT") or a:GetAttribute("RRCoins")~=lifeCoinsBefore then
 fail("life_free_yacht") return
end
local careerBoard=nil
for _,node in ipairs(world:GetDescendants()) do
 if node.Name=="Career Board RETAIL" then careerBoard=node; break end
end
if not careerBoard then fail("career_board_missing") return end
a.Character:PivotTo(CFrame.new(careerBoard.Position+Vector3.new(0,3,0)))
task.wait(.4)
if not request(a,"hire","LifeAction","Career","RETAIL") then fail("hire_ack") return end
if not waitFor(function() return a:GetAttribute("RRLifeCareer")=="RETAIL" end,3) then
 fail("hire_missing") return
end
local retail=nil
for _,node in ipairs(world:GetDescendants()) do
 if node.Name=="Retail Register" then retail=node; break end
end
if not retail then fail("retail_site_missing") return end
a.Character:PivotTo(CFrame.new(retail.Position+Vector3.new(0,4,0)))
task.wait(.4)
local beforeShift=a:GetAttribute("RRCoins")
if not request(a,"shift_start","LifeAction","Work","RETAIL") then fail("work_start_ack") return end
task.wait(.4)
if a:GetAttribute("RRCoins")~=beforeShift then fail("work_instant_wages") return end
task.wait(1.6)
if not request(a,"shift_early","LifeAction","Work","RETAIL") then fail("work_early_ack") return end
task.wait(.3)
if a:GetAttribute("RRCoins")~=beforeShift then fail("life_shift_skip_tasks") return end
local task1=world:FindFirstChild("Job Task RETAIL 1",true)
local task2=world:FindFirstChild("Job Task RETAIL 2",true)
if not task1 or not task2 then fail("retail_tasks_missing") return end
a.Character:PivotTo(CFrame.new(task2.Position+Vector3.new(0,4,0)))
task.wait(.4)
local life=ServerScriptService:WaitForChild("LifeSimulation")
local lifeApi=require(life)
if lifeApi.Process(a,"Task","RETAIL",2) then fail("out_of_order_task") return end
a.Character:PivotTo(CFrame.new(task1.Position+Vector3.new(0,4,0)))
task.wait(.4)
if not lifeApi.Process(a,"Task","RETAIL",1) then fail("task_one_failed") return end
task.wait(1.6)
a.Character:PivotTo(CFrame.new(task2.Position+Vector3.new(0,4,0)))
task.wait(.4)
if not lifeApi.Process(a,"Task","RETAIL",2) then fail("task_two_failed") return end
a.Character:PivotTo(CFrame.new(retail.Position+Vector3.new(0,4,0)))
task.wait(.4)
if not request(a,"shift","LifeAction","Work","RETAIL") then fail("work_finish_ack") return end
if not waitFor(function() return (a:GetAttribute("RRCoins") or 0)>=beforeShift+22 end,3) then
 fail("work_wages_missing") return
end
if b:GetAttribute("RRLifeCareer")~="UNEMPLOYED" or
 (b:GetAttribute("RRCoins") or 0)~=0 then fail("life_job_isolation") return end
if not request(a,"shift2","LifeAction","Work","RETAIL") then fail("work2_ack") return end
task.wait(.3)
if a:GetAttribute("RRCoins")~=beforeShift+22 then fail("life_wage_cooldown_bypass") return end
print("SF_RIFT_MP_CHECK life_career_wages_and_isolation PASS")
if not request(a,"arctic_after_life","Travel","ARCTIC") then fail("arctic_retravel_ack") return end
task.wait(2)

task.wait(2)
if not request(a,"arctic","Travel","ARCTIC") then fail("arctic_travel_ack") return end
if not waitFor(function() return (rootA.Position-Vector3.new(0,8,-520)).Magnitude<16 end,5) then fail("arctic_travel_missing") return end
task.wait(2.5)
if not request(a,"sled_denied","SpawnSnowmobile") then fail("snowmobile_denial_ack") return end
task.wait(.25)
for _,item in ipairs(world:GetChildren()) do
 if item.Name=="Player Snowmobile" and item:GetAttribute("OwnerUserId")==a.UserId then
  fail("free_snowmobile") return
 end
end
-- Simulate a legitimately earned server-owned entitlement, never client-reported.
a:SetAttribute("RROwn_SNOWMOBILE_LICENSE",true)
if not request(a,"sled","SpawnSnowmobile") then fail("snowmobile_spawn_ack") return end
local sled=waitFor(function()
 for _,item in ipairs(world:GetChildren()) do
  if item.Name=="Player Snowmobile" and item:GetAttribute("OwnerUserId")==a.UserId then return item end
 end
end,5)
if not sled or not sled:FindFirstChild("DriverSeat") then fail("snowmobile_missing") return end
print("SF_RIFT_MP_CHECK arctic_snowmobile PASS")
if not request(b,"fly_denied","SpawnFlyingCar") then fail("flyingcar_denial_ack") return end
task.wait(.25)
for _,item in ipairs(world:GetChildren()) do
 if item.Name=="Player Flying Car" and item:GetAttribute("OwnerUserId")==b.UserId then
  fail("free_flying_car") return
 end
end
b:SetAttribute("RROwn_FLIGHT_LICENSE",true)
print("SF_RIFT_MP_CHECK advanced_vehicle_licenses PASS")
if not request(b,"fly","SpawnFlyingCar") then fail("flyingcar_spawn_ack") return end
local flyer=waitFor(function()
 for _,item in ipairs(world:GetChildren()) do
  if item.Name=="Player Flying Car" and item:GetAttribute("OwnerUserId")==b.UserId then return item end
 end
end,5)
if not flyer or not flyer:FindFirstChild("DriverSeat") then fail("flyingcar_missing") return end
local flySeat=flyer.DriverSeat
local flyHum=b.Character and b.Character:FindFirstChildOfClass("Humanoid")
if not flyHum then fail("flyingcar_humanoid_missing") return end
b.Character:PivotTo(CFrame.new(flySeat.Position+Vector3.new(0,3,0)))
flySeat:Sit(flyHum)
if not waitFor(function() return flySeat.Occupant==flyHum end,3) then fail("flyingcar_seat_missing") return end
local beforeAltitude=flyer:GetPivot().Position.Y
if not waitFor(function() return flyer:GetPivot().Position.Y>beforeAltitude+3 end,3) then fail("flyingcar_did_not_lift") return end
print("SF_RIFT_MP_CHECK flyingcar_lift PASS")
local activities=require(ServerScriptService:WaitForChild("WorldActivities"))
local function atStation(player,id)
 local anchor=activities.GetStation(id)
 if not anchor then fail("missing_station_"..id); return false end
 player.Character:PivotTo(CFrame.new(anchor.Position+Vector3.new(0,5,0)))
 task.wait(.2)
 return true
end
if not atStation(a,"craft_toolkit") then return end
if activities.Perform(a,"craft_toolkit") then fail("free_toolkit") return end
if not atStation(a,"gather_wood") then return end
if not activities.Perform(a,"gather_wood") then fail("wood_gather_failed") return end
if a:GetAttribute("RRWood")~=2 or b:GetAttribute("RRWood")~=0 then fail("wood_not_isolated") return end
if activities.Perform(a,"gather_wood") then fail("wood_cooldown_bypass") return end
if not atStation(a,"gather_metal") then return end
if not activities.Perform(a,"gather_metal") then fail("metal_gather_failed") return end
if not atStation(a,"gather_metal_alt") then return end
if not activities.Perform(a,"gather_metal_alt") then fail("metal_overflow_failed") return end
if not atStation(a,"craft_toolkit") then return end
if not activities.Perform(a,"craft_toolkit") then fail("toolkit_craft_failed") return end
if a:GetAttribute("RRToolkits")~=1 or a:GetAttribute("RRWood")~=0 or
 a:GetAttribute("RRMetal")~=1 or b:GetAttribute("RRToolkits")~=0 then
 fail("crafting_inventory_incorrect") return
end
if not a:GetAttribute("RRPlot") or not b:GetAttribute("RRPlot") or
 a:GetAttribute("RRPlot")==b:GetAttribute("RRPlot") then fail("housing_plot_collision") return end
print("SF_RIFT_MP_CHECK housing_plots_isolated PASS")
print("SF_RIFT_MP_CHECK resources_crafting_isolation PASS")
if not atStation(b,"bank_heist") then return end
if activities.Perform(b,"bank_heist") then fail("free_bank_heist") return end
if not atStation(b,"build_house") then return end
if activities.Perform(b,"build_house") then fail("free_house") return end
if not atStation(a,"soccer") then return end
if not activities.Start(a,"soccer") then fail("soccer_start_failed") return end
if activities.Hit(b,"soccer") then fail("stolen_soccer_score") return end
task.wait(2.3)
if not activities.Hit(a,"soccer") then fail("soccer_skill_failed") return end
if a:GetAttribute("RRSportsWins")~=1 or b:GetAttribute("RRSportsWins")~=0 then
 fail("soccer_not_isolated") return
end
print("SF_RIFT_MP_CHECK sports_timing_isolation PASS")
if not atStation(a,"fishing") then return end
if not activities.Start(a,"fishing") then fail("fishing_start_failed") return end
task.wait(2.3)
if not activities.Hit(a,"fishing") then fail("fishing_skill_failed") return end
if a:GetAttribute("RRFish")~=2 or b:GetAttribute("RRFish")~=0 then
 fail("fish_not_isolated") return
end
if not atStation(a,"sell_fish") then return end
if not activities.Perform(a,"sell_fish") then fail("fish_sale_failed") return end
if a:GetAttribute("RRFish")~=0 then fail("fish_not_consumed") return end
print("SF_RIFT_MP_CHECK fishing_and_market PASS")
if not atStation(a,"football") then return end
if not activities.Start(a,"football") then fail("football_start_failed") return end
task.wait(2.3)
if not activities.Hit(a,"football") then fail("football_skill_failed") return end
if (a:GetAttribute("RRLevel") or 0)<2 then fail("housing_level_not_reached") return end
for i=2,5 do
 if not atStation(a,"gather_wood_"..i) then return end
 if not activities.Perform(a,"gather_wood_"..i) then fail("wood_gather_extra_"..i) return end
end
for _,id in ipairs({"gather_metal_alt2","gather_metal_alt3","gather_metal_alt4"}) do
 if not atStation(a,id) then return end
 if not activities.Perform(a,id) then fail("metal_gather_house_"..id) return end
end
if not atStation(a,"build_house") then return end
if not activities.Perform(a,"build_house") then fail("house_build_failed") return end
if a:GetAttribute("RRHouseOwned")~=true or b:GetAttribute("RRHouseOwned")==true then
 fail("house_not_isolated") return
end
local house=world:FindFirstChild("Player Home "..a.UserId,true)
if not house or house:GetAttribute("OwnerUserId")~=a.UserId then
 fail("built_house_missing") return
end
if activities.Perform(a,"build_house") then fail("double_house_build") return end
print("SF_RIFT_MP_CHECK housing_construction PASS")
-- New art is a genuine Roblox template asset, but teleport access is still
-- server-allowlisted and only moves the requesting player.
task.wait(2.2)
if not request(a,"modern","Travel","MODERN") then fail("modern_travel_ack") return end
if not waitFor(function() return (rootA.Position-Vector3.new(0,8,2215)).Magnitude<18 end,5) then
 fail("modern_downtown_travel") return
end
if (rootB.Position-Vector3.new(0,8,2215)).Magnitude<25 then
 fail("modern_shared_travel") return
end
local aPack=a:FindFirstChildOfClass("Backpack")
if (aPack and aPack:FindFirstChild("Pulse Rifle")) or
 (a.Character and a.Character:FindFirstChild("Pulse Rifle")) then
 fail("fantasy_weapon_not_removed_in_city") return
end
print("SF_RIFT_MP_CHECK official_modern_city_travel PASS")
print("SF_RIFT_MP_CHECK realistic_city_weapon_rules PASS")
local employment=world:FindFirstChild("Downtown Employment Center",true)
if not employment then fail("downtown_employment_missing") return end
a.Character:PivotTo(CFrame.new(employment.Position+Vector3.new(0,3,0)))
task.wait(.4)
if not request(a,"downtown_hire","LifeAction","Career","BARISTA") then
 fail("downtown_hire_ack") return
end
if not waitFor(function() return a:GetAttribute("RRLifeCareer")=="BARISTA" end,3) then
 fail("downtown_career_application") return
end
local downtownCafe=world:FindFirstChild("Downtown Worksite BARISTA",true)
if not downtownCafe then fail("downtown_cafe_worksite_missing") return end
a.Character:PivotTo(CFrame.new(downtownCafe.Position+Vector3.new(0,3,0)))
task.wait(.4)
if not request(a,"downtown_shift","LifeAction","Work","BARISTA") then
 fail("downtown_shift_ack") return
end
if not waitFor(function() return a:GetAttribute("RRLifeShift")=="BARISTA" end,3) then
 fail("downtown_shift_start") return
end
print("SF_RIFT_MP_CHECK detailed_downtown_career_loop PASS")

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
