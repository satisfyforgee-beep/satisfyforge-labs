-- SatisfyForge Brainrot Rush v0.3
-- Install as a Script in ServerScriptService.
-- Server-authoritative collection, upgrades, rebirths, persistence, combos, and timed Snackquake events.

local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local DataStoreService = game:GetService("DataStoreService")
local Debris = game:GetService("Debris")

local DATASTORE_NAME = "SatisfyForge_BrainrotRush_v1"
local SAVE_INTERVAL = 60
local MAX_ORBS = 34
local BASE_SPAWN_DELAY = 1.35
local COMBO_WINDOW = 8
local MAX_COMBO = 5
local SNACKQUAKE_EVERY = 90
local SNACKQUAKE_DURATION = 20

local store = DataStoreService:GetDataStore(DATASTORE_NAME)
local arena = Workspace:FindFirstChild("BrainrotRushArena") or Instance.new("Folder")
arena.Name = "BrainrotRushArena"
arena.Parent = Workspace

local remotes = ReplicatedStorage:FindFirstChild("BrainrotRushRemotes") or Instance.new("Folder")
remotes.Name = "BrainrotRushRemotes"
remotes.Parent = ReplicatedStorage
local announce = remotes:FindFirstChild("Announce") or Instance.new("RemoteEvent")
announce.Name = "Announce"
announce.Parent = remotes

local function makePart(name, size, position, color, material)
    local existing = arena:FindFirstChild(name)
    if existing then existing:Destroy() end
    local p = Instance.new("Part")
    p.Name = name
    p.Size = size
    p.Position = position
    p.Anchored = true
    p.Color = color
    p.Material = material or Enum.Material.SmoothPlastic
    p.Parent = arena
    return p
end

makePart("ArenaFloor", Vector3.new(140, 2, 140), Vector3.new(0, -1, 0), Color3.fromRGB(55, 60, 85))

local oldSpawn = arena:FindFirstChild("BrainrotSpawn")
if oldSpawn then oldSpawn:Destroy() end
local spawn = Instance.new("SpawnLocation")
spawn.Name = "BrainrotSpawn"
spawn.Size = Vector3.new(10, 1, 10)
spawn.Position = Vector3.new(0, 1, 0)
spawn.Anchored = true
spawn.Neutral = true
spawn.Parent = arena

local rarity = {
    {name = "Common", weight = 70, reward = 1, color = Color3.fromRGB(80, 239, 218)},
    {name = "Rare", weight = 23, reward = 5, color = Color3.fromRGB(83, 141, 255)},
    {name = "Epic", weight = 6, reward = 20, color = Color3.fromRGB(190, 92, 255)},
    {name = "Legendary", weight = 1, reward = 100, color = Color3.fromRGB(255, 204, 65)}
}

local rng = Random.new()
local activeOrbs = 0
local snackquakeActive = false
local lastCollectAt = {}

local function stat(parent, name, initial)
    local value = Instance.new("IntValue")
    value.Name = name
    value.Value = initial
    value.Parent = parent
    return value
end

local function upgradePrice(level)
    return 20 * (level + 1) * (level + 1)
end

local function setDerivedAttributes(player)
    local stats = player:FindFirstChild("leaderstats")
    if not stats then return end
    local level = stats:FindFirstChild("Level")
    if level then
        player:SetAttribute("NextUpgradeCost", level.Value >= 20 and 0 or upgradePrice(level.Value))
    end
    player:SetAttribute("Snackquake", snackquakeActive)
end

local function applyData(player, data)
    local stats = player:FindFirstChild("leaderstats")
    if not stats or type(data) ~= "table" then return end
    stats.Brainrot.Value = math.max(0, tonumber(data.Brainrot) or 0)
    stats.Collected.Value = math.max(0, tonumber(data.Collected) or 0)
    stats.Level.Value = math.clamp(tonumber(data.Level) or 0, 0, 20)
    stats.Rebirths.Value = math.max(0, tonumber(data.Rebirths) or 0)
end

