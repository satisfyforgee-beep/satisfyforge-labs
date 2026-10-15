local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")
local StarterPlayer = game:GetService("StarterPlayer")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

print("SF_SMOKE_BEGIN BrainrotRush")
assert(ServerScriptService:FindFirstChild("BrainrotRush"), "BrainrotRush server script missing")
assert(StarterPlayer.StarterPlayerScripts:FindFirstChild("BrainrotRushHUD"), "BrainrotRush HUD LocalScript missing")


RunService:Run()
task.wait(4)


local remotes = ReplicatedStorage:FindFirstChild("BrainrotRushRemotes")
assert(remotes, "BrainrotRushRemotes folder missing")
local announce = remotes:FindFirstChild("Announce")
assert(announce and announce:IsA("RemoteEvent"), "Announce RemoteEvent missing")
local announceCount = 0
for _, child in ipairs(remotes:GetChildren()) do
    if child.Name == "Announce" then announceCount += 1 end
end
assert(announceCount == 1, "Announce RemoteEvent was duplicated")

local arena = workspace:FindFirstChild("BrainrotRushArena")
assert(arena, "BrainrotRushArena was not created during simulation")
assert(arena:FindFirstChild("ArenaFloor"), "ArenaFloor missing")
assert(arena:FindFirstChild("BrainrotSpawn"), "BrainrotSpawn missing")
assert(arena:FindFirstChild("UpgradePad"), "UpgradePad missing")
assert(arena:FindFirstChild("RebirthPad"), "RebirthPad missing")

for _, name in ipairs({"ArenaFloor", "BrainrotSpawn", "UpgradePad", "RebirthPad"}) do
    local count = 0
    for _, child in ipairs(arena:GetChildren()) do
        if child.Name == name then count += 1 end
    end
    assert(count == 1, name .. " should exist exactly once")
end

local upgradePrompt = arena.UpgradePad:FindFirstChildOfClass("ProximityPrompt")
assert(upgradePrompt, "UpgradePad ProximityPrompt missing")
assert(upgradePrompt.ActionText == "Upgrade earnings", "Upgrade prompt action text drifted")
assert(upgradePrompt.ObjectText == "Brainrot Shop", "Upgrade prompt object text drifted")

local rebirthPrompt = arena.RebirthPad:FindFirstChildOfClass("ProximityPrompt")
assert(rebirthPrompt, "RebirthPad ProximityPrompt missing")
assert(string.find(rebirthPrompt.ActionText, "REBIRTH", 1, true), "Rebirth prompt action text drifted")
assert(string.find(rebirthPrompt.ObjectText, "Level 20", 1, true), "Rebirth prompt requirement text drifted")

local orbCount = 0
for _, child in ipairs(arena:GetChildren()) do
    if child:IsA("BasePart") and string.find(child.Name, "Brainrot", 1, true) then
        orbCount += 1
    end
end
assert(orbCount >= 1, "No Brainrot orbs spawned during runtime smoke")
assert(orbCount <= 34, "Orb count exceeded MAX_ORBS during runtime smoke")

task.wait(3)
local laterOrbCount = 0
for _, child in ipairs(arena:GetChildren()) do
    if child:IsA("BasePart") and string.find(child.Name, "Brainrot", 1, true) then
        laterOrbCount += 1
    end
end
assert(laterOrbCount <= 34, "Orb count exceeded MAX_ORBS after continued simulation")

print("SF_SMOKE_RUNTIME arena_parts=" .. tostring(#arena:GetChildren()) .. " orbs_initial=" .. tostring(orbCount) .. " orbs_later=" .. tostring(laterOrbCount))
RunService:Stop()
print("SF_SMOKE_PASS BrainrotRush")
