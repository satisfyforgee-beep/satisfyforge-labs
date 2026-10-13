local RunService = game:GetService("RunService")
local ServerScriptService = game:GetService("ServerScriptService")

print("SF_SMOKE_BEGIN TilePanic")
assert(ServerScriptService:FindFirstChild("Game"), "Tile Panic server script missing")

RunService:Run()
task.wait(2)

local arena = workspace:FindFirstChild("TilePanicArena")
assert(arena, "TilePanicArena missing")
assert(arena:FindFirstChild("Lobby"), "Lobby missing")
assert(arena:FindFirstChild("LobbySpawn"), "LobbySpawn missing")
local tiles = 0
for _, child in ipairs(arena:GetChildren()) do
    if child.Name == "Tile" then tiles += 1 end
end
assert(tiles == 64, "Expected 64 tiles, found " .. tostring(tiles))
print("SF_SMOKE_RUNTIME tiles=" .. tostring(tiles) .. " arenaChildren=" .. tostring(#arena:GetChildren()))
RunService:Stop()
print("SF_SMOKE_PASS TilePanic")
