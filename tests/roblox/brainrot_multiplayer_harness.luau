print("SF_MP_PROBE_BEGIN")
local StudioTestService = game:GetService("StudioTestService")
local ServerScriptService = game:GetService("ServerScriptService")
local StarterPlayer = game:GetService("StarterPlayer")

local serverTest = Instance.new("Script")
serverTest.Name = "SFMultiplayerServerTest"
serverTest.Source = [==[
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StudioTestService = game:GetService("StudioTestService")

local function fail(reason)
    warn("SF_MP_FAIL " .. reason)
    StudioTestService:EndTest("FAIL:" .. reason)
end

local function waitFor(predicate, timeout)
    local deadline = os.clock() + timeout
    while os.clock() < deadline do
        local ok, value = pcall(predicate)
        if ok and value then return value end
        task.wait(0.1)
    end
    return nil
end

local channel = Instance.new("RemoteEvent")
channel.Name = "SFMultiplayerTestChannel"
channel.Parent = ReplicatedStorage
local replies = {}
channel.OnServerEvent:Connect(function(player, kind, token, ok, detail)
    replies[player] = replies[player] or {}
    replies[player][kind .. ":" .. tostring(token)] = {ok = ok, detail = detail}
end)

local function ask(player, action, token, payload, timeout)
    channel:FireClient(player, action, token, payload)
    return waitFor(function()
        local bucket = replies[player]
        return bucket and bucket[action .. ":" .. tostring(token)]
    end, timeout or 6)
end

local players = waitFor(function()
    local list = Players:GetPlayers()
    if #list >= 2 then return list end
end, 20)
if not players then fail("expected_two_players") return end
local p1, p2 = players[1], players[2]

for _, player in ipairs({p1, p2}) do
    local stats = waitFor(function() return player:FindFirstChild("leaderstats") end, 10)
    if not stats then fail("missing_leaderstats") return end
    for _, name in ipairs({"Brainrot", "Collected", "Level", "Rebirths"}) do
        if not stats:FindFirstChild(name) then fail("missing_" .. name) return end
    end
    if not waitFor(function()
        local c = player.Character
        return c and c:FindFirstChild("HumanoidRootPart")
    end, 10) then fail("missing_character") return end
end

local arena = workspace:FindFirstChild("BrainrotRushArena")
if not arena then fail("missing_arena") return end
local remotes = ReplicatedStorage:FindFirstChild("BrainrotRushRemotes")
local announce = remotes and remotes:FindFirstChild("Announce")
if not announce then fail("missing_remotes") return end

local function findOrb()
    for _, child in ipairs(arena:GetChildren()) do
        if child:IsA("BasePart") and string.find(child.Name, " Brainrot", 1, true) then
            return child
        end
    end
end

local function touchWith(player, orb)
    local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
    if not root then return false end
    root.CFrame = orb.CFrame
    return waitFor(function() return orb.Parent == nil end, 4) ~= nil
end

-- 1) A pickup belongs only to the player who touches it.
local orb1 = waitFor(findOrb, 10)
if not orb1 then fail("no_orb_for_ownership") return end
local p1Collected0, p2Collected0 = p1.leaderstats.Collected.Value, p2.leaderstats.Collected.Value
if not touchWith(p1, orb1) then fail("pickup_touch_did_not_claim") return end
task.wait(0.3)
if p1.leaderstats.Collected.Value ~= p1Collected0 + 1 or p2.leaderstats.Collected.Value ~= p2Collected0 then
    fail("pickup_ownership") return
end
print("SF_MP_CHECK pickup_ownership PASS")

-- 2) Two players touching the same orb cannot double-award it.
local orb2 = waitFor(findOrb, 10)
if not orb2 then fail("no_orb_for_double_touch") return end
local beforeTotal = p1.leaderstats.Collected.Value + p2.leaderstats.Collected.Value
local r1 = p1.Character.HumanoidRootPart
local r2 = p2.Character.HumanoidRootPart
task.spawn(function() r1.CFrame = orb2.CFrame end)
task.spawn(function() r2.CFrame = orb2.CFrame end)
if not waitFor(function() return orb2.Parent == nil end, 4) then fail("double_touch_did_not_claim") return end
task.wait(0.3)
local afterTotal = p1.leaderstats.Collected.Value + p2.leaderstats.Collected.Value
if afterTotal ~= beforeTotal + 1 then fail("double_award") return end
print("SF_MP_CHECK simultaneous_touch_single_award PASS")

-- 3) Upgrade prompt changes only the player who triggers it.
p1.leaderstats.Brainrot.Value = 500
p1.leaderstats.Level.Value = 0
p2.leaderstats.Brainrot.Value = 500
p2.leaderstats.Level.Value = 0
p1.Character.HumanoidRootPart.CFrame = arena.UpgradePad.CFrame + Vector3.new(0, 3, 0)
local upgradeReply = ask(p1, "trigger_prompt", "upgrade", "UpgradePad", 8)
if not upgradeReply or not upgradeReply.ok then fail("upgrade_prompt_client:" .. tostring(upgradeReply and upgradeReply.detail)) return end
if not waitFor(function() return p1.leaderstats.Level.Value == 1 end, 4) then fail("upgrade_prompt_no_effect") return end
if p2.leaderstats.Level.Value ~= 0 or p2.leaderstats.Brainrot.Value ~= 500 then fail("upgrade_prompt_cross_player") return end
print("SF_MP_CHECK upgrade_prompt_isolation PASS")