local function savePlayer(player)
    local stats = player:FindFirstChild("leaderstats")
    if not stats then return end
    local payload = {
        Brainrot = stats.Brainrot.Value,
        Collected = stats.Collected.Value,
        Level = stats.Level.Value,
        Rebirths = stats.Rebirths.Value,
    }
    local ok, err = pcall(function()
        store:SetAsync("u_" .. player.UserId, payload)
    end)
    if not ok then
        warn("Brainrot Rush save failed for " .. player.Name .. ": " .. tostring(err))
    end
end

Players.PlayerAdded:Connect(function(player)
    local leaderstats = Instance.new("Folder")
    leaderstats.Name = "leaderstats"
    leaderstats.Parent = player
    stat(leaderstats, "Brainrot", 0)
    stat(leaderstats, "Collected", 0)
    stat(leaderstats, "Level", 0)
    stat(leaderstats, "Rebirths", 0)
    player:SetAttribute("Combo", 1)
    player:SetAttribute("Snackquake", snackquakeActive)

    local ok, data = pcall(function()
        return store:GetAsync("u_" .. player.UserId)
    end)
    if ok and data then
        applyData(player, data)
    elseif not ok then
        warn("Brainrot Rush load failed for " .. player.Name .. ": " .. tostring(data))
    end

    setDerivedAttributes(player)
    leaderstats.Level.Changed:Connect(function()
        setDerivedAttributes(player)
    end)
end)

Players.PlayerRemoving:Connect(function(player)
    savePlayer(player)
    lastCollectAt[player] = nil
end)

game:BindToClose(function()
    for _, player in ipairs(Players:GetPlayers()) do
        savePlayer(player)
    end
end)

task.spawn(function()
    while true do
        task.wait(SAVE_INTERVAL)
        for _, player in ipairs(Players:GetPlayers()) do
            savePlayer(player)
        end
    end
end)

local upgradePad = makePart("UpgradePad", Vector3.new(12, 1, 12), Vector3.new(20, 0.5, 0), Color3.fromRGB(75, 220, 105), Enum.Material.Neon)
local prompt = Instance.new("ProximityPrompt")
prompt.ActionText = "Upgrade earnings"
prompt.ObjectText = "Brainrot Shop"
prompt.HoldDuration = 0.15
prompt.MaxActivationDistance = 12
prompt.Parent = upgradePad
prompt.Triggered:Connect(function(player)
    local stats = player:FindFirstChild("leaderstats")
    if not stats then return end
    local currency, level = stats:FindFirstChild("Brainrot"), stats:FindFirstChild("Level")
    if not currency or not level or level.Value >= 20 then return end
    local cost = upgradePrice(level.Value)
    if currency.Value >= cost then
        currency.Value -= cost
        level.Value += 1
        announce:FireClient(player, "UPGRADE! Earnings level is now " .. level.Value)
    else
        announce:FireClient(player, "Need " .. (cost - currency.Value) .. " more Brainrot")
    end
end)

local rebirthPad = makePart("RebirthPad", Vector3.new(12, 1, 12), Vector3.new(-20, 0.5, 0), Color3.fromRGB(196, 72, 255), Enum.Material.Neon)
local rebirthPrompt = Instance.new("ProximityPrompt")
rebirthPrompt.ActionText = "REBIRTH (+50% permanent)"
rebirthPrompt.ObjectText = "Requires Level 20 + 2500 Brainrot"
rebirthPrompt.HoldDuration = 0.5
rebirthPrompt.MaxActivationDistance = 12
rebirthPrompt.Parent = rebirthPad
rebirthPrompt.Triggered:Connect(function(player)
    local stats = player:FindFirstChild("leaderstats")
    if not stats then return end
    if stats.Level.Value >= 20 and stats.Brainrot.Value >= 2500 then
        stats.Brainrot.Value = 0
        stats.Level.Value = 0
        stats.Rebirths.Value += 1
        player:SetAttribute("Combo", 1)
        announce:FireClient(player, "REBIRTH! Permanent earnings bonus increased.")
        savePlayer(player)
    else
        announce:FireClient(player, "Rebirth needs Level 20 and 2500 Brainrot")
    end
end)

local function pickRarity()
    local roll = rng:NextInteger(1, 100)
    local total = 0
    for _, item in ipairs(rarity) do
        total += item.weight
        if roll <= total then return item end
    end
    return rarity[1]
