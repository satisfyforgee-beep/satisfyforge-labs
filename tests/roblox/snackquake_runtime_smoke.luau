local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

print("SF_SMOKE_BEGIN Snackquake")
RunService:Run()
task.wait(6)

local shared = ReplicatedStorage:FindFirstChild("SnackquakeShared")
assert(shared, "SnackquakeShared missing")
local configModule = shared:FindFirstChild("Config")
assert(configModule, "Config module missing")
local config = require(configModule)
assert(config.Version == "0.2.1-save-fix", "Unexpected version: " .. tostring(config.Version))
assert(config.RoundSeconds == 105, "Unexpected round length: " .. tostring(config.RoundSeconds))

local world = workspace:FindFirstChild("SnackquakeWorld")
assert(world, "SnackquakeWorld missing")
assert(world:FindFirstChild("RescueChute"), "RescueChute missing")
assert(world:FindFirstChild("Creatures"), "Creatures folder missing")
assert(world:FindFirstChild("Disasters"), "Disasters folder missing")

local rescueSpots = 0
local refuges = 0
for _, child in ipairs(world:GetChildren()) do
    if child.Name == "RescueSpot" then rescueSpots += 1 end
    if child.Name == "BlueRefuge" then refuges += 1 end
end
assert(rescueSpots == 15, "Expected 15 RescueSpot parts, found " .. tostring(rescueSpots))
assert(refuges == 6, "Expected 6 BlueRefuge parts, found " .. tostring(refuges))

local report = ReplicatedStorage:FindFirstChild("SnackquakeStudioSmoke")
assert(report, "Embedded Studio smoke report missing")
local passed = report:GetAttribute("Passed")
local failed = report:GetAttribute("Failed")
assert(type(passed) == "number", "Smoke passed count missing")
assert(failed == 0, "Embedded Studio smoke failures: " .. tostring(failed) .. " / summary=" .. tostring(report:GetAttribute("Summary")))

print("SF_SMOKE_RUNTIME version=" .. tostring(config.Version) .. " rescueSpots=" .. tostring(rescueSpots) .. " refuges=" .. tostring(refuges) .. " embeddedPassed=" .. tostring(passed))
RunService:Stop()
print("SF_SMOKE_PASS Snackquake")
