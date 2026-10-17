local RunService=game:GetService("RunService")
RunService:Run()
task.wait(3)
local world=workspace:WaitForChild("RiftRaidersWorld",20)
assert(world,"missing world")
assert(world:GetAttribute("Version")=="0.1.0","version mismatch")
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
assert(game:GetService("ReplicatedStorage"):FindFirstChild("RiftRaidersAction"),"action missing")
assert(game:GetService("ReplicatedStorage"):FindFirstChild("RiftRaidersEvent"),"event missing")
print("SF_RIFT_SMOKE_PASS")
RunService:Stop()
