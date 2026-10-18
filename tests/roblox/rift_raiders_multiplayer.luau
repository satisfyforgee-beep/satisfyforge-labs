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
end,90)
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
-- The first legal shift now also grants one-time onboarding/daily
-- achievements. Those rewards are intentional, so only compare against the
-- actual balance immediately after collecting the legitimate shift.
local balanceAfterShift=a:GetAttribute("RRCoins") or 0
if not request(a,"shift2","LifeAction","Work","RETAIL") then fail("work2_ack") return end
task.wait(.3)
if a:GetAttribute("RRCoins")~=balanceAfterShift then
 fail("life_wage_cooldown_bypass") return
end
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
-- First-minute polish is not just decoration: real proximity-checked
-- transit stops take only the intended player to jobs, farms, and housing.
local streets=world:FindFirstChild("Detailed Downtown Streetscape")
local Transit=require(ServerScriptService:WaitForChild("DowntownStreetscape"))
assert(streets and streets:GetAttribute("TransitStopCount")==3,
 "bus stop street art absent from game")
if Transit.UseTransit(a,"FAKE_DESTINATION") or Transit.UseTransit(a,"GARDEN") then
 fail("transit_remote_or_fake_route_bypass") return
end
local gardenStop=streets:FindFirstChild("Transit Stop GARDEN")
if not gardenStop then fail("transit_garden_stop_missing") return end
local otherPlayerPosition=rootB.Position
a.Character:PivotTo(CFrame.new(gardenStop.Position+Vector3.new(0,4,0)))
task.wait(.25)
if not Transit.UseTransit(a,"GARDEN") then fail("free_transit_route_broken") return end
if not waitFor(function()
 return (rootA.Position-Vector3.new(0,5,2152)).Magnitude<15
end,4) then fail("transit_garden_destination_wrong") return end
if (rootB.Position-otherPlayerPosition).Magnitude>12 then
 fail("transit_teleported_another_player") return
end
print("SF_RIFT_MP_CHECK first_minute_free_transit_isolated PASS")
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
local cafe=world:FindFirstChild("Downtown Interactive Coffee Bar")
local cafeService=require(ServerScriptService:WaitForChild("CafeService"))
local lifeService=require(ServerScriptService:WaitForChild("LifeSimulation"))
local order=a:GetAttribute("RRLifeCafeOrder")
if not cafe or not table.find(cafeService.Recipes,order) then
 fail("barista_random_customer_order_missing") return
end
if lifeService.Process(a,"CafeServe") then
 fail("barista_served_without_brewing") return
end
local wrong=order=="ESPRESSO" and "MOCHA" or "ESPRESSO"
local wrongMachine=cafe:FindFirstChild("Coffee Brew "..wrong)
local rightMachine=cafe:FindFirstChild("Coffee Brew "..order)
if not wrongMachine or not rightMachine then
 fail("barista_recipe_buttons_missing") return
end
a.Character:PivotTo(CFrame.new(wrongMachine.Position+Vector3.new(0,4,0)))
task.wait(1.6)
if lifeService.Process(a,"CafeBrew",wrong) then
 fail("wrong_coffee_recipe_accepted") return
end
a.Character:PivotTo(CFrame.new(rightMachine.Position+Vector3.new(0,4,0)))
task.wait(.55)
if not lifeService.Process(a,"CafeBrew",order) then
 fail("correct_coffee_recipe_not_prepared") return
end
if a:GetAttribute("RRLifeTaskStep")~=1 then
 fail("coffee_brew_stage_not_recorded") return
end
local serviceCounter=cafe:FindFirstChild("Cafe Customer Service Register")
a.Character:PivotTo(CFrame.new(serviceCounter.Position+Vector3.new(0,4,0)))
task.wait(1.8)
local tipsBefore=a:GetAttribute("RRCoins") or 0
if not lifeService.Process(a,"CafeServe") then
 fail("coffee_not_served_after_correct_recipe") return
end
if a:GetAttribute("RRLifeTaskStep")~=2 or
 (a:GetAttribute("RRCoins") or 0)<=tipsBefore then
 fail("coffee_service_did_not_earn_tip") return
