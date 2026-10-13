local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")
local StarterPlayer = game:GetService("StarterPlayer")

print("SF_SMOKE_BEGIN BrainrotRush")
assert(ServerScriptService:FindFirstChild("BrainrotRush"), "BrainrotRush server script missing")
assert(StarterPlayer.StarterPlayerScripts:FindFirstChild("BrainrotRushHUD"), "BrainrotRush HUD LocalScript missing")

RunService:Run()
task.wait(4)

local arena = workspace:FindFirstChild("BrainrotRushArena")
assert(arena, "BrainrotRushArena was not created during simulation")
assert(arena:FindFirstChild("ArenaFloor"), "ArenaFloor missing")
assert(arena:FindFirstChild("BrainrotSpawn"), "BrainrotSpawn missing")
assert(arena:FindFirstChild("UpgradePad"), "UpgradePad missing")
assert(arena:FindFirstChild("RebirthPad"), "RebirthPad missing")

local orbCount = 0
for _, child in ipairs(arena:GetChildren()) do
    if child:IsA("BasePart") and string.find(child.Name, "Brainrot", 1, true) then
        orbCount += 1
    end
end
assert(orbCount >= 1, "No Brainrot orbs spawned during runtime smoke")

print("SF_SMOKE_RUNTIME arena_parts=" .. tostring(#arena:GetChildren()) .. " orbs=" .. tostring(orbCount))
RunService:Stop()
print("SF_SMOKE_PASS BrainrotRush")