-- 4) Rebirth prompt changes only the player who triggers it.
p1.leaderstats.Brainrot.Value = 3000
p1.leaderstats.Level.Value = 20
p1.leaderstats.Rebirths.Value = 0
local p2Brainrot, p2Level, p2Rebirths = p2.leaderstats.Brainrot.Value, p2.leaderstats.Level.Value, p2.leaderstats.Rebirths.Value
p1.Character.HumanoidRootPart.CFrame = arena.RebirthPad.CFrame + Vector3.new(0, 3, 0)
local rebirthReply = ask(p1, "trigger_prompt", "rebirth", "RebirthPad", 8)
if not rebirthReply or not rebirthReply.ok then fail("rebirth_prompt_client:" .. tostring(rebirthReply and rebirthReply.detail)) return end
if not waitFor(function() return p1.leaderstats.Rebirths.Value == 1 end, 4) then fail("rebirth_prompt_no_effect") return end
if p1.leaderstats.Brainrot.Value ~= 0 or p1.leaderstats.Level.Value ~= 0 then fail("rebirth_reset_values") return end
if p2.leaderstats.Brainrot.Value ~= p2Brainrot or p2.leaderstats.Level.Value ~= p2Level or p2.leaderstats.Rebirths.Value ~= p2Rebirths then
    fail("rebirth_prompt_cross_player") return
end
print("SF_MP_CHECK rebirth_prompt_isolation PASS")

-- 5) Player-specific announcements route to only the intended client.
local marker = "SF_TARGETED_ANNOUNCE_" .. tostring(math.floor(os.clock() * 1000))
announce:FireClient(p2, marker)
task.wait(0.25)
local a1 = ask(p1, "report_announce", marker, marker, 5)
local a2 = ask(p2, "report_announce", marker, marker, 5)
if not a1 or not a2 or not a1.ok or not a2.ok then fail("announce_probe_client") return end
if a1.detail == true or a2.detail ~= true then fail("targeted_announce_isolation") return end
print("SF_MP_CHECK targeted_announce_isolation PASS")

-- 6) One player leaving does not corrupt the remaining player's state or pickup loop.
p2:SetAttribute("Combo", 4)
local p2CollectedBeforeLeave = p2.leaderstats.Collected.Value
p1:Kick("SatisfyForge automated leave-isolation test")
if not waitFor(function() return #Players:GetPlayers() == 1 end, 8) then fail("player_leave_not_observed") return end
if p2.Parent ~= Players or p2:GetAttribute("Combo") ~= 4 then fail("remaining_player_state_after_leave") return end
local orb3 = waitFor(findOrb, 10)
if not orb3 then fail("no_orb_after_leave") return end
if not touchWith(p2, orb3) then fail("remaining_player_pickup_after_leave") return end
if not waitFor(function() return p2.leaderstats.Collected.Value == p2CollectedBeforeLeave + 1 end, 3) then
    fail("remaining_player_reward_after_leave") return
end
print("SF_MP_CHECK player_leave_isolation PASS")

print("SF_MP_SERVER_PASS players_tested=2")
StudioTestService:EndTest("PASS:multiplayer_behavior")
]==]
serverTest.Parent = ServerScriptService

local clientTest = Instance.new("LocalScript")
clientTest.Name = "SFMultiplayerClientTest"
clientTest.Source = [==[
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
if not game:IsLoaded() then game.Loaded:Wait() end
local player = Players.LocalPlayer
local channel = ReplicatedStorage:WaitForChild("SFMultiplayerTestChannel", 15)
local remotes = ReplicatedStorage:WaitForChild("BrainrotRushRemotes", 15)
local announce = remotes:WaitForChild("Announce", 15)
local seen = {}
announce.OnClientEvent:Connect(function(message)
    seen[tostring(message)] = true
end)
print("SF_MP_CLIENT_READY " .. (player and player.Name or "nil"))

channel.OnClientEvent:Connect(function(action, token, payload)
    if action == "trigger_prompt" then
        local ok, detail = pcall(function()
            local arena = workspace:WaitForChild("BrainrotRushArena", 10)
            local pad = arena:WaitForChild(tostring(payload), 10)
            local prompt = pad:FindFirstChildOfClass("ProximityPrompt")
            assert(prompt, "missing prompt")
            local character = player.Character or player.CharacterAdded:Wait()
            local root = character:WaitForChild("HumanoidRootPart", 10)
            root.CFrame = pad.CFrame + Vector3.new(0, 3, 0)
            task.wait(0.25)
            prompt:InputHoldBegin()
            task.wait(math.max(0.7, prompt.HoldDuration + 0.2))
            prompt:InputHoldEnd()
        end)
        channel:FireServer(action, token, ok, ok and "ok" or tostring(detail))
    elseif action == "report_announce" then
        channel:FireServer(action, token, true, seen[tostring(payload)] == true)
    end
end)
]==]
clientTest.Parent = StarterPlayer.StarterPlayerScripts

local ok, result = pcall(function()
    return StudioTestService:ExecuteMultiplayerTestAsync(2, "brainrot-two-player-behavior")
end)
print("SF_MP_PROBE_RESULT ok=" .. tostring(ok) .. " result=" .. tostring(result))
if not ok or result ~= "PASS:multiplayer_behavior" then
    error("multiplayer probe failed: " .. tostring(result))
end
print("SF_MP_PROBE_PASS")