end
task.wait(.55)
if lifeService.Process(a,"CafeServe") then
 fail("duplicate_coffee_customer_tip") return
end
a.Character:PivotTo(CFrame.new(downtownCafe.Position+Vector3.new(0,4,0)))
task.wait(.5)
local shiftsBefore=a:GetAttribute("RRLifeShifts") or 0
if not lifeService.Process(a,"Work","BARISTA") or
 (a:GetAttribute("RRLifeShifts") or 0)~=shiftsBefore+1 then
 fail("barista_shift_wage_collection") return
end
print("SF_RIFT_MP_CHECK correct_recipe_barista_job_real_wages PASS")
local living=world:FindFirstChild("Living Modern Downtown")
if not living then fail("living_downtown_missing") return end
local citizen=living:FindFirstChild("Downtown Citizen 1")
local traffic=living:FindFirstChild("Downtown Traffic Sedan 1")
if not citizen or not citizen:FindFirstChildOfClass("Humanoid") then
 fail("r15_citizen_missing") return
end
if citizen:FindFirstChildOfClass("Humanoid").RigType~=Enum.HumanoidRigType.R15 then
 fail("citizen_not_r15") return
end
if not traffic or traffic:GetAttribute("VisualModel")~="Official Modern City Sedan" then
 fail("detailed_city_traffic_missing") return
end
local beforeTraffic=world:GetAttribute("DowntownTrafficDistance") or 0
local beforeCitizen=citizen:GetPivot().Position
if not waitFor(function()
 return (world:GetAttribute("DowntownTrafficDistance") or 0)>beforeTraffic+10
end,3) then fail("downtown_traffic_not_moving") return end
if not waitFor(function()
 return (citizen:GetPivot().Position-beforeCitizen).Magnitude>2
end,4) then fail("downtown_citizen_not_walking") return end
print("SF_RIFT_MP_CHECK living_downtown_population PASS")

-- Test server authority for the new garden, including plot isolation and
-- rejection of planting without legitimately purchased tools and seed packs.
local gardens=world:FindFirstChild("Downtown Community Garden")
local gardenService=require(ServerScriptService:WaitForChild("UrbanGardening"))
local gardenA=gardenService.PlotFor(a)
local gardenB=gardenService.PlotFor(b)
if not gardens or not gardenA or not gardenB or gardenA==gardenB then
 fail("personal_garden_allocation") return
end
if gardenA:GetAttribute("OwnerUserId")~=a.UserId or
 gardenB:GetAttribute("OwnerUserId")~=b.UserId then
 fail("garden_owner_isolation") return
end
local lifeService=require(ServerScriptService:WaitForChild("LifeSimulation"))
a.Character:PivotTo(CFrame.new(gardenB.Position+Vector3.new(0,5,0)))
task.wait(.4)
if lifeService.Process(a,"GardenPlant","TOMATO_SEEDS") then
 fail("other_players_garden_bypass") return
end
a.Character:PivotTo(CFrame.new(gardenA.Position+Vector3.new(0,5,0)))
task.wait(.4)
if lifeService.Process(a,"GardenPlant","HACKED_SEED") or
 lifeService.Process(a,"GardenPlant","TOMATO_SEEDS") or
 a:GetAttribute("RRLifeGardenCrop")~="" then
 fail("garden_seeds_require_purchase") return