end

local function addBillboard(orb, item)
    local gui = Instance.new("BillboardGui")
    gui.Size = UDim2.fromOffset(120, 38)
    gui.StudsOffset = Vector3.new(0, 2.4, 0)
    gui.AlwaysOnTop = true
    gui.Parent = orb
    local label = Instance.new("TextLabel")
    label.BackgroundTransparency = 1
    label.Size = UDim2.fromScale(1, 1)
    label.Text = item.name .. " +" .. item.reward
    label.TextColor3 = Color3.new(1, 1, 1)
    label.TextStrokeTransparency = 0.35
    label.Font = Enum.Font.GothamBold
    label.TextScaled = true
    label.Parent = gui
end

local function rewardMultiplier(player)
    local stats = player:FindFirstChild("leaderstats")
    if not stats then return 1 end
    local levelMultiplier = 1 + stats.Level.Value
    local rebirthMultiplier = 1 + (stats.Rebirths.Value * 0.5)
    local combo = math.clamp(player:GetAttribute("Combo") or 1, 1, MAX_COMBO)
    local eventMultiplier = snackquakeActive and 2 or 1
    return levelMultiplier * rebirthMultiplier * combo * eventMultiplier
end

local function registerCombo(player)
    local now = os.clock()
    local previous = lastCollectAt[player]
    local combo = player:GetAttribute("Combo") or 1
    if previous and (now - previous) <= COMBO_WINDOW then
        combo = math.min(MAX_COMBO, combo + 1)
    else
        combo = 1
    end
    lastCollectAt[player] = now
    player:SetAttribute("Combo", combo)
end

local function spawnOrb()
    local item = pickRarity()
    local orb = Instance.new("Part")
    orb.Name = item.name .. " Brainrot"
    orb.Shape = Enum.PartType.Ball
    orb.Material = Enum.Material.Neon
    orb.Size = item.name == "Legendary" and Vector3.new(4.5, 4.5, 4.5) or Vector3.new(3, 3, 3)
    orb.Anchored = true
    orb.CanCollide = false
    orb.Position = Vector3.new(rng:NextInteger(-62, 62), 3, rng:NextInteger(-62, 62))
    orb.Color = item.color
    orb.Parent = arena
    addBillboard(orb, item)
    activeOrbs += 1

    local claimed = false
    orb.Touched:Connect(function(hit)
        if claimed then return end
        local character = hit:FindFirstAncestorOfClass("Model")
        local player = character and Players:GetPlayerFromCharacter(character)
        if not player then return end
        local stats = player:FindFirstChild("leaderstats")
        if not stats then return end
        claimed = true
        registerCombo(player)
        local payout = math.max(1, math.floor(item.reward * rewardMultiplier(player)))
        stats.Brainrot.Value += payout
        stats.Collected.Value += 1
        if item.name == "Legendary" then
            announce:FireAllClients(player.DisplayName .. " found LEGENDARY Brainrot! +" .. payout)
        end
        orb:Destroy()
    end)

    orb.Destroying:Connect(function()
        activeOrbs = math.max(0, activeOrbs - 1)
    end)
    Debris:AddItem(orb, snackquakeActive and 25 or 45)
end

task.spawn(function()
    while true do
        task.wait(SNACKQUAKE_EVERY)
        snackquakeActive = true
        for _, player in ipairs(Players:GetPlayers()) do
            player:SetAttribute("Snackquake", true)
        end
        announce:FireAllClients("SNACKQUAKE! 2X rewards + faster spawns for " .. SNACKQUAKE_DURATION .. " seconds!")
        task.wait(SNACKQUAKE_DURATION)
        snackquakeActive = false
        for _, player in ipairs(Players:GetPlayers()) do
            player:SetAttribute("Snackquake", false)
        end
        announce:FireAllClients("Snackquake ended. Keep the combo alive!")
    end
end)

while true do
    if activeOrbs < MAX_ORBS then
        spawnOrb()
    end
    task.wait(snackquakeActive and 0.55 or BASE_SPAWN_DELAY)
end
