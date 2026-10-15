print("SF_MP_PROBE_BEGIN")
local StudioTestService = game:GetService("StudioTestService")
local ServerScriptService = game:GetService("ServerScriptService")
local StarterPlayer = game:GetService("StarterPlayer")

local serverTest = Instance.new("Script")
serverTest.Name = "SFMultiplayerServerTest"
serverTest.Source = [==[
local Players = game:GetService("Players")
local StudioTestService = game:GetService("StudioTestService")
local deadline = os.clock() + 20
while #Players:GetPlayers() < 2 and os.clock() < deadline do
    task.wait(0.25)
end
local players = Players:GetPlayers()
print("SF_MP_SERVER_PLAYERS " .. tostring(#players))
if #players < 2 then
    StudioTestService:EndTest("FAIL:expected_two_players")
    return
end
for _, player in ipairs(players) do
    local statsDeadline = os.clock() + 10
    while not player:FindFirstChild("leaderstats") and os.clock() < statsDeadline do task.wait(0.1) end
    local stats = player:FindFirstChild("leaderstats")
    if not stats then StudioTestService:EndTest("FAIL:missing_leaderstats") return end
    for _, name in ipairs({"Brainrot", "Collected", "Level", "Rebirths"}) do
        if not stats:FindFirstChild(name) then StudioTestService:EndTest("FAIL:missing_" .. name) return end
    end
end
local arena = workspace:FindFirstChild("BrainrotRushArena")
if not arena then StudioTestService:EndTest("FAIL:missing_arena") return end
local remotes = game:GetService("ReplicatedStorage"):FindFirstChild("BrainrotRushRemotes")
if not remotes or not remotes:FindFirstChild("Announce") then StudioTestService:EndTest("FAIL:missing_remotes") return end
print("SF_MP_SERVER_PASS players=" .. tostring(#players))
StudioTestService:EndTest("PASS:two_players_initialized")
]==]
serverTest.Parent = ServerScriptService

local clientTest = Instance.new("LocalScript")
clientTest.Name = "SFMultiplayerClientTest"
clientTest.Source = [==[
local Players = game:GetService("Players")
if not game:IsLoaded() then game.Loaded:Wait() end
local player = Players.LocalPlayer
print("SF_MP_CLIENT_READY " .. (player and player.Name or "nil"))
]==]
clientTest.Parent = StarterPlayer.StarterPlayerScripts

local ok, result = pcall(function()
    return StudioTestService:ExecuteMultiplayerTestAsync(2, "brainrot-two-player-init")
end)
print("SF_MP_PROBE_RESULT ok=" .. tostring(ok) .. " result=" .. tostring(result))
if not ok or result ~= "PASS:two_players_initialized" then
    error("multiplayer probe failed: " .. tostring(result))
end
print("SF_MP_PROBE_PASS")
