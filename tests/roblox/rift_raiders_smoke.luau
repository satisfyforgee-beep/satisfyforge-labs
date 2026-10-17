local RunService=game:GetService("RunService")
RunService:Run()
task.wait(3)
local success,problem=pcall(function()
local world=workspace:WaitForChild("RiftRaidersWorld",20)
assert(world,"missing world")
assert(world:GetAttribute("Version")=="0.4.0","version mismatch")
local function count(name)
 local n=0
 for _,v in ipairs(world:GetDescendants()) do if v.Name==name then n+=1 end end
 return n
end
assert(count("Central Hub")==1,"hub missing")
assert(count("Safe Skybridge")==4,"four bridges required")
assert(count("Rift Shard")==36,"36 shards required")
assert(count("Rift Drone")==12,"12 drones required")
assert(count("Rift Core CYBER")==1,"cyber beacon missing")
assert(count("Rift Core CRYSTAL")==1,"crystal beacon missing")
assert(count("Rift Core VOLCANO")==1,"volcano beacon missing")
assert(count("Rift Core SKY")==1,"sky beacon missing")
assert(count("Cloud Summit")==1,"summit missing")
assert(count("ReusableWorldKit")==1,"reusable scenery missing")
assert(count("Tree_pine")>=9,"trees missing")
assert(count("Grass Patch")>=70,"grass missing")
assert(count("Parked Future Car")==3,"parked cars missing")
assert(count("Road Segment")>=1,"roads missing")
assert(count("Chaos Titan")==1,"boss missing")
assert(count("Seven New Worlds")==1,"new regions missing")
assert(count("Courier Dispatch Terminal")==1,"courier dispatch missing")
assert(count("Interworld Delivery Point")==7,"courier dropoffs missing")
assert(count("Walkable Arrival Plaza")==7,"seven world plazas missing")
assert(count("Portal to Central Hub")==7,"return portals missing")
assert(count("Royal Stone Castle")==1,"castle missing")
assert(count("Working Farm Barn")==1,"farm missing")
assert(count("Harvest Carrot")==6,"carrot crops missing")
assert(count("Japanese Torii Gate")==1,"japan missing")
assert(count("Five-Level Pagoda")==1,"pagoda missing")
assert(count("Snowmobile Display")==4,"snowmobiles missing")
assert(count("Jetpack Station")==1,"jetpack missing")
assert(count("Marina Dock")==1,"marina missing")
assert(count("City Bank")==1,"bank missing")
assert(count("Passenger Jet Display")==1,"airport jet missing")
assert(count("Animal Body")>=6,"animals missing")
assert(count("Sports and Life Activities")==1,"activity world missing")
assert(count("Sports Plaza")==1,"sports district missing")
assert(count("Player Housing Neighborhood")==1,"housing district missing")
assert(count("Home Floor")==0,"unowned houses should not spawn in smoke")
assert(count("Housing Construction Office")==1,"housing office missing")
assert(count("Soccer Pitch")==1,"soccer pitch missing")
assert(count("Football Field")==1,"football field missing")
assert(count("Baseball Diamond")==1,"baseball diamond missing")
assert(count("Stadium Floodlight")==4,"sports floodlights missing")
for _,id in ipairs({
 "football","baseball","soccer","fishing","hunting",
 "gather_wood","gather_wood_2","gather_wood_3","gather_wood_4","gather_wood_5",
 "gather_metal","gather_metal_alt","gather_metal_alt2","gather_metal_alt3","gather_metal_alt4","craft_toolkit","sell_fish",
 "bank_heist","steal_car","chop_shop","build_house"
}) do
 local found=false
 for _,node in ipairs(world:GetDescendants()) do
  if node:GetAttribute("ActivityId")==id then found=true; break end
 end
 assert(found,"activity missing: "..id)
end
assert(game:GetService("ReplicatedStorage"):FindFirstChild("RiftActivitiesSignal"),
 "activity challenge signal missing")
local terrainMaterials,terrainOccupancy=workspace.Terrain:ReadVoxels(
 Region3.new(Vector3.new(520,-8,-8),Vector3.new(528,0,0)):ExpandToGrid(4),4)
assert(terrainOccupancy[1][1][1]>.1,"castle terrain not filled")
assert(terrainMaterials[1][1][1]==Enum.Material.Grass,"castle terrain material wrong")
assert(game:GetService("ServerScriptService"):FindFirstChild("VehicleService"),"vehicle service missing")
assert(game:GetService("ReplicatedStorage"):FindFirstChild("RiftRaidersAction"),"action missing")
assert(game:GetService("ReplicatedStorage"):FindFirstChild("RiftRaidersEvent"),"event missing")
end)
if success then print("SF_RIFT_SMOKE_PASS") else warn("SF_RIFT_SMOKE_FAIL "..tostring(problem)) end
RunService:Stop()