end
print("SF_RIFT_MP_CHECK gardener_ownership_protection PASS")
-- Exercise the actual in-game coin purchase, planting and watering loop.
-- Only run when the earlier legitimate jobs/minigames earned sufficient funds.
local plantingBudget=a:GetAttribute("RRCoins") or 0
print("SF_RIFT_MP_GARDEN_EARNED_COIN_BUDGET "..plantingBudget)
if plantingBudget>=100 then
 local nursery=world:FindFirstChild("Downtown Store GARDEN",true)
 if not nursery then fail("nursery_missing") return end
 a.Character:PivotTo(CFrame.new(nursery.Position+Vector3.new(0,3,0)))
 task.wait(.4)
 for _,item in ipairs({"GARDEN_TROWEL","WATERING_CAN","TOMATO_SEEDS"}) do
  task.wait(.45)
  if not lifeService.Process(a,"Buy",item) then
   fail("real_garden_purchase_"..item) return
  end
 end
 if a:GetAttribute("RRLifeSeed_TOMATO_SEEDS")~=3 then
  fail("garden_seed_packet_three_plantings") return
 end
 a.Character:PivotTo(CFrame.new(gardenA.Position+Vector3.new(0,5,0)))
 task.wait(.5)
 if not lifeService.Process(a,"GardenPlant","TOMATO_SEEDS") then
  fail("garden_plant_with_purchased_seeds") return
 end
 if a:GetAttribute("RRLifeGardenCrop")~="TOMATO_SEEDS" or
  a:GetAttribute("RRLifeSeed_TOMATO_SEEDS")~=2 then
  fail("garden_seed_stock_consumption") return
 end
 task.wait(.5)
 if not lifeService.Process(a,"GardenWater") or
  a:GetAttribute("RRLifeGardenStatus")~="GROWING" then
  fail("garden_water_success") return
 end
 if b:GetAttribute("RRLifeGardenCrop")~="" then
  fail("garden_growth_isolation") return
 end
 print("SF_RIFT_MP_CHECK purchased_garden_planting_and_watering PASS")
else
 print("SF_RIFT_MP_CHECK garden_purchase_requires_more_earned_coins PASS")
end

-- Watercraft have different movement speeds and shapes, but boat ownership
-- remains authoritative: they cannot be launched from free UI commands.
task.wait(2.2)
if not request(a,"waterfront","Travel","WATERFRONT") then
 fail("waterfront_travel_ack") return
end
if not waitFor(function()
 return (rootA.Position-Vector3.new(600,8,520)).Magnitude<20
end,5) then fail("waterfront_destination") return end
local boatService=require(ServerScriptService:WaitForChild("BoatService"))
if boatService.Spawn(a,"INVALID_YACHT") or
 boatService.Spawn(a,"SPEEDBOAT") then
 fail("unauthorized_boat_launch") return
end
-- In Studio's isolated test only, simulate a previously purchased ownership
-- bit set by the trusted server, then exercise actual seat driving physics.
a:SetAttribute("RRLifeOwn_SPEEDBOAT",true)
local boatSuccess,message=boatService.Spawn(a,"SPEEDBOAT")
if not boatSuccess then fail("owned_speedboat_launch "..tostring(message)) return end
local dock=world:FindFirstChild("Navigable Ocean Marina")
local vessel
for _,candidate in ipairs(dock:GetChildren()) do
 if candidate:IsA("Model") and candidate:GetAttribute("OwnerUserId")==a.UserId then
  vessel=candidate
 end
end
local captainSeat=vessel and vessel:FindFirstChild("Boat Driver Seat")
if not captainSeat then fail("speedboat_seat_missing") return end
local captainHumanoid=a.Character and a.Character:FindFirstChildOfClass("Humanoid")
a.Character:PivotTo(CFrame.new(captainSeat.Position+Vector3.new(0,3,0)))
captainSeat:Sit(captainHumanoid)
if not waitFor(function() return captainSeat.Occupant==captainHumanoid end,3) then
 fail("speedboat_captain_seat") return
end
local boatStart=vessel:GetPivot().Position
captainSeat.ThrottleFloat=1
task.wait(.8)
if (vessel:GetPivot().Position-boatStart).Magnitude<.2 then
 fail("owned_speedboat_does_not_move") return
end
captainHumanoid.Sit=false;vessel:Destroy()
a:SetAttribute("RRLifeOwn_SPEEDBOAT",false)
print("SF_RIFT_MP_CHECK earned_watercraft_boat_controls PASS")

-- A home is not granted just because the player reaches the Estates district.
-- Paid cars cannot be selected by forging replicated owner attributes.
if lifeService.Process(a,"GoHome") then
 fail("free_personal_property_teleport") return
end
task.wait(2.2)
if not request(a,"modern_final","Travel","MODERN") then
 fail("garage_travel_ack") return
