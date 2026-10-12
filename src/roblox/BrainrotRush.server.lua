-- SatisfyForge Brainrot Rush: prototype server script
-- Place in ServerScriptService in Roblox Studio.
local Players = game:GetService("Players")
local Workspace = game:GetService("Workspace")
local Debris = game:GetService("Debris")
local arena = Instance.new("Folder")
arena.Name = "BrainrotRushArena"
arena.Parent = Workspace
local base = Instance.new("Part")
base.Name = "ArenaFloor"
base.Size = Vector3.new(140, 2, 140)
base.Position = Vector3.new(0, -1, 0)
base.Anchored = true
base.Color = Color3.fromRGB(55, 60, 85)
base.Parent = arena
local spawn = Instance.new("SpawnLocation")
spawn.Name = "BrainrotSpawn"
spawn.Size = Vector3.new(10, 1, 10)
spawn.Position = Vector3.new(0, 1, 0)
spawn.Anchored = true
spawn.Neutral = true
spawn.Parent = arena
Players.PlayerAdded:Connect(function(player)
    local leaderstats = Instance.new("Folder")
    leaderstats.Name = "leaderstats"
    leaderstats.Parent = player
    local points = Instance.new("IntValue")
    points.Name = "Brainrot"
    points.Value = 0
    points.Parent = leaderstats
end)
local colors = {
    Color3.fromRGB(255, 83, 131),
    Color3.fromRGB(80, 239, 218),
    Color3.fromRGB(255, 221, 87)
}
local function spawnCollectible()
    local orb = Instance.new("Part")
    orb.Name = "BrainrotOrb"
    orb.Shape = Enum.PartType.Ball
    orb.Material = Enum.Material.Neon
    orb.Size = Vector3.new(3, 3, 3)
    orb.Anchored = true
    orb.CanCollide = false
    orb.Position = Vector3.new(math.random(-62, 62), 3, math.random(-62, 62))
    orb.Color = colors[math.random(1, #colors)]
    orb.Parent = arena
    local claimed = false
    orb.Touched:Connect(function(hit)
        if claimed then return end
        local character = hit:FindFirstAncestorOfClass("Model")
        local player = character and Players:GetPlayerFromCharacter(character)
        if not player then return end
        claimed = true
        local score = player:FindFirstChild("leaderstats")
        local value = score and score:FindFirstChild("Brainrot")
        if value then value.Value += 1 end
        orb:Destroy()
    end)
    Debris:AddItem(orb, 45)
end
while true do
    if #arena:GetChildren() < 38 then
        spawnCollectible()
    end
    task.wait(1.5)
end
