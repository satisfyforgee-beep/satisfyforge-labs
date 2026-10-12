-- SatisfyForge Brainrot Rush v0.3 client HUD
-- Install as a LocalScript in StarterPlayer > StarterPlayerScripts.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")

local player = Players.LocalPlayer
local remotes = ReplicatedStorage:WaitForChild("BrainrotRushRemotes")
local announce = remotes:WaitForChild("Announce")

local gui = Instance.new("ScreenGui")
gui.Name = "BrainrotRushHUD"
gui.ResetOnSpawn = false
gui.IgnoreGuiInset = false
gui.Parent = player:WaitForChild("PlayerGui")

local top = Instance.new("Frame")
top.Name = "TopBar"
top.AnchorPoint = Vector2.new(0.5, 0)
top.Position = UDim2.fromScale(0.5, 0.02)
top.Size = UDim2.new(0.92, 0, 0, 72)
top.BackgroundColor3 = Color3.fromRGB(25, 27, 38)
top.BackgroundTransparency = 0.08
top.Parent = gui

local topCorner = Instance.new("UICorner")
topCorner.CornerRadius = UDim.new(0, 18)
topCorner.Parent = top

local grid = Instance.new("UIGridLayout")
grid.CellPadding = UDim2.fromOffset(5, 5)
grid.CellSize = UDim2.new(0.2, -4, 1, -10)
grid.HorizontalAlignment = Enum.HorizontalAlignment.Center
grid.VerticalAlignment = Enum.VerticalAlignment.Center
grid.Parent = top

local labels = {}
local function makeStatLabel(key)
    local label = Instance.new("TextLabel")
    label.Name = key
    label.BackgroundColor3 = Color3.fromRGB(39, 42, 58)
    label.TextColor3 = Color3.new(1, 1, 1)
    label.Font = Enum.Font.GothamBold
    label.TextScaled = true
    label.TextWrapped = true
    label.Parent = top
    local corner = Instance.new("UICorner")
    corner.CornerRadius = UDim.new(0, 12)
    corner.Parent = label
    labels[key] = label
end

for _, key in ipairs({"Brainrot", "Level", "Collected", "Rebirths", "Combo"}) do
    makeStatLabel(key)
end

local banner = Instance.new("TextLabel")
banner.Name = "Banner"
banner.AnchorPoint = Vector2.new(0.5, 0)
banner.Position = UDim2.fromScale(0.5, 0.14)
banner.Size = UDim2.new(0.88, 0, 0, 54)
banner.BackgroundColor3 = Color3.fromRGB(134, 49, 202)
banner.BackgroundTransparency = 0.08
banner.TextColor3 = Color3.new(1, 1, 1)
banner.TextStrokeTransparency = 0.5
banner.Font = Enum.Font.GothamBlack
banner.TextScaled = true
banner.TextWrapped = true
banner.Visible = false
banner.Parent = gui

local bannerCorner = Instance.new("UICorner")
bannerCorner.CornerRadius = UDim.new(0, 16)
bannerCorner.Parent = banner

local hint = Instance.new("TextLabel")
hint.AnchorPoint = Vector2.new(0.5, 1)
hint.Position = UDim2.fromScale(0.5, 0.965)
hint.Size = UDim2.new(0.9, 0, 0, 45)
hint.BackgroundColor3 = Color3.fromRGB(25, 27, 38)
hint.BackgroundTransparency = 0.18
hint.TextColor3 = Color3.new(1, 1, 1)
hint.Font = Enum.Font.GothamSemibold
hint.TextScaled = true
hint.TextWrapped = true
hint.Text = "Collect glowing Brainrot • Green pad = Upgrade • Purple pad = Rebirth"
hint.Parent = gui
local hintCorner = Instance.new("UICorner")
hintCorner.CornerRadius = UDim.new(0, 14)
hintCorner.Parent = hint

local function update()
    local stats = player:FindFirstChild("leaderstats")
    if not stats then return end
    labels.Brainrot.Text = "🧠 " .. tostring(stats.Brainrot.Value)
    labels.Level.Text = "LV " .. tostring(stats.Level.Value)
    labels.Collected.Text = "GET " .. tostring(stats.Collected.Value)
    labels.Rebirths.Text = "♻ " .. tostring(stats.Rebirths.Value)
    labels.Combo.Text = "x" .. tostring(player:GetAttribute("Combo") or 1)

    if player:GetAttribute("Snackquake") then
        labels.Combo.Text = "🔥 x" .. tostring(player:GetAttribute("Combo") or 1)
    end
end

local function connectStats()
    local stats = player:WaitForChild("leaderstats")
    for _, child in ipairs(stats:GetChildren()) do
        if child:IsA("ValueBase") then
            child.Changed:Connect(update)
        end
    end
    stats.ChildAdded:Connect(function(child)
        if child:IsA("ValueBase") then
            child.Changed:Connect(update)
            update()
        end
    end)
    player:GetAttributeChangedSignal("Combo"):Connect(update)
    player:GetAttributeChangedSignal("Snackquake"):Connect(update)
    update()
end

task.spawn(connectStats)

local bannerToken = 0
announce.OnClientEvent:Connect(function(message)
    bannerToken += 1
    local token = bannerToken
    banner.Text = tostring(message)
    banner.TextTransparency = 1
    banner.BackgroundTransparency = 1
    banner.Visible = true
    TweenService:Create(banner, TweenInfo.new(0.18), {
        TextTransparency = 0,
        BackgroundTransparency = 0.08,
    }):Play()
    task.delay(3.5, function()
        if token ~= bannerToken then return end
        local tween = TweenService:Create(banner, TweenInfo.new(0.25), {
            TextTransparency = 1,
            BackgroundTransparency = 1,
        })
        tween:Play()
        tween.Completed:Wait()
        if token == bannerToken then banner.Visible = false end
    end)
end)