end
local dealer=world:FindFirstChild("Downtown Store VEHICLE",true)
if not dealer then fail("garage_vehicle_dealer_missing") return end
a.Character:PivotTo(CFrame.new(dealer.Position+Vector3.new(0,4,0)))
task.wait(.5)
a:SetAttribute("RRLifeOwn_SPORTS_CAR",true)
if lifeService.Process(a,"SelectCar","SPORTS_CAR") then
 fail("free_car_selection_from_attribute") return
end
print("SF_RIFT_MP_CHECK garage_car_ownership_validation PASS")
-- In isolated Studio testing only, simulate the validated server's selected
-- owned car attribute to verify official-red detailed meshes and top speed.
a:SetAttribute("RRLifeSelectedCar","SPORTS_CAR")
local vehicleService=require(ServerScriptService:WaitForChild("VehicleService"))
local spawned,msg=vehicleService.Spawn(world,a,"car")
if not spawned then fail("red_sedan_spawn_"..tostring(msg)) return end
local redCar
for _,candidate in ipairs(world:GetChildren()) do
 if candidate.Name=="Player Hovercar" and candidate:GetAttribute("OwnerUserId")==a.UserId then
  redCar=candidate
 end
end
if not redCar or not redCar:FindFirstChild("Official Detailed Sedan Body") then
 fail("red_detailed_sedan_missing") return
end
if redCar:GetAttribute("SelectedVehicle")~="SPORTS_CAR" or
 redCar:GetAttribute("DetailedPaint")~="RED" or
 redCar:GetAttribute("TopSpeed")~=50 then
 fail("premium_car_speed_and_paint") return
end
print("SF_RIFT_MP_CHECK official_red_car_and_selected_driving_speed PASS")
-- The owner-only vehicle logic must prevent another player from hijacking it.
local foreignHumanoid=b.Character and b.Character:FindFirstChildOfClass("Humanoid")
local premiumSeat=redCar:FindFirstChild("DriverSeat")
if not foreignHumanoid or not premiumSeat then
 fail("car_driver_identity_test_missing") return
end
b.Character:PivotTo(CFrame.new(premiumSeat.Position+Vector3.new(0,3,0)))
premiumSeat:Sit(foreignHumanoid)
task.wait(.3)
local carBeforeHijack=redCar:GetPivot().Position
premiumSeat.ThrottleFloat=1
task.wait(.35)
if (redCar:GetPivot().Position-carBeforeHijack).Magnitude>.4 then
 fail("unauthorized_vehicle_driver") return
end
foreignHumanoid.Sit=false
print("SF_RIFT_MP_CHECK personal_car_owner_only_driving PASS")
redCar:Destroy()
a:SetAttribute("RRLifeOwn_SPORTS_CAR",false)
a:SetAttribute("RRLifeSelectedCar","")
-- A genuine 29-MeshPart Racing template body must render as an owned car.
task.wait(8.2)
a:SetAttribute("RRLifeOwn_RACE_CAR",true)
a:SetAttribute("RRLifeSelectedCar","RACE_CAR")
local spawnedRacing,racingError=vehicleService.Spawn(world,a,"car")
if not spawnedRacing then
 fail("official_race_car_spawn_"..tostring(racingError)) return
end
local raceVehicle
for _,candidate in ipairs(world:GetChildren()) do
 if candidate.Name=="Player Hovercar" and
  candidate:GetAttribute("OwnerUserId")==a.UserId then raceVehicle=candidate end
end
local raceBody=raceVehicle and raceVehicle:FindFirstChild("Official Detailed Racing Car Body")
if not raceBody or raceVehicle:GetAttribute("TopSpeed")~=60 or
 raceVehicle:GetAttribute("DetailedPaint")~="RACING" then
 fail("official_racing_car_mesh_not_equipped") return
end
local racingPieces=0
for _,part in ipairs(raceBody:GetDescendants()) do
 if part:IsA("MeshPart") then racingPieces+=1 end
end
if racingPieces~=29 then fail("official_racing_mesh_count") return end
print("SF_RIFT_MP_CHECK official_racing_car_29_meshes PASS")
raceVehicle:Destroy()
a:SetAttribute("RRLifeOwn_RACE_CAR",false)
a:SetAttribute("RRLifeSelectedCar","")
-- Official suburban destination and one-player travel isolation.
task.wait(2.2)
if not request(a,"suburb_final","Travel","SUBURBIA") then
 fail("official_suburban_travel_ack") return
