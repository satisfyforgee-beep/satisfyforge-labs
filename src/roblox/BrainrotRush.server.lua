-- SatisfyForge Brainrot Rush v0.2
-- Install as a Script in ServerScriptService. Server-authoritative collectible and upgrade loop.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local Debris = game:GetService("Debris")
local arena = Workspace:FindFirstChild("BrainrotRushArena") or Instance.new("Folder")
arena.Name = "BrainrotRushArena"
arena.Parent = Workspace

local function makePart(name, size, position, color)
    local p = Instance.new("Part")
    p.Name, p.Size, p.Position = name, size, position
    p.Anchored = true
    p.Color = color
    p.Parent = arena
    return p
end

makePart("ArenaFloor", Vector3.new(140, 2, 140), Vector3.new(0, -1, 0), Color3.fromRGB(55, 60, 85))
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
local MAX_ORBS = 30
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

Players.PlayerAdded:Connect(function(player)
    local leaderstats = Instance.new("Folder")
    leaderstats.Name = "leaderstats"
    leaderstats.Parent = player
    stat(leaderstats, "Brainrot", 0)
    stat(leaderstats, "Collected", 0)
    stat(leaderstats, "Level", 0)
end)

local upgradePad = makePart("UpgradePad", Vector3.new(12, 1, 12), Vector3.new(20, 0.5, 0), Color3.fromRGB(75, 220, 105))
local prompt = Instance.new("ProximityPrompt")
prompt.ActionText = "Upgrade earnings"
prompt.ObjectText = "Brainrot Shop"
prompt.HoldDuration = 0.3
prompt.MaxActivationDistance = 12
prompt.Parent = upgradePad
prompt.Triggered:Connect(function(player)
    local stats = player:FindFirstChild("leaderstats")
    if not stats then return end
    local currency = stats:FindFirstChild("Brainrot")
    local level = stats:FindFirstChild("Level")
    if not currency or not level or level.Value >= 20 then return end
    local cost = upgradePrice(level.Value)
    if currency.Value >= cost then
        currency.Value -= cost
        level.Value += 1
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

local function spawnOrb()
    local item = pickRarity()
    local orb = Instance.new("Part")
    orb.Name = item.name .. " Brainrot"
    orb.Shape = Enum.PartType.Ball
    orb.Material = Enum.Material.Neon
    orb.Size = Vector3.new(3, 3, 3)
    orb.Anchored = true
    orb.CanCollide = false
    orb.Position = Vector3.new(rng:NextInteger(-62, 62), 3, rng:NextInteger(-62, 62))
    orb.Color = item.color
    orb.Parent = arena
    activeOrbs += 1
    local claimed = false
    orb.Touched:Connect(function(hit)
        if claimed then return end
        local character = hit:FindFirstAncestorOfClass("Model")
        local player = character and Players:GetPlayerFromCharacter(character)
        if not player then return end
        local stats = player:FindFirstChild("leaderstats")
        local currency = stats and stats:FindFirstChild("Brainrot")
        local collected = stats and stats:FindFirstChild("Collected")
        local level = stats and stats:FindFirstChild("Level")
        if not currency or not collected or not level then return end
        claimed = true
        currency.Value += item.reward * (1 + level.Value)
        collected.Value += 1
        orb:Destroy()
    end)
    orb.Destroying:Connect(function()
        activeOrbs = math.max(0, activeOrbs - 1)
    end)
    Debris:AddItem(orb, 45)
end

while true do
    if activeOrbs < MAX_ORBS then spawnOrb() end
    task.wait(1.5)
end