end
if not waitFor(function() return
 (rootA.Position-Vector3.new(0,8,3425)).Magnitude<25 end,6) then
 fail("official_suburban_travel") return
end
if (rootB.Position-Vector3.new(0,8,3425)).Magnitude<50 then
 fail("suburban_other_player_teleported") return
end
print("SF_RIFT_MP_CHECK detailed_official_suburban_destination PASS")
if a:GetAttribute("RRGoalsIntro")~=1 or
 (a:GetAttribute("RRGoalsDailyDone") or 0)<1 then
 fail("first_session_suburb_goal_and_daily_travel") return
end
if (b:GetAttribute("RRGoalsIntro") or 0)>0 then
 fail("onboarding_progress_leaked_to_second_player") return
end
print("SF_RIFT_MP_CHECK first_session_guided_travel_reward PASS")
local services=world:FindFirstChild("Working Suburban Services",true)
local market=services and services:FindFirstChild("Official Suburban Market Checkout")
local garage=services and services:FindFirstChild("Official Suburban Auto Garage Checkout")
local station=services and services:FindFirstChild("Official Suburban Gas Station Kiosk")
if not market or not garage or not station then
 fail("suburban_validated_shops_missing") return
end
-- The same item may not be bought by remote replay far from a store.
a.Character:PivotTo(CFrame.new(0,8,3425))
task.wait(.6)
if lifeService.Process(a,"Buy","FIRST_AID_KIT") or
 lifeService.Process(a,"BuySnack","MARKET") then
 fail("suburban_shop_remote_purchase_bypass") return
end
print("SF_RIFT_MP_CHECK suburban_shop_proximity_enforced PASS")
-- The imported market now sells actual catalog goods, with the same
-- level/coin checks as the original town shop.
a.Character:PivotTo(CFrame.new(market.Position+Vector3.new(0,5,0)))
task.wait(.6)
local money=a:GetAttribute("RRCoins") or 0
local prePurchaseLevel=a:GetAttribute("RRLevel") or 1
local introBeforePurchase=a:GetAttribute("RRGoalsIntro") or 0
local already=a:GetAttribute("RRLifeOwn_FIRST_AID_KIT")==true
if money>=130 and not already then
 local bought=lifeService.Process(a,"Buy","FIRST_AID_KIT")
 if not bought then fail("suburban_legal_purchase_rejected") return end
 local remaining=a:GetAttribute("RRCoins") or 0
 local postPurchaseLevel=a:GetAttribute("RRLevel") or prePurchaseLevel
 -- Earned coins are reduced by the exact price, while a first purchase
 -- awards a one-time 85-coin tutorial reward and potential level-up coins.
 local legitimateBonus=introBeforePurchase==1 and 85 or 0
 local expected=money-130+legitimateBonus+
  math.max(0,postPurchaseLevel-prePurchaseLevel)*50
 if a:GetAttribute("RRLifeOwn_FIRST_AID_KIT")~=true or
  remaining~=expected then
  print("SF_RIFT_MP_BUY_ACCOUNTING actual",remaining,"expected",expected)
  fail("suburban_shop_did_not_charge_earned_coins") return
 end
 print("SF_RIFT_MP_CHECK detailed_suburban_market_real_purchase PASS")
 if a:GetAttribute("RRGoalsIntro")~=2 then
  fail("first_session_purchase_goal") return
 end
 print("SF_RIFT_MP_CHECK first_session_purchase_goal PASS")
else
 print("SF_RIFT_MP_CHECK suburban_market_purchase_level_and_budget_guard PASS")
end
-- The suburb garage is legitimately accepted as a dealer, but still
-- requires player-owned cars rather than spoofed client attributes.
task.wait(.5)
a.Character:PivotTo(CFrame.new(garage.Position+Vector3.new(0,5,0)))
task.wait(.6)
if lifeService.Process(a,"SelectCar","HYPERCAR") then
 fail("suburban_auto_shop_unowned_vehicle_selection") return
end
print("SF_RIFT_MP_CHECK suburban_auto_shop_owner_validation PASS")
-- Complete a legitimate extra suburban workplace to test that real
-- validated actions advance the intro and one-per-day challenge ledger.
local job=services:FindFirstChild("Suburban Worksite RETAIL")
local taskOne=services:FindFirstChild("Suburban Work Task RETAIL 1")
local taskTwo=services:FindFirstChild("Suburban Work Task RETAIL 2")
if not job or not taskOne or not taskTwo then
 fail("new_suburban_workplace_missing") return
end
a.Character:PivotTo(CFrame.new(job.Position+Vector3.new(0,4,0)))
task.wait(.65)
if not lifeService.Process(a,"Career","RETAIL") then
 fail("suburban_career_application_not_accepted") return
end
if money>=130 and not already and a:GetAttribute("RRGoalsIntro")~=3 then
 fail("first_session_apply_for_job_goal") return
end
task.wait(.8)
if not lifeService.Process(a,"Work","RETAIL") then
 fail("suburban_shift_not_started") return
end
task.wait(1.7)
a.Character:PivotTo(CFrame.new(taskOne.Position+Vector3.new(0,4,0)))
task.wait(.35)
if not lifeService.Process(a,"Task","RETAIL",1) then
 fail("suburban_shift_first_task_not_accepted") return
end
task.wait(1.7)
a.Character:PivotTo(CFrame.new(taskTwo.Position+Vector3.new(0,4,0)))
task.wait(.35)
if not lifeService.Process(a,"Task","RETAIL",2) then
 fail("suburban_shift_second_task_not_accepted") return
end
task.wait(.45)
a.Character:PivotTo(CFrame.new(job.Position+Vector3.new(0,4,0)))
task.wait(.4)
local preWages=a:GetAttribute("RRCoins") or 0
if not lifeService.Process(a,"Work","RETAIL") then
 fail("suburban_shift_wage_payout_denied") return
end
if (a:GetAttribute("RRCoins") or 0)<=preWages or
 (a:GetAttribute("RRGoalsDailyDone") or 0)<2 then
 fail("suburban_shift_daily_wages_not_awarded") return
end
if money>=130 and not already and a:GetAttribute("RRGoalsIntro")~=4 then
 fail("first_session_intro_never_completed") return
end
print("SF_RIFT_MP_CHECK suburban_live_shift_and_persistent_goal_awards PASS")
-- Actual hidden Suburbia collectibles are earned once per player/day;
-- replaying an old prompt cannot award duplicate coins.
local discoveries=require(ServerScriptService:WaitForChild("SuburbanDiscovery"))
local token=world:FindFirstChild("Hidden Keepsake 1",true)
if not token then fail("hidden_suburbia_keepsake_not_spawned") return end
if discoveries.Collect(a,1) then
 fail("remote_hidden_collectible_distance_bypass") return
end
a.Character:PivotTo(CFrame.new(token.Position+Vector3.new(0,4,0)))
task.wait(.5)
local beforeFind=a:GetAttribute("RRCoins") or 0
if not discoveries.Collect(a,1) then
 fail("nearby_keepsake_not_redeemed") return
end
local afterFind=a:GetAttribute("RRCoins") or 0
if afterFind<=beforeFind or a:GetAttribute("RRDiscoverCount")~=1 then
 fail("real_suburban_keepsake_reward_missing") return
end
if discoveries.Collect(a,1) or
 (a:GetAttribute("RRCoins") or 0)~=afterFind or
 (b:GetAttribute("RRDiscoverCount") or 0)~=0 then
 fail("keepsake_replay_or_player_isolation") return
end
print("SF_RIFT_MP_CHECK suburban_hidden_exploration_no_double_claim PASS")
print("SF_RIFT_MP_SERVER_PASS players=2")
StudioTestService:EndTest("PASS:rift_multiplayer")
]==]
server.Parent=ServerScriptService
local client=Instance.new("LocalScript"); client.Name="RiftMultiplayerClientHarness"
client.Source=[==[
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local channel=ReplicatedStorage:WaitForChild("RiftMPProbe",95)
local action=ReplicatedStorage:WaitForChild("RiftRaidersAction",95)
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
